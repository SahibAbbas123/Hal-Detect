#!/usr/bin/env python3
"""Is the RQ2 headline safe against the `nli__` cache-key collision bug?

`archive/scripts/relational_verifier_phase3d.py:194` keys NLI on
`claim[:60]` + `passage[:40]`, so two claims agreeing in their first 60
characters share one cache entry and the second silently inherits the first's
entail/contradict scores.  8 of the 356 baseline rows are affected.

Asserting that 2.2% of rows is immaterial is an *argument*.  Recomputing the
headline with those rows dropped is a *measurement*.  This does the
measurement, offline, with zero model calls -- it only re-reads the stored
verdict columns of `nonrouted_baseline_results.csv`.

    .venv/bin/python current/rq2_collision_robustness.py .

Result recorded 2026-08-25: largest movement in any headline figure 0.67pp,
3d's MCC unchanged at +0.180, and every delta favourable -- so the reported
77.2% coverage / 69.8% selective accuracy is if anything mildly pessimistic.
The run also reproduces the recorded figures exactly, which re-validates the
stored verdict columns independently.

A collision is only counted when the colliding claims differ in the *value*
being checked; two identical restatements would legitimately have earned the
same score, so sharing a cache entry costs nothing there.
"""
import collections
import csv
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
sys.path.insert(0, os.path.join(ROOT, "current"))
import metrics  # noqa: E402


def load(rel):
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def norm(v):
    v = (v or "").strip().upper()
    return v if v in ("TRUE", "FALSE", "UNVERIFIABLE") else "UNVERIFIABLE"


def keyprefix(claim):
    return f"nli__{claim[:60].replace(' ', '_')}"


pos = load("current/nonrouted_baseline_results.csv")

groups = collections.defaultdict(list)
for r in pos:
    groups[keyprefix(r["claim"])].append(r)

# A collision only corrupts a row if the colliding claims differ in the value
# being checked -- identical restatements would have earned the same score.
bad_ids = set()
for k, v in groups.items():
    if len(v) > 1 and len({r.get("value", "") for r in v}) > 1:
        bad_ids.update(r["claim_id"] for r in v)

print(f"total rows                : {len(pos)}")
print(f"rows on a value-differing collision: {len(bad_ids)} "
      f"({len(bad_ids)/len(pos):.1%})")
print(f"  ids: {sorted(bad_ids)}")

clean = [r for r in pos if r["claim_id"] not in bad_ids]


def show(rows, label):
    gold = [norm(r["gold_verdict"]) for r in rows]
    print(f"\n  {label}  (n={len(rows)})")
    for name, col in (("3d", "verdict"), ("3e", "verdict_margin")):
        pred = [norm(r[col]) for r in rows]
        s = metrics.selective(gold, pred)
        pr = metrics.per_class_prf(gold, pred)
        f1F = pr["FALSE"]["f1"] if "FALSE" in pr else 0.0
        print(f"    {name}: coverage {s['coverage']:>6.1%}   "
              f"selective acc {s['accuracy']:>6.1%}   "
              f"F1(FALSE) {f1F:>5.3f}   MCC {metrics.mcc(gold, pred):>+.3f}")


print("\n" + "=" * 74)
print("  RQ2 HEADLINE: as reported vs with collided rows dropped")
print("=" * 74)
show(pos, "ALL 356 (as reported)")
show(clean, "COLLISION-FREE")

deltas = []
for name, col in (("3d", "verdict"), ("3e", "verdict_margin")):
    a = metrics.selective([norm(r["gold_verdict"]) for r in pos],
                          [norm(r[col]) for r in pos])
    b = metrics.selective([norm(r["gold_verdict"]) for r in clean],
                          [norm(r[col]) for r in clean])
    deltas.append((name,
                   (b["coverage"] - a["coverage"]) * 100,
                   (b["accuracy"] - a["accuracy"]) * 100))

print("\n" + "=" * 74)
print("  DELTA (percentage points)")
print("=" * 74)
for name, dc, da in deltas:
    print(f"  {name}: coverage {dc:+.2f}pp   selective accuracy {da:+.2f}pp")
worst = max(abs(x) for _, dc, da in deltas for x in (dc, da))
print(f"\n  largest movement in any headline figure: {worst:.2f}pp")
print("  VERDICT:", "headline unaffected -- claim VERIFIED" if worst < 1.0
      else "headline moves by >=1pp -- claim NOT safe, revise the docs")
