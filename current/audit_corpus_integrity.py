#!/usr/bin/env python3
"""
Deep Corpus Integrity and Statistical Audit for HalDetect Master Benchmark Corpus v3.0 (N=1005).
"""
import csv
import json
import collections
from pathlib import Path

corpus_path = Path("current/haldetect_master_corpus_v2.csv")
assert corpus_path.exists(), f"Corpus not found at {corpus_path}"

with open(corpus_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"==================================================")
print(f" MASTER BENCHMARK CORPUS INTEGRITY AUDIT (N={len(rows)})")
print(f"==================================================")

# 1. Total Rows & ID Uniqueness
master_ids = [r.get("master_id", "").strip() for r in rows]
claim_ids = [r.get("claim_id", "").strip() for r in rows]
unique_master_ids = set(master_ids)
unique_claim_ids = set(claim_ids)

print(f"\n1. IDENTIFIER UNIQUENESS:")
print(f"   • Total rows: {len(rows)}")
print(f"   • Unique master_ids: {len(unique_master_ids)} (duplicates: {len(rows) - len(unique_master_ids)})")
print(f"   • Unique claim_ids: {len(unique_claim_ids)} (duplicates: {len(rows) - len(unique_claim_ids)})")

# 2. Null / Empty Required Fields
print(f"\n2. NULL / EMPTY FIELD CHECK:")
empty_claims = [r for r in rows if not r.get("claim", "").strip()]
empty_types = [r for r in rows if not r.get("type", "").strip()]
empty_verdicts = [r for r in rows if not r.get("gold_verdict", "").strip()]
empty_subjects = [r for r in rows if not r.get("subject", "").strip()]

print(f"   • Empty claim text: {len(empty_claims)}")
print(f"   • Empty type: {len(empty_types)}")
print(f"   • Empty gold_verdict: {len(empty_verdicts)}")
print(f"   • Empty subject: {len(empty_subjects)}")

# 3. Duplicate Claim Texts
claim_texts = collections.Counter([r.get("claim", "").strip().lower() for r in rows if r.get("claim")])
duplicates = {text: count for text, count in claim_texts.items() if count > 1}
print(f"\n3. EXACT DUPLICATE CLAIM TEXTS:")
print(f"   • Duplicate texts found: {len(duplicates)}")
for text, count in list(duplicates.items())[:5]:
    print(f"     - ({count}x): \"{text[:70]}...\"")

# 4. Modality Distribution & Gold Verdict Balance
print(f"\n4. MODALITY & CLASS DISTRIBUTION:")
by_type = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    t = r.get("type", "UNKNOWN")
    v = r.get("gold_verdict", "UNKNOWN")
    by_type[t][v] += 1

print(f"   {'Modality':<20} | {'Total':<6} | {'TRUE':<6} | {'FALSE':<6} | {'UNV':<6} | {'% FALSE'}")
print(f"   {'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}")
total_t = total_f = total_u = 0
for t, counts in sorted(by_type.items()):
    true_cnt = counts.get("TRUE", 0)
    false_cnt = counts.get("FALSE", 0)
    unv_cnt = counts.get("UNVERIFIABLE", 0)
    tot = true_cnt + false_cnt + unv_cnt
    pct_f = (false_cnt / tot * 100) if tot > 0 else 0
    total_t += true_cnt
    total_f += false_cnt
    total_u += unv_cnt
    print(f"   {t:<20} | {tot:<6} | {true_cnt:<6} | {false_cnt:<6} | {unv_cnt:<6} | {pct_f:>6.1f}%")
print(f"   {'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}")
print(f"   {'TOTAL':<20} | {len(rows):<6} | {total_t:<6} | {total_f:<6} | {total_u:<6} | {(total_f/len(rows)*100):>6.1f}%")

# 5. Provenance / Slice Distribution
print(f"\n5. PROVENANCE / SLICE DISTRIBUTION:")
by_origin = collections.defaultdict(collections.Counter)
for r in rows:
    orig = r.get("origin_dataset", "unknown")
    v = r.get("gold_verdict", "UNKNOWN")
    by_origin[orig][v] += 1

print(f"   {'Slice':<32} | {'Total':<6} | {'TRUE':<6} | {'FALSE':<6} | {'UNV':<6}")
print(f"   {'-'*32}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}-+-{'-'*6}")
for orig, counts in sorted(by_origin.items()):
    tot = sum(counts.values())
    print(f"   {orig:<32} | {tot:<6} | {counts.get('TRUE', 0):<6} | {counts.get('FALSE', 0):<6} | {counts.get('UNVERIFIABLE', 0):<6}")

# 6. Real vs Synthetic Ratio
print(f"\n6. REAL-WORLD vs SYNTHETIC RATIO:")
natural_slices = {"natural_corpus", "factscore_b1", "expansion_real", "expansion_v3", "domain_suite", "science_legal", "expansion_1000", "final_1000_claims"}
synthetic_slices = {"synthetic_diag", "external_neg"}

natural_count = sum(sum(by_origin[s].values()) for s in natural_slices if s in by_origin)
synthetic_count = sum(sum(by_origin[s].values()) for s in synthetic_slices if s in by_origin)
print(f"   • Real-world / Natural / Domain Queries: {natural_count} ({natural_count/len(rows)*100:.1f}%)")
print(f"   • Diagnostic Synthetic / Corrupted:    {synthetic_count} ({synthetic_count/len(rows)*100:.1f}%)")

print(f"\n==================================================")
print(f" AUDIT COMPLETE")
print(f"==================================================")
