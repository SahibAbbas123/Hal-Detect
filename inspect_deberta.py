import csv
import json

with open("current/nli_full_rescore_scores.json", "r") as f:
    scores = json.load(f)
    
print("Sample of DeBERTa scores:")
for s in scores[:10]:
    print(f"  {s['claim_id']}: entail={s['entail']} contradict={s['contradict']} -> {s['verdict']}")

# Are they mostly FALSE?
f_cnt = sum(1 for s in scores if s["verdict"] == "FALSE")
t_cnt = sum(1 for s in scores if s["verdict"] == "TRUE")
print(f"Total FALSE: {f_cnt}")
print(f"Total TRUE: {t_cnt}")

# Did I misinterpret the Kaggle model output?
# "if entail > contra: verdict = TRUE" ...
# Let's check a few true claims
import sys
sys.path.append("current")
master = list(csv.DictReader(open("current/haldetect_master_corpus_v2.csv", encoding="utf-8")))
g_map = {r["claim_id"]: r["gold_verdict"] for r in master}

print("\nError checking on Relational claims:")
errs = 0
for s in scores:
    cid = s["claim_id"]
    if cid in g_map and g_map[cid] == "TRUE" and s["verdict"] == "FALSE":
        print(f"  {cid}: Gold=TRUE, Pred=FALSE (e={s['entail']}, c={s['contradict']})")
        errs += 1
        if errs > 10: break

