#!/usr/bin/env python3
"""Cache-collision audit for the 85 synthetic negatives -- COMPUTED, not hardcoded.

    .venv/bin/python current/negatives_cache_audit.py            # full report
    .venv/bin/python current/negatives_cache_audit.py --selftest  # evidence checks

Offline, zero model calls, ~1 s.

WHY THIS FILE EXISTS
--------------------
Two other files carried hand-written lists of affected claim_ids
(`negatives_to_verifier_schema.CACHE_CORRUPT`, `rq2_quantitative_table.DUP_READ`).
Hand-written lists are what went wrong: three successive audits produced "12",
then "15", then this file's 16, because each hardcoded what the previous one had
found instead of recomputing it. Both now import from here.

THE BUG BEING AUDITED
---------------------
`archive/scripts/relational_verifier_phase3d.py:194` keys its NLI cache as

    nli__{claim[:60]}__{passage[:40]}

Truncating the claim at 60 characters means two claims that differ only past
character 60 share a cache entry. Synthetic negatives are perturbations of real
claims -- near-identical to their originals BY CONSTRUCTION -- so a changed
number sitting past character 60 collides with the original. The collision rate
here is structural, not incidental. (On the natural 356 the same key touches
~2.2% of rows and moves nothing by more than 0.67pp.)

THREE DISTINCT HARMS. They must not be pooled, because the correct remedy
differs and two of them move results in opposite directions.

  (a) FULL INHERITANCE -- both entail and contradict bit-identical to the base
      claim's, same claim[:60]. The row never received an NLI call of its own;
      it read the answer computed for a DIFFERENT claim. The verdict is
      fabricated. Remedy: EXCLUDE the row.

  (b) DUPLICATE READ -- two negatives share a key with each other and carry
      identical scores. Each verdict is a real NLI answer, but one answer was
      counted more than once. The rows are not wrong, they are not
      INDEPENDENT. Remedy: DISCOUNT all but one per identical group, i.e.
      reduce effective n without deleting evidence.

  (c) PARTIAL INHERITANCE -- entail bit-identical to the base, contradict not.
      The key is keyed on claim AND passage, so a row can inherit the cached
      answer for the passages that overlap and compute the rest fresh. This is
      the subtle one, and it was missed by the first two audits entirely.
      It matters because the 3d rule tests entail FIRST:

          entail >= et -> TRUE ; elif contradict >= ct -> FALSE ; else UNVERIFIABLE

      so the inherited half is the half that fires TRUE. Remedy: report which
      half actually decided each verdict, and offer a strict tier that drops
      them.

EVIDENCE STANDARD
-----------------
Bit-identical float STRINGS, compared as text, never as parsed floats -- 17
significant figures do not agree by chance. Every class is reported alongside a
CONTROL: rows whose keys do NOT collide, checked for the same score agreement.
If a control is non-zero the signal means nothing and `--selftest` fails.
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

NEG_RESULTS = "current/nonrouted_negatives_results.csv"
NAT_RESULTS = "current/nonrouted_baseline_results.csv"
NEG_SOURCE = "current/synthetic_negatives.csv"

# phase3d's thresholds, for reporting which half decided a verdict.
SHIPPED = (0.50, 0.40)
TUNED = (0.35, 0.30)


def _load(rel: str) -> list[dict]:
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def claim_key(claim: str) -> str:
    """Exactly phase3d's claim-side cache key component. Do not 'improve' this.

    It must reproduce the buggy behaviour being audited, not a corrected
    version of it -- an audit that keys correctly finds no collisions.
    """
    return claim[:60].replace(" ", "_")


def _scores(row: dict) -> tuple[str, str]:
    """Raw strings. Parsing to float would discard the bit-identity evidence."""
    return (row.get("entail") or "", row.get("contradict") or "")


class Audit:
    """The three collision classes, computed from the artifacts."""

    def __init__(self) -> None:
        self.neg = _load(NEG_RESULTS)
        self.nat = {r["claim_id"]: r for r in _load(NAT_RESULTS)}
        self.src = {r["claim_id"]: r for r in _load(NEG_SOURCE)}

        self.fabricated: dict[str, str] = {}   # claim_id -> base claim_id
        self.partial: dict[str, str] = {}      # claim_id -> base claim_id
        self.duplicate: set[str] = set()
        self.dup_groups: list[list[dict]] = []

        # Controls: the same agreement pattern among rows whose keys do NOT
        # collide. Both must come out 0 or the evidence is worthless.
        self.control_full = 0
        self.control_partial = 0
        self.control_n = 0

        self._find_inheritance()
        self._find_duplicates()

    # -- class (a) and (c): a negative vs the claim it was perturbed from ----
    def _find_inheritance(self) -> None:
        for r in self.neg:
            base_id = self.src.get(r["claim_id"], {}).get("base_claim_id", "")
            base = self.nat.get(base_id)
            if not base:
                continue
            same_key = claim_key(r["claim"]) == claim_key(base["claim"])
            e_match = bool(r.get("entail")) and r.get("entail") == base.get("entail")
            c_match = r.get("contradict") == base.get("contradict")

            if same_key and e_match and c_match:
                self.fabricated[r["claim_id"]] = base_id
            elif same_key and e_match and not c_match:
                self.partial[r["claim_id"]] = base_id
            else:
                self.control_n += 1
                if e_match and c_match:
                    self.control_full += 1
                elif e_match:
                    self.control_partial += 1

    # -- class (b): a negative vs another negative --------------------------
    def _find_duplicates(self) -> None:
        groups: dict[str, list[dict]] = collections.defaultdict(list)
        for r in self.neg:
            groups[claim_key(r["claim"])].append(r)
        for _, members in sorted(groups.items()):
            if len(members) < 2:
                continue
            self.dup_groups.append(members)
            buckets: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
            for r in members:
                buckets[_scores(r)].append(r)
            for _, rows in buckets.items():
                # Keep the first, discount the rest: one real answer, one vote.
                for r in rows[1:]:
                    self.duplicate.add(r["claim_id"])

    # -- tiers ---------------------------------------------------------------
    def tier(self, name: str, rows: list[dict] | None = None) -> list[dict]:
        """Successively stricter row sets.

        raw    every row as recorded
        clean  minus (a): fabricated verdicts removed
        indep  minus (a) and (b): one vote per real NLI answer
        strict minus (a), (b) and (c): no row whose entail was inherited
        """
        rows = self.neg if rows is None else rows
        if name == "raw":
            return list(rows)
        out = [r for r in rows if r["claim_id"] not in self.fabricated]
        if name == "clean":
            return out
        out = [r for r in out if r["claim_id"] not in self.duplicate]
        if name == "indep":
            return out
        if name == "strict":
            return [r for r in out if r["claim_id"] not in self.partial]
        raise ValueError(f"unknown tier {name!r}")

    @property
    def affected(self) -> set[str]:
        return set(self.fabricated) | set(self.duplicate) | set(self.partial)


TIERS = ("raw", "clean", "indep", "strict")


def _rate(rows: list[dict]) -> str:
    if not rows:
        return "    n=0    "
    det = sum(1 for r in rows if r["verdict"] == "FALSE")
    return f"{det:>2}/{len(rows):<2} {100 * det / len(rows):>5.1f}%"


def _decided_by(row: dict, et: float, ct: float) -> str:
    """Which half of the 3d rule produced this verdict."""
    try:
        e = float(row.get("entail") or 0.0)
        c = float(row.get("contradict") or 0.0)
    except ValueError:
        return "unparseable"
    if e >= et:
        return "entail (INHERITED half)"
    if c >= ct:
        return "contradict (fresh half)"
    return "neither cleared (both halves)"


def report(a: Audit) -> None:
    print("=" * 78)
    print("SYNTHETIC NEGATIVES -- cache-collision audit")
    print("=" * 78)
    by_type = collections.Counter(r["type"] for r in a.neg)
    print(f"rows: {len(a.neg)}   "
          f"gold: {dict(collections.Counter(r['gold_verdict'] for r in a.neg))}")
    print("  " + "   ".join(f"{t} {n}" for t, n in sorted(by_type.items(),
                                                          key=lambda kv: -kv[1])))
    print()

    print("-" * 78)
    print(f"(a) FULL INHERITANCE -- verdict fabricated, EXCLUDE   "
          f"[{len(a.fabricated)} rows]")
    print("-" * 78)
    for cid in sorted(a.fabricated):
        r = next(x for x in a.neg if x["claim_id"] == cid)
        base = a.nat[a.fabricated[cid]]
        print(f"  {cid:<14} {r['type']:<14} base={a.fabricated[cid]:<9} "
              f"e={r['entail']:<7} c={r['contradict']:<7} "
              f"3d={r['verdict']:<12} base_gold={base['gold_verdict']}")
    print(f"  CONTROL non-colliding rows matching base on BOTH: "
          f"{a.control_full}/{a.control_n}   (must be 0)")
    print()

    print("-" * 78)
    print(f"(b) DUPLICATE READ -- real but not independent, DISCOUNT   "
          f"[{len(a.duplicate)} rows]")
    print("-" * 78)
    for members in a.dup_groups:
        buckets: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
        for r in members:
            buckets[_scores(r)].append(r)
        print(f"  {len(members)} rows share a key -> {len(buckets)} distinct "
              f"score-pair(s)   [{members[0]['type']}]")
        for rows in buckets.values():
            for r in rows:
                tag = "  <- discount" if r["claim_id"] in a.duplicate else ""
                print(f"    {r['claim_id']:<14} e={r['entail']:<7} "
                      f"c={r['contradict']:<7} 3d={r['verdict']:<12}{tag}")
    print()

    print("-" * 78)
    print(f"(c) PARTIAL INHERITANCE -- entail inherited, contradict fresh   "
          f"[{len(a.partial)} rows]")
    print("-" * 78)
    print("  The 3d rule tests entail FIRST, so the inherited half is the half")
    print("  that fires TRUE. Which half actually decided each verdict:")
    for cid in sorted(a.partial):
        r = next(x for x in a.neg if x["claim_id"] == cid)
        print(f"  {cid:<14} {r['type']:<14} base={a.partial[cid]:<9} "
              f"e={r['entail']:<7} c={r['contradict']:<7} 3d={r['verdict']}")
        print(f"    @shipped {SHIPPED}: {_decided_by(r, *SHIPPED)}")
        print(f"    @tuned   {TUNED}: {_decided_by(r, *TUNED)}")
    print(f"  CONTROL non-colliding rows matching base on entail only: "
          f"{a.control_partial}/{a.control_n}   (must be 0)")
    print()

    print("=" * 78)
    print("BASELINE DETECTION RATE ON GOLD-FALSE NEGATIVES, per type and tier")
    print("=" * 78)
    print("  every row is gold FALSE, so 'detection' = the baseline said FALSE")
    print()
    print(f"  {'type':<18} " + " ".join(f"{t:>12}" for t in TIERS))
    print("  " + "-" * 68)
    for t in sorted(by_type):
        rows = [r for r in a.neg if r["type"] == t]
        cells = [_rate(a.tier(k, rows)) for k in TIERS]
        print(f"  {t:<18} " + " ".join(f"{c:>12}" for c in cells))
    print("  " + "-" * 68)
    print(f"  {'ALL':<18} " + " ".join(f"{_rate(a.tier(k)):>12}" for k in TIERS))
    print()
    print(f"collision-affected rows: {len(a.affected)} of {len(a.neg)} "
          f"= {100 * len(a.affected) / len(a.neg):.1f}%")
    print(f"  (a) fabricated {len(a.fabricated):>2}  "
          f"(b) duplicate {len(a.duplicate):>2}  "
          f"(c) partial {len(a.partial):>2}   "
          f"union {len(a.affected)} (the classes overlap)")
    print()
    print("Per-type note: QUANTITATIVE is untouched by class (c), so the")
    print("2026-08-25 RQ2 QUANTITATIVE figures stand unchanged.")
    print()
    _paired(a)


def _paired(a: Audit) -> None:
    """Detection rate is meaningless on an all-FALSE set unless paired with FPR.

    Every one of the 85 negatives is gold FALSE, so an unconditional "FALSE"
    detects 100% of them. A 53.6% detection rate therefore says nothing on its
    own -- it is WORSE than the degenerate strategy, exactly as 87.9% accuracy
    on the natural 356 is worse than an unconditional "TRUE". Same trap, mirrored.

    The pairing that does mean something: detection rate on the negatives (TPR)
    against false-alarm rate on the natural set's gold-TRUE claims (FPR). Both
    come from the same code path at the same operating point, so the difference
    is discrimination. TPR - FPR is Youden's J, which is 0 for every degenerate
    strategy in both directions -- the same property that makes MCC the safe
    metric in the RQ2 tables.
    """
    nat = _load(NAT_RESULTS)
    print("=" * 78)
    print("PAIRED: detection on negatives (TPR) vs false alarms on gold-TRUE (FPR)")
    print("=" * 78)
    print("  negatives are 100% gold FALSE, so an unconditional FALSE scores")
    print("  TPR 1.00 -- the detection column above is uninterpretable alone.")
    print("  Youden's J = TPR - FPR is 0 for Always-True AND Always-False.")
    print("  Rows use the `type` column (what the verifier receives), per the")
    print("  standing rule to say which column a per-type count came from.")
    print()
    print(f"  {'type':<18} {'TPR (strict neg)':>18} {'FPR (gold-TRUE)':>18} {'J':>8}")
    print("  " + "-" * 66)
    strict = a.tier("strict")
    for t in sorted({r["type"] for r in a.neg}):
        neg_rows = [r for r in strict if r["type"] == t]
        pos_rows = [r for r in nat
                    if r.get("type") == t and r.get("gold_verdict") == "TRUE"]
        if not neg_rows or not pos_rows:
            continue
        tp = sum(1 for r in neg_rows if r["verdict"] == "FALSE")
        fp = sum(1 for r in pos_rows if r["verdict"] == "FALSE")
        tpr, fpr = tp / len(neg_rows), fp / len(pos_rows)
        print(f"  {t:<18} {f'{tp}/{len(neg_rows)}  {100*tpr:5.1f}%':>18} "
              f"{f'{fp}/{len(pos_rows)}  {100*fpr:5.1f}%':>18} "
              f"{tpr - fpr:>+8.3f}")
    neg_all, pos_all = strict, [r for r in nat if r.get("gold_verdict") == "TRUE"]
    tp = sum(1 for r in neg_all if r["verdict"] == "FALSE")
    fp = sum(1 for r in pos_all if r["verdict"] == "FALSE")
    tpr, fpr = tp / len(neg_all), fp / len(pos_all)
    print("  " + "-" * 66)
    print(f"  {'ALL':<18} {f'{tp}/{len(neg_all)}  {100*tpr:5.1f}%':>18} "
          f"{f'{fp}/{len(pos_all)}  {100*fpr:5.1f}%':>18} {tpr - fpr:>+8.3f}")
    _prior_decomposition(nat, tpr, fpr)


def _prior_decomposition(nat: list[dict], tpr: float, fpr: float) -> None:
    """Is the baseline's 0.099 precision evidence of no discrimination, or of a
    low base rate? These are different claims and the project has conflated them.

    CLAUDE.md currently records two findings that sit in tension:

      * "Of 81 FALSE predictions, 8 are correct -- precision 0.099. Uniform
        retrieval+NLI manufactures hallucination alarms at ~9:1. This is the
        strongest empirical motivation for the taxonomy the project has."
      * "contradiction precision never leaves 0.08-0.12 across the whole sweep
        and caps at 0.20 over all 225 grid points ... cannot separate 'refutes
        this' from 'does not mention this' at ANY operating point."

    Both are measurements of PRECISION, which depends on the class prior. The
    natural 356 is 3.7% gold-FALSE. Precision at a fixed TPR/FPR is

        P = (pi * TPR) / (pi * TPR + (1 - pi) * FPR)

    so if the measured TPR/FPR reproduce the observed precision, then the low
    precision is explained by pi alone and is NOT evidence that the detector
    cannot separate the classes. That is a materially weaker claim than the one
    on record, and it has to be checked rather than assumed in either direction.
    """
    gold = [r.get("gold_verdict") for r in nat]
    n_false = sum(1 for g in gold if g == "FALSE")
    pi = n_false / len(gold)
    pred = (pi * tpr) / (pi * tpr + (1 - pi) * fpr) if (pi * tpr + (1 - pi) * fpr) else 0.0

    obs_tp = sum(1 for r in nat
                 if r["verdict"] == "FALSE" and r.get("gold_verdict") == "FALSE")
    obs_fp = sum(1 for r in nat
                 if r["verdict"] == "FALSE" and r.get("gold_verdict") != "FALSE")
    obs = obs_tp / (obs_tp + obs_fp) if (obs_tp + obs_fp) else 0.0

    print()
    print("=" * 78)
    print("IS THE LOW PRECISION A PRIOR ARTIFACT? -- decomposition")
    print("=" * 78)
    print(f"  natural set base rate pi(FALSE)     = {n_false}/{len(gold)} = {pi:.4f}")
    print(f"  TPR measured on synthetic negatives = {tpr:.4f}")
    print(f"  FPR measured on natural gold-TRUE   = {fpr:.4f}")
    print(f"  => precision PREDICTED at that pi   = {pred:.4f}")
    print(f"     precision OBSERVED on natural    = "
          f"{obs_tp}/{obs_tp + obs_fp} = {obs:.4f}")
    print(f"     gap                              = {abs(pred - obs):.4f}")
    print()
    if abs(pred - obs) < 0.05:
        print("  The observed precision is REPRODUCED by the base rate alone.")
        print("  Consequence: 'precision 0.099' and 'alarms at ~9:1' are")
        print("  statements about the 3.7% base rate, NOT evidence that")
        print("  retrieval+NLI cannot separate the classes. Youden's J is")
        print(f"  {tpr - fpr:+.3f}, which is not zero. The stronger claim on")
        print("  record -- 'cannot separate at any operating point' -- is not")
        print("  supported by a precision measurement and needs correcting.")
    else:
        print("  The base rate does NOT reproduce the observed precision, so")
        print("  something beyond the prior is depressing it. The 'cannot")
        print("  separate' reading survives this check.")
    print()
    print(f"  For reference, precision at a BALANCED prior would be "
          f"{tpr / (tpr + fpr):.3f}.")
    print("  CAVEAT that limits how far this generalises: the negatives are")
    print("  SYNTHETIC perturbations (a swapped number or date), which are")
    print("  plausibly easier to refute than a naturally-hallucinated causal")
    print("  claim. So this TPR is an UPPER estimate of discrimination on real")
    print("  hallucinations, and J is an upper bound, not a point estimate.")


def selftest(a: Audit) -> int:
    """Enforce the evidence standard in code, not in a comment."""
    fails = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal fails
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
        if not ok:
            fails += 1

    print("selftest")
    check("negatives load", len(a.neg) == 85, f"n={len(a.neg)}")
    check("all negatives are gold FALSE",
          all(r["gold_verdict"] == "FALSE" for r in a.neg))
    check("every negative has a locatable base row",
          all(a.nat.get(a.src.get(r["claim_id"], {}).get("base_claim_id", ""))
              for r in a.neg))
    check("CONTROL: no non-colliding row matches base on both scores",
          a.control_full == 0, f"{a.control_full}/{a.control_n}")
    check("CONTROL: no non-colliding row matches base on entail alone",
          a.control_partial == 0, f"{a.control_partial}/{a.control_n}")
    check("classes (a) and (c) are disjoint by construction",
          not (set(a.fabricated) & set(a.partial)))
    check("tiers are monotonically non-increasing",
          all(len(a.tier(TIERS[i])) >= len(a.tier(TIERS[i + 1]))
              for i in range(len(TIERS) - 1)),
          " >= ".join(str(len(a.tier(t))) for t in TIERS))
    check("every colliding row really shares its base's claim[:60]",
          all(claim_key(next(x for x in a.neg if x["claim_id"] == cid)["claim"])
              == claim_key(a.nat[b]["claim"])
              for cid, b in {**a.fabricated, **a.partial}.items()))

    # The two hardcoded sets this file replaces must reproduce exactly, or the
    # refactor silently changed a published number.
    legacy_corrupt = {
        "SYN_QUAN_027", "SYN_QUAN_028", "SYN_QUAN_032", "SYN_QUAN_033",
        "SYN_QUAN_034", "SYN_QUAN_035", "SYN_QUAN_036", "SYN_QUAN_037",
        "SYN_QUAN_038", "SYN_TEMP_056", "SYN_TEMP_057", "SYN_TEMP_058",
    }
    check("reproduces the legacy 12-row CACHE_CORRUPT set exactly",
          set(a.fabricated) == legacy_corrupt,
          f"diff={sorted(set(a.fabricated) ^ legacy_corrupt)}")
    quan_clean = [r for r in a.tier("clean") if r["type"] == "QUANTITATIVE"]
    quan_dup = {r["claim_id"] for r in quan_clean if r["claim_id"] in a.duplicate}
    check("reproduces the legacy DUP_READ set on clean QUANTITATIVE",
          quan_dup == {"SYN_QUAN_031"}, f"got={sorted(quan_dup)}")
    check("published QUANTITATIVE independent n is still 14",
          len([r for r in a.tier("indep") if r["type"] == "QUANTITATIVE"]) == 14)
    check("QUANTITATIVE untouched by class (c)",
          not any(r["type"] == "QUANTITATIVE" for r in a.neg
                  if r["claim_id"] in a.partial))

    print(f"\n{'ALL PASS' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true",
                    help="enforce the evidence standard and the legacy-set match")
    args = ap.parse_args()
    a = Audit()
    if args.selftest:
        return selftest(a)
    report(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
