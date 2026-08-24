# Literature findings — verified against source PDFs, 2026-08-22

Purpose: a citable index of what the 23 papers in `/Users/sahibabc/Papers/hallucination papers/`
actually say about the problems HalDetect currently has. Written for two later uses:
(1) solving a design problem, (2) drafting the literature review / thesis text.

## How to trust and re-verify this document

Per the CLAUDE.md standing rule, every quotation below was checked **verbatim against the
PDF text**, not taken from a summary. Two provenance notes:

* **Durable reference** = the PDF filename in `/Users/sahibabc/Papers/hallucination papers/`.
* **Line numbers** refer to plain text extracted with `pypdf`. That extraction lived in a
  job temp dir and is **ephemeral — assume it is gone.** Regenerate before re-checking:

  ```
  .venv/bin/python -c "
  import pypdf,sys,pathlib
  p=pathlib.Path(sys.argv[1]); r=pypdf.PdfReader(str(p))
  print('\n'.join((pg.extract_text() or '') for pg in r.pages))
  " "/Users/sahibabc/Papers/hallucination papers/<file>.pdf" > out.txt
  ```

* **Gotcha that already bit me once:** this extraction hyphen-wraps words across line
  breaks (`re-\ntrieval`). A grep for a multi-word phrase can return nothing even when the
  phrase is present verbatim. Grep for a short fragment, then read surrounding lines.

Paper-name → filename mapping that is not guessable:

| Paper | File |
|---|---|
| FinGround / FinHalu | `2604.23588v1.pdf` |
| RealFactBench | `realfactbench.pdf` |
| Factcheck-Bench | `Factcheck-Bench- Fine-Grained Evaluation Benchmark for Automatic Fact-Checkers.pdf` |
| Semantic entropy (Nature) | `Detecting hallucinations in large language models using semantic entropy.pdf` |

---

## 1. Does an LLM-with-web-search make a purpose-built verifier redundant?

**No — and there is a direct published measurement.** Factcheck-Bench Table 5 benchmarks
the *commercial product* Perplexity.ai against a purpose-built pipeline, on the same data.

| Verifier | Source | F1 (True) | F1 (**False**) |
|---|---|---|---|
| Random | — | 0.56 | 0.27 |
| Always-True | — | **0.88** | 0.00 |
| Always-False | — | 0.00 | 0.33 |
| Inst-LLAMA | Wiki | 0.80 | 0.42 |
| Inst-LLAMA | Web | 0.84 | 0.47 |
| GPT-3.5-Turbo | Wiki | 0.76 | 0.41 |
| GPT-3.5-Turbo | Web | 0.81 | 0.46 |
| **Perplexity.ai** | Web | 0.83 | **0.53** |
| **Factcheck-GPT** | Web | 0.79 | **0.63** |

Verbatim: *"Factcheck-GPT performs the best on false claims with F1=0.63, and then
Perplexity.ai by 0.53"*. Also verbatim: *"false claims tend to be identified less
accurately than true claims across all approaches, implying that it is more difficult to
detect factual errors than the correct statements."*

**Two things to carry into the thesis:**

1. Purpose-built beats commercial LLM+search by **10 F1 points on the hard class**. This is
   the answer to "why not just use Perplexity" (`thoughts.txt` Q1).
2. **Always-True scores F1 = 0.88 on the True class** while scoring 0.00 on False. A
   degenerate baseline can look excellent on one class. Therefore **report per-class F1,
   never accuracy alone** — our own "80.77% accuracy" is exposed to this criticism.
   Include Random / Always-True / Always-False as baselines; this table is the precedent.

**Cuts against our RELATIONAL design**, verbatim: *"Performance using Wikipedia as the
source is inferior to using web articles, this is largely limited by the knowledge coverage
of Wikipedia, esp. on open-domain benchmarks."* Wiki→Web is +5pp for both Inst-LLAMA and
GPT-3.5. Our RELATIONAL verifier is Wikipedia-passage-based at 55.32% coverage — that
ceiling is **expected**, not an implementation defect. Adding a web-search tier is the
literature-supported fix, and the expected shape of the gain is coverage more than accuracy.

---

## 2. Metrics for reporting accuracy AND coverage (abstention)

The fact-checking-benchmark literature cannot represent our contribution; the
**selective-prediction** literature can. Cite the latter.

* **Factcheck-Bench / OpenFactCheck fold NEI into the False class** and report no coverage
  axis. Structurally unable to score honest abstention. Do not frame against these.
* **RealFactBench** reports Macro-F1 + MCC + **Unknown Rate (UnR% ↓)** + Explanation
  Quality — the nearest published precedent for our accuracy+coverage split. It explicitly
  frames UnR as measuring *"over-conservatism or over-confidence"* (≈ line 120), i.e. a
  two-sided quantity, not just a penalty. Nuance to preserve: a nonzero UnR is not
  automatically bad.
* **Semantic entropy (Nature)** introduces **AURAC** — area under the *rejection accuracy*
  curve (≈ line 272), scored alongside AUROC. This is the formal, citable scalar that
  **rewards** correct abstention, computed over a risk-coverage curve. This is the metric
  our whole design is built for.

**DO NOT CITE RealFactBench's web-search improvement numbers.** Its 63.53→86.96 F1 gain
carries this caveat, verbatim at ≈ line 548: *"testing was restricted to samples initially
misclassified by the models."* Not a clean measurement of web-search benefit.

---

## 3. Is a ~122–500 claim gold set defensible?

**Yes, and there is a quotable authority.** Factcheck-Bench's own Limitations section:
it has only **94 (question, response) pairs**, and verbatim (≈ line 990):

> *"due to high cost (i.e., over 30-50 USD on average to evaluate 100 LLM responses
> depending on its length), developers generally evaluate on less than 100 examples in the
> development iterations, sometimes even 10 examples to save costs. Practically, our
> dataset is enough to be used as a benchmark for the preliminary evaluation of automatic
> fact-checking systems."*

Comparable published set sizes: FacTool-QA 233 · FELM-WK 532 · semantic entropy's
FactualBio **150** · Factcheck-Bench 678 claims / 94 pairs · RealFactBench 6,000.
Ours (122 / 126) sits inside the normal range.

**The misconception to avoid:** "people use 1000+ rows" is about **training**. HalDetect
trains nothing (BART-MNLI and SBERT are frozen, off-the-shelf); there is no train/val
split to starve. For *evaluation* the binding constraint is confidence-interval width.

**The real problem, which raw dataset size hides.** RELATIONAL's headline is
"80.77% acc / 55.32% cov" on 47 Batch-3 claims. Accuracy is therefore measured on
0.5532 × 47 ≈ **26 covered claims** (and 21/26 = 0.8077 confirms it). Coverage splits mean
**effective n for an accuracy claim is far below the dataset size.**

Wilson 95% intervals (hand-computed 2026-08-22; re-verify with the snippet below):

| Quantity | Point | 95% Wilson CI | ± |
|---|---|---|---|
| RELATIONAL accuracy (21/26) | 80.8% | [62.1%, 91.5%] | ±14.7pp |
| RELATIONAL coverage (26/47) | 55.3% | [41.3%, 68.6%] | ±13.7pp |
| TEMPORAL+EA coverage (6/34) | 17.6% | [8.4%, 33.5%] | ±12.6pp |
| *hypothetical* 81% @ n=100 | 81% | [72.2%, 87.5%] | ±7.6pp |
| *hypothetical* 81% @ n=250 | 81% | [75.7%, 85.4%] | ±4.8pp |
| *hypothetical* 81% @ n=500 | 81% | [77.3%, 84.2%] | ±3.4pp |

```python
import math
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = (z/d) * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return p, max(0.0, c-h), min(1.0, c+h)
```

Consequence: **the flagship result cannot statistically separate 80% from 65%.** Reaching
±5pp needs ~240–250 *covered* claims per type ≈ ~450 raw claims per type at 55% coverage.
So "~500" is the right order of magnitude, but **per verifier**, and what makes it
defensible is publishing the interval. FinGround reports ±95% CI on every cell of its
Table 1 — good precedent to copy.

---

## 4. QUANTITATIVE verifier architecture — settled by FinGround (`2604.23588v1`)

**Reject generic NLI as the primary mechanism.** Verbatim (≈ lines 332–335; note the
hyphen-wrap on `re-\ntrieval`):

> *"Generic NLI fails on ratio and margin verification even when the correct evidence
> passage is retrieved, because the failure is in reasoning rather than retrieval."*

This closes the "architecture undecided (text+NLI fallback vs stay UNVERIFIABLE)" question
in CLAUDE.md against the NLI option.

**The single best sentence in the corpus for our thesis introduction** — the line
immediately preceding the above:

> *"Computational claims show the highest hallucination rate (28.4%) despite being the most
> amenable to automated verification when properly typed, so **the bottleneck is routing
> rather than verification difficulty**."*

That is HalDetect's central bet, asserted by an independent paper. Use it in the intro.

### Their design, to mirror

* **Three numeric subtypes, not one bucket:**
  * *Numerical* — structured extraction → exact match against a table cell.
  * *Computational* — formula reconstruction: 47 financial formula templates → retrieve
    operands → recompute with **±0.5% tolerance** for rounding conventions.
    End-to-end computational verification = **90.2% F1**.
  * *Comparative*.
* **Extraction schema `(value, unit, entity, time_period)`.** Verbatim: *"For numerical
  claims, structured extraction identifies the specific value, unit, time period, and
  entity for exact matching against table cells."*
* **Alignment** via a cross-encoder fine-tuned on 8,400 financial NLI examples
  (TAT-QA + FinQA), 87.2% alignment F1.
* **Detection results (Table 1, ±95% CI):** SelfCheckGPT 72.8 · HHEM 76.3 · FActScore 76.7 ·
  Self-RAG 79.1 · CRAG 77.6 · GPT-4o teacher 95.0 · **FinGround 8B distilled 91.4**.

### Granularity ablation — validates our taxonomy size

6-type beats 3-type by **4.3 F1**; 10-type shows **no significant gain (p = 0.23)**
(≈ line 195). So splitting our QUANTITATIVE bucket into 2–3 subtypes moves us from 5 to
6–7 types and is **directly supported**; going finer is not. Rank-style claims such as
`launch_volume_rank` are *Comparative* and need multi-entity retrieval — which is why they
could never work inside a single QUANTITATIVE bucket.

### Hedging is the top false-positive driver

Verbatim: *"Hedged financial language ('approximately,' 'roughly') drives 52% of false
positives."* A **hedge detector must run before any numeric comparison.**

### Tolerance trade-off

Numerical tolerance thresholds catch **89% of near-misses** (≈ line 1074). Cost: recall
drops on hallucinated values that fall inside the tolerance band. Tolerance is a knob to
report, not a constant to hide.

### Citable defence of the UNVERIFIABLE verdict

Verbatim — this answers `thoughts.txt` Q2 ("will I be able to show greater scores?") by
legitimising coverage < 100%:

> *"We treat retrieval-induced unverifiability as a recoverable failure mode routed
> downstream rather than a silent miss; the alternative of defaulting unverifiable claims
> to supported would conflate evidence absence with evidence consistency, which the
> regulatory use case forbids."*

Their unverifiable path: below cross-encoder threshold → `unverifiable` → routed to
targeted re-retrieval, never silently resolved. Analyst pilot: false-negative rate 3.8%
over 1,847 queries; **56% of the 27 missed hallucinations were computational claims whose
operand evidence fell outside the retrieved window** — i.e. their residual failures are
retrieval-window failures, matching our own coverage-bound diagnosis.

**Open gap for us:** FinGround compares against **table cells** from financial reports. We
are open-domain with no tables. Planned substitution — Wikidata `quantity`-datatype
properties as tier 1, Wikipedia text/infobox number extraction as tier 2. FEVEROUS is the
alternative table-bearing source if that proves too thin.

---

## 5. Entailment-cluster papers (MiniCheck, CLATTER, Decomposed Entailment)

* **MiniCheck** reaches **74.7 balanced accuracy vs GPT-4's 75.3 at ~400× lower cost** —
  i.e. a small specialised entailment model is competitive with a frontier LLM for
  fact-checking. Supports our BART-MNLI choice against a "just use an LLM" objection.
* **Zero KG / Wikidata-based methods** appear in CLATTER or Decomposed Entailment. Our
  structured-source routing is genuinely under-explored — a novelty argument.
* **None of the three handles abstention.** Reinforces §2: the abstention framing must be
  borrowed from selective prediction, not from this cluster.
* **Decomposition errors accumulate multiplicatively** across
  Omission / Ambiguity / Over-decomposition / Alteration. Our claim-extraction step is
  upstream of everything, so its error rate multiplies through every verifier — worth
  measuring separately rather than assuming.

---

## 6. Benchmarking against FEVER / FActScore — why, and the caveat

Motivation, strongest first:

1. **FEVER has a NOT ENOUGH INFO class.** Per §2, Factcheck-Bench and OpenFactCheck fold
   NEI into False. Our abstention contribution needs a three-way-labelled benchmark to be
   measurable at all. This is the strongest single reason.
2. **Wikipedia-grounded** — the same evidence source as our best verifier (RELATIONAL),
   so it tests our strongest component on home turf at large n.
3. **Fixes the sample-size problem without new annotation** — gold labels already exist.
4. **FEVEROUS adds tables** — directly relevant to §4's missing structured numeric source.

FActScore is a weaker secondary: Wikipedia-grounded with atomic-fact decomposition that
maps onto our claim extraction, but **no NEI class** and single-domain (biographies).

**Caveat to state ourselves before a reviewer does:** FEVER claims are human-written
mutations of Wikipedia sentences, **not LLM-generated text**. FEVER therefore measures
*verifier quality*; our own gold set measures *hallucination detection on real LLM output*.
Different questions → report both tables and name the distinction explicitly. Owning it
gives external validity + task validity; letting a reviewer find it is a hole.

**Bonus experiment:** FEVER claims arrive untyped, so running our classifier over them
**isolates router accuracy from verifier accuracy** — currently indistinguishable in our
results. This is the `thoughts.txt` observability point (log retrieval / rerank / context /
generation separately) applied to our architecture: log **routing** separately from
**verification**.

*(FEVER / FEVEROUS / FActScore specifics here are from background knowledge — WebSearch was
unavailable when this was written. Confirm exact set sizes and label definitions before any
of it reaches thesis text.)*

---

## 7. Why chasing "beat 0.63" is the wrong target

* **Invalid as stated.** 0.63 is Factcheck-GPT's false-claim F1 **on Factcheck-Bench's
  dataset**. A number of ours on our dataset is not comparable — different claim
  distribution and difficulty. Cross-dataset F1 comparison gets rejected on sight.
* **Two valid routes**, ideally both: run an LLM+search baseline on **our** claims, or run
  **our** system on FEVER / Factcheck-Bench.
* **Wrong axis anyway.** Perplexity answers ~100% of claims; we answer ~55% and abstain.
  Not comparable at a point — comparable as **curves**. The strong, honest claim is
  *"at matched coverage our accuracy dominates the baseline at every operating point"*,
  scored with AURAC (§2).
* **Novelty is the method, not the score.** Ours is taxonomy-routed verification with
  honest abstention, independently supported by FinGround's "the bottleneck is routing
  rather than verification difficulty." A negative result with clean 5-Why attribution
  (which we already have for TEMPORAL/EA) is publishable; an unexplained leaderboard win
  is not.

---

## 8. Action list this literature implies

| # | Action | Driven by |
|---|---|---|
| 1 | Build QUANTITATIVE as structured extract-and-compare, 3 subtypes, hedge detector first, ±0.5% tolerance. **Not NLI.** | §4 |
| 2 | Stand up an LLM+search baseline on our own 122 claims | §1, §7 |
| 3 | Report per-class F1 + Random / Always-True / Always-False baselines | §1 |
| 4 | Report Wilson CIs on every rate; stop quoting bare point estimates | §3 |
| 5 | Report a risk-coverage curve + AURAC, not a single F1 | §2, §7 |
| 6 | Add a web-search tier *after* Wikipedia, with cached evidence + source logging | §1 |
| 7 | Benchmark on FEVER (three-way labels); state the synthetic-claim caveat | §6 |
| 8 | Log routing separately from verification | §5, §6 |
| 9 | Measure claim-extraction error separately — it multiplies downstream | §5 |
