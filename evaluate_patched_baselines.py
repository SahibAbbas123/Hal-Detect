import csv
import sys
sys.path.append("current")
from metrics import report

def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# The natural set baseline
nat = load_csv("current/nonrouted_baseline_results.csv")
g_nat = [r["gold_verdict"] for r in nat]
p_nat = [r["verdict"] for r in nat]

print("\n--- Non-Routed Baseline (Natural, N=313/356) ---")
report(g_nat, p_nat, title="Natural Non-Routed Baseline")

# The negatives baseline
neg = load_csv("current/nonrouted_negatives_results.csv")
g_neg = [r["gold_verdict"] for r in neg]
p_neg = [r["verdict"] for r in neg]

print("\n--- Non-Routed Baseline (Negatives, N=68) ---")
report(g_neg, p_neg, title="Negatives Non-Routed Baseline")
