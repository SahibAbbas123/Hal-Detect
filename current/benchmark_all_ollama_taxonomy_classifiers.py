#!/usr/bin/env python3
"""
HalDetect 2.0 -- Multi-LLM Taxonomy Classification Benchmark
============================================================
Evaluates the taxonomy classification accuracy and latency of all available
Ollama foundation models against HalDetect's deterministic symbolic router:
  1. Google Gemma 31B (gemma4:31b-cloud)
  2. OpenAI GPT-OSS 120B (gpt-oss:120b-cloud)
  3. MiniMax Text-01 M3 (minimax-m3:cloud)
  4. Bespoke MiniCheck 7B (bespoke-minicheck:latest)
"""

import csv
import json
import os
import re
import socket
import sys
import time
import urllib.request
from pathlib import Path
from collections import defaultdict, Counter

socket.setdefaulttimeout(15.0)

HERE = Path(__file__).resolve().parent
BENCHMARK_CSV = HERE / "haldetect_master_benchmark_1000.csv"
OUT_RESULTS_CSV = HERE / "all_ollama_taxonomy_classification_results.csv"
OUT_SUMMARY_CSV = HERE / "all_ollama_taxonomy_summary.csv"

OLLAMA_MODELS = [
    {"name": "Gemma 31B (Cloud)", "model_id": "gemma4:31b-cloud"},
    {"name": "GPT-OSS 120B (Cloud)", "model_id": "gpt-oss:120b-cloud"},
    {"name": "MiniMax M3 (Cloud)", "model_id": "minimax-m3:cloud"},
    {"name": "Bespoke MiniCheck 7B", "model_id": "bespoke-minicheck:latest"}
]

PROMPT_TEMPLATE = """You are a linguist and factual claim classifier.
Classify the following factual claim into exactly ONE of the 5 categories:
- QUANTITATIVE (numbers, counts, physical measurements, currencies, percentages)
- TEMPORAL (years, dates, historical timelines, lifespans)
- ENTITY_ATTRIBUTE (birthplaces, locations, official awards, static properties)
- CITATION (scientific DOIs, paper venues, journals, author attribution)
- RELATIONAL (general entity relationships, actions, non-numeric assertions)

Claim: "{claim}"

Output ONLY the category name. No other words."""

def haldetect_router(claim_text: str) -> str:
    """HalDetect's symbolic regex & lexicon router."""
    c = claim_text.strip()
    if re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+|doi|published in|journal|conference|arxiv|states that|reports that|according to)\b", c, re.I):
        return "CITATION"
    elif re.search(r"\b(\d+(\.\d+)?\s*(k|c|kelvin|celsius|meters|kg|m/s|billion|million|cores|qubits|gb|tb|nm|watts|tflops|ghz|\$|usd|%))\b", c, re.I):
        return "QUANTITATIVE"
    elif re.search(r"\b(in \d{4}|from \d{4}|between \d{4}|born in \d{4}|died in \d{4}|published in \d{4}|\b(19\d\d|20\d\d)\b)\b", c, re.I):
        return "TEMPORAL"
    elif re.search(r"\b(born in|died in|capital of|located in|awarded|invented by|authored by)\b", c, re.I):
        return "ENTITY_ATTRIBUTE"
    else:
        return "RELATIONAL"

def query_ollama_classifier(model_id: str, claim: str) -> tuple[str, float]:
    t0 = time.time()
    payload = {
        "model": model_id,
        "prompt": PROMPT_TEMPLATE.format(claim=claim),
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 15}
    }
    
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data.get("response", "").strip().upper()
            elapsed = (time.time() - t0) * 1000
            
            for m in ["QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"]:
                if m in raw:
                    return m, elapsed
            return "RELATIONAL", elapsed
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        return "ERROR", elapsed

def main():
    print("=" * 90)
    print(" 🚀 STARTING MULTI-LLM TAXONOMY CLASSIFICATION BENCHMARK")
    print("=" * 90)
    
    with open(BENCHMARK_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    # Select 50 balanced claims (10 per modality)
    sample_50 = []
    by_modality = defaultdict(list)
    for r in rows:
        m = r['type']
        if len(by_modality[m]) < 10:
            by_modality[m].append(r)
            sample_50.append(r)
            
    print(f"Loaded {len(sample_50)} balanced claims across all 5 modalities (10/modality).")
    
    all_results = []
    summary_stats = {}
    
    # 1. Benchmark HalDetect Router
    hd_correct = 0
    t0 = time.time()
    for r in sample_50:
        pred = haldetect_router(r['claim'])
        if pred == r['type']:
            hd_correct += 1
    hd_latency = ((time.time() - t0) / len(sample_50)) * 1000
    summary_stats["HalDetect Symbolic Router"] = {
        "correct": hd_correct,
        "total": len(sample_50),
        "accuracy": (hd_correct / len(sample_50)) * 100,
        "avg_latency_ms": hd_latency
    }
    
    # 2. Benchmark Ollama Models
    for m in OLLAMA_MODELS:
        m_name = m["name"]
        m_id = m["model_id"]
        print(f"\n--- Testing Model: {m_name} ({m_id}) ---")
        
        m_correct = 0
        latencies = []
        modality_correct = defaultdict(int)
        
        for idx, r in enumerate(sample_50, 1):
            c_text = r['claim']
            gold_type = r['type']
            
            pred_type, lat = query_ollama_classifier(m_id, c_text)
            latencies.append(lat)
            
            is_corr = (pred_type == gold_type)
            if is_corr:
                m_correct += 1
                modality_correct[gold_type] += 1
                
            all_results.append({
                "model_name": m_name,
                "model_id": m_id,
                "claim_id": r.get("claim_id", f"CLM_{idx:03d}"),
                "claim_text": c_text,
                "gold_type": gold_type,
                "predicted_type": pred_type,
                "is_correct": is_corr,
                "latency_ms": round(lat, 1)
            })
            
            if idx % 10 == 0:
                print(f"  [{idx:02d}/50] Current Acc: {m_correct}/{idx} ({m_correct/idx:.1%}) | Last Latency: {lat:.0f}ms")
                
        summary_stats[m_name] = {
            "correct": m_correct,
            "total": len(sample_50),
            "accuracy": (m_correct / len(sample_50)) * 100,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0
        }
        
    # Save granular results
    with open(OUT_RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
        fields = list(all_results[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_results)
        
    # Print Master Summary Table
    print("\n" + "=" * 90)
    print(f"{'Classifier / Pipeline Paradigm':<30} | {'Correct':<8} | {'Total':<6} | {'Accuracy':<10} | {'Avg Latency':<14} | {'Speedup'}")
    print("-" * 90)
    
    hd_lat = summary_stats["HalDetect Symbolic Router"]["avg_latency_ms"]
    for name, s in summary_stats.items():
        corr = s['correct']
        tot = s['total']
        acc = s['accuracy']
        lat = s['avg_latency_ms']
        speedup = "BASELINE (1.0x)" if name == "HalDetect Symbolic Router" else f"{lat/hd_lat:,.0f}x slower" if hd_lat > 0 else "N/A"
        print(f"{name:<30} | {corr:>4}     | {tot:>4}   | {acc:>6.2f}%    | {lat:>7.2f} ms     | {speedup}")
    print("=" * 90)
    print(f"\n🎉 Saved granular results to: {OUT_RESULTS_CSV}")

if __name__ == "__main__":
    main()
