# HalDetect — verifier status report, 2026-08-23

Every number here is measured, from a named results file, on a stated row count.
Nothing is projected or estimated.

---

## 1. How many verifiers work

**All five now return verdicts. This morning two did.**

| verifier | rows | coverage | accuracy | 95% CI | evidence source | detection proven? |
|---|---|---|---|---|---|---|
| RELATIONAL | 174 | 52.3% | **79.1%** | ±8pp | Wikipedia + BART-MNLI | no |
| TEMPORAL + EA (hybrid) | 34 | **82.4%** | 78.6% | [60%, 90%] | Wikidata → Wikipedia+NLI | partly |
| QUANTITATIVE | 29 | 27.6% | **8/8** | — | Wikidata `quantity` | **yes** |
| CITATION (level 1) | 29 | 75.9% | **90.9%** | [72%, 97%] | Wikidata org resolution | no |

Started the day at: RELATIONAL working, QUANTITATIVE never executed, TEMPORAL 0%,
ENTITY_ATTRIBUTE 0%, CITATION 0/12.

---

## 2. The two baselines it must beat

| system | rows | coverage | accuracy | F1(FALSE) | MCC |
|---|---|---|---|---|---|
| **Always-True** (degenerate) | 356 | 100% | **88.2%** | 0.00 | 0.000 |
| non-routed NLI baseline (3d) | 356 | 77.2% | 69.8% | 0.17 | **+0.180** |
| non-routed NLI baseline (3e margin) | 356 | 53.7% | 81.2% | 0.17 | +0.144 |
| **LLM, gemma4:31b-cloud, closed-book** | 355 | **93.2%** | **83.1%** | 0.14 | +0.099 |

### The single most important sentence in this report

**Neither baseline beats "always say TRUE" on accuracy, and neither does any of our
verifiers on the pooled set.** With 314 TRUE / 13 FALSE / 29 UNVERIFIABLE, accuracy
rewards a system that never flags anything. Any table in the thesis that leads with
accuracy invites an examiner to point this out.

**Lead with F1(FALSE) and MCC.** On those, Always-True scores 0.00 / 0.000 — it
detects nothing — and every real system beats it, which is the honest form of the
claim.

---

## 3. What the numbers mean

### The LLM is *more* accurate and *worse* at detection

`gemma4:31b-cloud` asked directly, no evidence: 93.2% coverage, 83.1% accuracy —
higher than our NLI baseline on both. But:

* **F1(FALSE) 0.14, precision 0.10.** Of 31 FALSE verdicts, ~3 were right. The same
  ~9:1 false-alarm rate as retrieval+NLI, reached by a completely different mechanism.
* **MCC +0.099 vs the NLI baseline's +0.180.** On the imbalance-robust metric it is
  *worse*, despite looking better on accuracy.
* **22 confident verdicts on gold-UNVERIFIABLE claims.** It answers questions that
  cannot be answered, which is the calibration failure the abstention literature
  describes.

This is a genuinely strong result for the thesis: **"just ask a capable LLM" reaches
higher coverage but does not detect hallucinations better, and knows less about what
it doesn't know.**

### The abstention ablation — and a prediction that failed

Same model, same prompt, same temperature 0 / seed 7. The only change is an override
forbidding `UNVERIFIABLE`, so the contrast isolates abstention and nothing else.

| | three-way | forced binary |
|---|---|---|
| coverage | 93.2% | **99.4%** |
| accuracy | 83.1% | **83.1%** |
| F1(FALSE) | 0.14 | **0.19** |
| P(FALSE) | 0.10 | **0.14** |
| R(FALSE) | 0.23 | **0.31** |
| MCC | +0.099 | **+0.161** |
| overreach | 22 | 28 |
| UnR | 6.8% | 0.6% |

**The prediction was that forbidding abstention would push accuracy toward 88.2% and
collapse F1(FALSE) toward 0.00, reproducing Factcheck-Bench Table 5. That did not
happen.** Accuracy was identical to three decimal places, and every detection metric
improved slightly.

Recorded as a failed prediction rather than quietly dropped, because the real result
is more useful than the expected one:

> gemma abstained on 24 claims in three-way mode. Forcing it to answer those 24 cost
> **nothing** in accuracy and *gained* FALSE recall. So its abstentions were not
> landing on the hard cases — **its "I can't tell" carries almost no information
> about whether it actually knows.**

That is a stronger argument for structured verification than the one originally
sought. This system abstains for a **nameable** reason — "no Wikidata property matched
`record_time`", "entity unresolved at 0.53", "predicate/property agreement 0.12 below
threshold" — and tier 1 is 100% accurate on what it does answer. gemma abstains
without a reason, which is demonstrable by removing the option and observing that
nothing degrades.

Note also that forced-binary drove UNVERIFIABLE recall from 0.24 to **0.03** and
overreach from 22 to 28: it lost nearly all ability to flag the unanswerable. That
barely moved accuracy only because gold-UNVERIFIABLE is 29 of 356 — another reason
accuracy is the wrong headline.

**Do not frame the thesis's abstention design as "the LLM collapses without it."** On
this evidence it does not. Frame it as: abstention is only valuable when it is
*informative*, ours is tied to a stated evidential gap, and the LLM's is not.

### Contradiction detection by reading text has no working operating point

225 threshold combinations swept. FALSE precision never left 0.08–0.12 and capped at
0.20. Raising the threshold destroys recall while precision stays flat; by ct=0.65 it
catches **0 of 13** negatives while accuracy climbs to 92.5% purely by abstaining.

The model cannot separate *"this passage refutes the claim"* from *"this passage does
not mention it"*. That is the strongest available argument for structured
verification: Wikidata either holds a conflicting value or it does not.

### The tiering result — routing's clearest win

TEMPORAL + EA hybrid, by tier:

| tier | answered | correct | accuracy | confidence |
|---|---|---|---|---|
| tier 1 — Wikidata | 5 | 5 | **100.0%** | 0.80 |
| tier 2 — Wikipedia+NLI | 23 | 17 | 73.9% | 0.63–0.65 |

Confidence bands **never overlap**, so a risk-coverage curve ranks structured
evidence strictly above textual inference. Structured is narrow and reliable; text is
broad and noisy; tiering delivers both with honest ordering.

### QUANTITATIVE is the only verifier with proven detection

Controlled perturbation: **8/8 claims flip TRUE→FALSE at ≤1% value change, and none
flips inside the 0.5% tolerance.** That is discrimination, not base rate. It is the
only place in the project where a verifier is proven to read the evidence rather than
agree with the claim.

---

## 4. What they lack — stated plainly

**Row counts are small.** RELATIONAL's 174 is the largest slice; QUANTITATIVE and
CITATION rest on 29 each, and the hybrid on 34. A 29-row result carries a ±20pp
confidence interval no matter how good the point estimate looks.

**Only 13 natural gold negatives across 356 claims.** This caps everything: no
accuracy figure can distinguish detection from agreement. 85 synthetic negatives were
generated to work around it, and they are a narrower, easier distribution than real
model error — they must be reported separately, never pooled.

**CITATION level 1 cannot return FALSE.** A source that fails to resolve is
UNVERIFIABLE, not fabricated. So F1(FALSE) = 0.00 by construction and all 3 gold-FALSE
CITATION claims are missed — including *"The FAO reports that 82.6% of stocks…"*,
where the source is genuine and the falsehood is entirely in the assertion. Level 2
(attribution) is unbuilt.

**The hybrid's aggregate advantage over the baseline is ~3pp, not a win.** On
negatives: hybrid 83.3% recall vs baseline 80.6%. Tier 1 answered only 2 of 36 claims,
so the hybrid is ~94% fall-through — i.e. mostly the baseline wearing a routed label.
Routing's real advantage is precision at the top of the confidence ordering, which is
a narrower claim and the one the data supports.

**QUANTITATIVE reaches 27.6% and abstains on 72%.** 6 COMPUTATIONAL and 1 COMPARATIVE
abstain by design; the rest hit a genuine `PROPERTY_TO_WIKIDATA` ceiling — Wikidata has
no property for "Usain Bolt's record time" because it is not an entity attribute.

**Notebook cells 69/75 still contain the old buggy resolver.** Every measurement here
comes from the standalone harnesses, not the live notebook.

**109 of 356 gold labels were AI-generated.** The 31 highest-risk (AI-flipped) rows
have now been reviewed against primary sources and all confirmed; 78 remain unreviewed
at lower risk. Results with and without Phase 2 differ by under 2pp, so nothing
currently hinges on them.

---

## 5. Honest one-paragraph summary

Five verifiers return verdicts on 356 claims. RELATIONAL (79.1% @ 52.3%) and CITATION
level 1 (90.9% @ 75.9%) are the strongest; QUANTITATIVE is the only one with proven
detection (8/8 flips at ≤1%); the TEMPORAL/EA hybrid reaches 82.4% coverage but mostly
via text fall-through rather than structured lookup. Both baselines — retrieval+NLI and
a 31B LLM asked directly — fail to beat "always say TRUE" on accuracy, and both show a
~10% precision on FALSE verdicts, which is the central empirical argument for
structured verification. The binding constraint on every claim in this report is that
only 13 of 356 gold labels are negative.
