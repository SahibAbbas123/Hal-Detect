#!/usr/bin/env python3
"""
HalDetect -- Adversarial Stumper Stress Test Runner (N = 100)
============================================================
Runs HalDetect's live verifier across all 100 adversarial stress-test claims,
measuring pass rate, failure modes, false alarms, and abstention patterns.
"""

import collections
import csv
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

import verify_live as VL

INPUT_CSV = HERE / "adversarial_stumpers_100.csv"
OUTPUT_CSV = HERE / "adversarial_stumpers_100_results.csv"

def run_stress_test():
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        stumpers = list(csv.DictReader(f))

    print("=" * 95)
    print(f"  RUNNING 100 ADVERSARIAL STUMPERS THROUGH HALDETECT (N = {len(stumpers)})")
    print("=" * 95)

    results = []
    t_start = time.time()

    for idx, s in enumerate(stumpers, 1):
        claim_text = s["claim"]
        gold = s["gold_verdict"].strip().upper()
        cat = s["category"]

        res = VL.verify_text(claim_text)
        pred = res["verdict"]
        conf = res["confidence"]
        mod = res["modality"]
        ev = res["evidence"]

        is_answered = (pred != "UNVERIFIABLE")
        is_correct = (pred == gold) if is_answered else False
        is_stumped = not is_correct

        row_res = {
            "stumper_id": s["stumper_id"],
            "category": cat,
            "claim": claim_text,
            "gold_verdict": gold,
            "predicted_verdict": pred,
            "confidence": conf,
            "modality": mod,
            "verifier_used": res["verifier"],
            "is_answered": is_answered,
            "is_correct": is_correct,
            "is_stumped": is_stumped,
            "latency_ms": res["latency_ms"],
            "why_it_stumps": s["why_it_stumps"],
            "evidence": ev
        }
        results.append(row_res)

        status_icon = "✅ PASS" if is_correct else ("⚠️ ABSTAIN" if pred == "UNVERIFIABLE" else "❌ WRONG")
        print(f"[{idx:3d}/100] {s['stumper_id']} | {cat:<24} | Gold: {gold:<5} | Pred: {pred:<12} | {status_icon} | {claim_text[:45]}...")

    # Save output CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    elapsed = time.time() - t_start
    print("\n" + "=" * 95)
    print("  100 ADVERSARIAL STUMPERS: EVALUATION SUMMARY")
    print("=" * 95)

    n_total = len(results)
    answered = [r for r in results if r["is_answered"]]
    n_ans = len(answered)
    correct = [r for r in answered if r["is_correct"]]
    wrong = [r for r in answered if not r["is_correct"]]
    abstains = [r for r in results if not r["is_answered"]]

    print(f" • Total Adversarial Claims:    {n_total}")
    print(f" • Answered Confidently:        {n_ans} ({n_ans/n_total*100:.1f}%)")
    print(f" • Safely Abstained (UNVERIF):  {len(abstains)} ({len(abstains)/n_total*100:.1f}%)")
    print(f" • Correct Detections:          {len(correct)} ({len(correct)/n_ans*100:.1f}% selective accuracy)")
    print(f" • Confident Errors (Stumped):  {len(wrong)} ({len(wrong)/n_total*100:.1f}% critical failure rate)")
    print(f" • Total Latency:               {elapsed:.2f}s ({elapsed/n_total*1000:.1f} ms/claim)")
    print("-" * 95)

    print(f"\n{'Category':<28} | {'Total':<6} | {'Answered':<8} | {'Correct':<8} | {'Abstained':<10} | {'Wrong'}")
    print(f"{'-'*28}-+-{'-'*6}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}-+-{'-'*6}")
    
    by_cat = collections.defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)

    for cat_name, cat_rows in sorted(by_cat.items()):
        c_tot = len(cat_rows)
        c_ans = sum(1 for r in cat_rows if r["is_answered"])
        c_corr = sum(1 for r in cat_rows if r["is_correct"])
        c_abs = sum(1 for r in cat_rows if not r["is_answered"])
        c_wrong = c_ans - c_corr
        print(f"{cat_name:<28} | {c_tot:<6} | {c_ans:<8} | {c_corr:<8} | {c_abs:<10} | {c_wrong:<6}")

    print("=" * 95)

if __name__ == "__main__":
    run_stress_test()
