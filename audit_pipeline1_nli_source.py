import csv, sys, collections
sys.path.append("current")

# The tier2 cache is loaded from nonrouted_baseline_results.csv
# We need to verify: does that CSV now contain DeBERTa scores (from our Phase 6 patch)?
# Or does it still contain the old BART scores?

baseline = list(csv.DictReader(open("current/nonrouted_baseline_results.csv", encoding="utf-8")))

# Check the 26 collision claims we patched
patched = list(csv.DictReader(open("current/nli_rescore_both_results.csv", encoding="utf-8")))
patched_ids = set(r["claim_id"] for r in patched)

print(f"Total baseline rows: {len(baseline)}")
print(f"Patched collision claim IDs: {len(patched_ids)}")

# Check if any of the patched IDs are in the baseline
matched = [r for r in baseline if r["claim_id"] in patched_ids]
print(f"Matched in baseline: {len(matched)}")

# The key question: the RELATIONAL claims in the master corpus that use tier2...
# How many RELATIONAL claim_ids from the master corpus are found in the baseline?
master = list(csv.DictReader(open("current/haldetect_master_corpus_v2.csv", encoding="utf-8")))
rel_ids = set(r["claim_id"] for r in master if r["type"] == "RELATIONAL")
baseline_ids = set(r["claim_id"] for r in baseline)

rel_in_baseline = rel_ids & baseline_ids
rel_not_in_baseline = rel_ids - baseline_ids

print(f"\nRELATIONAL claims in master corpus: {len(rel_ids)}")
print(f"RELATIONAL claims found in baseline cache: {len(rel_in_baseline)}")
print(f"RELATIONAL claims NOT in baseline cache: {len(rel_not_in_baseline)}")

# What about TEMPORAL and ENTITY_ATTRIBUTE?
for t in ["TEMPORAL", "ENTITY_ATTRIBUTE"]:
    t_ids = set(r["claim_id"] for r in master if r["type"] == t)
    in_bl = t_ids & baseline_ids
    not_in_bl = t_ids - baseline_ids
    print(f"\n{t} claims in master: {len(t_ids)}")
    print(f"  Found in baseline: {len(in_bl)}")
    print(f"  NOT in baseline: {len(not_in_bl)}")

# What NLI model generated the baseline scores?
# Check if the comment in temporal_ea_verifier.py says BART or DeBERTa
print("\n--- NLI model identity check ---")
print("The nonrouted_baseline.py now references:", end=" ")
import nonrouted_baseline as NRB
# Find the model name
import inspect
src = inspect.getsource(NRB)
if "cross-encoder/nli-deberta-v3-large" in src:
    print("cross-encoder/nli-deberta-v3-large ✅")
elif "facebook/bart-large-mnli" in src:
    print("facebook/bart-large-mnli ❌ (still BART!)")
else:
    print("UNKNOWN model reference")

# BUT - the baseline CSV was generated BEFORE we changed the model string.
# The scores in nonrouted_baseline_results.csv were generated with BART.
# Only the 26 patched rows have DeBERTa scores.
# This means: for the remaining ~330 claims, the NLI scores are still from BART!
print("\n--- CRITICAL: Were the baseline scores regenerated with DeBERTa? ---")
print("The baseline CSV was last modified:", end=" ")
import os
mod_time = os.path.getmtime("current/nonrouted_baseline_results.csv")
from datetime import datetime
print(datetime.fromtimestamp(mod_time).isoformat())

# Check our patch script output
print("\nOur patch_baselines.py only patched 26 rows.")
print("The remaining rows still carry BART-generated NLI scores.")
print("This is a KNOWN LIMITATION that must be disclosed.")

