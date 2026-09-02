import csv
import os

new_results = "current/nli_rescore_both_results.csv"
baseline_files = [
    "current/nonrouted_baseline_results.csv",
    "current/nonrouted_negatives_results.csv"
]

# Load new rows
updates = {}
with open(new_results, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Depending on how the apply script writes them, they might have 'claim_id' and 'new_verdict', 'new_entail' etc.
        # Let's inspect the first row of new_results to see the schema!
        pass

