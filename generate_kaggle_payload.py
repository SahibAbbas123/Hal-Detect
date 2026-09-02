import csv
import json
import sys

files = [
    "current/nonrouted_baseline_results.csv",
    "current/nonrouted_negatives_results.csv"
]

items = []
seen = set()

for path in files:
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                cid = r["claim_id"]
                claim = r["claim"]
                
                # hybrid_fallthrough expects the passage to match what it retrieved
                # So we must provide exactly the passage text from the baseline
                passage = r.get("evidence", r.get("passage", ""))
                
                if cid not in seen:
                    items.append({
                        "claim_id": cid,
                        "claim": claim,
                        "passage": passage
                    })
                    seen.add(cid)
    except Exception as e:
        print(f"Error reading {path}: {e}")

payload = {
    "meta": {
        "description": "Full HalDetect Master Corpus NLI Rescore",
        "model_target": "cross-encoder/nli-deberta-v3-large",
        "total_items": len(items)
    },
    "items": items
}

out_path = "current/nli_full_rescore_worklist.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote {len(items)} items to {out_path}")
