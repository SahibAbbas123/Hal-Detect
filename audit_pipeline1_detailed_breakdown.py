import csv, sys, collections
sys.path.append("current")

# Load the actual Pipeline 1 output
eval1 = list(csv.DictReader(open("current/master_corpus_v2_evaluation_results.csv", encoding="utf-8")))

# Per-modality: answered vs abstained, and which verifier/tier produced the answer
print("="*100)
print("PIPELINE 1 DETAILED AUDIT: What engine answered each claim?")
print("="*100)

for ctype in ["QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"]:
    sub = [r for r in eval1 if r["type"] == ctype]
    answered = [r for r in sub if r["verdict"] != "UNVERIFIABLE"]
    abstained = [r for r in sub if r["verdict"] == "UNVERIFIABLE"]
    correct = [r for r in answered if r["verdict"] == r["gold_verdict"]]
    
    print(f"\n{'─'*80}")
    print(f"  {ctype}: {len(sub)} total, {len(answered)} answered ({len(answered)/len(sub)*100:.1f}%), {len(correct)} correct ({len(correct)/len(answered)*100 if answered else 0:.1f}%)")
    print(f"{'─'*80}")
    
    # By verifier
    by_verifier = collections.Counter(r.get("verifier","?") for r in answered)
    for v, c in by_verifier.most_common():
        vc = len([r for r in answered if r.get("verifier") == v and r["verdict"] == r["gold_verdict"]])
        print(f"    {v:<50} ans={c:>4}  cor={vc:>4}  acc={vc/c*100:.1f}%")
    
    # By tier
    by_tier = collections.Counter(r.get("tier","?") for r in answered)
    for t, c in by_tier.most_common():
        print(f"    tier: {t:<20} {c:>4}")
    
    # What do the abstained reasons look like?
    abs_reasons = collections.Counter(r.get("reason","")[:80] for r in abstained)
    if abs_reasons:
        print(f"  Abstention reasons (top 3):")
        for reason, c in abs_reasons.most_common(3):
            print(f"    [{c:>4}x] {reason}")

# Overall confusion
print(f"\n\n{'='*100}")
print("OVERALL CONFUSION MATRIX")
print(f"{'='*100}")
conf = collections.Counter()
for r in eval1:
    conf[(r["gold_verdict"], r["verdict"])] += 1
verdicts = sorted(set(v for g, v in conf))
golds = sorted(set(g for g, v in conf))
print(f"{'gold\\pred':<15}", end="")
for v in verdicts:
    print(f"{v:>15}", end="")
print()
for g in golds:
    print(f"{g:<15}", end="")
    for v in verdicts:
        print(f"{conf[(g,v)]:>15}", end="")
    print()

