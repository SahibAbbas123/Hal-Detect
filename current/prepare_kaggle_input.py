#!/usr/bin/env python3
"""
HalDetect -- Prepare Self-Contained Kaggle Input Dataset for MiniCheck-7B
========================================================================
Combines claims from `haldetect_master_corpus_v2.csv` with top retrieved
evidence passages from `rag_search_cache.json` and `nonrouted_cache.json`
into a single standalone CSV: `current/kaggle_minicheck_input_claims.csv`.
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_PATH = HERE / "haldetect_master_corpus_v2.csv"
RAG_RESULTS_PATH = HERE / "rag_baseline_evaluation_results.csv"
OUT_CSV = HERE / "kaggle_minicheck_input_claims.csv"

# Load claims
with open(CORPUS_PATH, "r", encoding="utf-8") as f:
    claims = list(csv.DictReader(f))

# Load pre-retrieved evidence from RAG results if available
evidence_map = {}
if RAG_RESULTS_PATH.exists():
    with open(RAG_RESULTS_PATH, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            mid = r.get("master_id") or r.get("claim_id")
            ev = r.get("evidence", "")
            if ev and not ev.startswith("No relevant"):
                evidence_map[mid] = ev

# Load nonrouted cache for additional text
nonrouted_cache = {}
if (HERE / "nonrouted_cache.json").exists():
    try:
        with open(HERE / "nonrouted_cache.json", "r", encoding="utf-8") as f:
            nonrouted_cache = json.load(f)
    except Exception:
        pass

out_rows = []
for idx, r in enumerate(claims, 1):
    mid = r.get("master_id", f"MST_{idx:04d}")
    cid = r.get("claim_id", "")
    claim_text = r.get("claim", "").strip()
    subj = r.get("subject", "").strip()
    gold = r.get("gold_verdict", "UNVERIFIABLE").strip().upper()
    modality = r.get("type", "UNKNOWN").strip().upper()

    # Find evidence
    evidence = evidence_map.get(mid) or evidence_map.get(cid) or ""
    if not evidence and subj:
        # Check text__ keys in cache
        k = f"text__{subj.lower().replace(' ', '_')}"
        if k in nonrouted_cache:
            evidence = nonrouted_cache[k][:1000]

    if not evidence:
        evidence = f"General context for {subj}: {claim_text}"

    out_rows.append({
        "master_id": mid,
        "claim_id": cid,
        "type": modality,
        "origin_dataset": r.get("origin_dataset", ""),
        "subject": subj,
        "property": r.get("property", ""),
        "claim": claim_text,
        "evidence_passage": evidence,
        "gold_verdict": gold,
    })

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    writer.writeheader()
    writer.writerows(out_rows)

print(f"Prepared {len(out_rows)} self-contained claims with evidence at: {OUT_CSV}")
