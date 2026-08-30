#!/usr/bin/env python3
"""
HalDetect 2.0 -- Frontier LLM Taxonomy Classification Benchmark
================================================================
Evaluates 3 Frontier Models on the 5-Modality Classification Task:
  1. 💎 Google Gemma 31B (gemma4:31b-cloud)
  2. 🧠 OpenAI GPT-OSS 120B (gpt-oss:120b-cloud)
  3. 🌐 MiniMax Text-01 M3 (minimax-m3:cloud)

Across 50 balanced claims (10 per modality) from the Master Benchmark.
"""

import csv
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict, Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCHMARK_CSV = HERE / "haldetect_master_benchmark_1000.csv"
OUT_CSV = HERE / "llm_taxonomy_classification_benchmark.csv"

MODELS = [
    {"name": "Gemma 31B (Cloud)", "model_id": "gemma4:31b-cloud"},
    {"name": "GPT-OSS 120B (Cloud)", "model_id": "gpt-oss:120b-cloud"},
    {"name": "MiniMax M3 (Cloud)", "model_id": "minimax-m3:cloud"}
]

PROMPT_TEMPLATE = """You are an expert computational linguist.
Classify the following factual claim into exactly ONE of the 5 categories:
- QUANTITATIVE (numbers, counts, physical measurements, currencies, percentages, arithmetic properties)
- TEMPORAL (years, dates, historical timelines, lifespans, calendar spans)
- ENTITY_ATTRIBUTE (birthplaces, locations, official awards, static entity definitions)
- CITATION (scientific DOIs, paper publication venues, journals, official author attribution)
- RELATIONAL (general entity relationships, actions, causal links, non-numeric assertions)

Claim: "{claim}"

Output ONLY the category name. Do not write explanation or intro."""

def main():
    print("=" * 80)
    print(" 🚀 STARTING 3-MODEL LLM TAXONOMY CLASSIFICATION BENCHMARK (N = 50 CLAIMS)")
    print("=" * 80)
    
    with open(BENCHMARK_CSV, "r", encoding="utf-8") as f:
        all_claims = list(csv.DictReader(f))
        
    # Select 10 balanced claims per modality (50 total)
    sample_claims = []
    by_mod = defaultdict(list)
    for c in all_claims:
        m = c["type"]
        if len(by_mod[m]) < 10:
            by_mod[m].append(c)
            sample_claims.append(c)
            
    print(f"Selected {len(sample_claims)} balanced claims (10 per modality).")
    
    results = []
    
    for model_info in MODELS:
        m_name = model_info["name"]
        m_id = model_info["model_id"]
        print(f"\n--- Benchmarking Classifier: {m_name} ({m_id}) ---")
        
        correct = 0
        latencies = []
        
        for idx, c in enumerate(sample_claims, 1):
            claim_text = c["claim"]
            gold_type = c["type"]
            
            payload = {
                "model": m_id,
                "prompt": PROMPT_TEMPLATE.format(claim=claim_text),
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 15}
            }
            
            t0 = time.time()
            try:
                req = urllib.request.Request(
                    "http://localhost:11434/api/generate",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_pred = data.get("response", "").strip().upper()
            except Exception as e:
                raw_pred = "ERROR"
            elapsed_ms = (time.time() - t0) * 1000
            latencies.append(elapsed_ms)
            
            # Normalize prediction
            clean_pred = "RELATIONAL"
            for candidate in ["QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"]:
                if candidate in raw_pred:
                    clean_pred = candidate
                    break
                    
            is_corr = (clean_pred == gold_type)
            if is_corr:
                correct += 1
                
            print(f"  [{idx:02d}/50] ({elapsed_ms:5.0f}ms) Gold: {gold_type:<18} | Pred: {clean_pred:<18} | {'✅' if is_corr else '❌'}")
            
            results.append({
                "model_name": m_name,
                "model_id": m_id,
                "claim_id": c.get("claim_id", f"C_{idx:02d}"),
                "gold_modality": gold_type,
                "predicted_modality": clean_pred,
                "is_correct": is_corr,
                "latency_ms": round(elapsed_ms, 2),
                "claim_text": claim_text
            })
            
        acc = (correct / len(sample_claims)) * 100
        avg_lat = sum(latencies) / len(latencies)
        print(f"\n>> {m_name} Overall Classification Accuracy: {correct}/50 ({acc:.1f}%) | Avg Latency: {avg_lat:.1f}ms")
        
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        fields = list(results[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n🎉 Saved all 150 classification trials to: {OUT_CSV}")

if __name__ == "__main__":
    main()
