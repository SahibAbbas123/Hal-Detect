import csv, collections, sys
sys.path.append("current")

rows = list(csv.DictReader(open("current/master_corpus_v2_evolved_hd2_results.csv", encoding="utf-8")))

# 1. By modality
by_type = collections.defaultdict(lambda: {"total":0, "answered":0, "correct":0, "unverifiable":0})
for r in rows:
    t = r["type"]
    by_type[t]["total"] += 1
    v = r["hd2_verdict"]
    if v == "UNVERIFIABLE":
        by_type[t]["unverifiable"] += 1
    else:
        by_type[t]["answered"] += 1
        if r["is_correct"] == "True":
            by_type[t]["correct"] += 1

print("="*90)
print(f"{'Modality':<20} {'Total':>6} {'Answered':>8} {'Correct':>8} {'Unverif':>8} {'Coverage':>10} {'Sel.Acc':>10}")
print("-"*90)
for t in sorted(by_type):
    d = by_type[t]
    cov = d["answered"] / d["total"] * 100 if d["total"] else 0
    acc = d["correct"] / d["answered"] * 100 if d["answered"] else 0
    print(f"{t:<20} {d['total']:>6} {d['answered']:>8} {d['correct']:>8} {d['unverifiable']:>8} {cov:>9.1f}% {acc:>9.1f}%")

total_ans = sum(d["answered"] for d in by_type.values())
total_cor = sum(d["correct"] for d in by_type.values())
total_all = len(rows)
total_unv = sum(d["unverifiable"] for d in by_type.values())
print("-"*90)
print(f"{'TOTAL':<20} {total_all:>6} {total_ans:>8} {total_cor:>8} {total_unv:>8} {total_ans/total_all*100:>9.1f}% {total_cor/total_ans*100 if total_ans else 0:>9.1f}%")

# 2. By engine used
print("\n\n--- Breakdown by engine ---")
by_eng = collections.defaultdict(lambda: {"total":0, "answered":0, "correct":0})
for r in rows:
    eng = r.get("hd2_engine", "unknown")
    by_eng[eng]["total"] += 1
    if r["hd2_verdict"] != "UNVERIFIABLE":
        by_eng[eng]["answered"] += 1
        if r["is_correct"] == "True":
            by_eng[eng]["correct"] += 1

for eng in sorted(by_eng, key=lambda e: by_eng[e]["total"], reverse=True):
    d = by_eng[eng]
    cov = d["answered"] / d["total"] * 100 if d["total"] else 0
    acc = d["correct"] / d["answered"] * 100 if d["answered"] else 0
    print(f"  {eng:<50} n={d['total']:>4}  ans={d['answered']:>4}  cor={d['correct']:>4}  cov={cov:5.1f}%  acc={acc:5.1f}%")

# 3. By origin
print("\n\n--- Breakdown by origin ---")
by_orig = collections.defaultdict(lambda: {"total":0, "answered":0, "correct":0})
for r in rows:
    orig = r.get("origin", r.get("source", "unknown"))
    by_orig[orig]["total"] += 1
    if r["hd2_verdict"] != "UNVERIFIABLE":
        by_orig[orig]["answered"] += 1
        if r["is_correct"] == "True":
            by_orig[orig]["correct"] += 1

for orig in sorted(by_orig, key=lambda o: by_orig[o]["total"], reverse=True):
    d = by_orig[orig]
    cov = d["answered"] / d["total"] * 100 if d["total"] else 0
    acc = d["correct"] / d["answered"] * 100 if d["answered"] else 0
    print(f"  {orig:<40} n={d['total']:>4}  ans={d['answered']:>4}  cor={d['correct']:>4}  cov={cov:5.1f}%  acc={acc:5.1f}%")

# 4. Gold verdict vs system verdict confusion
print("\n\n--- Confusion matrix ---")
conf = collections.Counter()
for r in rows:
    conf[(r["gold_verdict"], r["hd2_verdict"])] += 1
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

