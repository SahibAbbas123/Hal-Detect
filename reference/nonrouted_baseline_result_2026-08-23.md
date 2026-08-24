# Non-routed baseline (RQ2) — first complete result, 2026-08-23

Run: `nonrouted_baseline.py` on Colab T4, all **356 labeled claims**, 0 failures.
Code path: `archive/scripts/relational_verifier_phase3d.py` imported unmodified,
so retrieval, ranking, NLI and thresholds are byte-identical to the authoritative
RELATIONAL verifier. Premise cap 3000 chars. Output:
`current/nonrouted_baseline_results.csv`, log `run.log`.

---

## 1. Headline

| | coverage | selective accuracy | AURAC |
|---|---|---|---|
| **3d-style** (threshold only) | **77.2%** [72.6, 81.3] | **69.8%** [64.2, 74.9] | 0.842 |
| **3e-style** (margin ≥ 0.15) | 53.7% | 81.2% [75.0, 86.1] | — |
| *Always-True* | 100% | **88.2%** | — |

**The baseline scores 18 points BELOW always guessing "TRUE".** That is not a bug,
and it is the whole reason `metrics.py` prints degenerate baselines next to every
result. With 314 TRUE / 13 FALSE / 29 UNVERIFIABLE, accuracy rewards a system that
never says FALSE, and punishes any system that tries to detect anything.

So **accuracy is the wrong headline for this project.** The defensible metrics are
F1(FALSE) and MCC:

| system | F1(FALSE) | MCC | hallucinations caught |
|---|---|---|---|
| Always-True | 0.00 | 0.000 | 0 of 13 |
| **Non-routed baseline (3d)** | **0.170** | **+0.180** | **8 of 13** |
| Routed TEMPORAL / EA (post-QID-fix) | 0.00 | 0.000 | 0 (0% coverage) |

---

## 2. The most important number in the run

**Of 81 FALSE predictions, only 8 are correct. Precision = 0.099.**

    gold TRUE          -> pred FALSE           67     <-- false alarms
    gold UNVERIFIABLE  -> pred FALSE            6
    gold FALSE         -> pred FALSE            8     <-- real catches

For every genuine hallucination it finds, the uniform pipeline invents roughly
**eight**. This is the same failure class the project already documented as the
`1 - entail` contradiction proxy — moving to proper 3-way NLI reduced it but did
**not** eliminate it. `CONTRADICT_THRESHOLD = 0.40` is simply too permissive: a
passage that merely *fails to support* a claim clears 0.40 routinely, and
"unsupported" is then reported as "contradicted".

**This is the strongest empirical argument for the routed design the project has
produced**, and it is a genuine contribution: uniform retrieval+NLI over
heterogeneous claims manufactures false hallucination alarms at ~9:1. Prior work
(FActScore, and the systems that fold NEI into False) cannot see this, because
folding NEI into False is exactly what creates it.

### The margin gate does not fix it

| | FALSE P | FALSE R | FALSE F1 | n predicted | MCC |
|---|---|---|---|---|---|
| 3d | 0.099 | 0.615 | 0.170 | 81 | **+0.180** |
| 3e (margin) | 0.121 | 0.308 | 0.174 | 33 | +0.144 |

The margin gate halves recall to buy 2 points of precision. F1 is flat and **MCC
gets worse**. Raising the contradiction threshold, or requiring explicit negation
evidence, is the direction — not a margin on entailment.

---

## 3. Per type, both variants

| type | n | 3d cov | 3d acc | 3e cov | 3e acc |
|---|---|---|---|---|---|
| RELATIONAL | 174 | 77.0% | 66.4% | 52.3% | 79.1% |
| TEMPORAL | 65 | 90.8% | 67.8% | 61.5% | 82.5% |
| QUANTITATIVE | 45 | 82.2% | 73.0% | 55.6% | 84.0% |
| ENTITY_ATTRIBUTE | 43 | 74.4% | **81.2%** | 60.5% | 80.8% |
| CITATION | 29 | 44.8% | 76.9% | 31.0% | 88.9% |

The 3d→3e trade is remarkably uniform: about **−22pp coverage for +12pp accuracy**.
Two exceptions worth reporting:

* **ENTITY_ATTRIBUTE is the one type where 3d dominates** — 3e loses 14pp of
  coverage and gains nothing (81.2% → 80.8%). Any per-type operating point should
  use 3d here.
* **CITATION has the worst coverage (44.8%)** and the pattern is diagnostic: the
  subject field is an organisation name, so "FAO" retrieves the *Aquaculture*
  page and no passage clears the similarity threshold. Uniform retrieval is
  structurally wrong for CITATION, which is what the two-level design was for.

---

## 4. RELATIONAL on the pooled set — the number CLAUDE.md was waiting for

**RELATIONAL, pooled n=174:  3d = 66.4% acc @ 77.0% cov;  3e = 79.1% acc @ 52.3% cov.**

Compare the recorded Batch-3-only figure, 80.77% acc @ 55.32% cov (cell 57, Phase 3e):

| | coverage | accuracy | n covered | 95% CI width |
|---|---|---|---|---|
| Batch 3 only (recorded) | 55.32% | 80.77% | ~26 | ±14.7pp |
| **Pooled 174 (3e, this run)** | 52.3% | **79.1%** | 91 | ≈±8pp |

**The Batch-3 number reproduces.** 80.77% → 79.1% with coverage 55.3% → 52.3%, on
6.7× the covered claims. That was the single biggest open statistical risk in the
project — that "80.77%" was an artifact of 26 claims — and it survived. The CI is
now narrow enough to separate 79% from 65%.

---

## 5. Phase 2's suspect labels are NOT driving the result

| | coverage | accuracy | Always-True |
|---|---|---|---|
| All labeled (n=356) | 77.2% | 69.8% | 88.2% |
| Human-labeled only, b1+b3 (n=247) | 76.9% | **71.6%** | 91.9% |

1.8pp apart on accuracy, 0.3pp on coverage. **The pooled figure does not lean on
the 109 AI-filled Phase 2 verdicts.** This robustness check was built in
precisely because it might have failed; it passed, and that is reportable.

(Author review of those 31 flipped rows is still worth doing, but it is no longer
blocking this result.)

---

## 6. The honest RQ2 verdict

Stated plainly, because it will be the first thing an examiner asks:

**Routing currently loses to not-routing on four of five claim types** — not
because routing is a bad idea, but because four of the five routed verifiers are
non-functional: TEMPORAL 0%/0%, ENTITY_ATTRIBUTE 0%/0%, QUANTITATIVE never
executed, CITATION 0/12 matched. The baseline reaches 67–81% accuracy with real
coverage on every one of those types.

The defence is *not* "accuracy is unfair". It is the error profile:

* the baseline answers a lot and is **wrong 90% of the time when it says FALSE**;
* the routed TEMPORAL/EA verifiers, after the 2026-08-21 QID fix, produce **zero
  confident-wrong verdicts** — they abstain and name the gap.

That is the coverage-versus-trustworthiness trade the thesis is actually about.
But right now it is an argument about *design intent*, not a measured win, because
a verifier at 0% coverage detects nothing and scores identically to Always-True on
the FALSE class. **To turn RQ2 into a measured result, the routed verifiers have to
produce non-zero coverage.** That makes task #8 — the entity-resolution prominence
prior — the critical path, not a side quest.

---

## 7. What this changes

1. **Report F1(FALSE) and MCC as primary; accuracy only alongside Always-True.**
   Any table that leads with accuracy makes this project look worse than it is and
   is trivially attacked.
2. **The 9:1 false-alarm rate is a headline finding, not a defect to hide.** It is
   the empirical motivation for the entire taxonomy.
3. **Report 3d and 3e as a curve, per type** — the −22pp/+12pp trade is stable
   enough to state as a general property, with EA as the documented exception.
4. **`CONTRADICT_THRESHOLD = 0.40` needs an ablation.** It is the direct cause of
   the 67 false alarms. Sweeping it costs nothing: the raw entail/contradict scores
   are already in the results CSV, so the whole curve is recomputable with no model
   calls.
5. **Fix the resolver (task #8) before claiming anything about routing.**

---

## 8. Reproducibility

* Single cached run, per the standing rule. Cache: 904 entries at start
  (nli=541, text=163, llmquery=35, title=126), merged from
  `relational_retrieval_cache.json` + `relational_nli_cache.json`.
* One Gemini read timeout (`Q5_C02`, 15 s) fell back to the bare subject as
  designed, resolving "human activities" → *Human behavior* → 0 passages →
  UNVERIFIABLE. Documented degradation, not an error.
* Premise cap 3000 chars is recorded in every row's `method` field. **The routed
  side must use the same cap** or the two halves see different premises.
* `chunk_passages()` has no maximum length, so before this cap long Wikipedia
  paragraphs overran bart-large-mnli's 1024-token window on **both** sides of the
  ablation. Worth a sentence in the method section.
