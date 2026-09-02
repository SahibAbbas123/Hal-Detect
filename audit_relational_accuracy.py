import csv, sys, collections
sys.path.append("current")

# RELATIONAL has 65.7% accuracy - let's understand the errors
eval1 = list(csv.DictReader(open("current/master_corpus_v2_evaluation_results.csv", encoding="utf-8")))
rel = [r for r in eval1 if r["type"] == "RELATIONAL" and r["verdict"] != "UNVERIFIABLE"]

# Error analysis
errors = [r for r in rel if r["verdict"] != r["gold_verdict"]]
correct = [r for r in rel if r["verdict"] == r["gold_verdict"]]

print(f"RELATIONAL answered: {len(rel)}, correct: {len(correct)}, errors: {len(errors)}")
print(f"\nError breakdown:")
err_types = collections.Counter((r["gold_verdict"], r["verdict"]) for r in errors)
for (g, p), c in err_types.most_common():
    print(f"  gold={g} predicted={p}: {c}")

# What are the entail/contradict scores on the errors?
print(f"\nSample errors (gold -> predicted, NLI scores):")
for r in errors[:10]:
    print(f"  {r['claim_id']}: gold={r['gold_verdict']} pred={r['verdict']}  {r['reason'][:60]}")

# What are the thresholds used?
print("\n\n--- NLI Threshold analysis ---")
import re
entail_scores = []
contra_scores = []
for r in rel:
    m = re.search(r"entail=([\d.]+), contradict=([\d.]+)", r.get("reason", ""))
    if m:
        e = float(m.group(1))
        c = float(m.group(2))
        entail_scores.append((e, c, r["verdict"], r["gold_verdict"], r["verdict"] == r["gold_verdict"]))

print(f"Total with NLI scores: {len(entail_scores)}")
# What threshold produces the verdict?
print("\nScore distribution for CORRECT predictions:")
cor_e = [x for x in entail_scores if x[4]]
wrong_e = [x for x in entail_scores if not x[4]]
print(f"  Correct: n={len(cor_e)}")
if cor_e:
    print(f"    entail range: [{min(x[0] for x in cor_e):.4f}, {max(x[0] for x in cor_e):.4f}]")
    print(f"    contra range: [{min(x[1] for x in cor_e):.4f}, {max(x[1] for x in cor_e):.4f}]")
print(f"  Wrong: n={len(wrong_e)}")
if wrong_e:
    print(f"    entail range: [{min(x[0] for x in wrong_e):.4f}, {max(x[0] for x in wrong_e):.4f}]")
    print(f"    contra range: [{min(x[1] for x in wrong_e):.4f}, {max(x[1] for x in wrong_e):.4f}]")

