#!/usr/bin/env python3
"""
HalDetect -- Oracle-Passage Neural NLI Grounding Baseline (MiniCheck / FActScore Paradigm)
========================================================================================
A standardized Neural NLI fact-verification baseline that pairs:
  1. Passage-level Salience Chunking & Token-Overlap Filtering
  2. DeBERTa-v3 Cross-Encoder Entailment Grounding (cross-encoder/nli-deberta-v3-small)
  3. Calibrated Margin-Based Decision Thresholding with Explicit Abstention

Evaluates against benchmark datasets with attached reference document passages.
Note: For open-world search-augmented retrieval, see `rag_baseline.py`.
"""

from __future__ import annotations

import collections
import csv
import json
import math
import os
import re
import sys
import time
import warnings
from pathlib import Path

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore")

import torch

HERE = Path(__file__).resolve().parent
INPUT_CSV = HERE / "kaggle_minicheck_input_claims.csv"
OUTPUT_CSV = HERE / "sota_rag_evaluation_results.csv"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"

def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def run_sota_rag_benchmark():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    dev = get_device()
    print(f"Loading Oracle-Passage Neural NLI Engine ({NLI_MODEL}) onto {dev}...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL).to(dev)
    model.eval()
    print(f"Neural NLI Engine initialized in {time.time()-t0:.1f}s.")

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        claims = list(csv.DictReader(f))

    print(f"\nRunning Oracle-Passage NLI Grounding evaluation on {len(claims)} claims...")
    results = []
    t_start = time.time()

    for idx, r in enumerate(claims, 1):
        c_start = time.time()
        claim_text = r.get("claim", "").strip()
        evidence = r.get("evidence_passage", "").strip()
        gold = r.get("gold_verdict", "UNVERIFIABLE").strip().upper()
        mid = r.get("master_id", f"MST_{idx:04d}")
        cid = r.get("claim_id", "")
        mod = r.get("type", "UNKNOWN")

        # Guard: If evidence is missing, ABSTAIN explicitly (DO NOT compare claim against itself!)
        if not evidence:
            res = {
                "master_id": mid,
                "claim_id": cid,
                "type": mod,
                "origin_dataset": r.get("origin_dataset", ""),
                "claim": claim_text,
                "gold_verdict": gold,
                "sota_rag_verdict": "UNVERIFIABLE",
                "sota_rag_conf": 0.0,
                "p_entail": 0.0,
                "p_contra": 0.0,
                "p_neutral": 1.0,
                "is_answered": False,
                "is_correct": False,
                "latency_ms": 0.1,
                "retrieved_context": "MISSING_EVIDENCE_PASSAGE"
            }
            results.append(res)
            continue

        # 1. Sliding Window Chunking & Relevance Filtering
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", evidence) if len(s.strip()) > 15]
        if not sentences:
            sentences = [evidence]

        # Score relevance of sentences via token overlap
        claim_tokens = set(re.findall(r"\b\w{3,}\b", claim_text.lower()))
        scored_chunks = []
        for s in sentences:
            s_tokens = set(re.findall(r"\b\w{3,}\b", s.lower()))
            overlap = len(claim_tokens & s_tokens) / len(claim_tokens) if claim_tokens else 0.0
            scored_chunks.append((overlap, s))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_context = " ".join([c[1] for c in scored_chunks[:3]]) if scored_chunks else evidence

        # 2. DeBERTa-v3 Cross-Encoder Entailment Verification
        inputs = tokenizer(top_context, claim_text, return_tensors="pt", truncation=True, max_length=512).to(dev)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]

        # classes: [contradiction, entailment, neutral]
        p_contra = float(probs[0].item())
        p_entail = float(probs[1].item())
        p_neutral = float(probs[2].item())
        elapsed_ms = (time.time() - c_start) * 1000

        # Calibrated Decision Threshold with Abstention
        if p_entail >= 0.55 and (p_entail - p_contra) >= 0.20:
            pred = "TRUE"
            conf = round(0.55 + p_entail * 0.40, 3)
        elif p_contra >= 0.45 and (p_contra - p_entail) >= 0.15:
            pred = "FALSE"
            conf = round(0.55 + p_contra * 0.40, 3)
        else:
            pred = "UNVERIFIABLE"
            conf = 0.35

        is_answered = (pred != "UNVERIFIABLE")
        is_correct = (pred == gold) if is_answered else False

        res = {
            "master_id": mid,
            "claim_id": cid,
            "type": mod,
            "origin_dataset": r.get("origin_dataset", ""),
            "claim": claim_text,
            "gold_verdict": gold,
            "sota_rag_verdict": pred,
            "sota_rag_conf": conf,
            "p_entail": round(p_entail, 4),
            "p_contra": round(p_contra, 4),
            "p_neutral": round(p_neutral, 4),
            "is_answered": is_answered,
            "is_correct": is_correct,
            "latency_ms": round(elapsed_ms, 1),
            "retrieved_context": top_context[:180] + "..." if len(top_context) > 180 else top_context
        }
        results.append(res)

        if idx % 100 == 0 or idx == len(claims):
            tot_el = time.time() - t_start
            rate = idx / tot_el if tot_el > 0 else 0
            print(f"  [{idx:4d}/{len(claims):4d}] ({tot_el:5.1f}s | {rate:4.1f} claims/s) Last: {cid:<12} -> {pred:<12} (Gold: {gold})")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        fields = list(results[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved {len(results)} evaluation results to {OUTPUT_CSV}")

if __name__ == "__main__":
    run_sota_rag_benchmark()
