#!/usr/bin/env python3
"""
Runnable TEMPORAL + ENTITY_ATTRIBUTE verifier, wired to the FIXED resolver.

WHY THIS EXISTS
---------------
TEMPORAL and ENTITY_ATTRIBUTE are recorded at **0% coverage / 0% accuracy** on
Batch 3, with that 0% diagnosed as "entirely a `PROPERTY_TO_WIKIDATA` gap". That
diagnosis predates three resolver bugs found on 2026-08-23, all of which sit
*upstream* of property matching:

  1. **`mul` labels.** Wikidata stores language-agnostic labels under the
     pseudo-language `mul`, and many items have no `en` label at all. Requesting
     only `en` returned an EMPTY label, so the lexical tier could not recognise the
     entity by its own name. Denali lost to an asteroid this way.
  2. **Prefix-only search.** `wbsearchentities` matches label *prefixes*, so it can
     omit the canonical entity even on an exact label match (searching "Denali"
     omits Q130018) and returns nothing for descriptive multi-word queries.
  3. **No prominence tie-break.** Any entity whose label is literally "Mount
     Everest" scores tier 3, so a stub could outrank the mountain.

Fixing those three took QUANTITATIVE from **0% -> 27.6%** coverage. TEMPORAL and EA
share the same resolver, so part of their 0% may be the same cause rather than a
property-mapping gap. This script measures that instead of assuming it.

A fourth bug, specific to this path, was fixed in `property_resolver.py` at the
same time: `fetch_item_labels` rendered **statement values** with `languages=en`,
so a `mul`-labelled value entity came back blank and the comparison failed even
when the entity AND the property were both correct.

NO LOGIC IS REIMPLEMENTED HERE
------------------------------
This is a wiring harness. Every substantive step is imported:

    resolve_entity          <- quantitative_verifier   (the fixed resolver)
    resolve_property_values <- property_resolver       (predicate matching)
    compare_tier1           <- hybrid_fallthrough      (the verdict step)

That matters because this project's recurring failure is the same logic existing in
three places and drifting apart (`temporal_verifier.py` vs cell 75; cells 67/69 and
73/75 both still in the notebook). One definition, imported.

WHAT THIS IS NOT
----------------
It is not a replacement for notebook cells 69/75. It is a measurement harness that
answers one question -- "do the resolver fixes move TEMPORAL/EA off zero?" -- with
numbers, before anyone edits the live notebook. If the answer is yes, the same
imports go into the cells. If no, the property-mapping diagnosis is confirmed and
the notebook is left alone.

READ BEFORE QUOTING ANY NUMBER FROM THIS
-----------------------------------------
Batch 3's 34 TEMPORAL+EA claims contain **zero gold negatives**, so accuracy here
cannot distinguish this verifier from one that always says TRUE. `--negatives` runs
the synthetic negatives instead, which is the only place detection can be measured.
Both are reported, never merged.
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M                     # noqa: E402
import property_resolver as PR          # noqa: E402
import hybrid_fallthrough as HF         # noqa: E402
import quantitative_verifier as QV      # noqa: E402

B3 = os.path.join(HERE, "haldetect_claims_b3_gold.csv")
SYN = os.path.join(HERE, "synthetic_negatives.csv")
OUT = os.path.join(HERE, "temporal_ea_results.csv")
BASELINE = os.path.join(HERE, "nonrouted_baseline_results.csv")
# The negatives run is a SEPARATE file (--out), so tier 2 must consult both:
# positives come from the 356-claim run, SYN_* ids from the negatives run.
BASELINE_NEG = os.path.join(HERE, "nonrouted_negatives_results.csv")

HANDLED = ("TEMPORAL", "ENTITY_ATTRIBUTE")

# A tier-1 MISMATCH may only be reported as FALSE if the matched Wikidata property
# is actually asking the claim's question. Added 2026-08-23 after B3_11_C08:
# "ISRO has a commercial satellite program" (gold TRUE) matched P1056 "product or
# material produced" = "spacecraft", and the mismatch was reported as FALSE --
# reintroducing the confident-wrong class that the 2026-08-21 QID fix had driven to
# zero. Wikidata simply does not list ISRO's commercial programme, and
# **knowledge-graph absence is not falsity**. Below this predicate/property
# agreement score a mismatch degrades to an honest UNVERIFIABLE instead.
MISMATCH_CORE_MIN = 0.35


def _core_agreement(predicate: str, prop_label: str) -> float:
    """Cheap lexical agreement between the claim's predicate and the matched PID.

    Deliberately lexical, not SBERT: embeddings rate "product produced" and "has
    program" as fairly similar, which is exactly the confusion that produced the
    ISRO error. Token overlap does not.
    """
    def toks(s: str) -> set[str]:
        return {t for t in re.split(r"[^a-z0-9]+", (s or "").lower())
                if len(t) > 2 and t not in {"the", "and", "for", "has", "date",
                                            "number", "material", "type"}}
    a, b = toks(predicate), toks(prop_label)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def load_tier2() -> dict[str, dict]:
    """Tier-2 verdicts from the completed non-routed baseline run.

    The baseline already applied Wikipedia retrieval + BART-MNLI to all 356 claims,
    TEMPORAL and EA included, and its results are on disk with the raw entail /
    contradict scores. So the hybrid's tier 2 needs no model call at all -- which
    also sidesteps the local SIGBUS, since nothing loads BART.

    Using the baseline's own output is not a shortcut, it is the correct comparison:
    tier 2 is *defined* as the same generic pipeline, consulted only when tier 1
    abstains. Same evidence, same NLI, same thresholds.
    """
    out = {}
    for path in (BASELINE, BASELINE_NEG):
        if not os.path.isfile(path):
            continue
        for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
            out[r["claim_id"]] = r
    return out


def _sbert_sim(a: str, b: str) -> float:
    """Cosine similarity via the SBERT model quantitative_verifier already loads.

    Injected into compare_tier1 so ENTITY_ATTRIBUTE comparison can recognise
    paraphrases. Reuses QV.get_sbert() rather than loading a second copy of
    MiniLM -- on an 8 GB machine a duplicate model is not free.
    """
    from sentence_transformers import util as sbert_util
    m = QV.get_sbert()
    e = m.encode([a, b], convert_to_tensor=True, normalize_embeddings=True,
                 show_progress_bar=False)
    return float(sbert_util.cos_sim(e[0], e[1]))


def resolve_fn(subject: str, ctx: str, cache: dict):
    """Adapter: hybrid_fallthrough wants (subject, ctx, cache) -> qid|None.

    `quantitative_verifier.resolve_entity` is (subject, cache, ctx) -> dict. Kept as
    a thin adapter rather than changing either signature, so the fixed resolver has
    exactly one definition and this file cannot drift from it.
    """
    r = QV.resolve_entity(subject, cache, ctx=ctx or "")
    return r.get("qid"), r.get("score", 0.0), r.get("detail", "")


def verify(row: dict, cache: dict,
           tier2: dict[str, dict] | None = None) -> dict:
    ctype = (row.get("type") or "").upper()
    subject = (row.get("subject") or "").strip()
    prop = (row.get("property") or "").strip()
    claimed = (row.get("value") or "").strip()

    out = {
        "claim_id": row.get("claim_id", ""), "type": ctype,
        "subject": subject, "property": prop, "value": claimed,
        "gold_verdict": row.get("gold_verdict", ""),
        "claim": row.get("claim", ""),
        "qid": "", "resolution_score": "", "pid": "", "pid_score": "",
        "retrieved_values": "", "verdict": "UNVERIFIABLE", "confidence": 0.0,
        "stage": "", "reason": "", "tier": "tier1-wikidata",
        "core_agreement": "",
    }
    if not subject or not prop:
        out["stage"], out["reason"] = "input", "missing subject or property"
        return out

    qid, score, detail = resolve_fn(subject, row.get("claim", ""), cache)
    out["resolution_score"] = round(score, 3)
    if not qid:
        out["stage"], out["reason"] = "resolution", detail
        return out
    out["qid"] = qid

    m = PR.resolve_property_values(qid, prop, ctype, cache,
                                   row.get("claim", ""))
    out["pid"] = m.get("pid") or ""
    out["pid_score"] = round(m.get("score", 0.0), 3)
    values = m.get("values") or []
    out["retrieved_values"] = " | ".join(str(v)[:60] for v in values[:4])
    if not m.get("pid"):
        out["stage"], out["reason"] = "property", m.get("detail", "no PID matched")
        return out
    if not values:
        out["stage"] = "values"
        out["reason"] = f"PID {m['pid']} matched but has no values"
        return out

    verdict, conf, reason = HF.compare_tier1(claimed, [str(v) for v in values],
                                             ctype, sim_fn=_sbert_sim)

    # Guard the mismatch->FALSE path. See MISMATCH_CORE_MIN.
    if verdict == "FALSE":
        plabel = PR.fetch_property_meta([m["pid"]], cache).get(
            m["pid"], {}).get("label", "")
        agree = _core_agreement(prop, plabel)
        out["core_agreement"] = round(agree, 3)
        if agree < MISMATCH_CORE_MIN:
            out["verdict"], out["confidence"] = "UNVERIFIABLE", 0.0
            out["stage"] = "mismatch-guard"
            out["reason"] = (
                f"mismatch NOT reported as FALSE: predicate '{prop}' vs matched "
                f"property '{plabel}' agree only {agree:.2f} < "
                f"{MISMATCH_CORE_MIN}; Wikidata absence is not falsity")
            return out

    out["verdict"], out["confidence"] = verdict, conf
    out["stage"] = "compare" if verdict != "UNVERIFIABLE" else "compare-abstain"
    out["reason"] = reason

    return out


def _apply_tier2(out: dict, tier2: dict[str, dict]) -> None:
    """Fall through to the generic Wikipedia+NLI verdict on tier-1 abstention.

    Tier 1 always wins: this is only reached when tier 1 produced no verdict. The
    confidence is capped below tier 1's floor so a risk-coverage curve ranks
    structured evidence above textual inference -- the whole point of tiering rather
    than simply unioning the two.
    """
    b = tier2.get(out["claim_id"])
    if not b:
        return
    v = (b.get("verdict") or "").upper()
    if v not in ("TRUE", "FALSE"):
        return
    try:
        conf = min(float(b.get("verdict_confidence") or 0.0), HF.TIER2_CEILING)
    except ValueError:
        conf = HF.TIER2_CEILING
    out["verdict"] = v
    out["confidence"] = round(conf, 3)
    out["tier"] = "tier2-nli"
    out["stage"] = "tier2"
    out["reason"] = (f"tier 1 abstained; generic Wikipedia+NLI says {v} "
                     f"(entail={b.get('entail')}, contradict={b.get('contradict')}), "
                     f"confidence capped at {HF.TIER2_CEILING}")


def load_rows(path: str, negatives: bool) -> list[dict]:
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    keep = []
    for r in rows:
        if (r.get("type") or "").upper() not in HANDLED:
            continue
        if not (r.get("gold_verdict") or "").strip():
            continue
        if negatives:
            # synthetic_negatives.csv stores the corrupted value in
            # `corrupted_value`; make it the value under test.
            if r.get("corrupted_value"):
                r["value"] = r["corrupted_value"]
        keep.append(r)
    return keep


def report(results: list[dict], title: str) -> None:
    gold = [r["gold_verdict"] for r in results]
    pred = [r["verdict"] for r in results]
    conf = [float(r["confidence"] or 0.0) for r in results]

    print(f"\n{'=' * 74}")
    print(f"  WHERE EACH CLAIM STOPPED — {title}")
    print(f"{'=' * 74}")
    stages = collections.Counter(r["stage"] for r in results)
    order = ["input", "resolution", "property", "values",
             "compare-abstain", "compare"]
    labels = {
        "input": "no subject/property in the row",
        "resolution": "entity not resolved (was the #1 blocker before the fixes)",
        "property": "entity resolved, but NO Wikidata property matched",
        "values": "property matched, but it holds no values",
        "compare-abstain": "values retrieved, comparison inconclusive",
        "compare": "ANSWERED (TRUE/FALSE)",
    }
    for s in order:
        if stages.get(s):
            print(f"  {stages[s]:>3}  {s:<17} {labels[s]}")
    for t in HANDLED:
        sub = [r for r in results if r["type"] == t]
        if sub:
            n_ans = sum(1 for r in sub if r["verdict"] != "UNVERIFIABLE")
            print(f"     {t:<20} {n_ans}/{len(sub)} answered "
                  f"({n_ans / len(sub):.1%})")
    M.report(gold, pred, conf, title=title)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="TEMPORAL + ENTITY_ATTRIBUTE verifier with the fixed resolver.")
    ap.add_argument("--claims", default=B3)
    ap.add_argument("--out", default=None,
                    help="custom output CSV path (defaults to temporal_ea_results.csv)")
    ap.add_argument("--negatives", action="store_true",
                    help=f"run {os.path.basename(SYN)} instead — the only slice "
                         f"with gold negatives, so the only place detection can "
                         f"be measured")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--hybrid", action="store_true",
                    help="on tier-1 abstention, fall through to the "
                         "non-routed baseline's cached Wikipedia+NLI "
                         "verdict (no model call, no GPU)")
    args = ap.parse_args()

    out_file = args.out if args.out else OUT
    path = SYN if args.negatives else args.claims
    if not os.path.isfile(path):
        print(f"FATAL: {path} not found")
        return 1
    rows = load_rows(path, args.negatives)
    if args.limit:
        rows = rows[:args.limit]

    label = ("synthetic negatives" if args.negatives
             else os.path.basename(args.claims))
    print(f"{len(rows)} TEMPORAL+EA claims from {label}")
    print(f"  by type: " + ", ".join(
        f"{k} {v}" for k, v in sorted(
            collections.Counter(r['type'].upper() for r in rows).items())))
    gd = collections.Counter(r["gold_verdict"] for r in rows)
    print(f"  gold: {dict(gd)}")
    if gd.get("FALSE", 0) == 0:
        print("  !! zero gold negatives — accuracy below measures the base rate, "
              "not detection.\n     Use --negatives for a real measurement.")

    tier2 = load_tier2() if args.hybrid else None
    if args.hybrid:
        print(f'  tier 2 enabled: {len(tier2)} cached baseline verdicts'
              if tier2 else '  !! --hybrid but no baseline results found')
    cache = QV.load_cache()
    results = []
    for i, r in enumerate(rows, 1):
        res = verify(r, cache)
        # Tier 2 is applied HERE, not inside verify(), because most
        # tier-1 abstentions return early (resolution / property /
        # no-values) and would otherwise never reach the fall-through.
        if tier2 and res['verdict'] == 'UNVERIFIABLE':
            _apply_tier2(res, tier2)
        results.append(res)
        print(f"  [{i}/{len(rows)}] {res['claim_id']:<14}{res['type'][:4]:<6}"
              f"{res['verdict']:<14}{res['stage']:<17}{res['reason'][:52]}")
    QV.save_cache(cache)

    with open(out_file, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nwrote {out_file}")

    report(results, f"TEMPORAL+EA, fixed resolver — {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
