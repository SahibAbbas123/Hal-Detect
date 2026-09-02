#!/usr/bin/env python3
"""
HalDetect 2.5 -- Bidirectional & Superlative Knowledge Graph Resolver (v2 - Option A)
========================================================================
Solves the "Inverse Superlative" and "Topological Meronym/Holonym" lookup failure.
  • Forward Lookup: S -> P -> O  (Standard Wikidata queries)
  • Inverse Container Lookup: Container -> P610 (highest point) / P36 (capital) -> S
  • Real Dynamic SPARQL Resolution (Zero Hardcoded Stubs).
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
import requests

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
USER_AGENT = "AcademicResearchBot/2.5 (contact@example.com)"

_SUPERLATIVE_PATTERNS = [
    (r"^(.*?)\s+is\s+(?:the\s+)?(?:highest|tallest)\s+(?:mountain|peak|point)\s+in\s+(.*?)(?:\.|$)", "P610"),
    (r"^(.*?)\s+is\s+(?:the\s+)?(?:lowest)\s+(?:point)\s+in\s+(.*?)(?:\.|$)", "P1589"),
    (r"^(.*?)\s+is\s+(?:the\s+)?(?:capital|largest city)\s+of\s+(.*?)(?:\.|$)", "P36")
]

class BidirectionalKGResolver:
    """
    Executes dynamic bidirectional and inverse topological traversals using pure SPARQL.
    """

    @classmethod
    def query_wikidata_property_by_label(cls, container_name: str, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Queries a specific property for a container (by its English label) and fetches English labels and altLabels.
        """
        query = f"""
        SELECT ?item ?itemLabel (GROUP_CONCAT(?altLabel; separator="|") AS ?altLabels) WHERE {{
          ?container rdfs:label "{container_name}"@en .
          ?container wdt:{property_id} ?item .
          OPTIONAL {{ ?item skos:altLabel ?altLabel . FILTER (lang(?altLabel) = "en") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }} GROUP BY ?item ?itemLabel LIMIT 1
        """
        try:
            resp = requests.get(
                WIKIDATA_SPARQL,
                params={"query": query, "format": "json"},
                headers={"User-Agent": USER_AGENT},
                timeout=5.0
            )
            if resp.status_code == 200:
                bindings = resp.json().get("results", {}).get("bindings", [])
                if bindings:
                    b = bindings[0]
                    aliases = [a.strip() for a in b.get("altLabels", {}).get("value", "").split("|") if a.strip()]
                    return {
                        "name": b.get("itemLabel", {}).get("value", ""),
                        "qid": b.get("item", {}).get("value", "").split("/")[-1],
                        "aliases": aliases
                    }
        except Exception:
            pass
        return None

    @classmethod
    def resolve_superlative_claim(cls, claim_text: str) -> Optional[Dict[str, Any]]:
        """
        Detects superlative container claims and performs inverse lookup.
        """
        t0 = time.time()
        for pat, prop_id in _SUPERLATIVE_PATTERNS:
            m = re.search(pat, claim_text, re.I)
            if m:
                subj = m.group(1).strip()
                container = m.group(2).strip()
                
                # Fetch the topological superlative from Wikidata
                grounded = cls.query_wikidata_property_by_label(container, prop_id)
                if not grounded:
                    return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "evidence": f"No data found for property {prop_id} on container '{container}'"}

                grounded_name = grounded.get("name", "")
                aliases = grounded.get("aliases", [])
                
                # Robust alias-aware matching instead of simple substring
                valid_names = [grounded_name.lower()] + [a.lower() for a in aliases]
                subj_lower = subj.lower()
                
                is_match = False
                for vn in valid_names:
                    # Allow exact match or if the subject is a substantive part of the true name (or vice-versa)
                    # For example, "Mount Everest" and "Everest" should match.
                    if subj_lower == vn or subj_lower in vn or vn in subj_lower:
                        is_match = True
                        break
                
                return {
                    "verdict": "TRUE" if is_match else "FALSE",
                    "confidence": 0.98,
                    "container_name": container.title(),
                    "grounded_target": grounded_name,
                    "claimed_subject": subj,
                    "engine": "Bidirectional Superlative KG Resolver (Option A)",
                    "latency_ms": round((time.time() - t0) * 1000, 2),
                    "evidence": f"SPARQL resolution: Container '{container.title()}' has P{prop_id} = '{grounded_name}', asserted subject '{subj}' (Match={is_match})."
                }
        return None

if __name__ == "__main__":
    print("=" * 80)
    print(" TESTING PURE SPARQL KG RESOLVER (OPTION A)")
    print("=" * 80)

    test_claims = [
        "Denali is the tallest mountain in North America",
        "K2 is the highest mountain in Africa",
        "Paris is the capital of France",
        "Sydney is the capital of Australia",
        "Death Valley is the lowest point in North America"
    ]

    for tc in test_claims:
        res = BidirectionalKGResolver.resolve_superlative_claim(tc)
        print(f"\nCLAIM: \"{tc}\"")
        if res:
            print(f"  VERDICT: {res['verdict']} (Confidence: {res['confidence']})")
            print(f"  EVIDENCE: {res['evidence']}")
        else:
            print("  No inverse pattern triggered.")
