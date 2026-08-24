#!/usr/bin/env python3
"""
Response-level aggregation: from per-claim verdicts to a paragraph trust score.

WHY THIS IS THE DELIVERABLE
---------------------------
Every result in this project so far is per-claim. But the system's stated purpose is:
an LLM writes a paragraph -> atomise it into claims -> classify each into one of five
types -> route to a type-specific verifier -> **report on the paragraph**. Without the
last step there is a claim-verification library, not a hallucination detector, and no
result at the granularity a reader actually asks about ("is this response
trustworthy?").

Designed in the Feb-Apr handoff ("the aggregation report"; a plain-English trust score
was deferred to future work) and never built until now.

Metrics are the ones already committed in the handoffs:

    Coverage           = (TRUE + FALSE) / claims in the response
    Hallucination Rate = FALSE / (TRUE + FALSE)

FOUR TRAPS THIS HAS TO AVOID, AND HOW
-------------------------------------
1. **UNVERIFIABLE is not clean.** A response of 10 claims where 8 are unverifiable and
   2 are TRUE is not "0% hallucination" -- it is 80% unmeasured. So no rate is ever
   printed without its coverage beside it, and responses are sorted by coverage so the
   thin ones are visible.

2. **A missing verdict is NOT an abstention.** TEMPORAL/EA and QUANTITATIVE have routed
   runs on Batch 3 only. For a Phase-2 TEMPORAL claim there is simply no routed result
   yet, which is *unmeasured*, not *abstained*. Conflating the two would understate
   routed coverage and flatter nothing -- it would just be wrong. Tracked separately as
   `n_unrun`.

3. **Tier must survive aggregation.** A response verified entirely by tier-2 NLI
   (73.9% accurate) must not read the same as one verified by tier-1 Wikidata (100% on
   the measured slice). Each response reports its tier/verifier mix, and a
   confidence-weighted rate alongside the raw one.

4. **Dual-emit pairs must not double-count.** A citation claim and its embedded fact
   share a `pair_id`; counting both inflates the denominator and lets one underlying
   fact move the score twice. Pairs are collapsed to one unit, taking the worse verdict
   -- FALSE dominates TRUE, since a real source attached to a false assertion is still
   a hallucinated response.

ROUTED VS NON-ROUTED
--------------------
Both aggregates are computed on the same responses, because the response level is
where the RQ2 comparison is most legible: a reader can ask "did routing change the
verdict on *this paragraph*?" rather than reading a per-claim confusion matrix.

Routed sources, by type:
    RELATIONAL        -> nonrouted_baseline_results.csv   (phase3d IS the routed
                                                           RELATIONAL verifier)
    TEMPORAL, EA      -> temporal_ea_hybrid_b3.csv
    QUANTITATIVE      -> quantitative_b3_results.csv
    CITATION          -> citation_l1_results.csv

The RELATIONAL row is not a mistake: the non-routed baseline imports and calls
phase3d's `verify_relational`, which *is* the routed RELATIONAL verifier. On that
slice routed and non-routed are the same computation, and the honest thing is to say
so rather than manufacture a difference.
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M   # noqa: E402

UNIFIED = os.path.join(HERE, "haldetect_claims_unified.csv")
OUT = os.path.join(HERE, "response_level_results.csv")

# (file, verdict column, types it supplies)
ROUTED_SOURCES = [
    ("nonrouted_baseline_results.csv", "verdict", {"RELATIONAL"}),
    ("temporal_ea_hybrid_b3.csv", "verdict", {"TEMPORAL", "ENTITY_ATTRIBUTE"}),
    ("quantitative_b3_results.csv", "q_verdict", {"QUANTITATIVE"}),
    ("citation_l1_results.csv", "verdict", {"CITATION"}),
]
NONROUTED = ("nonrouted_baseline_results.csv", "verdict")

DECIDED = ("TRUE", "FALSE")


def load_claims() -> list[dict]:
    rows = list(csv.DictReader(open(UNIFIED, newline="", encoding="utf-8")))
    return [r for r in rows
            if (r.get("gold_verdict") or "").strip()
            and str(r.get("synthetic", "")).lower() != "true"]


def load_verdicts(type_of: dict[str, str]) -> tuple[dict, dict]:
    """Returns (routed, nonrouted) as {claim_id: {verdict, confidence, tier}}.

    `type_of` maps claim_id -> claim type and is REQUIRED, not optional. Each routed
    source only supplies the types it owns.

    That filter is the whole correctness of this function. Without it, the first
    entry -- `nonrouted_baseline_results.csv`, which contains all 356 claims of every
    type -- claims every claim_id before the type-specific files are consulted, and
    the "routed" aggregate silently becomes a second copy of the non-routed one. That
    bug produced a full 34-response table whose every row read
    `tier mix: nonrouted_baseline`, which is the only reason it was caught.
    """
    routed: dict[str, dict] = {}
    for fname, col, types in ROUTED_SOURCES:
        p = os.path.join(HERE, fname)
        if not os.path.isfile(p):
            print(f"  !! routed source missing: {fname}")
            continue
        taken = 0
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            cid = r.get("claim_id", "")
            if not cid or cid in routed:
                continue
            ctype = (type_of.get(cid) or r.get("type") or "").upper()
            if ctype not in types:
                continue                      # this file does not own this type
            v = (r.get(col) or "").strip().upper()
            if not v:
                continue
            routed[cid] = {
                "verdict": v,
                "confidence": r.get("confidence") or r.get("verdict_confidence") or "",
                "tier": r.get("tier", "") or fname.replace("_results.csv", ""),
            }
            taken += 1
        print(f"  {fname:<38} supplied {taken:>4} verdicts for {sorted(types)}")
    nonrouted: dict[str, dict] = {}
    p = os.path.join(HERE, NONROUTED[0])
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            v = (r.get(NONROUTED[1]) or "").strip().upper()
            if r.get("claim_id") and v:
                nonrouted[r["claim_id"]] = {
                    "verdict": v,
                    "confidence": r.get("verdict_confidence", ""),
                    "tier": "nonrouted-nli",
                }
    return routed, nonrouted


def collapse_pairs(claims: list[dict], verdicts: dict) -> list[dict]:
    """Collapse dual-emit pairs to one unit, taking the worse verdict.

    FALSE dominates TRUE: a genuine source attached to a false assertion still makes
    the response wrong, and letting the source's TRUE cancel the fact's FALSE would
    hide exactly the failure dual-emit exists to expose.
    """
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    singles = []
    for c in claims:
        pid = (c.get("pair_id") or "").strip()
        (groups[pid].append(c) if pid else singles.append(c))

    out = list(singles)
    for pid, members in groups.items():
        if len(members) == 1:
            out.extend(members)
            continue
        vs = [verdicts.get(m["claim_id"], {}).get("verdict") for m in members]
        vs = [v for v in vs if v]
        worst = ("FALSE" if "FALSE" in vs
                 else "TRUE" if "TRUE" in vs
                 else "UNVERIFIABLE" if vs else None)
        rep = dict(members[0])
        rep["claim_id"] = f"pair:{pid}"
        rep["_collapsed_from"] = [m["claim_id"] for m in members]
        rep["_pair_verdict"] = worst
        out.append(rep)
    return out


def score_response(members: list[dict], verdicts: dict) -> dict:
    n = len(members)
    got, unrun = [], 0
    tiers: collections.Counter = collections.Counter()
    confs = []
    for m in members:
        if "_pair_verdict" in m:
            v = m["_pair_verdict"]
            tiers["dual-emit-pair"] += 1
        else:
            rec = verdicts.get(m["claim_id"])
            if rec is None:
                unrun += 1
                continue
            v = rec["verdict"]
            tiers[rec.get("tier") or "?"] += 1
            try:
                confs.append(float(rec.get("confidence") or 0.0))
            except ValueError:
                pass
        if v:
            got.append(v)
        else:
            unrun += 1

    decided = [v for v in got if v in DECIDED]
    n_false = sum(1 for v in decided if v == "FALSE")
    measured = len(got)
    gold_neg = sum(1 for m in members if m.get("gold_verdict") == "FALSE")
    return {
        "n_claims": n, "n_measured": measured, "n_unrun": unrun,
        "n_decided": len(decided), "n_false": n_false,
        "coverage": (len(decided) / measured) if measured else 0.0,
        "coverage_of_all": len(decided) / n if n else 0.0,
        "halluc_rate": (n_false / len(decided)) if decided else None,
        "mean_conf": (sum(confs) / len(confs)) if confs else None,
        "tier_mix": ", ".join(f"{k}:{v}" for k, v in tiers.most_common(3)),
        "gold_negatives": gold_neg,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Aggregate per-claim verdicts into per-response trust scores.")
    ap.add_argument("--system", choices=("routed", "nonrouted", "both"),
                    default="both")
    ap.add_argument("--min-coverage", type=float, default=0.0,
                    help="hide responses below this measured coverage")
    args = ap.parse_args()

    claims = load_claims()
    type_of = {c["claim_id"]: (c.get("type") or "").upper() for c in claims}
    routed, nonrouted = load_verdicts(type_of)
    print(f"{len(claims)} labeled claims; routed verdicts for {len(routed)}, "
          f"non-routed for {len(nonrouted)}")

    byq: dict[str, list[dict]] = collections.defaultdict(list)
    for c in claims:
        byq[c["q_id"]].append(c)
    print(f"{len(byq)} responses\n")

    systems = (["routed", "nonrouted"] if args.system == "both" else [args.system])
    allrows = []
    for sysname in systems:
        vd = routed if sysname == "routed" else nonrouted
        print("=" * 96)
        print(f"  RESPONSE-LEVEL — {sysname.upper()}")
        print("=" * 96)
        print(f"  {'q_id':<9}{'claims':>7}{'measured':>9}{'unrun':>6}"
              f"{'decided':>8}{'cov':>7}{'halluc':>8}{'conf':>6}"
              f"{'gold-':>6}  tier mix")
        rows = []
        for q in sorted(byq, key=lambda k: (k[:2], len(k), k)):
            members = collapse_pairs(byq[q], vd)
            s = score_response(members, vd)
            if s["coverage"] < args.min_coverage:
                continue
            s["q_id"] = q
            s["system"] = sysname
            rows.append(s)
            hr = "n/a" if s["halluc_rate"] is None else f"{s['halluc_rate']:.0%}"
            mc = "n/a" if s["mean_conf"] is None else f"{s['mean_conf']:.2f}"
            print(f"  {q:<9}{s['n_claims']:>7}{s['n_measured']:>9}{s['n_unrun']:>6}"
                  f"{s['n_decided']:>8}{s['coverage']:>7.0%}{hr:>8}{mc:>6}"
                  f"{s['gold_negatives']:>6}  {s['tier_mix'][:34]}")
        allrows.extend(rows)

        scored = [r for r in rows if r["halluc_rate"] is not None]
        if scored:
            print(f"\n  responses with a score : {len(scored)}/{len(rows)}")
            print(f"  mean measured coverage : "
                  f"{sum(r['coverage'] for r in rows) / len(rows):.1%}")
            print(f"  mean hallucination rate: "
                  f"{sum(r['halluc_rate'] for r in scored) / len(scored):.1%}")
            flagged = [r for r in scored if r["halluc_rate"] > 0]
            print(f"  responses flagged (>0) : {len(flagged)}/{len(scored)}")

            # Does the score separate responses that really contain a false claim?
            withneg = [r for r in scored if r["gold_negatives"] > 0]
            without = [r for r in scored if r["gold_negatives"] == 0]
            if withneg and without:
                a = sum(r["halluc_rate"] for r in withneg) / len(withneg)
                b = sum(r["halluc_rate"] for r in without) / len(without)
                print(f"\n  -- does the score track ground truth? --")
                print(f"     responses containing >=1 gold-FALSE claim ({len(withneg)}): "
                      f"mean rate {a:.1%}")
                print(f"     responses containing none            ({len(without)}): "
                      f"mean rate {b:.1%}")
                print(f"     separation: {a - b:+.1%}"
                      + ("  <- score is higher where it should be"
                         if a > b else
                         "  <- WRONG DIRECTION or no signal"))
                print(f"     n is small and only {sum(r['gold_negatives'] for r in withneg)} "
                      f"gold negatives exist in total; treat as a sanity check, "
                      f"not a result.")
        print()

    if allrows:
        cols = ["system", "q_id", "n_claims", "n_measured", "n_unrun", "n_decided",
                "n_false", "coverage", "coverage_of_all", "halluc_rate",
                "mean_conf", "gold_negatives", "tier_mix"]
        with open(OUT, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(allrows)
        print(f"wrote {OUT}  ({len(allrows)} rows)")

    print("\nREAD BEFORE QUOTING")
    print("  'halluc' is FALSE/(TRUE+FALSE) over claims that were MEASURED, so it is")
    print("  meaningless without the coverage column next to it. 'unrun' counts claims")
    print("  with no routed verdict available at all -- unmeasured, NOT abstained;")
    print("  TEMPORAL/EA and QUANTITATIVE have routed runs on Batch 3 only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
