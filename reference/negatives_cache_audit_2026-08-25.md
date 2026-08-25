# The negatives cache audit, and a correction to the project's RQ2 motivation

**Date:** 2026-08-25
**Reproduce:** `.venv/bin/python current/negatives_cache_audit.py` (offline, zero
model calls, ~1 s) · `--selftest` enforces the evidence standard.
**Inputs:** `current/nonrouted_negatives_results.csv` (85),
`current/nonrouted_baseline_results.csv` (356), `current/synthetic_negatives.csv`.

This started as a bookkeeping fix to a collision count and ended up correcting a
claim this project has been treating as its strongest result. Both parts are
below; the second matters more.

---

## Part 1 — the collision inventory: 16 of 85, in three classes

`archive/scripts/relational_verifier_phase3d.py:194` keys its NLI cache as
`nli__{claim[:60]}__{passage[:40]}`. Truncating the claim at 60 characters means
two claims differing only past character 60 share an entry. Synthetic negatives
are perturbations of real claims — **near-identical to their originals by
construction** — so a changed number past character 60 collides. The rate here is
structural, not incidental. (On the natural 356 the same key touches ~2.2% and
moves nothing by more than 0.67pp.)

| class | what it is | remedy | rows |
|---|---|---|---|
| **(a) full inheritance** | entail *and* contradict bit-identical to the base claim's; no NLI call of its own | **exclude** — verdict fabricated | 12 |
| **(b) duplicate read** | two negatives share a key and identical scores; one real answer counted twice | **discount** — real, but not independent | 10 |
| **(c) partial inheritance** | entail bit-identical to base, contradict not | **report which half decided** | 3 |
| | | **union (classes overlap)** | **16 = 18.8%** |

**Correction to my own earlier note.** The 2026-08-25 QUANTITATIVE writeup said
*"the earlier '12 corrupt rows' figure is an undercount — 15 of 85 negatives are
involved in collisions."* That was wrong twice over. **12 fabricated rows was
correct.** The 15 was the count of rows *sitting in shared-key groups*, which is
a different quantity from rows *needing correction*; and the true affected count
is **16**, reached not by fixing the 12 but by adding two further classes. The
counting error is the reason `negatives_cache_audit.py` **computes** these sets
and no file hardcodes them any more — three successive audits reported 12, 15,
16, each copying the previous count instead of recomputing.

**Evidence standard.** Bit-identical float *strings*, compared as text — 17
significant figures do not agree by chance. Every class is reported with a
control: rows whose keys do **not** collide, checked for the same agreement.
Both controls are **0/70**, and `--selftest` fails if either is non-zero.

### Class (c) is new, and it is the interesting one

The key is keyed on claim **and** passage, so a row can inherit the cached answer
for overlapping passages and compute the rest fresh. The 3d rule tests entail
*first* (`entail ≥ et → TRUE; elif contradict ≥ ct → FALSE`), so **the inherited
half is the half that fires TRUE.**

| row | base | entail | contradict | 3d | decided by @shipped | @tuned |
|---|---|---|---|---|---|---|
| `SYN_CITA_001` | `Q5_C02` | 0.6209 | 0.1599 | TRUE | **entail (inherited)** | **entail (inherited)** |
| `SYN_TEMP_059` | `Q1_C02` | 0.4814 | 0.4619 | FALSE | contradict (fresh) | **entail (inherited)** |
| `SYN_TEMP_060` | `Q1_C02` | 0.4814 | 0.4619 | FALSE | contradict (fresh) | **entail (inherited)** |

`SYN_CITA_001`'s TRUE is decided by an inherited number at **both** operating
points, so that verdict is unsound outright. The two TEMPORAL rows are sound at
the shipped point — their FALSE came from the fresh contradict — but at the tuned
(0.35/0.30) point the inherited 0.4814 clears the entail bar and they flip to
TRUE **off a number computed for a different claim.** All five `SYN_TEMP_056–060`
perturb one base (Einstein at the Bern patent office, years 1906/1907/1910/1915/
2005), which is why one base claim contaminates five rows.

### Corrected baseline detection rate, per type and tier

Every negative is gold FALSE, so "detection" = the baseline said FALSE.

| type | raw | clean (−a) | indep (−a,−b) | strict (−a,−b,−c) |
|---|---|---|---|---|
| CITATION | 5/25 20.0% | 5/25 20.0% | 5/25 20.0% | **5/24 20.8%** |
| ENTITY_ATTRIBUTE | 5/5 100% | 5/5 100% | 5/5 100% | **5/5 100%** |
| QUANTITATIVE | 9/24 37.5% | 9/15 60.0% | 8/14 57.1% | **8/14 57.1%** |
| TEMPORAL | 24/31 77.4% | 21/28 75.0% | 20/27 74.1% | **19/26 73.1%** |
| **ALL** | 43/85 50.6% | 40/73 54.8% | 38/71 53.5% | **37/69 53.6%** |

**QUANTITATIVE is untouched by class (c), so every figure in
`reference/rq2_quantitative_negatives_2026-08-25.md` stands unchanged.** The
refactor that replaced the hardcoded sets with computed ones produces
byte-identical output from `rq2_quantitative_table.py`, and `--selftest` asserts
both legacy sets still reproduce.

TEMPORAL's recorded 75.0% on 28 clean rows was **right**; the independence and
partial-inheritance corrections move it to 73.1%, which is not material.

---

## Part 2 — the correction that matters: low precision is a base-rate artifact

**A detection rate on an all-FALSE set is uninterpretable alone.** All 85
negatives are gold FALSE, so an unconditional "FALSE" detects **100%** of them,
and the baseline's 53.6% is *worse than the degenerate strategy* — the exact
mirror of 88.2% accuracy on the natural 356 being worse than an unconditional
"TRUE". Same trap, opposite direction.

The pairing that does mean something is detection rate on the negatives (TPR)
against false-alarm rate on the natural set's gold-TRUE claims (FPR) — same code
path, same operating point, so the difference is discrimination. Youden's
**J = TPR − FPR** is 0 for Always-True *and* Always-False, the same property that
makes MCC the safe metric in the RQ2 tables.

| type (`type` column) | TPR on negatives | FPR on gold-TRUE | J |
|---|---|---|---|
| CITATION | 5/24 20.8% | 2/25 8.0% | **+0.128** |
| ENTITY_ATTRIBUTE | 5/5 100% | 5/42 11.9% | +0.881 |
| QUANTITATIVE | 8/14 57.1% | 9/41 22.0% | +0.352 |
| TEMPORAL | 19/26 73.1% | 19/62 30.6% | +0.424 |
| **ALL** | **37/69 53.6%** | **67/314 21.3%** | **+0.323** |

### The decomposition

Precision at fixed TPR/FPR is `P = πT / (πT + (1−π)F)`. The natural 356 is
**π = 13/356 = 0.0365** gold-FALSE. Substituting the measured rates:

```
predicted precision  0.0870
observed precision   8/81 = 0.0988
gap                  0.0118
```

**The observed precision is reproduced by the base rate alone.** Two claims on
record in CLAUDE.md therefore need correcting:

1. *"Of 81 FALSE predictions, 8 are correct — precision 0.099. Uniform
   retrieval+NLI manufactures hallucination alarms at ~9:1. **This is the
   strongest empirical motivation for the taxonomy the project has, and a real
   contribution.**"*
2. *"Contradiction precision never leaves 0.08–0.12 across the whole sweep and
   caps at 0.20 over all 225 grid points … **BART-MNLI's contradiction score over
   retrieved passages cannot separate 'refutes this' from 'does not mention this'
   at any operating point.**"*

Both are **precision** measurements, and precision is prior-dependent. At
π = 0.0365 a detector needs a TPR/FPR ratio of **26.4:1** to reach 50% precision
and **6.6:1** to reach 20%. The measured ratio is 2.5:1, so ~9:1 false alarms is
what the arithmetic *requires* — it is not evidence the detector cannot separate
the classes. **J = +0.323 is not zero.** At a balanced prior the same detector
would show precision **0.715**.

**What the threshold sweep actually established,** restated defensibly: the ROC
never reaches a high-precision regime at this base rate — the best TPR/FPR ratio
available anywhere on it is ~6.6:1, where ~26:1 is needed for even coin-flip
precision. That is a real and useful finding about the *shape* of the ROC. It is
not "cannot separate," and it should not be written that way.

**This is the project's own class-prior trap operating on its own headline
claim** — one level up again, now on the motivation rather than the metric or the
hyperparameter.

### What survives as motivation for routing, unchanged

None of these are precision figures and none depends on the class prior:

- **Confident-error count.** Routed QUANTITATIVE makes **0** confident errors on
  the combined 53 where the baseline makes **19**. Both systems saw the same rows.
- **MCC**, which no degenerate strategy games: routed **+0.378** vs baseline's
  best **+0.202**.
- **The same-number control** — 6 of 8 distinct covered values receive both a
  TRUE and a FALSE verdict, differing only in subject. No threshold, no prior, and
  no surface-form method can produce it.
- **The routed verifier has no operating point at all**, so there is nothing in it
  to fit to a class prior. That difference is now measured rather than asserted.
- **CITATION is the baseline's genuinely weakest type, J = +0.128** — close to no
  discrimination on fabricated citations, and prior-independent. This is a better
  motivation for structured citation checking than the precision figure was.

### The caveat that bounds all of Part 2

The negatives are **synthetic perturbations** — a swapped number or date —
plausibly easier to refute than a naturally-hallucinated causal claim. So the
measured TPR is an **upper** estimate of discrimination on real hallucinations,
and every J above is an upper bound rather than a point estimate. `EA`'s
5/5 is n = 5, Wilson [56.6%, 100%], and its J = +0.881 should not be quoted as a
figure at all.

---

## What this changes for reporting

1. **Never quote the baseline's precision or the "9:1 alarms" ratio without the
   base rate next to it**, and give J alongside.
2. **Stop writing "cannot separate at any operating point."** Write the
   ROC-shape version: no high-precision operating point exists at π = 0.037.
3. **Detection rate on the negatives is never quotable alone** — Always-False
   scores 100% there. Pair it with FPR, or report J.
4. **CITATION, not the aggregate precision figure, is where the baseline is
   weakest on a prior-independent measure.** Lead with that.
5. Both hardcoded collision sets are gone; anything needing them imports
   `negatives_cache_audit.Audit`.
