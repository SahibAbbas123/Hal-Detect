#!/usr/bin/env python3
"""Exact McNemar for RQ2: is routed-vs-baseline a difference or a coincidence?

WHY THIS SCRIPT EXISTS
----------------------
Every routed-vs-baseline figure in this project is a point estimate with a Wilson
interval on each arm separately. That is the wrong tool for the comparison being
made. The two systems are run on THE SAME CLAIMS, so their errors are paired and
the arms are not independent -- two overlapping intervals do not tell you the
systems differ, and two disjoint ones overstate how much. McNemar's test is the
paired test, and it uses only the claims where the two systems DISAGREE.

The project already knew the headline answer and recorded it as a prediction:
`CLAIM.md` #22 says the 4-0 disagreement table gives p = 0.125, not significant,
"so this will likely make a quoted claim weaker. Do it anyway." That prediction is
confirmed below. But the useful finding is not the 0.125.

THE USEFUL FINDING: A POWER FLOOR, NOT A NEGATIVE RESULT
--------------------------------------------------------
With n discordant pairs the smallest two-sided p the exact test can EVER return is
2 / 2**n, reached only when every discordant pair falls the same way. So:

    n = 4  ->  min possible p = 0.1250     significance unreachable
    n = 5  ->  min possible p = 0.0625     significance unreachable
    n = 6  ->  min possible p = 0.0312     reachable

At n = 4 the result is not "not significant". It is INCAPABLE of significance: a
perfect 4-0 sweep is the most extreme outcome the design admits and it still
returns 0.125. That converts a weak-looking p into a statement about corpus size,
which is the constraint CLAUDE.md already names as binding ("14 gold negatives
across the natural 356 is the binding constraint on every detection claim").
Report the floor beside the p, always -- a reader who sees only p = 0.125 will
conclude the systems are similar, which is not what the data says.

THREE SCORING CONVENTIONS, BECAUSE ABSTENTION MAKES "CORRECT" AMBIGUOUS
----------------------------------------------------------------------
McNemar needs one binary outcome per item per system. Both systems here can return
UNVERIFIABLE, so "correct" has to be defined, and the definition drives the answer.
Picking one silently would be choosing the result. All three are reported:

  C1  both-covered     Restrict to claims where BOTH systems return a confident
                       verdict; outcome = matches gold. Answers: *at equal
                       willingness to answer, who is right?* This is the
                       convention the project's existing 4-0 table already uses
                       implicitly.
  C2  exact-match      All paired claims; outcome = the three-valued prediction
                       equals the three-valued gold. Abstaining on a gold TRUE is
                       an error here, so C2 charges routing for its coverage.
                       Note it also credits abstaining on a gold UNVERIFIABLE,
                       which is correct per R7 -- a confident verdict on a
                       not-checkable claim is a mistake, not a win.
  C3  confident-error  All paired claims; outcome = did NOT emit a confident wrong
                       verdict (abstention is not an error). This is the exact
                       claim the thesis makes for QUANTITATIVE, "0 confident
                       errors against the baseline's 19".

C1 penalises nobody, C2 penalises abstention, C3 rewards it. They are not
variations on a theme; they answer three different questions and they disagree.

EVERY ROW CARRIES ITS DEGENERATE COMPARATORS, AND C3 IS GAMED
-------------------------------------------------------------
R3's discipline applied to a significance test. Always-True, Always-False and
Always-UNVERIFIABLE are each run against the same baseline under the same
convention. The result that matters:

    under C3, Always-UNVERIFIABLE scores the SAME p as the routed verifier,

because a system that never answers never emits a confident error. So C3 alone
cannot support "routing wins" -- it is the significance-test mirror of the
Always-False F1(FALSE) = 0.641 trap. C1 is the convention no degenerate strategy
games: Always-UNVERIFIABLE has no covered rows so its test is empty (n = 0), and
Always-True's discordant pairs fall against it on a negatives-enriched set.

SCOPE LIMIT, STATED RATHER THAN OMITTED
---------------------------------------
There is no whole-system McNemar over the natural 356. The routed system is not a
single artifact there: TEMPORAL and EA sit at 0% coverage, and RELATIONAL's live
logic is a notebook cell with no committed per-claim CSV. So the test runs
per-type, on the two types with committed routed output -- QUANTITATIVE and
CITATION Level 1b. A per-type test cannot be pooled into a system-level claim.

Offline. Zero model calls, zero network. Everything recomputed from cached CSVs.
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M                                     # noqa: E402
from negatives_cache_audit import DROPPED, Audit        # noqa: E402
from threshold_sweep import verdicts as bl_verdicts     # noqa: E402

ROOT = os.path.dirname(HERE)

ROUTED_QUANT_POS = os.path.join(HERE, "quantitative_b3_results.csv")
ROUTED_QUANT_NEG = os.path.join(
    HERE, "quantitative_negatives_verifier_quantitative_all_results.csv")
ROUTED_CITA = os.path.join(HERE, "citation_l1b_results.csv")

BASE_NAT = os.path.join(HERE, "nonrouted_baseline_results.csv")
BASE_NEG = os.path.join(HERE, "nonrouted_negatives_results.csv")

SHIPPED = (0.50, 0.40)
TUNED = (0.35, 0.30)

VERDICTS = ("TRUE", "FALSE", "UNVERIFIABLE")
CONFIDENT = ("TRUE", "FALSE")
ALPHA = 0.05


# ------------------------------------------------------------------- the test

def mcnemar_exact(b: int, c: int) -> dict:
    """Two-sided exact (binomial) McNemar test on discordant pairs only.

    b = A right, B wrong.  c = A wrong, B right.  b > c favours A.

    The exact binomial is used rather than the chi-square approximation because
    n is single-digit here; the approximation is not valid below roughly 25
    discordant pairs and would report a spuriously small p exactly where this
    project has the least data.

    Returns `p`, and `min_p` -- the smallest p this n could possibly produce.
    `min_p` is why the test is worth running at all: it separates "measured to be
    similar" from "underpowered to tell", which a bare p cannot do.
    """
    n = b + c
    if n == 0:
        # No claim distinguishes the systems. Not evidence of equivalence.
        return {"b": b, "c": c, "n": n, "p": 1.0, "min_p": 1.0,
                "empty": True, "favours": "-"}
    m = max(b, c)
    tail = sum(comb(n, k) for k in range(m, n + 1))   # exact integer arithmetic
    p = min(1.0, 2 * tail / 2 ** n)
    return {"b": b, "c": c, "n": n, "p": p,
            "min_p": min(1.0, 2 / 2 ** n),
            "empty": False,
            "favours": "A" if b > c else ("B" if c > b else "tie")}


def min_discordant_for(alpha: float = ALPHA) -> int:
    """Fewest discordant pairs at which two-sided significance is reachable."""
    n = 1
    while min(1.0, 2 / 2 ** n) > alpha:
        n += 1
    return n


# ----------------------------------------------------------- the conventions

def correct(gold: str, pred: str) -> bool:
    """Three-valued exact match.

    Deliberately NOT "abstention is always wrong": predicting UNVERIFIABLE on a
    gold-UNVERIFIABLE claim is right, and a confident verdict on one is an error.
    That is R7 -- gold UNVERIFIABLE (not checkable in principle) and predicted
    UNVERIFIABLE (could not reach evidence) must never be merged, and the place
    that distinction bites is exactly here.
    """
    return pred == gold


def conf_error(gold: str, pred: str) -> bool:
    """A confident wrong verdict -- the one output class a detector must not emit."""
    return pred in CONFIDENT and pred != gold


def table(rows: list[tuple[str, str, str, str]], convention: str) -> dict:
    """Build the paired 2x2 table under one convention.

    rows are (claim_id, gold, pred_A, pred_B).
    """
    if convention == "C1":
        rows = [r for r in rows if r[2] in CONFIDENT and r[3] in CONFIDENT]
        ok = lambda g, p: correct(g, p)                            # noqa: E731
    elif convention == "C2":
        ok = lambda g, p: correct(g, p)                            # noqa: E731
    elif convention == "C3":
        ok = lambda g, p: not conf_error(g, p)                     # noqa: E731
    else:
        raise ValueError(convention)

    n11 = n10 = n01 = n00 = 0
    disc_rows = []
    for cid, g, pa, pb in rows:
        a, bb = ok(g, pa), ok(g, pb)
        if a and bb:
            n11 += 1
        elif a and not bb:
            n10 += 1
            disc_rows.append((cid, g, pa, pb, "A"))
        elif bb and not a:
            n01 += 1
            disc_rows.append((cid, g, pa, pb, "B"))
        else:
            n00 += 1

    res = mcnemar_exact(n10, n01)
    res.update({"n11": n11, "n10": n10, "n01": n01, "n00": n00,
                "considered": len(rows), "disc_rows": disc_rows})
    return res


# ------------------------------------------------------------------- io / prep

def load(path: str) -> list[dict]:
    if not os.path.isfile(path):
        raise SystemExit(f"missing input: {os.path.relpath(path, ROOT)}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def gold_of(row: dict) -> str:
    return (row.get("gold_verdict") or "").strip().upper()


def routed_pred(row: dict) -> str:
    v = (row.get("q_verdict") or row.get("verdict") or "").strip().upper()
    return v if v in VERDICTS else "UNVERIFIABLE"


def prep_baseline(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if not gold_of(r):
            continue
        try:
            r["_e"] = float(r.get("entail") or 0.0)
            r["_c"] = float(r.get("contradict") or 0.0)
            r["_n"] = int(float(r.get("scored_passages") or 0))
        except ValueError:
            r["_e"] = r["_c"] = 0.0
            r["_n"] = 0
        out.append(r)
    return out


def pair_up(routed: list[dict], base: list[dict],
            thresholds: tuple[float, float]) -> list[tuple[str, str, str, str]]:
    """Join routed and baseline output on claim_id. Unmatched rows are DROPPED
    from the test, not defaulted -- a claim the baseline never scored is not a
    claim the baseline got wrong, and defaulting it to UNVERIFIABLE would invent
    a discordant pair. The count of unmatched rows is printed by the caller.
    """
    bmap = {r["claim_id"]: r for r in base}
    bl = dict(zip([r["claim_id"] for r in base], bl_verdicts(base, *thresholds)))
    out = []
    for r in routed:
        cid = r["claim_id"]
        if cid not in bmap:
            continue
        g = gold_of(r)
        if not g:
            continue
        assert g == gold_of(bmap[cid]), (
            f"gold mismatch on {cid}: routed {g!r} vs baseline "
            f"{gold_of(bmap[cid])!r} -- the two files disagree about the label, "
            "which invalidates the pairing")
        out.append((cid, g, routed_pred(r), bl[cid]))
    return out


# ---------------------------------------------------------------- presentation

def hdr(t: str) -> None:
    print()
    print("=" * 78)
    print(t)
    print("=" * 78)


def sub(t: str) -> None:
    print()
    print(f"--- {t} " + "-" * max(0, 72 - len(t)))


def pfmt(p: float) -> str:
    return f"{p:.4f}" if p >= 0.0001 else f"{p:.2e}"


def verdict_word(res: dict, alpha: float = ALPHA) -> str:
    if res["empty"]:
        return "NO DISCORDANT PAIRS"
    if res["p"] <= alpha:
        return f"significant, favours {res['favours']}"
    if res["min_p"] > alpha:
        return "UNDERPOWERED (significance unreachable at this n)"
    return "not significant"


def row_line(label: str, res: dict) -> None:
    print(f"  {label:<30} {res['b']:>3} {res['c']:>3} {res['n']:>4}  "
          f"{pfmt(res['p']):>9}  {pfmt(res['min_p']):>9}   {verdict_word(res)}")


def head_line() -> None:
    print(f"  {'comparison (A vs baseline)':<30} {'b':>3} {'c':>3} {'n':>4}  "
          f"{'p (exact)':>9}  {'min p @n':>9}   interpretation")
    print("  " + "-" * 76)


def prior(rows: list[tuple[str, str, str, str]]) -> str:
    """R6: the class prior travels with every operating point, every time."""
    n = len(rows)
    if not n:
        return "n=0"
    c = collections.Counter(g for _, g, _, _ in rows)
    return (f"n={n}  gold TRUE {c['TRUE']} / FALSE {c['FALSE']} / "
            f"UNVERIFIABLE {c['UNVERIFIABLE']}  "
            f"(pi_FALSE = {100 * c['FALSE'] / n:.1f}%)")


def degenerate_arms(rows: list[tuple[str, str, str, str]]) -> list[tuple[str, list]]:
    """The same rows with system A replaced by each degenerate strategy."""
    return [
        ("Always-True vs baseline",
         [(cid, g, "TRUE", pb) for cid, g, _, pb in rows]),
        ("Always-False vs baseline",
         [(cid, g, "FALSE", pb) for cid, g, _, pb in rows]),
        ("Always-UNVERIFIABLE vs base",
         [(cid, g, "UNVERIFIABLE", pb) for cid, g, _, pb in rows]),
    ]


def run_block(title: str, rows: list[tuple[str, str, str, str]],
              a_label: str, show_disc: bool = False,
              inadmissible: dict[str, str] | None = None) -> dict:
    """One population x one operating point: all three conventions + degenerates."""
    sub(title)
    print(f"  population: {prior(rows)}")
    print()
    out = {}
    for conv, blurb in (("C1", "both-covered      (equal willingness to answer)"),
                        ("C2", "exact-match       (abstention charged as error)"),
                        ("C3", "confident-error   (abstention not an error)")):
        print(f"  [{conv}] {blurb}")
        head_line()
        res = table(rows, conv)
        out[conv] = res
        row_line(a_label, res)
        for dlabel, drows in degenerate_arms(rows):
            row_line(dlabel, table(drows, conv))
        note = (inadmissible or {}).get(conv)
        if note:
            print(f"  !! INADMISSIBLE HERE: {note}")
        # Flag the specific failure this table exists to catch: a degenerate arm
        # reaching a p at least as small as the real system's, in the same
        # direction. That is the test being gamed, not the system winning.
        gamed = [dl for dl, dr in degenerate_arms(rows)
                 for dres in [table(dr, conv)]
                 if not dres["empty"] and not res["empty"]
                 and dres["favours"] == "A" and dres["p"] <= res["p"]]
        if gamed:
            print(f"  !! GAMED under {conv}: {', '.join(gamed)} reaches a p at "
                  f"least as small,")
            print(f"     in the same direction. {conv} alone cannot support a "
                  f"claim about {a_label}.")
        print()
    if show_disc:
        res = out["C1"]
        if res["disc_rows"]:
            print("  the discordant pairs under C1 (the ones the test is built on):")
            print(f"    {'claim_id':<15} {'gold':<13} {'routed':<13} "
                  f"{'baseline':<13} won by")
            for cid, g, pa, pb, w in res["disc_rows"]:
                print(f"    {cid:<15} {g:<13} {pa:<13} {pb:<13} {w}")
    return out


# -------------------------------------------------------------------- sections

def section_power() -> None:
    hdr("[0] THE POWER FLOOR -- read this before any p below")
    print()
    print("  The exact two-sided McNemar p is bounded below by 2/2**n, where n is")
    print("  the number of DISCORDANT pairs (claims where the two systems differ")
    print("  in correctness). Concordant claims carry no information and are not")
    print("  in n, so n is far smaller than any population size quoted elsewhere.")
    print()
    print(f"  {'discordant n':>12}  {'min possible p':>15}   "
          f"significance at alpha={ALPHA} ...")
    print("  " + "-" * 62)
    for n in range(1, 11):
        mp = min(1.0, 2 / 2 ** n)
        print(f"  {n:>12}  {pfmt(mp):>15}   "
              f"{'REACHABLE' if mp <= ALPHA else 'unreachable, whatever the data'}")
    print()
    need = min_discordant_for(ALPHA)
    print(f"  So {need} discordant pairs is the minimum for significance to be")
    print("  POSSIBLE, and that requires every one of them to fall the same way.")
    print("  Below it, 'not significant' is a statement about the corpus, not")
    print("  about the systems -- and the corpus is the constraint this project")
    print("  already documents (14 gold negatives across the natural 356).")


def section_quant() -> None:
    hdr("[1] QUANTITATIVE -- routed verifier vs non-routed baseline")
    print()
    print("  The only type with committed routed output on both classes.")

    pos_r = [r for r in load(ROUTED_QUANT_POS) if gold_of(r)]
    neg_r = [r for r in load(ROUTED_QUANT_NEG) if gold_of(r)]
    base_nat = prep_baseline(load(BASE_NAT))
    base_neg = prep_baseline(load(BASE_NEG))

    # Membership authority is the negatives SOURCE file, exactly as the audit
    # does it -- R1a: the denominator comes from the loader, not the filename.
    aud = Audit()
    neg_r = [r for r in neg_r if r["claim_id"] in aud.src]
    base_neg = [r for r in base_neg if r["claim_id"] in aud.src]

    ids = {r["claim_id"] for r in pos_r} | {r["claim_id"] for r in neg_r}
    base_q = [r for r in base_nat + base_neg if r["claim_id"] in ids]

    print(f"  routed rows {len(pos_r) + len(neg_r)}  "
          f"(29 Batch 3 positives + {len(neg_r)} negatives)")
    print(f"  baseline rows matched {len(base_q)}   "
          f"unmatched routed rows excluded: {len(ids) - len(base_q)}")
    if DROPPED:
        print(f"  dropped from the population by DROPPED: {sorted(DROPPED)}")

    for tname, thr in (("shipped", SHIPPED), ("tuned", TUNED)):
        rows = pair_up(pos_r + neg_r, base_q, thr)
        run_block(f"combined 53, baseline @{tname} {thr}", rows,
                  "routed QUANTITATIVE", show_disc=(tname == "shipped"))
        if tname == "shipped":
            print("  CLAUDE.md's settled decision: the SHIPPED point is the one to")
            print("  quote on a negatives-enriched population, and the tuned point")
            print("  on the natural 356. Both are printed so the choice is visible")
            print("  rather than assumed -- moving a threshold between populations")
            print("  is a reverse strawman (R6).")

    # The cache-clean tier: the only population where a PAIRED comparison is
    # valid at all, because 9 of the 24 negatives read their base claim's cached
    # NLI scores and are therefore not evidence about the baseline.
    clean_ids = {r["claim_id"] for r in aud.tier("clean")}
    indep_ids = {r["claim_id"] for r in aud.tier("indep")}
    for label, keep in (("cache-clean", clean_ids), ("independent", indep_ids)):
        nr = [r for r in neg_r if r["claim_id"] in keep]
        nb = [r for r in base_neg if r["claim_id"] in keep]
        rows = pair_up(nr, nb, SHIPPED)
        run_block(f"negatives only, {label} tier, baseline @shipped", rows,
                  "routed QUANTITATIVE", show_disc=(label == "independent"))


def section_citation() -> None:
    hdr("[2] CITATION Level 1b -- routed component vs non-routed baseline")
    print()
    print("  L1b emits FALSE or UNVERIFIABLE and NEVER TRUE -- Level 1 owns TRUE.")
    print("  That is a design decision, not a gap, and it makes one convention")
    print("  below inadmissible rather than merely unflattering. Said out loud")
    print("  because omitting the number would look like hiding it.")

    l1b = [r for r in load(ROUTED_CITA) if gold_of(r)]
    aud = Audit()
    before = len(l1b)
    l1b = [r for r in l1b
           if not r["claim_id"].startswith("SYN_") or r["claim_id"] in aud.src]
    print(f"\n  L1b rows {before} -> {len(l1b)} after DROPPED "
          f"({sorted(DROPPED)})")

    base_nat = prep_baseline(load(BASE_NAT))
    base_neg = prep_baseline(load(BASE_NEG))
    base_all = base_nat + base_neg

    inadm = {"C2": "L1b emits no TRUE by design, so it is wrong on every "
                   "gold-TRUE row under an exact-match rule. C2 measures the "
                   "L1+L1b stack, which is not what is being compared here."}

    groups = [("all CITATION (natural + negatives)", l1b),
              ("negatives only",
               [r for r in l1b if r["claim_id"].startswith("SYN_")]),
              ("natural only",
               [r for r in l1b if not r["claim_id"].startswith("SYN_")])]

    for label, rr in groups:
        ids = {r["claim_id"] for r in rr}
        bq = [r for r in base_all if r["claim_id"] in ids]
        rows = pair_up(rr, bq, SHIPPED)
        run_block(f"{label}, baseline @shipped", rows, "CITATION L1b",
                  show_disc=True, inadmissible=inadm)


# -------------------------------------------------------------------- selftest

def selftest() -> int:
    fails = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}"
              + (f"   {detail}" if detail else ""))
        if not ok:
            fails.append(label)

    hdr("SELFTEST")

    sub("the exact test itself, against a textbook value and against scipy")
    r = mcnemar_exact(4, 0)
    check("b=4 c=0 -> p = 0.125 exactly", abs(r["p"] - 0.125) < 1e-12,
          f"p={r['p']}")
    check("CLAUDE.md #22's prediction (p=0.125) reproduces",
          abs(r["p"] - 0.125) < 1e-12)
    r = mcnemar_exact(0, 0)
    check("b=0 c=0 -> empty, p=1.0, no crash", r["empty"] and r["p"] == 1.0)
    check("symmetry: p(b,c) == p(c,b)",
          all(abs(mcnemar_exact(i, j)["p"] - mcnemar_exact(j, i)["p"]) < 1e-15
              for i in range(6) for j in range(6)))
    check("b==c -> p = 1.0 (never spuriously small)",
          all(mcnemar_exact(i, i)["p"] == 1.0 for i in range(1, 8)))

    # Independent implementation. scipy is present, so the arithmetic above is
    # cross-checked rather than trusted; a hand-rolled tail sum is exactly the
    # kind of thing that is off by one row and never noticed.
    try:
        from scipy.stats import binomtest
        worst = 0.0
        for b in range(0, 25):
            for c in range(0, 25):
                if b + c == 0:
                    continue
                mine = mcnemar_exact(b, c)["p"]
                theirs = binomtest(max(b, c), b + c, 0.5,
                                   alternative="two-sided").pvalue
                worst = max(worst, abs(mine - theirs))
        check("matches scipy.binomtest over all b,c in [0,24]", worst < 1e-12,
              f"max abs diff {worst:.2e}")
    except ImportError:
        check("scipy cross-check", True, "scipy absent -- SKIPPED, not verified")

    sub("the power floor")
    check("min_p(n=4) = 0.125 -> a perfect 4-0 cannot be significant",
          abs(mcnemar_exact(4, 0)["min_p"] - 0.125) < 1e-12)
    check("min_p(n=5) = 0.0625 -> still unreachable",
          abs(mcnemar_exact(5, 0)["min_p"] - 0.0625) < 1e-12)
    check("min_p(n=6) = 0.03125 -> first reachable n",
          abs(mcnemar_exact(6, 0)["min_p"] - 0.03125) < 1e-12)
    check("min_discordant_for(0.05) == 6", min_discordant_for(0.05) == 6,
          f"got {min_discordant_for(0.05)}")
    check("min_p <= p always (a floor really is a floor)",
          all(mcnemar_exact(b, c)["min_p"] <= mcnemar_exact(b, c)["p"] + 1e-15
              for b in range(15) for c in range(15) if b + c))

    sub("R7: gold UNVERIFIABLE is not merged with predicted UNVERIFIABLE")
    check("predicting UNVERIFIABLE on gold UNVERIFIABLE is CORRECT",
          correct("UNVERIFIABLE", "UNVERIFIABLE"))
    check("predicting TRUE on gold UNVERIFIABLE is a CONFIDENT ERROR",
          conf_error("UNVERIFIABLE", "TRUE"))
    check("abstaining on gold TRUE is wrong under C2 but NOT a confident error",
          not correct("TRUE", "UNVERIFIABLE")
          and not conf_error("TRUE", "UNVERIFIABLE"))

    sub("the conventions disagree, and C3 is gamed -- both are the point")
    toy = [("x1", "FALSE", "FALSE", "TRUE"),          # routed detects, base misses
           ("x2", "FALSE", "UNVERIFIABLE", "TRUE"),   # routed abstains, base wrong
           ("x3", "TRUE", "UNVERIFIABLE", "TRUE")]    # routed abstains, base right
    c1, c2, c3 = (table(toy, k) for k in ("C1", "C2", "C3"))
    check("C1 considers only the both-covered row", c1["considered"] == 1,
          f"considered={c1['considered']}")
    check("C2 charges the abstentions (c=1 from x3)", c2["c"] == 1,
          f"b={c2['b']} c={c2['c']}")
    check("C3 credits the abstention on x2 (b=2)", c3["b"] == 2,
          f"b={c3['b']} c={c3['c']}")
    allu = [(cid, g, "UNVERIFIABLE", pb) for cid, g, _, pb in toy]
    check("under C3 Always-UNVERIFIABLE ties the real system -> C3 is gamed",
          table(allu, "C3")["p"] == c3["p"],
          f"degenerate p={table(allu, 'C3')['p']:.4f} vs routed p={c3['p']:.4f}")
    check("under C1 Always-UNVERIFIABLE has an EMPTY test -> C1 is not gamed",
          table(allu, "C1")["empty"])

    sub("population membership matches the audit (R1a)")
    aud = Audit()
    l1b = [r for r in load(ROUTED_CITA) if gold_of(r)]
    kept = [r for r in l1b
            if not r["claim_id"].startswith("SYN_") or r["claim_id"] in aud.src]
    check("L1b results file still holds the dropped row as evidence",
          any(r["claim_id"] in DROPPED for r in l1b))
    check("...but it is excluded from the counted population",
          not any(r["claim_id"] in DROPPED for r in kept))
    check("L1b counted population 54 -> 53", len(l1b) == 54 and len(kept) == 53,
          f"raw={len(l1b)} kept={len(kept)}")

    sub("published figures reproduce (a re-derivation that cannot is not evidence)")
    pos_r = [r for r in load(ROUTED_QUANT_POS) if gold_of(r)]
    neg_r = [r for r in load(ROUTED_QUANT_NEG) if gold_of(r)]
    neg_r = [r for r in neg_r if r["claim_id"] in aud.src]
    base_q = [r for r in prep_baseline(load(BASE_NAT)) + prep_baseline(load(BASE_NEG))
              if r["claim_id"] in {x["claim_id"] for x in pos_r + neg_r}]
    rows = pair_up(pos_r + neg_r, base_q, SHIPPED)
    cov = [(g, pa) for _, g, pa, _ in rows if pa in CONFIDENT]
    check("routed QUANTITATIVE is 14/14 on the combined 53",
          len(cov) == 14 and all(g == p for g, p in cov),
          f"{sum(1 for g, p in cov if g == p)}/{len(cov)}")
    cw_base = sum(1 for _, g, _, pb in rows if conf_error(g, pb))
    cw_rout = sum(1 for _, g, pa, _ in rows if conf_error(g, pa))
    check("baseline @shipped makes 19 confident errors, routed 0",
          cw_base == 19 and cw_rout == 0, f"base={cw_base} routed={cw_rout}")
    check("the combined population is 53 rows", len(rows) == 53, f"{len(rows)}")

    c1 = table(rows, "C1")
    check("C1 on the combined 53 reproduces the 4-0 disagreement table",
          c1["b"] == 4 and c1["c"] == 0, f"b={c1['b']} c={c1['c']}")
    check("...and therefore p = 0.125, matching CLAUDE.md #22's prediction",
          abs(c1["p"] - 0.125) < 1e-12, f"p={c1['p']:.4f}")

    print()
    print("=" * 78)
    print("ALL PASS" if not fails else f"{len(fails)} FAILURE(S): {fails}")
    print("=" * 78)
    return 0 if not fails else 1


# ------------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--section", default="all",
                    choices=["all", "power", "quant", "citation"])
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.section in ("all", "power"):
        section_power()
    if args.section in ("all", "quant"):
        section_quant()
    if args.section in ("all", "citation"):
        section_citation()

    print()
    print("=" * 78)
    print("HOW TO QUOTE THIS. Report (b, c) beside every p, and the min-p floor")
    print("beside both. A p above alpha with min_p also above alpha is not a")
    print("measurement that the systems are alike -- it is a measurement that")
    print("this corpus cannot tell. And no C3 row may be quoted on its own,")
    print("because a system that never answers scores the same p.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
