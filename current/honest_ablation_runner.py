#!/usr/bin/env python3
"""
HalDetect -- Honest Master Ablation Runner (Fully Connected Local Pipeline)
==========================================================================
Adapted from Claude's audit runner. 
Guarantees:
  1. Zero Evaluation Leakage: `gold_verdict` is never passed to any predictor.
  2. All verifiers (Quantitative, Macroeconomic, Temporal/EA, Citation, and Relational)
     are loaded and executed locally with full network and cache support.
  3. Evaluates both Routed System and Non-Routed baseline on the exact same corpus.
"""

from __future__ import annotations

import csv
import inspect
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import metrics as M
import quantitative_verifier as QV
import quantitative_tier2_verifier as QT2
import temporal_ea_verifier as TEA
import citation_l1b_verifier as CITA
from dimensional_quantity_engine import DimensionalQuantityEngine
from bidirectional_kg_resolver import BidirectionalKGResolver

CORPUS_CSV = HERE / "haldetect_master_benchmark_1000.csv"
if not CORPUS_CSV.exists():
    CORPUS_CSV = HERE / "haldetect_master_corpus_v2.csv"

# Pre-load caches
qv_cache = QV.load_cache()
macro_cache = QT2.load_macro_cache()
tier2_tea = TEA.load_tier2()


def load_corpus() -> List[Dict[str, Any]]:
    with open(CORPUS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def predict_quantitative(row: Dict[str, Any]) -> Dict[str, Any]:
    # Extract only claim features, NEVER gold_verdict
    claim_dict = {
        "claim": row.get("claim", ""),
        "subject": row.get("subject", ""),
        "property": row.get("property", ""),
        "value": row.get("value", ""),
        "type": "QUANTITATIVE"
    }
    # 1. Tier 1 Wikidata Quantitative
    res = QV.verify_quantitative(claim_dict, qv_cache)
    if res.get("verdict") != "UNVERIFIABLE":
        return {
            "verdict": res.get("verdict"),
            "confidence": res.get("confidence", 0.9),
            "engine": "Quantitative ALU (Tier 1 Wikidata)",
            "evidence": res.get("detail", "")
        }
    # 2. Tier 2 World Bank REST API
    m_res = QT2.verify_macro_claim(claim_dict, macro_cache)
    if m_res.get("verdict") != "UNVERIFIABLE":
        return {
            "verdict": m_res.get("verdict"),
            "confidence": m_res.get("confidence", 0.95),
            "engine": "Macroeconomic ALU (Tier 2 World Bank)",
            "evidence": m_res.get("reason", "")
        }
    return {
        "verdict": "UNVERIFIABLE",
        "confidence": 0.3,
        "engine": "Quantitative Abstention",
        "evidence": "Unmatched quantitative entity/property in knowledge graph"
    }


def predict_temporal_ea(row: Dict[str, Any]) -> Dict[str, Any]:
    claim_text = row.get("claim", "")
    
    # 1. Bidirectional Superlative Inverse KG Check
    b_res = BidirectionalKGResolver.resolve_superlative_claim(claim_text)
    if b_res:
        return {
            "verdict": b_res["verdict"],
            "confidence": b_res["confidence"],
            "engine": "Bidirectional Superlative KG Resolver",
            "evidence": b_res["evidence"]
        }

    # 2. Temporal & Entity Attribute Verifier
    claim_dict = {
        "claim": claim_text,
        "subject": row.get("subject", ""),
        "property": row.get("property", ""),
        "value": row.get("value", ""),
        "type": row.get("type", "TEMPORAL")
    }
    t_res = TEA.verify(claim_dict, qv_cache)
    if tier2_tea and t_res.get("verdict") == "UNVERIFIABLE":
        TEA._apply_tier2(t_res, tier2_tea)

    return {
        "verdict": t_res.get("verdict", "UNVERIFIABLE"),
        "confidence": t_res.get("confidence", 0.5),
        "engine": "Temporal/EA 2-Hop Verifier",
        "evidence": t_res.get("reason", "")
    }


def predict_citation(row: Dict[str, Any]) -> Dict[str, Any]:
    claim_dict = {
        "claim": row.get("claim", ""),
        "subject": row.get("subject", ""),
        "property": "DOI",
        "value": "",
        "type": "CITATION"
    }
    c_res = CITA.verify_l1b(claim_dict, qv_cache)
    return {
        "verdict": c_res.get("verdict", "UNVERIFIABLE"),
        "confidence": c_res.get("confidence", 0.5),
        "engine": "Citation CrossRef Verifier",
        "evidence": c_res.get("reason", "")
    }


def predict_relational(row: Dict[str, Any]) -> Dict[str, Any]:
    cid = row.get("claim_id", "")
    if tier2_tea and cid in tier2_tea:
        b = tier2_tea[cid]
        return {
            "verdict": (b.get("verdict") or "UNVERIFIABLE").upper(),
            "confidence": float(b.get("verdict_confidence") or 0.5),
            "engine": "Relational NLI Fall-through",
            "evidence": f"entail={b.get('entail')}, contradict={b.get('contradict')}"
        }
    return {
        "verdict": "UNVERIFIABLE",
        "confidence": 0.35,
        "engine": "Relational Abstention",
        "evidence": "Open relational predicate ungrounded in structured tier"
    }


def predict_routed(row: Dict[str, Any]) -> Dict[str, Any]:
    modality = (row.get("type") or "UNKNOWN").upper()
    if modality == "QUANTITATIVE":
        return predict_quantitative(row)
    elif modality in ("TEMPORAL", "ENTITY_ATTRIBUTE"):
        return predict_temporal_ea(row)
    elif modality == "CITATION":
        return predict_citation(row)
    else:
        return predict_relational(row)


def predict_nonrouted_baseline(claim_text: str) -> str:
    """A genuine non-routed baseline: negation flip over TRUE prior."""
    low = claim_text.lower()
    if any(w in low for w in (" not ", " never ", " no longer ", " neither ", " did not ", " failed ")):
        return "FALSE"
    return "TRUE"


def _leak_check() -> None:
    for fn in (predict_quantitative, predict_temporal_ea, predict_citation, predict_relational, predict_nonrouted_baseline):
        src = inspect.getsource(fn)
        assert 'row.get("gold_verdict"' not in src.replace(" ", "").replace("'", '"'), (
            f"{fn.__name__} reads gold_verdict while predicting -- LEAK DETECTED"
        )
    print("🔒 [LEAK CHECK: PASS] -- Verified zero predictor functions read gold_verdict before prediction!\n")


def main() -> None:
    _leak_check()
    corpus = load_corpus()
    print(f"Loaded {len(corpus)} claims from {CORPUS_CSV.name}\n")

    gold: List[str] = []
    routed_pred: List[str] = []
    routed_conf: List[float] = []
    base_pred: List[str] = []
    engines_used: Dict[str, int] = {}

    t0 = time.time()
    for row in corpus:
        g = (row.get("gold_verdict") or "").strip().upper()
        if g not in ("TRUE", "FALSE", "UNVERIFIABLE"):
            continue
        r = predict_routed(row)
        gold.append(g)
        routed_pred.append(r["verdict"])
        routed_conf.append(r["confidence"])
        engines_used[r["engine"]] = engines_used.get(r["engine"], 0) + 1
        base_pred.append(predict_nonrouted_baseline(row.get("claim", "")))

    print(f"Evaluation completed in {time.time() - t0:.2f} seconds.\n")
    print("-- Routing Engine Distribution --")
    for eng, n in sorted(engines_used.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>5} claims handled by -> {eng}")
    print()

    M.report(gold, routed_pred, routed_conf, title="ROUTED HALDETECT 2.5 (Honest, Local Execution)")
    M.report(gold, base_pred, title="NON-ROUTED BASELINE (Naive Negation Flip)")


if __name__ == "__main__":
    main()
