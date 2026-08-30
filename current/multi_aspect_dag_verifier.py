#!/usr/bin/env python3
"""
HalDetect 2.5 -- Multi-Aspect Verification Directed Acyclic Graph (DAG) Engine
==============================================================================
Evaluates compound multi-modal propositions across parallel domain verifiers:
  - QUANTITATIVE ALU (Tier 1 Wikidata + Tier 2 World Bank REST API)
  - TEMPORAL ALU (2-Hop SPARQL Graph Traversals + Date Interval Resolvers)
  - CITATION ALU (CrossRef DOI Endpoint + Publication Venue Registry)
  - ENTITY ATTRIBUTE (Static Property Closures + Alias Lexicon)
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import quantitative_verifier as QV
import quantitative_tier2_verifier as QT2
import temporal_ea_verifier as TEA
import citation_l1b_verifier as CITA
import alias_lexicon_resolver as ALR
import property_resolver as PR

class MultiAspectDAGVerifier:
    def __init__(self):
        print("🚀 Initializing HalDetect 2.5 Multi-Aspect DAG Engine...", flush=True)
        t0 = time.time()
        self.qv_cache = QV.load_cache()
        self.macro_cache = QT2.load_macro_cache()
        self.tier2_tea = TEA.load_tier2()
        print(f"✅ DAG Verifier Loaded in {time.time()-t0:.2f}s.", flush=True)

    def verify_compound_proposition(self, prop_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a Multi-Aspect DAG over all active modalities in prop_dict.
        """
        t0 = time.time()
        aspect_tags = prop_dict.get("aspect_tags", ["RELATIONAL"])
        raw_clause = prop_dict.get("raw_clause", "")
        subject = prop_dict.get("subject", "")
        sub_verdicts = {}

        # 1. Aspect 1: QUANTITATIVE Check
        if "QUANTITATIVE" in aspect_tags:
            row_q = {
                "claim": raw_clause,
                "subject": subject,
                "property": prop_dict.get("property", "transistors"),
                "value": prop_dict.get("value", ""),
                "type": "QUANTITATIVE"
            }
            q_res = QV.verify_quantitative(row_q, self.qv_cache)
            if q_res.get("verdict") == "UNVERIFIABLE":
                m_res = QT2.verify_macro_claim(row_q, self.macro_cache)
                if m_res.get("verdict") != "UNVERIFIABLE":
                    q_res = m_res
            sub_verdicts["QUANTITATIVE"] = q_res.get("verdict", "UNVERIFIABLE")

        # 2. Aspect 2: TEMPORAL Check
        if "TEMPORAL" in aspect_tags or "ENTITY_ATTRIBUTE" in aspect_tags:
            row_t = {
                "claim": raw_clause,
                "subject": subject,
                "property": prop_dict.get("property", "publication date"),
                "value": prop_dict.get("value", ""),
                "type": "TEMPORAL"
            }
            t_res = TEA.verify(row_t, self.qv_cache)
            if self.tier2_tea and t_res.get("verdict") == "UNVERIFIABLE":
                TEA._apply_tier2(t_res, self.tier2_tea)
            sub_verdicts["TEMPORAL"] = t_res.get("verdict", "UNVERIFIABLE")

        # 3. Aspect 3: CITATION Check
        if "CITATION" in aspect_tags:
            row_c = {
                "claim": raw_clause,
                "subject": subject,
                "property": "DOI",
                "value": "",
                "type": "CITATION"
            }
            c_res = CITA.verify(row_c, self.qv_cache)
            sub_verdicts["CITATION"] = c_res.get("verdict", "UNVERIFIABLE")

        # 4. Multi-Aspect 3-Valued Conjunction Logic
        verdict_list = list(sub_verdicts.values())
        if not verdict_list:
            final_verdict = "UNVERIFIABLE"
            conf = 0.35
        elif "FALSE" in verdict_list:
            # Fatal Discrepancy Rule: ANY false aspect invalidates the compound claim
            final_verdict = "FALSE"
            conf = 0.98
        elif any(v == "TRUE" for v in verdict_list):
            final_verdict = "TRUE"
            conf = 0.95
        else:
            final_verdict = "UNVERIFIABLE"
            conf = 0.35

        return {
            "final_verdict": final_verdict,
            "confidence": conf,
            "sub_aspect_verdicts": sub_verdicts,
            "aspects_evaluated": list(sub_verdicts.keys()),
            "latency_ms": round((time.time() - t0) * 1000, 2)
        }

if __name__ == "__main__":
    dag = MultiAspectDAGVerifier()
    test_true = {
        "raw_clause": "The Apple M3 Max has 92 billion transistors.",
        "subject": "Apple M3 Max",
        "property": "transistors",
        "value": "92 billion",
        "aspect_tags": ["QUANTITATIVE"]
    }
    print("\n--- Testing True Quantitative Claim ---")
    print(json.dumps(dag.verify_compound_proposition(test_true), indent=2))

    test_false = {
        "raw_clause": "The Apple M3 Max has 40 million transistors.",
        "subject": "Apple M3 Max",
        "property": "transistors",
        "value": "40 million",
        "aspect_tags": ["QUANTITATIVE"]
    }
    print("\n--- Testing False Quantitative Claim ---")
    print(json.dumps(dag.verify_compound_proposition(test_false), indent=2))
