# SOFI 2023, calibrated abstention, and entity-linking inventories — assessed

**Written 2026-08-26.** The author ran three lookups I could not (WebSearch unsupported on
this model; FAO returned 403 to WebFetch again, twice now) and supplied
`~/.gemini/antigravity-cli/brain/13bfc77d-…/sofi_abstention_entity_linking_results.md`,
7,120 bytes. This assesses all three parts against the project's own data.

**Headline: one of the three retracts an analysis of mine.** §3 below corrects
`external_catalog_assessment_2026-08-26.md` §2, which was right about two systems and wrong
about the one that mattered.

**Provenance.** The supplied file is another tool's output. It is treated as evidence to be
audited, not inherited — the standing lesson from `external_catalog_assessment` §6. Where I
could test a claim against project data or internal arithmetic, I did; where I could not, it
is marked.

> **STATUS UPDATE, same day.** After this document was written the author authorised the flip
> ("ok flip it") and it was **applied and measured**. §1's numbers below were *predictions*;
> **§5 records what actually happened**, scores those predictions against the measurements, and
> corrects one count this document got wrong. Read §5 before quoting anything from §1's blast-
> radius table. Sections 2–4 are unaffected except where §5 says otherwise.

---

## 1. `Q22_C01` — the flip is justified, and it costs the thesis rather than helping it

### The claim, verbatim from the authoritative file

`current/haldetect_phase2_goldlabeled (3).csv`, row `Q22_C01`, 126 rows, 15 columns:

| field | value |
|---|---|
| `claim` | **"The FAO reported in 2023 that global food insecurity increased during 2022."** |
| `type` / `gold_type` | CITATION |
| `property` | `trend_during_period` |
| `value` | **`increased`** |
| `secondary` | `{"time_period": "2022", "source": "FAO", "report_year": "2023"}` |
| `gold_verdict` | **TRUE** ← currently |

### What SOFI 2023 says

FAO document code **`cc3017en`**, Executive Summary **p. 10**, quoted verbatim in the
supplied file:

> *"The prevalence of moderate or severe food insecurity at the global level remained
> **unchanged for the second year in a row**, affecting 29.6 percent of the world population
> in 2022 (2.4 billion people) – still 391 million more than in 2019."*

Supporting locations given: **§2.1, pp. 16–18** (FIES narrative), **Figure 4**, **Table 3**
(*prevalence by region and severity, 2015–2022*).

**The claim is FALSE.** Its `property`/`value`/`time_period` triple asserts a trend of
`increased` **during 2022**. The report states the trend during 2022 was *unchanged* — 29.6%
in both 2021 and 2022. The **+391 million is measured against 2019**, and the surge it
reflects occurred 2019→2020 at the pandemic's onset. The claim collapses a four-year horizon
into a one-year one and attributes the result to a named source that says the opposite.

**Falsity class: misattribution to a named source.** The source exists, the report year is
correct, the topic is correct — and the source does not say what the claim says it says.

### Arithmetic audit of the supplied table — 5/5 reconcile

Run because the table is another tool's output. A fabricated table rarely reconciles on
several independent axes.

| check | result |
|---|---|
| severe-only 11.3% + moderate-only 18.3% == total 29.6% | **PASS** (exact) |
| 2.4B − 2.0B ≈ +391M | **PASS** (400M vs 391M, within 5%) |
| 29.6% − 25.3% ≈ +4.3pp | **PASS** (exact) |
| 2021 == 2022, i.e. the "unchanged" | **PASS** (29.6 == 29.6) |
| implied world population 2022 = 2.4B ÷ 29.6% | **PASS** (8.11B, plausible) |

**This is self-consistency, not primary confirmation.** FAO `openknowledge` returned **403**
to WebFetch again. The 403 is now recorded twice and should be treated as a permanent
property of that host from this environment, not retried.

### What every system said about it — the finding worth more than the flip

| system | verdict on `Q22_C01` | detail |
|---|---|---|
| non-routed baseline | **TRUE** | confidence 0.809, entail 0.7719, contradict 0.1798, 3 scored passages |
| CITATION **L1** | **TRUE** | `source exists: Q28767587 is a scholarly article` |
| CITATION **L1b** | **UNVERIFIABLE** | `work title 'FAO' has 0 content word(s) (<2) — a bare organisation reference, not a cited work` |
| LLM baseline (closed-book) | **TRUE** | reason: *"The FAO's 'State of Food Security and Nutrition in the World 2023' report **confirmed** that global food insecurit[y increased]…"* |

Two things fall out, and both are thesis material:

**(a) The LLM baseline hallucinated the confirmation.** Its stated reason asserts that the
SOFI 2023 report *confirmed* the increase — which is precisely the false attribution under
test. This is a clean, in-corpus example of the failure mode the thesis is built around: an
LLM asked to check a misattribution reproduces the misattribution with confidence. It is
worth quoting directly in the RQ2 discussion.

**(b) Only the structured verifier declined to be wrong.** Four systems saw this claim; three
asserted TRUE on a gold-FALSE claim; **L1b abstained** — and it abstained for a *stated
structural reason* (`'FAO'` is an organisation, not a cited work, so `MIN_WORK_CONTENT = 2`
gates it out). That is the architecture working as designed: it declined a claim it could not
reach rather than guessing. Note the honest framing — **this is abstention, not detection.**
L1b gets no credit for a TP here; it gets credit for having **zero confident errors**, which
is the property the RQ2 defence actually rests on.

### A second finding, independent of the flip: `SYN_CITA_083` is an invalid negative

This came out of chasing the knock-on the prior session recorded, and it is the more
consequential half.

`current/synthetic_negatives.csv` holds `SYN_CITA_083`, gold **FALSE**:

> *"The **WHO** reported in 2023 that global food insecurity increased during 2022."*
> `injection_type = source_swap` · `original_value = FAO` · `corrupted_value = WHO` ·
> `base_claim_id = Q22_C01` · `notes = attribution moved FAO -> WHO; assertion unchanged`

**The source swap does not create a falsity, because WHO genuinely co-published the report.**
SOFI is a joint publication of **FAO, IFAD, UNICEF, WFP and WHO** — and the supplied
document's own table header says exactly that (*"Specific Data Points (FAO / IFAD / UNICEF /
WFP / WHO 2023)"*). So swapping the attributed agency from one co-publisher to another leaves
the attribution **true**. The perturbation is void on its own terms.

That is grounds to drop the row **whatever happens to `Q22_C01`**, and it is a cleaner reason
than the one on record. The recorded reason — that a `source_swap` off an already-false base
gives a claim that is false on two independent grounds, so a detection could not be credited
to the perturbation (**R10**) — only applies *if* the flip happens. The co-publisher problem
applies now.

**No measured detection is invalidated, because both systems missed it:**

| system | verdict on `SYN_CITA_083` | |
|---|---|---|
| non-routed baseline | **TRUE**, confidence 0.733 (entail 0.5813, contradict 0.2863) | a miss — and its top evidence passage is about *the Brookings Institution and a 65% increase in the United States*, i.e. retrieval was entirely off-target |
| CITATION **L1b** | **UNVERIFIABLE** | gated: `work title 'WHO' has 0 content word(s) (<2)` — the same bare-organisation rule that gated `Q22_C01`'s `'FAO'` |

It **is** inside the strict tier (confirmed by importing the audit's own `tier('strict')`; the
one CITATION row dropped at strict is `SYN_CITA_001`, not this one). So the correction is to
**denominators only**, and both move slightly *in each system's favour* — which is a caution
worth stating rather than a benefit worth claiming.

### Blast radius — computed, not estimated

> **This subsection's file count is WRONG and is corrected in §5.** It said 17 CSVs (12 archive,
> 5 current); the verified figure is **18 mentioning `Q22_C01` — 9 `current/` + 9 `archive/`**,
> of which **8 current files carry the label** and **only 2 archive files hold a stale `TRUE`**.
> The predictions in table (a) all held; the *inventory* did not. Left in place unstruck because
> the error is the point: "computed, not estimated" was a claim about the numbers below it, and
> the count above them had not been computed at all.

`Q22_C01` appears in **17 CSVs** (12 archive, 5 current). Only the authoritative Phase 2 file
holds the gold label; the result CSVs each carry a **copy** of it, so a flip is a scripted
propagation, not 17 hand edits.

**(a) From the `Q22_C01` flip:**

| quoted number | now | after the flip | direction |
|---|---|---|---|
| natural set composition | 314 T / 13 F / 29 U | **313 T / 14 F / 29 U** | — |
| **Always-True accuracy** | **88.2%** | **87.9%** | the degenerate baseline gets *easier* to beat |
| class prior π | 0.0365 | 0.0393 | — |
| TPR/FPR ratio needed for 50% precision | 26.4:1 | **24.4:1** | — |
| **CITATION L1 accuracy** | **20/22 = 90.9%** | **19/22 = 86.4%** | **worse — L1 said TRUE on a gold FALSE** |
| baseline confident errors | as published | **+1** | **worse for the baseline** |
| CITATION FPR (per-type J table) | 2/25 = 8.0% | **2/24 = 8.3%** | denominator only; the baseline's TRUE here is not an FP but a new confident error |
| **L1b FPR** | **0/25** [0.0, 13.3] | **0/24** [0.0, 13.8] | CI widens; **0 confident errors preserved** |
| gold-FALSE natural CITATION claims | 3 | 4 | — |

**(b) From dropping `SYN_CITA_083`** — required by the co-publisher finding regardless of (a):

| quoted number | now | after the drop | direction |
|---|---|---|---|
| strict tier size | **69** | **68** | CITATION 24 → 23 |
| baseline CITATION TPR | 5/24 = 20.8% | **5/23 = 21.7%** | improves — it was a miss |
| baseline **ALL** TPR | 37/69 = 53.6% | **37/68 = 54.4%** | improves |
| baseline CITATION **J** | +0.128 | **+0.134** | (TPR 21.7% − FPR 8.3%, with (a) applied) |
| **L1b CITATION TPR** | 9/25 = 36.0% | **9/24 = 37.5%** | improves — it was an abstention |
| **L1b J** | **+0.360** | **+0.375** | |

**The L1b-vs-baseline comparison is essentially unmoved** (+0.375 vs +0.134, against +0.360 vs
+0.128), and the caveat that already governs it still binds: **n = 24 cannot separate 37.5%
from 21.7%** — the TPR CIs overlap heavily, so the prior-independent part of that result
remains **FPR 0/24 vs 2/24** and the **0 confident errors**, not the TPR gap.

**Per-type strict-tier counts were re-derived and CLAUDE.md §5 is confirmed correct** —
CITATION 24, TEMPORAL 26, QUANTITATIVE 14, EA 5 = 69, reproduced by running
`current/negatives_cache_audit.py`. An independent reconstruction of mine gave CITATION 23 /
QUANTITATIVE 14→15 and briefly looked like a discrepancy; it was measuring a different
quantity (collisions against *all* natural claims rather than against each row's *own base
claim*, which is the audit's definition). **R1 resolved in CLAUDE.md's favour this time** — the
script that owns the definition was run rather than either summary being trusted.

**The "max TP on the natural set is 0 by construction" claim SURVIVES.** A misattribution is
unreachable by `P577` (publication date) and `P123` (publisher) just as the other three
content falsities are. It is **Level 2** work — *does the source actually say this* — which is
unbuilt. So the argument holds over 4 claims instead of 3, and is slightly strengthened by
having a fourth independent instance.

### Recommendation, and why it is not self-serving

**Two separable actions.**

1. **Drop `SYN_CITA_083` from the negatives.** The co-publisher finding voids it on its own
   terms, independent of the gold label. Neither system detected it, so nothing measured is
   invalidated — the strict tier goes 69 → 68 and CITATION 24 → 23.
2. **Flip `Q22_C01` TRUE → FALSE — but the author authorises the flip, not me.** The evidence
   condition in `CLAUDE.md` §4 is now satisfied; the *authorship* condition is not. "The author
   ran the lookup and pasted the result" is not the same as "the author says change the gold
   label," and this moves several published numbers.

What makes the case strong is the **direction**: flipping makes **Always-True easier to beat,
CITATION L1 less accurate, and the baseline worse by one confident error**, while the routed
system gains **no detection** — L1b abstained. A relabel that costs the thesis on three numbers
and gains it none is not a relabel fitted to a desired result. That asymmetry is the reason to
trust it, and it belongs in the thesis wherever the correction is mentioned.

The one place to be careful: dropping `SYN_CITA_083` nudges **both** systems' negative-set TPRs
up by under 2pp, because both missed it. That is a denominator effect on n = 24, far inside the
CI, and should not be presented as an improvement to either system.

**A correction to the flag already on record.** `current/phase2_labels_for_review.csv` carried
`FLAG = PROPOSED FLIP TRUE -> FALSE` with evidence text asserting the 2019→2022 rise was
**+122M**. The report says **+391 million** (p. 10, quoted above); +122M does not appear in the
supplied figures and appears to have been a model-knowledge artifact from the session that wrote
the flag — which is exactly why that text also said *"NOT VERIFIED IN SESSION."* The
`FLAG_EVIDENCE` cell is updated to the verbatim `cc3017en` p. 10 quote. **The gold label itself
is untouched, and no `AUTHOR_*` cell is written** (both remain empty, as `CLAUDE.md` §4
requires).

`Q22_C03` stays **premise-dependent, not false**, exactly as flagged: *"The FAO report
attributed the rise in food insecurity to the combined effects of conflict, economic shocks,
and climate extremes."* SOFI 2023 does make that attribution, and there **is** a rise on the
2019→2022 horizon (+391M), so the claim survives under the report's own framing. It should be
decided after `Q22_C01`, not with it.

---

## 2. ConfQA and R-Tuning — usable, with one framing correction and one check to run

### Citations as supplied

**R-Tuning** — Zhang, Diao, Lin, Fung, Lian, Wang, Zhang. *R-Tuning: Instructing Large
Language Models to Say 'I Don't Know'.* **NAACL 2024**, pp. 7831–7848. Noted as an
**Outstanding Paper**.

**ConfQA / ConfRAG** — Huang, Xu, Sun, Yan, Sun, Khan, Nguyen, Chen, Kachuee, Lin, Liu,
Colak, Kumar, Yih, Dong. *ConfRAG: Confidence-Guided Retrieval-Augmenting Generation.*
arXiv **2506.07309**, 2025. ConfQA (*"Answer only if you are confident"*) is the method
inside that framework.

**Check before either enters the bibliography:** the **page range and the arXiv ID** against
the ACL Anthology / arXiv listing. Author lists and venues are the kind of detail these
summaries get right; four-digit page numbers and arXiv identifiers are the kind they get
subtly wrong, and a wrong identifier in a bibliography is a visible error. One lookup each.

### What they actually argue

**R-Tuning:** standard SFT penalises refusal, so it *cultivates* overconfident hallucination
when a query exceeds parametric memory. R-Tuning probes the base model to partition training
questions into *certain* / *uncertain*, pairs the uncertain ones with refusal completions,
and finds refusal is a **learnable, generalising meta-skill** — better risk-coverage curves
out of distribution than logit thresholding, temperature scaling, or verbalised probability,
without degrading known-question performance.

**ConfQA:** softmax probabilities *and* post-hoc self-reported confidence are both badly
calibrated and overconfident on out-of-knowledge queries. Fine-tuning on KG assertions with a
dampening instruction (*"answer only if you are confident, otherwise output 'I am unsure'"*)
produces a near-linear confidence mapping, cutting hallucination from 20–40% to <5%, and the
calibrated "unsure" then serves as a **gate that triggers retrieval only when internal
certainty is insufficient**.

### The framing correction — state this precisely or a reviewer will catch it

Both papers are about **training the generator to abstain**. HalDetect's UNVERIFIABLE class
is **post-hoc verifier abstention** — a different mechanism, at a different pipeline stage,
with no fine-tuning involved. They ground the **principle**, not the mechanism:

> calibrated abstention beats forced answering, and a system that abstains must be evaluated
> on a risk-coverage curve rather than a single accuracy number.

Claiming more than that is an overreach. Claiming that much is well supported and is exactly
what the thesis needs.

### Two genuine payoffs

1. **`MIN_MARGIN = 0.15` stops being a tuned constant** and becomes an instance of a
   literature-grounded design choice — the decision to abstain below a confidence margin,
   with UNVERIFIABLE as the abstention token. Pure writing, no code, no number changes.
2. **R-Tuning independently justifies the 3d-vs-3e reporting decision.** `CLAUDE.md` §4
   already rules that both variants must be reported side by side as one coverage-accuracy
   tradeoff table. R-Tuning's central evaluation result is that **risk-coverage curves are
   the right frame for abstaining systems, and that they separate methods that single-point
   accuracy cannot.** That is the same argument, from the literature, for a decision this
   project reached on its own — which is the strongest form a justification can take. Cite it
   in the table caption.

ConfQA's *"unsure as a gate that triggers retrieval"* is also a precise description of the
**TEMPORAL/EA hybrid fall-through** (task #3): abstain on the structured path, then fall
through to retrieval. Worth one sentence there.

---

## 3. Entity linking — RETRACTION: my objection was wrong about ReFinED specifically

### What I claimed, and what is wrong with it

`external_catalog_assessment_2026-08-26.md` §2 argued that the external catalog's Tier-1 pick
— *replace `resolve_entity` with a trained entity linker (ReFinED/GENRE)* — probably cannot
reach the serial-edition failure mode, because all three Lancet candidates have **0 sitelinks**
and *"standard entity linkers (ReFinED, GENRE, BLINK) restrict their candidate sets to
Wikipedia-derived inventories."*

**That premise is right for two of the three and wrong for the one the catalog named first.**

| system | candidate generation | inventory | Wikipedia-bound? |
|---|---|---|---|
| **BLINK** (Wu et al. 2020) | dense bi-encoder, FAISS over 1024-d embeddings of candidate *descriptions* | English Wikipedia, ~5.9M pages | **Yes, practically** — needs rich text per candidate; extending to ~100M+ QIDs means authoring and indexing descriptions for millions of description-less entities |
| **GENRE / mGENRE** (De Cao et al. 2021) | autoregressive BART with constrained beam search over an offline **prefix trie** | Wikipedia page **titles** | **Yes, structurally** — the trie *is* the output space; it cannot emit a QID or a non-Wikipedia entity unless rebuilt over another catalog |
| **ReFinED** (Ayoola et al. 2022) | single-pass transformer over a prebuilt **entity alias table**, scored by fine-grained typing (**`P31`/`P279`**) + description embeddings | **Wikidata & Wikipedia, ~33M entities** | **No** — built for zero-shot generalisation over Wikidata; candidates resolve natively to **QIDs**, using Wikidata's ontology rather than page titles |

**So my §2 objection is retracted for ReFinED and stands for BLINK and GENRE.** The
"defined by the absence of exactly the signal those models depend on" argument was a good
argument applied to the wrong member of the list.

### But the falsification test survives, sharpened — and it is now decisive

The objection was about the **output namespace**; the live question is about the **alias
table's coverage**, and those are not the same thing. Three reasons the serial-edition class
may still be out of reach:

1. **~33M ≪ ~100M+.** ReFinED's inventory is roughly a third of Wikidata. Which third is an
   empirical question, and *obscure, sitelink-less editions of serial publications* are a
   plausible member of the excluded two-thirds.
2. **The alias table's provenance is Wikipedia hyperlinks.** The supplied summary says
   Wikipedia is used as the *hyperlinked training corpus*. If surface forms are harvested from
   Wikipedia anchor text, then a 0-sitelink entity contributes **no aliases**, and it is
   unreachable by candidate generation even though the output namespace could name it. This
   is the same structural point as my original objection, relocated one layer down — and it is
   the version that needs testing.
3. **Dump recency, which is probably decisive.** The three Lancet candidates are
   **Q92676744, Q98186330, Q139937996**. Wikidata QIDs are allocated roughly in creation
   order, and Q100000000 was reached around 2020–21 — so **Q139937996 almost certainly
   postdates ReFinED (2022) entirely** and cannot be in any alias table it shipped with. That
   item is the one `series_resolver` guard 1 exists for: it *is* the real 2024 Lancet report,
   and its `P577` is simply absent. Stated as an inference from QID magnitude, not a verified
   fact — but it is cheap to check and it decides the question.

**The test to run, if ReFinED is ever considered:** feed `Lancet Commission on dementia
prevention` and check whether **Q92676744 / Q98186330 / Q139937996** appear in the candidate
set *at all*. If they do not, §2's conclusion holds by a different mechanism and the swap is
orthogonal to the live bug. **`series_resolver.py` already fixes this class** (`--selftest`
ALL PASS, measured ceiling 8/12 on `year_shift`), so this is a question about whether to add
a dependency, not about whether the failure mode is handled.

### The part that genuinely strengthens the project — task #21

**ReFinED scores candidates by fine-grained typing over `P31`/`P279`.** That is the mechanism
task #21 proposes to build (`P31` instance-of type-check, as a sibling of
`source_consistency.py`). So #21 is not merely *"the best item in either external document"* —
it is **the candidate-scoring signal a SOTA entity linker relies on**, which converts #21 from
a sensible local heuristic into a design decision with a citable precedent.

This matters specifically because of the recorded circularity: the resolver's 72/72 "correct"
was verified by **label matching, the same signal used for selection**, so it could not fail,
and is downgraded to *"0% refusal, correctness unverified by an independent signal."*
`source_consistency.py` supplied the first independent signal for **provenance**
(`P1433`/`P123`, selftest 12/12, and it immediately rejected Q92676744 — whose publisher is
the *Irish Journal of Psychological Medicine*, not *The Lancet*). `P31` supplies it for
**type**, and reaches the Rosetta-Stone-as-a-punk-band class head-on.

Inherit `source_consistency.py`'s four load-bearing decisions unchanged: only strong
properties may veto; **any** match wins; `NO_EVIDENCE` must **never** reject; and both error
directions stay safe because the check only ever *removes* a verdict, so neither direction can
manufacture a confident-wrong one.

---

## 4. What changed in the project's records because of this document

| file | change |
|---|---|
| `current/phase2_labels_for_review.csv` | `FLAG_EVIDENCE` for `Q22_C01` rewritten: the unverified **+122M** replaced with the verbatim `cc3017en` p. 10 quote and **+391M**, plus the `SYN_CITA_083` co-publisher finding. **Gold label untouched; both `AUTHOR_*` cells still empty.** |
| `external_catalog_assessment_2026-08-26.md` §2 | retraction recorded — the Wikipedia-bound premise holds for BLINK and GENRE, **not** ReFinED |
| `CLAUDE.md` §4 (`Q22_C01` row) | evidence status changed from *UNVERIFIED IN SESSION* to *confirmed against `cc3017en` p. 10*; ruling still **FLAGGED, NOT FLIPPED**, now awaiting only the author's word |
| `CLAUDE.md` §5 | `SYN_CITA_083` recorded as an invalid negative (WHO co-published SOFI 2023), with the 69 → 68 consequence |
| `CLAUDE.md` §7 | task #21 notes that `P31`/`P279` typing is ReFinED's own candidate-scoring signal; a new task added for the `SYN_CITA_083` drop |

**Nothing was flipped, no gold label changed, no result CSV rewritten, no cache touched, no
model called.** One script was executed — `current/negatives_cache_audit.py`, which is offline,
~1 s, and reads the existing cache; it confirmed CLAUDE.md §5's strict-tier decomposition
rather than changing it.

> **Superseded later the same day by §5** — the author then authorised the flip, so gold labels
> in 8 `current/` files *were* changed and the result CSVs *were* rewritten. Still true of
> everything else: no cache touched, no model called, no archive file edited.

### Open items this hands to the author

1. ~~**One word on the `Q22_C01` flip.**~~ **DONE — authorised and applied 2026-08-26; see §5.**
2. **Verify two bibliography entries** — R-Tuning's page range `7831–7848` and ConfRAG's arXiv
   `2506.07309`, against the ACL Anthology and arXiv listings. One lookup each.
3. **`SYN_CITA_083`** — my recommendation is still to drop it, but **the reason has changed now
   that the flip is applied**: the row inherits gold FALSE from its flipped base, so its label is
   *accidentally correct* while the `source_swap` perturbation still injects no falsity. It
   therefore cannot measure `source_swap` detection, which is what a negative is for (**R10**).
   Do not let "the label is correct now" argue for keeping it.
4. Optional, cheap, decides a question I could only reason about: check whether ReFinED's
   candidate set contains **Q139937996** at all. If not, §3's conclusion holds by dump recency
   and the entity-linker swap is orthogonal to the live bug.

---

## 5. OUTCOME — the flip was authorised, applied and measured (2026-08-26, later the same day)

The author read §1 and replied **"ok flip it."** This section records what the flip actually did,
scores §1's predictions against it, and corrects the one thing §1 got wrong. Everything below is
**measured, not projected** — zero model calls, zero API calls.

### How it was applied

The label is `FALSE` in **all 8 `current/` files that carry it**. Seven are result/gold CSVs that
each changed by **exactly one field in exactly one row** — `gold_verdict` TRUE → FALSE on
`Q22_C01`, with row counts preserved and every other field in every other row byte-identical:

| file | rows | changed |
|---|---|---|
| `current/haldetect_phase2_goldlabeled (3).csv` | 126 | the authoritative label |
| `current/nonrouted_baseline_results.csv` | 356 | copy |
| `current/haldetect_claims_unified.csv` | 400 | copy |
| `current/citation_l1_results.csv` | 29 | copy |
| `current/citation_l1b_results.csv` | 54 | copy |
| `current/llm_baseline_results_closed.csv` | 355 | copy |
| `current/llm_baseline_results_closed_binary.csv` | 356 | copy |

The eighth is `current/phase2_labels_for_review.csv`, where the decision itself is recorded in
**additive** columns: `current_label=FALSE`, `AUTHOR_VERDICT=FALSE`, `AUTHOR_NOTE` carrying the
`cc3017en` p. 10 quote, `FLAG='FLIP APPLIED 2026-08-26 (author-authorised)'`. `Q22_C03` was
resolved on the same pass and **RETAINED as TRUE** (see below).

Two supporting files were edited for consistency: `current/consolidate_claims.py`'s Phase 2
`expect` block (now `TRUE 86 / FALSE 2 / UNVERIFIABLE 21`, with a comment naming the *only*
authoritative site for the label, so a silent revert fails `--verify` rather than propagating) and
`current/metrics.py`'s `__main__` fixture (now `313/14/29`, kept hardcoded on purpose — it is a
unit test of the metric functions, not a read of the corpus).

Edits used **span-precise byte replacement**, not `csv.writer`: every one of these files fails a
no-op `csv.writer` round-trip, so rewriting through the csv module would have buried a one-field
change in a whole-file reformat.

### The count §1 got wrong — R1 applied to my own document

§1 said *"`Q22_C01` appears in 17 CSVs (12 archive, 5 current)"* under a heading that read
**"computed, not estimated."** Verified against the files:

| | §1 claimed | verified |
|---|---|---|
| total CSVs mentioning `Q22_C01` | 17 | **18** |
| `current/` | 5 | **9** (8 carrying the label, +1 pointer-only) |
| `archive/` | 12 | **9** |
| archive files holding a stale `TRUE` | implied 12 | **2** |

The two stale-`TRUE` archive files are `archive/csvs/haldetect_phase2_goldlabeled (2).csv` and
`archive/csvs/temporal_verified_results_v2.csv`. The other seven archive files mention the claim
id but have an **empty** `gold_verdict`, so "12 archive copies" overstated the contamination by
about 6×. The ninth `current/` file is `current/synthetic_negatives.csv`, which carries
`Q22_C01` only as `SYN_CITA_083`'s `base_claim_id` — a **pointer, not a label** — and was
correctly left untouched.

Archive is still deliberately left alone: those files are historical records, and rewriting them
would destroy the audit trail the flip needs.

### The gate — why these numbers are quotable

Before any post-flip figure was written down, the same script recomputed **every affected figure
against the PRE-flip gold** and asserted it reproduced the value `CLAUDE.md` already recorded,
aborting otherwise. All four documented rows matched to under 0.15pp:

| pre-flip row | documented (cov / acc / F1(FALSE) / MCC) | recomputed | |
|---|---|---|---|
| 3d-style | 77.2 / 69.8 / 0.170 / +0.180 | identical | MATCH |
| 3e-style | 53.7 / 81.2 / 0.174 / +0.144 | identical | MATCH |
| retuned (0.35/0.30) | 90.2 / 84.7 / 0.292 / +0.288 | identical | MATCH |
| Always-True | 88.2% | identical | MATCH |

A re-derivation that cannot reproduce the number it replaces is not evidence. The script also
imports the project's **own** `threshold_sweep.load/verdicts` and `metrics.mcc/wilson/aurac`
rather than reimplementing the decision rule — the same one-code-path principle that makes the
RQ2 ablation defensible.

An incidental confirmation fell out of the gate: **3d-style is arithmetically identical to the
shipped (0.50/0.40) point**, which is what `CLAUDE.md` §4 asserts when it calls the shipped point
"strictly dominated on the natural 356." That row is now verified rather than asserted.

### §1's predictions, scored

**All nine held exactly.** Predicted → measured:

| quantity | §1 predicted | measured | held? |
|---|---|---|---|
| natural set composition | 313 T / 14 F / 29 U | 313 / 14 / 29 | yes |
| Always-True accuracy | 87.9% | **87.9%** [84.1, 90.9] | yes |
| class prior π | 0.0393 | **0.0393** | yes |
| ratio needed for 50% precision | 24.4:1 | **24.4:1** | yes |
| CITATION L1 accuracy | 19/22 = 86.4% | **19/22 = 86.4%** [66.7, 95.3] | yes |
| baseline confident errors | +1 | **+1** | yes |
| CITATION FPR | 2/24 = 8.3% | **2/24 = 8.3%** | yes |
| L1b FPR | 0/24 [0.0, 13.8] | **0/24** [0.0, 13.8] | yes |
| gold-FALSE natural CITATION | 4 | **4** | yes |

**But the estimate was incomplete — seven further quantities moved that §1 never enumerated.** It
predicted "baseline confident errors +1" without following that through to the metrics computed
from it:

| quantity not in §1's table | pre-flip | post-flip |
|---|---|---|
| 3d selective accuracy / F1(FALSE) / MCC | 69.8% / 0.170 / +0.180 | **69.5%** [63.8, 74.6] / **0.168** / **+0.166** |
| 3e selective accuracy / F1(FALSE) / MCC | 81.2% / 0.174 / +0.144 | **80.6%** [74.4, 85.6] / **0.170** / **+0.135** |
| retuned selective accuracy / F1(FALSE) / MCC | 84.7% / 0.292 / +0.288 | **84.4%** [80.1, 88.0] / **0.286** / **+0.273** |
| CITATION L1 **AURAC** | 0.934 | **0.898** |
| per-type CITATION 3d → 3e (cov/acc) | 44.8/76.9 → 31.0/88.9 | **44.8/69.2 → 31.0/77.8** |
| **ALL** J (per-type discrimination table) | +0.323 (FPR 67/314) | **+0.322** (FPR 67/313) |
| `metrics.py` self-check fixture: Always-True **AURAC** + its CI | 0.993, 88.2% [84.4, 91.2] | **0.992**, 87.9% [84.1, 90.9] |

**Lesson for the next blast-radius estimate: enumerate the numbers *derived from* the ones you
list, not just the files the label appears in.** A confident-error count is an input to four
published metrics; listing the input and not the outputs made a 9-row table look complete when it
was covering just over half the moving parts.

The seventh row is the one worth pausing on, because it is a different *kind* of miss. The other
six are scores a system earned. That one is the **bar** — the degenerate-baseline figure every
accuracy claim in the thesis is measured against, hardcoded as a fixture in `current/metrics.py`
and quoted as a measured execution record in `current/README.md`. A gold edit moves the yardstick
as well as the measurements, and the yardstick is the easier one to forget because it lives in a
self-test rather than in a results table. Re-ran `python3 current/metrics.py` after the flip and
recorded the new output in both places rather than leaving a 2026-08-22 execution record standing
over a 2026-08-26 fixture.

### Everything the flip did NOT move — verified, not assumed

- **Coverage, at every operating point** (77.2% / 53.7% / 90.2%). Coverage does not depend on
  gold, so no label change can move it. This is the cleanest internal check that the propagation
  touched only gold columns.
- **All TPRs on negatives** — baseline 37/69, L1b 9/25. `Q22_C01` is a natural claim, so it is in
  no negatives population. Only the FPR *denominators* moved.
- **The observed FALSE precision, 8/81 = 0.0988.** The claim was read TRUE by the baseline, so it
  is a false negative at every operating point: FN +1, TP +0, FP +0.
- **The balanced-prior precision, 0.715.**
- **L1b's 0 confident errors and 0-FPR** — it abstained on `Q22_C01` (gated: work title `'FAO'`
  has 0 content words, `< MIN_WORK_CONTENT = 2`), so it earns no detection either. The
  load-bearing routing-win claim survives intact.
- **The entire threshold-sweep precision surface.** `Q22_C01`'s contradiction score is **0.1798**,
  below the grid's minimum `ct` of 0.30, so it is never predicted FALSE anywhere on the grid. A
  gold negative below the sweep's floor is invisible to the whole surface.
- **`current/synthetic_negatives.csv`** — untouched, and no negatives-population number changed.

### One argument the flip made *stronger*

The base-rate explanation for the baseline's low FALSE precision got **tighter**, not weaker. At
π = 0.0393 the measured TPR/FPR predicts precision **0.0930** against an observed **0.0988** — a
gap of **0.0058**, down from **0.0118** pre-flip. The extra gold negative is one the baseline
missed, which is exactly what a base-rate account of the low precision predicts. So the
correction that costs the thesis on seven numbers repays it on the one argument doing the most
defensive work.

### One new finding from the corrected data

**Two of CITATION L1's three confident errors are now gold-FALSE bare-`'FAO'` claims** —
`Q22_C01` and `B3_12_C07`. That states the existence-vs-content gap as *measured data* rather
than as design intent: L1 checks whether a source resolves, both of these resolve, and both
misreport what the source says.

### The load-bearing argument was tested, not assumed

**"Max TP on the natural set is 0 by construction" SURVIVES.** Re-derived by enumerating all four
gold-FALSE natural CITATION claims and the gate each hit:

| claim | L1b verdict | gate |
|---|---|---|
| `Q12_C11` | UNVERIFIABLE | `DATE` |
| `B3_05_C02` | UNVERIFIABLE | `DATE` |
| `Q22_C01` | UNVERIFIABLE | `NONE` — bare `'FAO'`, 0 content words |
| `B3_12_C07` | UNVERIFIABLE | `NONE` — bare `'FAO'`, 0 content words |

The count went 3 → 4, L1b abstained on the new one, and true positives on the natural set stayed
**0**. The argument now rests on four independent instances instead of three. All four are
*content* falsities — what the source says — which `P577` (publication date) and `P123`
(publisher) cannot reach by construction. That is **Level 2** territory, and it is unbuilt.

### `Q22_C03` — resolved, and retained as TRUE

§1 flagged `Q22_C03` (*"The FAO report attributed the rise in food insecurity to the combined
effects of conflict, economic shocks, and climate extremes"*) as premise-dependent on `Q22_C01`,
to be decided after it. It was decided **on the second reading §1 anticipated** and **retained as
TRUE**: SOFI 2023 does make that triad attribution, and *"the rise"* has a referent — the +391M
vs 2019 that p. 10 states in the same sentence as the 2022 no-change finding — that never
depended on the 2022 trend. Recorded explicitly in `FLAG_EVIDENCE` rather than left implicit,
because a stale "PREMISE-DEPENDENT" flag on a resolved premise is exactly the kind of dangling
note that later gets read as an open question.

**A resolved premise dependency is not a second flip.** `Q22_C01` moving did not license moving
anything downstream of it; `Q22_C03` was re-examined on its own evidence and held.

### Net

Seven published numbers got worse, one argument got tighter, one new finding appeared, and the
corpus gained its **14th gold negative** against a constraint — negative scarcity — that binds
every detection claim in the thesis. `AUTHOR_*` cells written: **2**, both on author
authorisation, both recorded with their evidence. Archive copies edited: **0**. Caches touched:
**0**. Model calls: **0**.
