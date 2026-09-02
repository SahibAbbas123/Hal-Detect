import csv
import os

new_results = "current/nli_rescore_both_results.csv"
baseline_files = [
    "current/nonrouted_baseline_results.csv",
    "current/nonrouted_negatives_results.csv"
]

# Load updates
updates = {}
with open(new_results, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        updates[row["claim_id"]] = {
            "verdict": row["new_verdict"],
            "entail": row["new_entail"],
            "contradict": row["new_contradict"],
            "verdict_confidence": row["new_verdict_confidence"],
            "verdict_margin": row["new_verdict_margin"]
        }

print(f"Loaded {len(updates)} updates.")

# Patch each baseline
for bf in baseline_files:
    if not os.path.exists(bf): continue
    
    with open(bf, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = f.readline().strip().split(",") if f.tell()==0 else None
        
    if not rows: continue
    
    with open(bf, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        fieldnames = next(reader)
        
    patched = 0
    for row in rows:
        cid = row["claim_id"]
        if cid in updates:
            upd = updates[cid]
            row["verdict"] = upd["verdict"]
            # If the CSV has specific entail/contradict columns, map them
            if "entailment_prob" in row: row["entailment_prob"] = upd["entail"]
            elif "entail" in row: row["entail"] = upd["entail"]
            
            if "contradiction_prob" in row: row["contradiction_prob"] = upd["contradict"]
            elif "contradict" in row: row["contradict"] = upd["contradict"]
            
            # For confidence
            if "confidence" in row: row["confidence"] = upd["verdict_confidence"]
            elif "verdict_confidence" in row: row["verdict_confidence"] = upd["verdict_confidence"]
            patched += 1
            
    with open(bf, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Patched {patched} rows in {bf}")

