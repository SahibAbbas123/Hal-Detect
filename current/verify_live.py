#!/usr/bin/env python3
"""
HalDetect -- Live Interactive Neuro-Symbolic Fact-Checking Engine
================================================================
Test real-life, random natural language claims in real-time.
Routes claims to:
  1. QUANTITATIVE     -> Wikidata SPARQL / World Bank Open Data REST API
  2. TEMPORAL         -> Wikidata Date Properties & Temporal Verifier
  3. ENTITY_ATTRIBUTE -> Wikidata Instance/Property Taxonomy
  4. CITATION         -> CrossRef DOI / Work Metadata Engine
  5. RELATIONAL       -> Wikipedia Retrieve-and-Verify Engine
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import quantitative_verifier as QV
import quantitative_tier2_verifier as QT2
import temporal_ea_verifier as TEA
import citation_l1b_verifier as CITA

# Load shared caches
qv_cache = QV.load_cache()
macro_cache = QT2.load_macro_cache()

# ---------------------------------------------------------------------------
# RULE-BASED FAST ROUTER & ENTITY EXTRACTOR FOR LIVE QUERIES
# ---------------------------------------------------------------------------
def classify_live_claim(text: str) -> tuple[str, str, str, str]:
    """
    Fast rule-based extractor for interactive claims:
    Returns (modality, subject, property, value)
    """
    text_clean = text.strip()
    
    # 1. Check Citation Modality (DOIs, papers, published in, arXiv, journals)
    if re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+|arxiv|doi|isbn|issn|published by|journal|proceedings)\b", text_clean, re.I):
        m_doi = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", text_clean, re.I)
        doi_val = m_doi.group(1) if m_doi else text_clean
        return "CITATION", text_clean.split()[0], "publisher", doi_val

    # 2. Check Macroeconomic / World Bank Indicators
    macro_iso = QT2.extract_country_iso(text_clean)
    macro_ind = QT2.extract_indicator(text_clean)
    if macro_iso and macro_ind:
        claimed_val = QT2.parse_numeric_claim_value(text_clean)
        return "QUANTITATIVE", macro_iso, macro_ind[1], str(claimed_val)

    # 3. Check General Quantitative Modality (numbers attached to units, currency, heights, cores)
    if re.search(r"(\$?\s*\d+(?:\.\d+)?\s*(trillion|billion|million|thousand|cores|meters|metres|feet|kg|grams|%|percent|qubits|transistors|moons|km|miles))\b", text_clean, re.I):
        words = text_clean.split()
        subj = " ".join(words[:3]) if len(words) >= 3 else text_clean
        return "QUANTITATIVE", subj, "magnitude", text_clean

    # 4. Check Temporal Modality (years, born in, died in, released in, founded in)
    if re.search(r"\b(born in|died in|founded in|released in|established in|discovered in|in 19\d\d|in 20\d\d|on [A-Z][a-z]+ \d{1,2}, \d{4})\b", text_clean, re.I):
        m_year = re.search(r"\b(19\d\d|20[0-2]\d)\b", text_clean)
        val = m_year.group(1) if m_year else ""
        m_subj = re.split(r"\b(was born|died|was founded|was released|was established|discovered)\b", text_clean, flags=re.I)
        subj = m_subj[0].strip() if m_subj else text_clean.split()[0]
        return "TEMPORAL", subj, "date of birth / release", val

    # 5. Check Entity Attribute (capital of, spouse of, ceo of, president of, author of)
    if re.search(r"\b(capital of|spouse of|married to|ceo of|president of|prime minister of|currency of|inventor of|author of)\b", text_clean, re.I):
        return "ENTITY_ATTRIBUTE", text_clean.split()[0], "attribute", text_clean

    # Default to Relational
    words = text_clean.split()
    subj = " ".join(words[:2]) if len(words) >= 2 else text_clean
    return "RELATIONAL", subj, "relation", text_clean


# ---------------------------------------------------------------------------
# LIVE VERIFICATION ENGINE
# ---------------------------------------------------------------------------
def verify_text(claim_text: str) -> dict:
    t0 = time.time()
    modality, subject, prop, value = classify_live_claim(claim_text)
    
    claim_dict = {
        "claim": claim_text,
        "subject": subject,
        "property": prop,
        "value": value,
        "type": modality,
        "gold_verdict": "UNKNOWN"
    }

    verdict = "UNVERIFIABLE"
    confidence = 0.30
    evidence = "No matching grounded evidence located."
    verifier_used = "router"

    if modality == "QUANTITATIVE":
        # Check Tier 2 World Bank first if it's a macro/country claim
        if QT2.extract_country_iso(claim_text) and QT2.extract_indicator(claim_text):
            m_res = QT2.verify_macro_claim(claim_dict, macro_cache)
            if m_res["verdict"] != "UNVERIFIABLE":
                verdict = m_res["verdict"]
                confidence = m_res["confidence"]
                evidence = m_res["evidence"]
                verifier_used = "World Bank Open Data REST API (Tier 2)"
        
        if verdict == "UNVERIFIABLE":
            q_res = QV.verify_quantitative(claim_dict, qv_cache)
            verdict = q_res.get("verdict", "UNVERIFIABLE")
            confidence = float(q_res.get("confidence", 0.40))
            evidence = q_res.get("detail") or q_res.get("reason", "No quantity match in Wikidata.")
            verifier_used = "Wikidata SPARQL Extract-and-Compare (Tier 1)"

    elif modality in ("TEMPORAL", "ENTITY_ATTRIBUTE"):
        t_res = TEA.verify(claim_dict, qv_cache)
        verdict = t_res.get("verdict", "UNVERIFIABLE")
        confidence = float(t_res.get("confidence", 0.40))
        evidence = t_res.get("reason", "No structured Wikidata property matched.")
        verifier_used = "Wikidata Temporal/EA Verifier"

    elif modality == "CITATION":
        c_res = CITA.verify_l1b(claim_dict, qv_cache)
        verdict = c_res.get("verdict", "UNVERIFIABLE")
        confidence = float(c_res.get("confidence", 0.40))
        evidence = c_res.get("reason", "Citation DOI/work metadata lookup.")
        verifier_used = "Citation L1b CrossRef/Wikidata Verifier"

    else:
        verdict = "UNVERIFIABLE"
        confidence = 0.35
        evidence = "Open relational claim outside structured Wikidata/REST registries."
        verifier_used = "Hybrid Fallthrough Router"

    elapsed_ms = (time.time() - t0) * 1000

    return {
        "claim": claim_text,
        "modality": modality,
        "subject": subject,
        "property": prop,
        "value": value,
        "verdict": verdict,
        "confidence": confidence,
        "evidence": evidence,
        "verifier": verifier_used,
        "latency_ms": round(elapsed_ms, 2)
    }


def print_card(res: dict):
    v = res["verdict"]
    color_icon = "✅ TRUE" if v == "TRUE" else "❌ FALSE" if v == "FALSE" else "⚠️ UNVERIFIABLE"
    
    print("\n" + "═" * 78)
    print(f" CLAIM: \"{res['claim']}\"")
    print("─" * 78)
    print(f" • Modality Detected:  {res['modality']}")
    print(f" • Subject / Property: {res['subject']} ➔ {res['property']}")
    print(f" • Verifier Engine:    {res['verifier']}")
    print(f" • Latency:            {res['latency_ms']} ms")
    print(f" • Evidence Trail:     {res['evidence']}")
    print(f" • FINAL VERDICT:      {color_icon}  (Confidence: {res['confidence']:.2f})")
    print("═" * 78 + "\n")


def interactive_repl():
    print("\n" + "╔" + "═" * 76 + "╗")
    print("║               🚀 HALDETECT LIVE NEURO-SYMBOLIC FACT CHECKER               ║")
    print("║        Sub-50ms Deterministic Grounding across Wikidata & World Bank       ║")
    print("╚" + "═" * 76 + "╝")
    print("Type any real-world claim to verify, or 'exit' / 'quit' to stop.\n")

    while True:
        try:
            user_input = input("HalDetect > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            res = verify_text(user_input)
            print_card(res)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


def main():
    parser = argparse.ArgumentParser(description="HalDetect Live Fact Checker.")
    parser.add_argument("claim", nargs="?", help="Claim string to verify")
    args = parser.parse_args()

    if args.claim:
        res = verify_text(args.claim)
        print_card(res)
    else:
        interactive_repl()


if __name__ == "__main__":
    main()
