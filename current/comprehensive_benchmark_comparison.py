#!/usr/bin/env python3
"""
HalDetect -- Master 4-Way System Benchmark Comparison (N = 1,005 Claims)
========================================================================
Compares:
1. HalDetect Neuro-Symbolic Taxonomy Router (Ours)
2. Web-Search RAG Baseline (MediaWiki + SBERT + BART-MNLI)
3. Uniform DeBERTa-v3 (Cross-Encoder NLI)
4. Uniform MiniCheck (SOTA EMNLP 2024 Fact-Checker from Kaggle)
"""

import collections
import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

HALDETECT_CSV = HERE / "master_corpus_v2_evaluation_results.csv"
RAG_CSV = HERE / "rag_baseline_evaluation_results.csv"
DEBERTA_CSV = HERE / "deberta_rescore_results.csv"
MINICHECK_CSV = HERE / "haldetect_minicheck7b_results.csv"

def load_csv(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

claims_hal = load_csv(HALDETECT_CSV)
claims_rag = load_csv(RAG_CSV)
claims_deb = load_csv(DEBERTA_CSV)
claims_mini = load_csv(MINICHECK_CSV)

systems = [
    ("HalDetect (Ours)", claims_hal, "verdict"),
    ("Web-Search RAG", claims_rag, "rag_predicted_verdict"),
    ("Uniform DeBERTa-v3", claims_deb, "deberta_pred"),
    ("Uniform MiniCheck", claims_mini, "minicheck_pred"),
]

print("=" * 96)
print("  HALDETECT MASTER BENCHMARK: 4-WAY SYSTEM COMPARISON (N = 1,005 CLAIMS)")
print("=" * 96)
print(f"{'System':<22} | {'Coverage':<10} | {'Selective Acc':<15} | {'P(TRUE)':<10} | {'P(FALSE)':<10} | {'F1(FALSE)':<10} | {'MCC':<8}")
print("-" * 96)

for name, rows, pred_key in systems:
    n_total = len(rows)
    answered = [r for r in rows if (r.get(pred_key) or "").upper() != "UNVERIFIABLE"]
    n_ans = len(answered)
    cov = n_ans / n_total if n_total > 0 else 0.0

    # Selective Accuracy on answered
    correct = [r for r in answered if (r.get(pred_key) or "").upper() == (r.get("gold_verdict") or "").upper()]
    sel_acc = len(correct) / n_ans if n_ans > 0 else 0.0

    # Precision on TRUE
    pred_t = [r for r in rows if (r.get(pred_key) or "").upper() == "TRUE"]
    p_true = sum(1 for r in pred_t if (r.get("gold_verdict") or "").upper() == "TRUE") / len(pred_t) if pred_t else 0.0

    # Precision, Recall, F1 on FALSE
    pred_f = [r for r in rows if (r.get(pred_key) or "").upper() == "FALSE"]
    gold_f = [r for r in rows if (r.get("gold_verdict") or "").upper() == "FALSE"]
    tp_f = sum(1 for r in pred_f if (r.get("gold_verdict") or "").upper() == "FALSE")
    p_false = tp_f / len(pred_f) if pred_f else 0.0
    r_false = tp_f / len(gold_f) if gold_f else 0.0
    f1_false = (2 * p_false * r_false / (p_false + r_false)) if (p_false + r_false) > 0 else 0.0

    # Matthews Correlation Coefficient (FALSE = 1, other = 0)
    tp = tp_f
    fp = len(pred_f) - tp_f
    fn = len(gold_f) - tp_f
    tn = (n_total - len(gold_f)) - fp
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) if (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn) > 0 else 1.0
    mcc = (tp * tn - fp * fn) / denom

    print(f"{name:<22} | {cov*100:>6.1f}%     | {sel_acc*100:>6.1f}%          | {p_true*100:>6.1f}%     | {p_false*100:>6.1f}%     | {f1_false:>8.3f}   | {mcc:>+6.3f}")

print("=" * 96)

# Breakdown by Modality
print("\n" + "=" * 96)
print("  SELECTIVE ACCURACY BY MODALITY (%)")
print("=" * 96)
print(f"{'Modality':<18} | {'Total':<6} | {'HalDetect (Ours)':<18} | {'Web-Search RAG':<16} | {'Uniform DeBERTa':<16} | {'Uniform MiniCheck'}")
print("-" * 96)

modalities = sorted(list(set((r.get("type") or "").upper() for r in claims_hal)))
for mod in modalities:
    n_mod = sum(1 for r in claims_hal if (r.get("type") or "").upper() == mod)
    
    mod_accs = []
    for name, rows, pred_key in systems:
        sub = [r for r in rows if (r.get("type") or "").upper() == mod]
        sub_ans = [r for r in sub if (r.get(pred_key) or "").upper() != "UNVERIFIABLE"]
        sub_corr = [r for r in sub_ans if (r.get(pred_key) or "").upper() == (r.get("gold_verdict") or "").upper()]
        acc = (len(sub_corr) / len(sub_ans) * 100) if sub_ans else 0.0
        cov_mod = (len(sub_ans) / len(sub) * 100) if sub else 0.0
        mod_accs.append(f"{acc:>5.1f}% ({cov_mod:>4.1f}% cov)")
    
    print(f"{mod:<18} | {n_mod:<6} | {mod_accs[0]:<18} | {mod_accs[1]:<16} | {mod_accs[2]:<16} | {mod_accs[3]}")

print("=" * 96)
