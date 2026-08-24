# Threshold sweep over the non-routed baseline — 2026-08-23

`current/threshold_sweep.py --write` → `current/threshold_sweep.csv` (225 points).
**Zero model calls**: the raw `entail`/`contradict` scores were already in
`nonrouted_baseline_results.csv`, so the whole surface is arithmetic. Run in
seconds, both on all 356 labeled claims and on human-labeled-only (b1+b3, n=247)
as a robustness check.

---

## 1. The shipped operating point is strictly dominated

| point | coverage | accuracy | F1(FALSE) | P(FALSE) | R(FALSE) | MCC |
|---|---|---|---|---|---|---|
| **shipped (0.50 / 0.40)** | 77.2% | 69.8% | 0.170 | 0.099 | 0.615 | +0.180 |
| **best (0.35 / 0.30)** | **90.2%** | **84.7%** | **0.292** | 0.200 | 0.538 | **+0.288** |

Not a trade — **every metric improves at once**: coverage +13pp, accuracy
+14.9pp, F1(FALSE) +0.12, MCC +0.108. The same point wins on MCC, F1(FALSE) *and*
macro-F1, and it holds on the human-only subset (90.7% / 86.6% / 0.308 / +0.283),
so it is not an artifact of Phase 2's AI-filled labels.

Coverage at the optimum (90.2%) is essentially **at the ceiling**: NLI scored a
passage for 322/356 = 90.4% of claims. The other 34 abstained before NLI (no page
resolved, or nothing cleared the SBERT gate) and no threshold can move them —
lifting that is a *retrieval* problem, not a threshold problem.

### Methodological consequence: the baseline must be reported at its best point

The committed spec calls this "the natural non-strawman baseline". Reporting it at
`phase3d`'s shipped defaults, when a better operating point exists on the same
scores, would make it a strawman by exactly the amount above — and the routed
system would be credited with a 15-point accuracy gap that is really just an
untuned constant.

**So the RQ2 comparison must use the baseline at (0.35 / 0.30): 90.2% coverage,
84.7% accuracy.** That is a considerably harder target than 77.2% / 69.8%, and
adopting it is the honest choice, not the convenient one.

---

## 2. The real finding: contradiction precision has no good operating point

Sweeping the contradiction threshold at entail = 0.50:

| ct | coverage | accuracy | n FALSE | true pos | P(FALSE) | R(FALSE) | MCC |
|---|---|---|---|---|---|---|---|
| 0.30 | 86.0% | 63.4% | 112 | 10 | 0.089 | 0.769 | +0.191 |
| 0.35 | 83.1% | 65.5% | 102 | 10 | 0.098 | 0.769 | +0.208 |
| **0.40** *(shipped)* | 77.2% | 69.8% | 81 | 8 | 0.099 | 0.615 | +0.180 |
| 0.45 | 71.3% | 74.4% | 60 | 5 | 0.083 | 0.385 | +0.112 |
| 0.50 | 64.3% | 81.7% | 35 | 3 | 0.086 | 0.231 | +0.087 |
| 0.55 | 59.3% | 88.2% | 17 | 2 | 0.118 | 0.154 | +0.097 |
| 0.60 | 57.6% | 90.2% | 11 | 1 | 0.091 | 0.077 | +0.052 |
| 0.65 | 55.9% | 92.5% | 5 | **0** | 0.000 | 0.000 | −0.023 |
| ≥0.80 | 54.5% | 94.8% | 0 | 0 | 0.000 | 0.000 | 0.000 |

**Precision never leaves the 0.08–0.12 band anywhere in this sweep, and tops out
at 0.20 over the entire 225-point grid.** Raising the threshold does not buy
precision — it destroys recall while precision stays flat, and by ct = 0.65 the
system catches **zero of 13** negatives while accuracy climbs to 92.5% purely by
abstaining more.

That is a materially stronger claim than "0.40 was set too low". The original
hypothesis was that one badly chosen constant produced the 67 false alarms. It is
worse than that:

> **The contradiction score from BART-MNLI over retrieved Wikipedia passages is
> close to uninformative for this task. There is no threshold at which it
> separates "this passage refutes the claim" from "this passage does not mention
> the claim".**

This is the same defect the project already documented for the `1 − entail`
proxy — and it survives the fix. Proper 3-way NLI made contradiction *independently
scored* but not *discriminative*. It is a limitation of the evidence-and-inference
architecture, not of a hyperparameter.

**Why this is the best available motivation for structured verification.** The
routed verifiers do not infer refutation from prose at all: Wikidata either holds a
conflicting value or it does not. That is the one thing this sweep proves textual
NLI cannot do at any operating point. It also explains why Factcheck-Bench and
OpenFactCheck fold NEI into False — doing so hides precisely this failure, which is
why the project decided not to frame results against them.

Also note the accuracy column read alone is actively misleading: 94.8% at ct = 0.80
looks excellent and is a system that has stopped detecting anything, answering only
54.5% of claims. Effective n, not accuracy.

---

## 3. Per-type optima — a real signal, but overfit numbers

| type | n | best e/c (all) | best e/c (human-only) | shipped MCC | best MCC | Δ |
|---|---|---|---|---|---|---|
| RELATIONAL | 174 | 0.35 / 0.40 | 0.40 / **0.30** | +0.105 | +0.333 | +0.228 |
| TEMPORAL | 65 | 0.35 / 0.45 | 0.45 / **0.30** | +0.308 | +0.364 | +0.056 |
| QUANTITATIVE | 45 | 0.35 / **0.50** | 0.35 / **0.50** | +0.419 | +0.643 | +0.224 |
| ENTITY_ATTRIBUTE | 43 | 0.20 / 0.30 | 0.20 / 0.30 | 0.000 | 0.000 | 0.000 |
| CITATION | 29 | 0.35 / **0.30** | 0.35 / **0.30** | **−0.115** | +0.192 | +0.308 |

**Read this cautiously — the exact values are overfit.** They are tuned on the same
rows they are scored on, and there are only **13 gold negatives across all five
types**. RELATIONAL and TEMPORAL's optima move between the two label sets
(0.40 → 0.30 on contradiction), which is what noise-dominated tuning looks like.
Per-type threshold *values* are not a result and must not be quoted as tuned
constants.

Three things **are** stable across both label sets and are reportable:

1. **QUANTITATIVE wants a strict contradiction threshold (0.50); CITATION wants a
   permissive one (0.30).** A 0.20 spread in the same direction in both runs. Types
   genuinely differ in how much textual contradiction evidence to trust.
2. **CITATION has NEGATIVE MCC at the shipped threshold** — −0.115 pooled, −0.150
   human-only. The uniform pipeline is *worse than chance* at detecting false
   citations. Combined with CITATION's 44.8% coverage and the "FAO" → *Aquaculture*
   retrieval failure, this is the strongest per-type evidence in the project that
   one pipeline cannot serve all five types.
3. **ENTITY_ATTRIBUTE's MCC is 0.000 everywhere** because it has essentially no gold
   negatives. Its 97.4% "accuracy" at the optimum is uninformative by construction —
   the exact trap `metrics.py` was built to surface. EA needs controlled
   perturbation, not tuning.

**What would make the per-type claim real:** a dev/test split, or synthetic
negatives per type (the `--sensitivity` route). With 13 negatives, per-type tuning
cannot be validated, only hypothesised.

---

## 4. Actions

1. **Re-report the baseline at (0.35 / 0.30).** 90.2% cov / 84.7% acc. Anything
   else is a strawman comparison. No re-run needed — recomputable from the CSV.
2. **The flat-precision result is a headline finding.** Contradiction detection via
   retrieval+NLI has no good operating point; that is the argument for structured
   verification, and it is stronger than the false-alarm count alone.
3. **Report accuracy only with coverage and effective n.** The ct ≥ 0.65 rows show
   how easily accuracy alone is gamed by abstention.
4. **Do not quote per-type threshold values.** Quote the qualitative finding
   (QUANTITATIVE strict, CITATION permissive, CITATION worse-than-chance uniform)
   and label the values as unvalidated.
5. **EA and the negatives problem is now the binding constraint on every claim
   about detection.** 13 negatives across 356 claims caps what any of this can
   establish. Controlled perturbation is not optional polish.
