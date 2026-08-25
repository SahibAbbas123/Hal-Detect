# RQ2 for QUANTITATIVE — the first routed-vs-baseline result with both classes

**Date:** 2026-08-25
**Reproduce:** `.venv/bin/python current/rq2_quantitative_table.py` (offline, zero
model calls, ~1 s). Sections: `--section standalone|paired|combined|pairs|samenumber|prior`.
**Inputs:** `current/quantitative_b3_results.csv` (29),
`current/quantitative_negatives_verifier_quantitative_all_results.csv` (24),
`current/nonrouted_baseline_results.csv`, `current/nonrouted_negatives_results.csv`.

---

## Why this measurement exists

Until now the routed QUANTITATIVE verifier's number was **8/8 = 100% on 8 covered
Batch 3 claims** — and it carried no information about detection, because all 8
were gold TRUE. A verifier that unconditionally answered "TRUE" would have scored
identically. The project's own rule says so: *never merge a bare 100% with
evidence*, and *where gold negatives don't exist, measure discrimination by
controlled perturbation.*

The 24 gold-FALSE synthetic QUANTITATIVE negatives supply the missing class. On
that set an unconditional "TRUE" scores **0.0%** — versus the 88.2% it scores on
the natural 356. That inversion is what makes the numbers below informative.

---

## 1. The headline

**Routed QUANTITATIVE is 14/14 correct across 14 covered claims with both classes
represented, and makes zero confident errors.**

| combined population (n=53: 28 TRUE / 25 FALSE) | coverage | selective acc | F1(FALSE) | MCC | confidently wrong |
|---|---|---|---|---|---|
| **routed QUANTITATIVE** | 26.4% [16.4, 39.6] | **100% [78.5, 100]** (14/14) | 0.387 | **+0.378** | **0** |
| baseline 3d @shipped (0.50/0.40) | 83.0% | 56.8% [42.2, 70.3] | 0.488 | +0.202 | 19 |
| baseline 3d @tuned (0.35/0.30) | 94.3% | 52.0% [38.5, 65.2] | 0.200 | +0.083 | 24 |
| *Always-True* | 100% | 52.8% | 0.000 | 0.000 | 25 |
| *Always-False* | 100% | 47.2% | **0.641** | 0.000 | 28 |

Per-class, routed: TRUE **P 1.00** R 0.29 F1 0.44 · FALSE **P 1.00** R 0.24 F1 0.39
· abstention rate 73.6%.

**Read the `Always-False` row before quoting F1(FALSE).** On this near-balanced
set an unconditional FALSE scores **F1(FALSE) = 0.641**, beating every real
system including ours. This is the exact mirror of the accuracy trap the project
documented on the natural 356, where Always-True scores 88.2%: **the safe headline
metric depends on the class prior of the set, so no single metric is safe across
both.** MCC is the one figure in this table that no degenerate strategy games in
either direction — Always-True, Always-False and Always-UNVERIFIABLE all score
0.000. On MCC, routed **+0.378** vs the baseline's best **+0.202**.

The honest summary of coverage: routed answers **26.4%** where the baseline
answers 83–94%. Routing is *narrower and cleaner*, not better across the board.

---

## 2. The sharpest evidence: same claim, opposite confident verdicts

On four claims both systems return a confident verdict and they disagree:

| claim | subject | claimed | actual (Wikidata) | routed | baseline | gold |
|---|---|---|---|---|---|---|
| SYN_QUAN_010 | Mount Everest | 6961.0 | 8844.43 | **FALSE** | TRUE | FALSE |
| SYN_QUAN_011 | Aconcagua | 6190.0 | 6962.0 | **FALSE** | TRUE | FALSE |
| SYN_QUAN_012 | Denali | 5895.0 | 6190.0 | **FALSE** | TRUE | FALSE |
| SYN_QUAN_013 | Kilimanjaro | 5642.0 | 5895.0 | **FALSE** | TRUE | FALSE |

**Routed 4/4 correct; baseline 0/4.** These are hallucinated elevations the
baseline *positively vouched for*, at entail 0.53–0.65 against retrieved Wikipedia
passages that do mention the mountain — just not that number. This is the same
failure the threshold sweep identified architecturally: BART-MNLI over retrieved
passages cannot separate "this passage supports the number 6961" from "this
passage is about Everest." A Wikidata `quantity` comparison has no inference step
to fool; the value either matches within tolerance or it does not.

## 3. The control no surface-form method can pass

`cross_substitute` injects **another real entity's true value** in a rotation, so
every claimed number in the set is a genuine mountain elevation carrying no
implausibility signal. **6 of the 8 distinct claimed values among the 14 covered
claims receive both a TRUE and a FALSE verdict:**

| value | TRUE for | FALSE for |
|---|---|---|
| 8848.86 | Mount Everest | Puncak Jaya |
| 6961.0 | Aconcagua | Mount Everest |
| 6190.0 | Denali | Aconcagua |
| 5895.0 | Kilimanjaro | Denali |
| 5642.0 | Mount Elbrus | Kilimanjaro |
| 4892.0 | Mount Vinson | Mount Elbrus |

Identical number, identical property (P2044), opposite verdict. The only differing
input is the **subject**. No plausibility heuristic, LLM numeric prior, or NLI
numeral-match can produce this pattern, because the digits are the same both
times. Equivalently, on the **6 matched pairs** (a Batch 3 claim and its own
perturbation, both covered) the verifier is correct on both sides **6/6 [61.0,
100]** — where an unconditional TRUE scores 0/6 and an unconditional FALSE also
scores 0/6.

This, not the accuracy figure, is the discrimination evidence.

---

## 4. Standalone on all 24 negatives

```
coverage             6/24    25.0% [12.0, 44.9]
accuracy on covered  6/6    100.0% [61.0, 100.0]
confident wrong      0
Always-True on this set  0.0%
```

The 18 abstentions each name their own gap, and none is a silent failure:

| n | reason |
|---|---|
| 5 | COMPUTATIONAL — needs operand retrieval + formula reconstruction (abstains by design) |
| 4 | entity unresolved (best candidate `Q391478`, a U.S. legislature item, below the 0.60 threshold) |
| 1 | entity unresolved — no Wikidata hits for "French effort to…" |
| 2 | no matching quantity property — best candidate P8687 (social-media followers) rejected |
| 2 | no matching quantity property — core-term guard, `record time` |
| 4 | no matching quantity property — entity has 14/19/63 properties, none of datatype `quantity` |

All 6 detections are `cross_substitute` mountain elevations via P2044. **Coverage
25.0% is the number to quote alongside every accuracy figure here.**

One implementation detail worth a footnote: Wikidata holds **two** P2044 values for
Everest (8848.86, the 2020 joint survey, and 8844.43, the 2005 Chinese survey) and
the verifier compares against the closer one. That is a *lenient* tie-break —
benefit of the doubt to the claim — which is the safe direction for a detector, and
it did not prevent any detection.

---

## 5. Two cache-collision corrections, in opposite directions

Both stem from phase3d's `nli__{claim[:60]}__{passage[:40]}` key
(`archive/scripts/relational_verifier_phase3d.py:194`). A perturbed claim and its
original share a key whenever the changed number sits past character 60 — and
synthetic negatives are near-identical to their originals *by construction*, so
the collision rate here is structural, not incidental. (On the natural 356 it
touches 8 rows / 2.2% and moves nothing by more than 0.67pp.)

**(a) Base-inheritance — 9 QUANTITATIVE rows, correction moves AGAINST us.**
Proven by bit-identical entail/contradict floats against the base claim, with
**0 of 69 non-colliding rows matching as a control**. All 9 inherited a gold-TRUE
original's TRUE, so they were scored as baseline *misses the baseline never made*.
Excluding them raises the baseline's detection rate 37.5% → 60.0% (+22.5pp) and
makes it *harder* to beat. Applied.

**(b) Negative-vs-negative duplication — 1 row, correction moves FOR us.** The
first audit only asked whether a negative inherited its *base's* scores. It never
asked whether two negatives collide with *each other* — and they do.
`SYN_QUAN_030` and `031` share a key (both entail 0.3594 / contradict 0.4227,
both from base Q2_C11, neither matching Q2_C11's own 0.7222/0.4430). One is a
duplicate read; which one is not recoverable from the artifact. On the 14
independent rows the baseline detects **8/14 = 57.1%** rather than 9/15 = 60.0%.
Applied.

Both are applied because whether a correction is convenient has no bearing on
whether it is right.

**Resolved, and my own count above was wrong.** The full audit is
`reference/negatives_cache_audit_2026-08-25.md`
(`current/negatives_cache_audit.py`, which **computes** these sets instead of
hardcoding them). Three corrections to the paragraph this replaces:

- **"12 corrupt rows is an undercount" was wrong — 12 is correct.** The 15 was
  the count of rows *sitting in shared-key groups*, which is not the same
  quantity as rows *needing correction*.
- The true affected count is **16 of 85 (18.8%)**, reached by finding a **third**
  class — *partial* inheritance, where entail is bit-identical to the base but
  contradict is not, because the key covers claim **and** passage. It affects
  `SYN_TEMP_059`, `SYN_TEMP_060`, `SYN_CITA_001`.
- **TEMPORAL's recorded 75.0% on 28 clean rows was right.** The independence and
  partial-inheritance corrections move it to 20/27 = 74.1% and then 19/26 =
  73.1% — not material. All five `SYN_TEMP_056–060` perturb one base, which is
  how a single claim contaminates five rows.

**Every QUANTITATIVE figure in this document is unaffected**: class (c) contains
no QUANTITATIVE row, and after the refactor `rq2_quantitative_table.py` produces
byte-identical output, asserted by `negatives_cache_audit.py --selftest`.

**One finding in this document is now qualified, though — see Part 2 of that
audit.** The baseline's low precision (0.099, "~9:1 false alarms") is
**reproduced by the 3.7% base rate alone** (predicted 0.0870 vs observed 0.0988),
so it is not evidence that retrieval+NLI cannot separate the classes: Youden's
J = +0.323. What survives from this document untouched is everything that is not
a precision figure — the 0-vs-19 confident-error count, MCC +0.378 vs +0.202, and
the same-number control.

---

## 6. The swept "optimum" is fit to the class prior, not to discrimination

`threshold_sweep.py` (2026-08-23) found **(0.35/0.30) strictly dominates** the
shipped (0.50/0.40) on the natural 356 — every metric improved at once — and
CLAUDE.md accordingly directs that RQ2 quote the baseline at the tuned point so as
not to strawman it. **On this negatives-enriched population the tuned point is far
worse:** F1(FALSE) 0.488 → 0.200, MCC +0.202 → +0.083, confident errors 19 → 24.
On the clean 15 it detects **2/15 while confidently asserting 13 hallucinations
are true.**

Both observations are correct. The mechanism is the reconciliation — the entail
threshold is a knob on how often the system says TRUE, and rows in `[0.35, 0.50)`
become TRUE under tuning:

| population | n | gold FALSE | rows in [0.35, 0.50) | of those gold TRUE (tuning helps) | gold FALSE (tuning hurts) |
|---|---|---|---|---|---|
| natural 356 (what was swept) | 356 | 3.7% | 92 | **81** | 3 |
| the 24 QUANTITATIVE negatives | 24 | 100% | 9 | 0 | **9** |

A 27:1 helpful-to-harmful ratio on the swept set; 0:9 here. **The sweep did not
find a better discriminator — it found a better fit to the natural set's 24:1
class imbalance.** This is the project's own class-imbalance trap operating one
level up: not on the metric being *reported* but on the hyperparameter being
*selected*.

**Verified not an artifact:** the 9 flipping rows and the 9 base-inheritance
corrupt rows are **disjoint** (overlap 0). All 9 flipping rows are in the clean 15.

### Consequences for reporting

1. **CLAUDE.md's instruction needs a scope qualifier.** "Report RQ2 against the
   baseline at (0.35/0.30)" holds for the natural 356. It does **not** transfer to
   negatives-enriched populations, where it hands the baseline its worst
   operating point — a reverse strawman, equally inadmissible.
2. **Quote the baseline at whichever point is stronger on the population being
   reported** (shipped, here), and say which.
3. **The routed verifier has no threshold at all.** It finds a Wikidata quantity
   statement and compares, or abstains. There is no operating point in it to fit
   to a class prior, so nothing to overfit. That architectural difference is now
   measured rather than asserted.
4. **State the class prior of the set any threshold was tuned on**, and never
   carry that threshold to a set with a different prior.

---

## 7. What this does and does not settle

**Settled.** QUANTITATIVE is the first type where routing beats the baseline on a
prior-independent metric (MCC +0.378 vs +0.202) with both classes present, zero
confident errors against the baseline's 19, and a discrimination control that no
surface-form method can pass. The 2026-08-23 RQ2 verdict — *"routing currently
loses to not-routing on four of five types… a verifier at 0% coverage detects
nothing"* — no longer applies to QUANTITATIVE. It still applies to TEMPORAL, EA
and CITATION.

**Not settled.** Effective n is small: 14 covered claims combined, 6 detections,
6 matched pairs. Every CI here is wide and must be printed with the figure. All 24
negatives are perturbations of Batch 1/3 claims, so they inherit that subject
distribution — 6 of 6 detections are mountain elevations via a single property
(P2044), which is *one property working*, not "QUANTITATIVE working." Coverage
25–26% is the binding limitation, and lifting it is property matching (the
`no matching quantity property` rows), not thresholds. The World Bank / WHO GHO
tier-2 backend remains unbuilt.

**Do not write:** "routed QUANTITATIVE is 100% accurate." Write: *100% on 14
covered claims [78.5, 100], at 26.4% coverage, with 0 confident errors, on a set
where an unconditional TRUE scores 52.8% and an unconditional FALSE scores 47.2%.*
