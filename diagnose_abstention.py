import csv, collections, sys
sys.path.append("current")

rows = list(csv.DictReader(open("current/master_corpus_v2_evolved_hd2_results.csv", encoding="utf-8")))

# For the 911 rows routed to "Evolved Abstention Router", what types are they?
abstained = [r for r in rows if r.get("hd2_engine") == "Evolved Abstention Router"]
print(f"Total abstained: {len(abstained)}")
print("\nAbstained by type:")
by_type = collections.Counter(r["type"] for r in abstained)
for t, c in by_type.most_common():
    print(f"  {t:<25} {c:>4}")

print("\nAbstained by gold_verdict:")
by_gold = collections.Counter(r["gold_verdict"] for r in abstained)
for g, c in by_gold.most_common():
    print(f"  {g:<15} {c:>4}")

# What about the evidence field? Does it tell us WHY it abstained?
print("\nSample evidence strings from abstained claims:")
evidence_types = collections.Counter()
for r in abstained[:100]:
    ev = r.get("evidence", "")
    # Truncate
    key = ev[:120] if ev else "(empty)"
    evidence_types[key] += 1

for ev, c in evidence_types.most_common(15):
    print(f"  [{c:>3}x] {ev}")

# How many answered claims come from which engine?
answered = [r for r in rows if r.get("hd2_engine") != "Evolved Abstention Router"]
print(f"\n\nTotal answered: {len(answered)}")
print("\nAnswered by engine:")
by_eng = collections.Counter(r.get("hd2_engine", "?") for r in answered)
for eng, c in by_eng.most_common():
    print(f"  {eng:<55} {c:>4}")

# Look at the hybrid_fallthrough specifically - how many RELATIONAL claims go there and get answered?
rel = [r for r in rows if r["type"] == "RELATIONAL"]
rel_answered = [r for r in rel if r["hd2_verdict"] != "UNVERIFIABLE"]
rel_abstained = [r for r in rel if r["hd2_verdict"] == "UNVERIFIABLE"]
print(f"\n\nRELATIONAL: {len(rel)} total, {len(rel_answered)} answered, {len(rel_abstained)} abstained")
print("Answered engines:", collections.Counter(r.get("hd2_engine") for r in rel_answered))
print("Abstained engines:", collections.Counter(r.get("hd2_engine") for r in rel_abstained))

