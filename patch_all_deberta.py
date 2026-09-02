import csv, json

with open("current/nli_full_rescore_scores.json", "r") as f:
    scores = json.load(f)

score_map = {item["claim_id"]: item for item in scores}

def patch_csv(filepath):
    with open(filepath, "r") as f:
        reader = list(csv.DictReader(f))
    
    if not reader: return
    
    patched = 0
    for row in reader:
        cid = row["claim_id"]
        if cid in score_map:
            s = score_map[cid]
            row["entail"] = s["entail"]
            row["contradict"] = s["contradict"]
            row["verdict"] = s["verdict"]
            row["verdict_confidence"] = s["verdict_confidence"]
            patched += 1
            
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader[0].keys())
        writer.writeheader()
        writer.writerows(reader)
    print(f"Patched {patched} rows in {filepath}")

patch_csv("current/nonrouted_baseline_results.csv")
patch_csv("current/nonrouted_negatives_results.csv")
