import csv
import sys
import collections
sys.path.append("current")
from metrics import report

results = list(csv.DictReader(open("current/master_corpus_v2_evaluation_results.csv", "r", encoding="utf-8")))

g = [r["gold_verdict"] for r in results]
p = [r["verdict"] for r in results]

print("--- FINAL MASTER EVALUATION ---")
report(g, p, title="Final HalDetect (Pipeline 1 + DeBERTa)")

by_type = collections.defaultdict(list)
for r in results:
    by_type[r["type"]].append(r)
print("\n--- PER MODALITY ---")
for t in sorted(by_type):
    sg = [x["gold_verdict"] for x in by_type[t]]
    sp = [x["verdict"] for x in by_type[t]]
    answered = [x for x in by_type[t] if x["verdict"] != "UNVERIFIABLE"]
    cov = len(answered) / len(by_type[t]) * 100
    acc = sum(1 for x in answered if x["verdict"] == x["gold_verdict"]) / len(answered) * 100 if answered else 0
    print(f"{t:<20}: Cov = {cov:>5.1f}%, Acc = {acc:>5.1f}%")

