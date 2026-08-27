#!/usr/bin/env python3
"""
HalDetect — Master Benchmark Corpus Evaluation Runner (with Track C Tier 2)
===========================================================================

Executes the full taxonomy-routed HalDetect verification pipeline across
all claims in `haldetect_master_corpus_v2.csv`:
  - QUANTITATIVE     -> quantitative_verifier.py (Tier 1 Wikidata) +
                        quantitative_tier2_verifier.py (Tier 2 World Bank Open Data REST API)
  - TEMPORAL         -> temporal_ea_verifier.py  (Fixed resolver, date clusters)
  - ENTITY_ATTRIBUTE -> temporal_ea_verifier.py  (Fixed resolver, P31 guards)
  - CITATION         -> citation_l1b_verifier.py (Series & publisher consistency)
  - RELATIONAL       -> hybrid_fallthrough.py    (Wikipedia + NLI / Cache)

Outputs: `current/master_corpus_v2_evaluation_results.csv`
Computes: Population breakdowns, Selective Accuracy, Precision(FALSE), MCC, AURAC.
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

import metrics as M
import quantitative_verifier as QV
import quantitative_tier2_verifier as QT2
import temporal_ea_verifier as TEA
import citation_l1b_verifier as CITA
import property_resolver as PR
import hybrid_fallthrough as HF

CORPUS_CSV = os.path.join(HERE, "haldetect_master_corpus_v2.csv")
OUT_CSV = os.path.join(HERE, "master_corpus_v2_evaluation_results.csv")


def evaluate_master_corpus(corpus_path: str = CORPUS_CSV,
                           output_path: str = OUT_CSV,
                           hybrid: bool = True) -> list[dict]:
    with open(corpus_path, newline="", encoding="utf-8") as fh:
        claims = list(csv.DictReader(fh))

    print(f"Loaded {len(claims)} claims from {os.path.basename(corpus_path)}")
    by_type = collections.Counter(r["type"] for r in claims)
    print(f"Modality split: {dict(by_type)}")

    # Load caches
    qv_cache = QV.load_cache()
    macro_cache = QT2.load_macro_cache()
    tier2 = TEA.load_tier2() if hybrid else None

    results = []
    print("\nRunning taxonomy-routed verifiers with Quantitative Tier 2 (World Bank)...")

    for i, r in enumerate(claims, 1):
        ctype = (r.get("type") or "").upper()
        mid = r.get("master_id", f"MST_{i:04d}")
        cid = r.get("claim_id", "")
        gold = (r.get("gold_verdict") or "").upper()
        claim_text = r.get("claim", "")
        subject = r.get("subject", "")
        prop = r.get("property", "")
        val = r.get("value", "")
        origin = r.get("origin_dataset", "")

        res = {
            "master_id": mid,
            "claim_id": cid,
            "origin_dataset": origin,
            "type": ctype,
            "subject": subject,
            "property": prop,
            "value": val,
            "gold_verdict": gold,
            "claim": claim_text,
            "verdict": "UNVERIFIABLE",
            "confidence": 0.0,
            "verifier": "",
            "stage": "",
            "reason": "",
            "tier": "tier1"
        }

        if ctype == "QUANTITATIVE":
            # Tier 1: Wikidata quantity extract-and-compare
            q_res = QV.verify_quantitative(r, qv_cache)
            
            # Tier 2: World Bank Macro REST API Fallback
            if hybrid and q_res.get("verdict") == "UNVERIFIABLE":
                m_res = QT2.verify_macro_claim(r, macro_cache)
                if m_res.get("verdict") != "UNVERIFIABLE":
                    q_res = {
                        "verdict": m_res["verdict"],
                        "confidence": m_res["confidence"],
                        "stage": m_res["method"],
                        "reason": m_res["evidence"],
                        "tier": "tier2-worldbank"
                    }

            res["verdict"] = q_res.get("verdict", "UNVERIFIABLE")
            res["confidence"] = round(float(q_res.get("confidence", 0.0)), 3)
            res["verifier"] = "quantitative_tier2_verifier" if q_res.get("tier") == "tier2-worldbank" else "quantitative_verifier"
            res["stage"] = q_res.get("stage", "compare")
            res["reason"] = q_res.get("reason", q_res.get("detail", ""))
            res["tier"] = q_res.get("tier", "tier1")

        elif ctype in ("TEMPORAL", "ENTITY_ATTRIBUTE"):
            # Temporal & Entity Attribute verifier
            t_res = TEA.verify(r, qv_cache)
            if hybrid and tier2 and t_res["verdict"] == "UNVERIFIABLE":
                TEA._apply_tier2(t_res, tier2)
            res["verdict"] = t_res.get("verdict", "UNVERIFIABLE")
            res["confidence"] = round(float(t_res.get("confidence", 0.0)), 3)
            res["verifier"] = "temporal_ea_verifier"
            res["stage"] = t_res.get("stage", "")
            res["reason"] = t_res.get("reason", "")
            res["tier"] = t_res.get("tier", "tier1")

        elif ctype == "CITATION":
            # Citation L1/L1b verifier
            c_res = CITA.verify_l1b(r, qv_cache)
            res["verdict"] = c_res.get("verdict", "UNVERIFIABLE")
            res["confidence"] = round(float(c_res.get("confidence", 0.0)), 3)
            res["verifier"] = "citation_l1b_verifier"
            res["stage"] = c_res.get("route", "citation")
            res["reason"] = c_res.get("reason", "")

        elif ctype == "RELATIONAL":
            # Relational fall-through
            if tier2 and cid in tier2:
                b = tier2[cid]
                v = (b.get("verdict") or "UNVERIFIABLE").upper()
                res["verdict"] = v
                res["confidence"] = round(float(b.get("verdict_confidence") or 0.5), 3)
                res["stage"] = "nli_baseline"
                res["reason"] = f"NLI: entail={b.get('entail')}, contradict={b.get('contradict')}"
                res["tier"] = "tier2-nli"
            else:
                res["verdict"] = "UNVERIFIABLE"
                res["stage"] = "unverified_relational"
                res["reason"] = "open relational claim; outside structured Wikidata tier"

        results.append(res)
        if i % 100 == 0 or i == len(claims):
            print(f"  [{i:>4}/{len(claims)}] {mid:<10} {ctype:<16} {res['verdict']:<14} {res['reason'][:40]}")

    QV.save_cache(qv_cache)
    QT2.save_macro_cache(macro_cache)

    # Save output
    fieldnames = list(results[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nWrote {len(results)} evaluated claims to {output_path}")

    # Generate Reports
    generate_full_report(results)
    return results


def generate_full_report(results: list[dict]) -> None:
    print(f"\n{'=' * 78}")
    print(f"  HALDETECT MASTER BENCHMARK CORPUS (v3.0) — EVALUATION REPORT (N={len(results)})")
    print(f"{'=' * 78}")

    gold = [r["gold_verdict"] for r in results]
    pred = [r["verdict"] for r in results]
    conf = [float(r["confidence"] or 0.0) for r in results]

    M.report(gold, pred, conf, title="Master Corpus v3.0 (Pooled Total)")

    print(f"\n{'=' * 78}")
    print("  BREAKDOWN BY MODALITY TYPE")
    print(f"{'=' * 78}")
    by_type = collections.defaultdict(list)
    for r in results:
        by_type[r["type"]].append(r)

    for ctype in sorted(by_type.keys()):
        sub = by_type[ctype]
        sub_gold = [r["gold_verdict"] for r in sub]
        sub_pred = [r["verdict"] for r in sub]
        sub_conf = [float(r["confidence"] or 0.0) for r in sub]
        M.report(sub_gold, sub_pred, sub_conf, title=f"Modality: {ctype} (N={len(sub)})")

    print(f"\n{'=' * 78}")
    print("  BREAKDOWN BY ORIGIN DATASET")
    print(f"{'=' * 78}")
    by_origin = collections.defaultdict(list)
    for r in results:
        by_origin[r["origin_dataset"]].append(r)

    for orig in sorted(by_origin.keys()):
        sub = by_origin[orig]
        sub_gold = [r["gold_verdict"] for r in sub]
        sub_pred = [r["verdict"] for r in sub]
        sub_conf = [float(r["confidence"] or 0.0) for r in sub]
        M.report(sub_gold, sub_pred, sub_conf, title=f"Origin: {orig} (N={len(sub)})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Master Benchmark Corpus.")
    parser.add_argument("--corpus", default=CORPUS_CSV, help="Master corpus CSV path")
    parser.add_argument("--out", default=OUT_CSV, help="Output evaluation CSV path")
    parser.add_argument("--no-hybrid", action="store_true", help="Disable Tier 2 fall-through")
    args = parser.parse_args()

    evaluate_master_corpus(args.corpus, args.out, hybrid=not args.no_hybrid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
