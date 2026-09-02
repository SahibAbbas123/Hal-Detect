import csv, sys
sys.path.append("current")

# How many unique premise-hypothesis pairs exist in the baseline?
# This is what would need to be re-scored on Kaggle with DeBERTa
baseline = list(csv.DictReader(open("current/nonrouted_baseline_results.csv", encoding="utf-8")))
negatives = list(csv.DictReader(open("current/nonrouted_negatives_results.csv", encoding="utf-8")))

all_rows = baseline + negatives
print(f"Total baseline rows: {len(baseline)}")
print(f"Total negatives rows: {len(negatives)}")
print(f"Combined: {len(all_rows)}")

# How many have NLI scores (entail/contradict)?
has_scores = [r for r in all_rows if r.get("entail") and r.get("contradict")]
no_scores = [r for r in all_rows if not r.get("entail") or not r.get("contradict")]
print(f"\nRows with NLI scores: {len(has_scores)}")
print(f"Rows without NLI scores: {len(no_scores)}")

# How many unique claim_ids?
cids = set(r["claim_id"] for r in all_rows)
print(f"Unique claim_ids: {len(cids)}")

# The 26 already patched
patched = list(csv.DictReader(open("current/nli_rescore_both_results.csv", encoding="utf-8")))
patched_ids = set(r["claim_id"] for r in patched)
remaining = cids - patched_ids
print(f"Already patched with DeBERTa: {len(patched_ids)}")
print(f"Still need DeBERTa re-scoring: {len(remaining)}")

