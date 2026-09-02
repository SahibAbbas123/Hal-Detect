import csv
import sys
sys.path.append("current")
from metrics import report

hd2 = list(csv.DictReader(open("current/master_corpus_v2_evolved_hd2_results.csv", "r", encoding="utf-8")))
g = [r["gold_verdict"] for r in hd2]
p = [r["hd2_verdict"] for r in hd2]

print("\n--- HalDetect 2.5 (Evolved, N=1005) ---")
report(g, p, title="HalDetect 2.5 Evolved")
