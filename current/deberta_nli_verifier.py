#!/usr/bin/env python3
"""
HalDetect -- Local DeBERTa-v3 Fact-Checking NLI Modernizer (Track D Local)
=========================================================================
Runs modern cross-encoder NLI (cross-encoder/nli-deberta-v3-small) natively
on Apple Silicon Metal GPU (mps) to modernize the NLI engine on the local Mac.
"""

import collections
import csv
import math
import os
import sys
import time
from pathlib import Path
import torch

HERE = Path(__file__).resolve().parent
INPUT_CSV = HERE / "kaggle_minicheck_input_claims.csv"
OUT_CSV = HERE / "deberta_rescore_results.csv"
MODEL_NAME = "cross-encoder/nli-deberta-v3-small"

def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def run_deberta_evaluation():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    dev = get_device()
    print(f"Loading {MODEL_NAME} onto {dev}...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).to(dev)
    model.eval()
    print(f"Model ready in {time.time()-t0:.1f}s.")

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Evaluating {len(rows)} claims with DeBERTa-v3 on {dev}...")
    results = []
    t_start = time.time()

    # Model outputs for cross-encoder/nli-deberta-v3: [contradiction (0), entailment (1), neutral (2)]
    for i, r in enumerate(rows, 1):
        c_start = time.time()
        premise = r.get("evidence_passage", "").strip() or r.get("claim", "")
        claim = r.get("claim", "").strip()
        gold = r.get("gold_verdict", "UNVERIFIABLE").strip().upper()

        inputs = tokenizer(premise, claim, return_tensors="pt", truncation=True, max_length=512).to(dev)
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]

        p_contra = float(probs[0].item())
        p_entail = float(probs[1].item())
        p_neutral = float(probs[2].item())
        c_elapsed = (time.time() - c_start) * 1000

        # Calibrated 3-way decision rule
        if p_entail >= 0.50 and (p_entail - p_contra) >= 0.15:
            pred = "TRUE"
            conf = round(0.50 + p_entail * 0.45, 3)
        elif p_contra >= 0.40 and (p_contra - p_entail) >= 0.10:
            pred = "FALSE"
            conf = round(0.50 + p_contra * 0.40, 3)
        else:
            pred = "UNVERIFIABLE"
            conf = 0.40

        is_answered = (pred != "UNVERIFIABLE")
        is_correct = (pred == gold) if is_answered else False

        entry = {
            **r,
            "deberta_pred": pred,
            "deberta_conf": conf,
            "p_entail": round(p_entail, 4),
            "p_contra": round(p_contra, 4),
            "p_neutral": round(p_neutral, 4),
            "is_answered": is_answered,
            "is_correct": is_correct,
            "latency_ms": round(c_elapsed, 1),
        }
        results.append(entry)

        if i % 100 == 0 or i == len(rows):
            elapsed = time.time() - t_start
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  [{i:4d}/{len(rows):4d}] ({elapsed:5.1f}s | {rate:4.1f} claims/s) Last: {r['claim_id']} -> {pred} (Gold: {gold})")

    # Save CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved DeBERTa results to {OUT_CSV}")

    # Compute Metrics
    answered = [x for x in results if x["is_answered"]]
    n_ans = len(answered)
    cov = n_ans / len(results) if results else 0.0
    corr = sum(1 for x in answered if x["is_correct"])
    sel_acc = corr / n_ans if n_ans > 0 else 0.0

    pred_true = [x for x in results if x["deberta_pred"] == "TRUE"]
    p_true = sum(1 for x in pred_true if x["gold_verdict"] == "TRUE") / len(pred_true) if pred_true else 0.0

    pred_false = [x for x in results if x["deberta_pred"] == "FALSE"]
    p_false = sum(1 for x in pred_false if x["gold_verdict"] == "FALSE") / len(pred_false) if pred_false else 0.0
    gold_false = [x for x in results if x["gold_verdict"] == "FALSE"]
    r_false = sum(1 for x in pred_false if x["gold_verdict"] == "FALSE") / len(gold_false) if gold_false else 0.0
    f1_false = (2 * p_false * r_false / (p_false + r_false)) if (p_false + r_false) > 0 else 0.0

    print("\n" + "="*80)
    print(f" LOCAL DEBERTA-V3 FACT-CHECKING REPORT (N={len(results)})")
    print("="*80)
    print(f"  • Coverage:              {cov*100:.1f}% ({n_ans}/{len(results)})")
    print(f"  • Selective Accuracy:    {sel_acc*100:.1f}% ({corr}/{n_ans})")
    print(f"  • Precision (TRUE):      {p_true*100:.1f}% ({len(pred_true)} predicted)")
    print(f"  • Precision (FALSE):     {p_false*100:.1f}% ({len(pred_false)} predicted)")
    print(f"  • Hallucination F1:      {f1_false:.3f} (Recall: {r_false*100:.1f}%)")
    print(f"  • Total Time:            {time.time()-t_start:.1f}s ({len(results)/(time.time()-t_start):.1f} claims/s)")
    print("-"*80)

    by_type = collections.defaultdict(list)
    for x in results:
        by_type[x["type"]].append(x)

    print(f"\n{'Modality':<20} | {'Total':<6} | {'Cov %':<6} | {'Sel Acc %':<10} | {'P(TRUE)':<8} | {'P(FALSE)':<8} | {'F1(FALSE)'}")
    print(f"{'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*10}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}")
    for mod, mod_res in sorted(by_type.items()):
        ans = [x for x in mod_res if x["is_answered"]]
        m_cov = len(ans) / len(mod_res) if mod_res else 0.0
        m_acc = sum(1 for x in ans if x["is_correct"]) / len(ans) if ans else 0.0
        pt = [x for x in mod_res if x["deberta_pred"] == "TRUE"]
        ppt = sum(1 for x in pt if x["gold_verdict"] == "TRUE") / len(pt) if pt else 0.0
        pf = [x for x in mod_res if x["deberta_pred"] == "FALSE"]
        ppf = sum(1 for x in pf if x["gold_verdict"] == "FALSE") / len(pf) if pf else 0.0
        gf = [x for x in mod_res if x["gold_verdict"] == "FALSE"]
        rf = sum(1 for x in pf if x["gold_verdict"] == "FALSE") / len(gf) if gf else 0.0
        f1f = (2 * ppf * rf / (ppf + rf)) if (ppf + rf) > 0 else 0.0
        print(f"{mod:<20} | {len(mod_res):<6} | {m_cov*100:>5.1f}% | {m_acc*100:>9.1f}% | {ppt*100:>6.1f}% | {ppf*100:>6.1f}% | {f1f:>8.3f}")
    print("="*80)

if __name__ == "__main__":
    run_deberta_evaluation()
