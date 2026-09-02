import csv, collections, sys
sys.path.append("current")
from metrics import report

# Load both evaluation results
# 1. evaluate_master_corpus.py output (the original pipeline with hybrid fallthrough + NLI tier 2)
eval1 = list(csv.DictReader(open("current/master_corpus_v2_evaluation_results.csv", encoding="utf-8")))
# 2. run_all_master_ablations (EVP pipeline)
eval2 = list(csv.DictReader(open("current/master_corpus_v2_evolved_hd2_results.csv", encoding="utf-8")))

print("="*80)
print("PIPELINE 1: evaluate_master_corpus.py (Taxonomy-Routed + hybrid_fallthrough NLI tier2)")
print("="*80)
g1 = [r["gold_verdict"] for r in eval1]
p1 = [r["verdict"] for r in eval1]
report(g1, p1, title="HalDetect Taxonomy-Routed (evaluate_master_corpus)")

by_type1 = collections.defaultdict(lambda: {"total":0, "answered":0, "correct":0})
for r in eval1:
    t = r["type"]
    by_type1[t]["total"] += 1
    if r["verdict"] != "UNVERIFIABLE":
        by_type1[t]["answered"] += 1
        if r["verdict"] == r["gold_verdict"]:
            by_type1[t]["correct"] += 1

print(f"\n{'Type':<20} {'N':>5} {'Ans':>5} {'Cor':>5} {'Cov':>8} {'Acc':>8}")
for t in sorted(by_type1):
    d = by_type1[t]
    cov = d["answered"]/d["total"]*100 if d["total"] else 0
    acc = d["correct"]/d["answered"]*100 if d["answered"] else 0
    print(f"{t:<20} {d['total']:>5} {d['answered']:>5} {d['correct']:>5} {cov:>7.1f}% {acc:>7.1f}%")

print("\n\n" + "="*80)
print("PIPELINE 2: run_all_master_ablations (EVP evolved verifier)")
print("="*80)
g2 = [r["gold_verdict"] for r in eval2]
p2 = [r["hd2_verdict"] for r in eval2]
report(g2, p2, title="HalDetect 2.0 Evolved (EVP)")

