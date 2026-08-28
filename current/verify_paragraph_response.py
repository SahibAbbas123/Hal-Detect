#!/usr/bin/env python3
"""
HalDetect Evolved (v2.0) -- End-to-End LLM Paragraph Factuality Evaluator
========================================================================
Evaluates the trustworthiness of an entire LLM-generated paragraph response:
  1. Decomposes raw multi-sentence text into Schema-Enriched 5-Tuple Propositions
  2. Executes Multi-Tier Neuro-Symbolic Verification on each proposition
  3. Aggregates results into a Response-Level Factuality Index & Hallucination Audit
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from schema_atomizer import SchemaAtomizer
from dimensional_quantity_engine import DimensionalQuantityEngine
from bidirectional_kg_resolver import BidirectionalKGResolver
import evolved_verifier_pipeline as EVP


class ParagraphFactualityEvaluator:
    """
    End-to-End Evaluator for multi-sentence LLM responses.
    """

    @classmethod
    def evaluate_response(cls, prompt: str, response_text: str) -> Dict[str, Any]:
        t0 = time.time()
        
        # 1. Split paragraph into sentences
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", response_text) if len(s.strip()) > 5]
        if not raw_sentences:
            raw_sentences = [response_text.strip()]

        # 2. Decompose all sentences into 5-Tuple Propositions
        all_propositions = []
        for sent_idx, sent in enumerate(raw_sentences, 1):
            props = SchemaAtomizer.atomize_sentence(sent)
            for p in props:
                p["sentence_index"] = sent_idx
                p["parent_sentence"] = sent
                all_propositions.append(p)

        # 3. Verify each proposition
        verified_claims = []
        for prop in all_propositions:
            raw_clause = prop.get("raw_clause", "")
            
            # Try Superlative Resolver first
            b_res = BidirectionalKGResolver.resolve_superlative_claim(raw_clause)
            if b_res:
                v_res = {
                    "verdict": b_res["verdict"],
                    "confidence": b_res["confidence"],
                    "evidence": b_res["evidence"],
                    "verifier": b_res["engine"]
                }
            else:
                v_res = EVP.verify_evolved_proposition(prop)

            verified_claims.append({
                "sentence_index": prop["sentence_index"],
                "parent_sentence": prop["parent_sentence"],
                "claim_text": raw_clause,
                "proposition": prop,
                "verdict": v_res["verdict"],
                "confidence": v_res["confidence"],
                "evidence": v_res["evidence"],
                "verifier": v_res["verifier"]
            })

        # 4. Aggregate Response-Level Factuality Metrics
        n_total = len(verified_claims)
        n_true = sum(1 for c in verified_claims if c["verdict"] == "TRUE")
        n_false = sum(1 for c in verified_claims if c["verdict"] == "FALSE")
        n_unv = sum(1 for c in verified_claims if c["verdict"] == "UNVERIFIABLE")
        n_answered = n_true + n_false

        factuality_score = (n_true / n_answered * 100.0) if n_answered > 0 else 0.0
        coverage = (n_answered / n_total * 100.0) if n_total > 0 else 0.0
        hallucination_rate = (n_false / n_total * 100.0) if n_total > 0 else 0.0

        elapsed_ms = round((time.time() - t0) * 1000, 2)

        return {
            "prompt": prompt,
            "response_text": response_text,
            "total_sentences": len(raw_sentences),
            "total_claims": n_total,
            "verified_true": n_true,
            "verified_false": n_false,
            "unverifiable": n_unv,
            "coverage_pct": round(coverage, 1),
            "factuality_index_pct": round(factuality_score, 1),
            "hallucination_rate_pct": round(hallucination_rate, 1),
            "latency_ms": elapsed_ms,
            "claims": verified_claims
        }

    @classmethod
    def print_audit_report(cls, report: Dict[str, Any]):
        print("\n" + "═" * 85)
        print("  HALDETECT RESPONSE-LEVEL FACTUALITY AUDIT CERTIFICATE")
        print("═" * 85)
        print(f" PROMPT: \"{report['prompt']}\"")
        print(f" TOTAL SENTENCES: {report['total_sentences']}  |  ATOMIC CLAIMS: {report['total_claims']}  |  LATENCY: {report['latency_ms']} ms")
        print("─" * 85)
        print(f" 📊 FACTUALITY INDEX (PRECISION):  {report['factuality_index_pct']}%")
        print(f" 🚨 HALLUCINATION RATE:            {report['hallucination_rate_pct']}%  ({report['verified_false']} false claims detected)")
        print(f" 🎯 COVERAGE:                      {report['coverage_pct']}%  ({report['verified_true'] + report['verified_false']}/{report['total_claims']} answered)")
        print("─" * 85)
        print(" CLAIMS BREAKDOWN:")
        for idx, c in enumerate(report["claims"], 1):
            icon = "✅ TRUE" if c["verdict"] == "TRUE" else "❌ FALSE" if c["verdict"] == "FALSE" else "⚠️ UNVERIFIED"
            print(f"\n [{idx:2d}] {icon:<14} (Conf: {c['confidence']:.2f}) | Engine: {c['verifier']}")
            print(f"      Claim:    \"{c['claim_text']}\"")
            print(f"      Evidence: {c['evidence'][:140]}...")
        print("═" * 85 + "\n")


if __name__ == "__main__":
    # Test on a realistic multi-sentence LLM response containing both truths and subtle hallucinations
    test_prompt = "Provide a biographical and economic summary of the United States and Barack Obama."
    test_llm_paragraph = (
        "Barack Obama served as the 44th President of the United States from 2009 to 2017. "
        "However, Barack Obama is currently the President of the United States in 2026. "
        "The nominal GDP of the United States reached 27.8 trillion dollars in 2023. "
        "Mount Everest is the highest mountain in Asia with an elevation of 8,848 meters."
    )

    report = ParagraphFactualityEvaluator.evaluate_response(test_prompt, test_llm_paragraph)
    ParagraphFactualityEvaluator.print_audit_report(report)
