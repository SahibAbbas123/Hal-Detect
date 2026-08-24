# HalDetect — Session Handoff (today, 2026-08-22)

> Chat name: Comparing systems against FActScore's dataset
> Source chat span: created 2026-05-23, last updated 2026-07-12, exported 2026-08-22

_Read this first. Everything below assumes no prior context._

---

## What This Project Is

HalDetect: a taxonomy-routed claim-verification pipeline for detecting hallucinations in LLM-generated text (BSc thesis, CSE 700, University of Chittagong). An LLM response is atomized into claims; each claim is classified into one of five types and routed to a type-specific verifier that queries a public knowledge source in real time and returns TRUE / FALSE / UNVERIFIABLE.

**Five types, in priority order:** CITATION > TEMPORAL > QUANTITATIVE > ENTITY_ATTRIBUTE > RELATIONAL.

**Core contribution:** taxonomy-guided routing instead of one uniform verifier for every claim. Nothing is trained — LLM/structured extraction + public APIs + similarity/NLI.

**This chat is the middle build phase**, later than the "Taxonomy-based hallucination detection" chat (which finished Task 1, the taxonomy rules, and only *sketched* a TEMPORAL verifier). This chat does three big things: (1) settles the **evaluation design** against FActScore, (2) **pivots the whole extraction pipeline to LLM-based** (Gemma 4 31B via local Ollama, replacing the earlier spaCy/rule plan), and (3) **builds and runs the first two real verifiers** (TEMPORAL end-to-end + evaluated; CITATION built + spot-tested). It is a distinct code track from the later Colab/Gemini notebook — see "Files NOT to Trust."

---

## A. What Happened This Session, In Order

1. **The FActScore comparison problem, stated and resolved.** Student opened worried that comparing HalDetect against FActScore is invalid: FActScore stores **Wikipedia snapshots from annotation time** (snapshot-relative S/NS gold labels) while HalDetect hits **live** Wikidata/Wikipedia/APIs — same prompt can yield different verdicts, and models differ (GPT-3/3.5 vs Gemma 4 31B). Resolution: **do not compare verdict-for-verdict against FActScore.** Staleness is a real but documentable threat-to-validity affecting all live-data systems, not unique to HalDetect.
2. **Chose the ablation instead: routed vs non-routed.** The evaluation is HalDetect's taxonomy-routed verifiers **vs a non-routed baseline**, on the **same claim set + same gold labels + same evidence sources** — the only variable is routing. **Non-routed baseline spec:** every claim → top-k Wikipedia passage retrieval → `facebook/bart-large-mnli` NLI → threshold → TRUE/FALSE/UNVERIFIABLE. This is essentially what FActScore does, so it is the natural (non-strawman) baseline.
3. **Killed the "1000 prompts per category" worry.** No need to build a 1000-prompt-per-type dataset. HalDetect is a *verification* system, not a prompt dataset. Evaluation data = the existing claim corpus + FActScore's **labeled subset (183 examples per model)**. The 30-item pilot is the dev/tuning set. Domain stratification is deliberate.
4. **Positioned low-parameter models as claim *sources*, not verifiers.** Run the same prompts through 1B/3B/web-enabled/RAG models, extract claims, run HalDetect, report hallucination rate per configuration. Framing: "HalDetect is a measurement instrument you point at different LLM configs." The models' older knowledge cutoffs do **not** make this unfair, because verifiers use live sources regardless of the generating model's cutoff.
5. **Pivoted the pipeline to LLM-based.** Decided to use the LLM (Gemma 4 31B) for atomization AND structured JSON extraction AND classification, keeping only verification on structured APIs. spaCy dependency parsing rejected as unreliable on complex sentences.
6. **Classification: rules → LLM (with a walk-back).** Assistant first argued rule-based classification for auditability, then **corrected itself** — the real and only argument for rules is *reproducibility/consistency*, not auditability or speed. Final decision: **LLM few-shot classification at temperature=0 + fixed seed** (deterministic), using the 140-corpus examples as few-shot demonstrations; the taxonomy rules doc becomes the *prompt spec*. Rule-based `classify()` kept only as a documented fallback.
7. **Softened an over-claim.** "NLI handles numbers poorly" was walked back as lacking a citation → reworded to "NLI models may struggle with precise numerical comparisons, whereas explicit numeric matching provides deterministic verification."
8. **Ollama setup nailed down.** `gemma4:31b` at `http://localhost:11434/api/generate`, `temperature=0, seed=42, num_ctx=8192`, `format:"json"` on extraction calls only. **Local (VS Code)**, NOT Colab (localhost unreachable from Colab), Open WebUI only for interactive prompt testing. Built `llm_client.py`, then the full `haldetect_pipeline.py`.
9. **Redefined CITATION + dropped trivial existence claims.** CITATION verifies whether a named source *made a specific claim*, not that it exists. Drop/rewrite "WHO exists" (Gr1) and "UN HDR exists" (G14). Dual-emit now emits "The WHO reported that air pollution causes 7M deaths annually" (source+assertion), not a bare existence claim.
10. **Added a drift/semantic-containment check.** Cosine similarity (Sentence-BERT `all-MiniLM-L6-v2`) between each claim and its source paragraph, to catch claims the LLM *invented during decomposition*. Threshold discussed at ~0.65, **lowered to 0.50**, and reframed as hallucination-during-decomposition detection (flag, don't discard). Dedup threshold = 0.90.
11. **Ran the pipeline; revised the question set to fix type balance.** An earlier run left CITATION very thin (~3.8%). Swapping in source-directed questions **Q11–Q14** (WHO / Lancet / CDC / World Bank) and dropping **Q3/Q4/Q6/Q8** raised CITATION to **11 (8.8%)** and QUANTITATIVE to **~12.8%** — but left **ENTITY_ATTRIBUTE at only 6.4% (8 claims)**, the under-represented type (the dropped questions had been its main source). Final pilot draws on questions Q1, Q2, Q5, Q7, Q9, Q10, Q11–Q14 → **130 raw claims, 5 removed by dedup (τ=0.90) → 125 claims** for manual gold-labeling; drift-flagged rate 8.5% (11/130).
12. **Gold-labeling pass (partial).** Assistant supplied quick-lookup Google prompts + provisional gold verdicts across Q1 (Einstein — all TRUE), Q2 (2008 crisis), Q5 (IPCC — all TRUE), Q7 (Silk Road), Q9 (quantum), Q10 (WWI), Q11 (air pollution), Q12 (dementia/Lancet), Q13 (CDC vaccines), Q14 (global poverty). `gold_verdict` = human judgment/quick lookup, **NOT** verifier output.
13. **Answered CSV-structure questions.** `subject/property/value/secondary` are the structured decomposition fed to verifiers. Problem flagged: LLM `property` names are freeform snake_case, not Wikidata-aligned → use a `PROPERTY_TO_WIKIDATA` lookup; unmapped → UNVERIFIABLE. `wikidata_qid` gets added **automatically during verification**, not by hand.
14. **Ran `verifier_setup.py` — all 5 checks passed:** Wikidata SPARQL, Wikidata opensearch (entity resolution), CrossRef (no key; `mailto` param), `facebook/bart-large-mnli` (~1.6 GB, cached), JSON cache.
15. **Built + ran the TEMPORAL verifier.** 5 steps: guard → entity resolution (opensearch → QID) → SPARQL → year-granularity value comparison (±1 tol) → verdict. First run: 27 TEMPORAL claims, **5 verifiable, 4 correct → 80% acc, 18.5% coverage.** Diagnostic showed **17/27 properties UNMAPPED.** After adding 4 mappable PIDs (P570, P571, P800, P585): **8 verifiable, 6 correct → 75% acc, 29.6% coverage.** Student hit the ceiling and moved on.
16. **Built the CITATION verifier (not yet evaluated on gold).** Two levels: L1 source existence (trivially-known orgs → immediate TRUE @0.85; else CrossRef → Semantic Scholar → direct org-URL fetch), L2 attribution (page text chunked to 400 chars, BART NLI per chunk, best score: ≥0.50 entail → TRUE, ≥0.40 contradict → FALSE, else UNVERIFIABLE). Confidences reported per level. Spot-tested on samples; **not run on the full gold set yet.**
17. **Planned Phase 2 dataset expansion.** Student wanted ~500 claims; assistant pushed back to a realistic **250–300** (annotation burden ~triples). 12 new questions **Q15–Q26** (IDs start at 15 to avoid collision) targeting ENTITY_ATTRIBUTE (biggest gap), plus CITATION/QUANTITATIVE and harder TEMPORAL. Reuse pipeline unchanged; save to a **separate** `haldetect_claims_phase2_[timestamp].csv`; merge later with pandas.
18. **Produced three chat summaries** at student's request (design-doc version, then a non-judgmental version, then a "third-person progress report" version). The progress-report version is the most useful successor artifact and is reproduced in condensed form throughout this handoff.

---

## B. Current File / Artifact State

| Artifact | Stage | Status | Notes |
| --- | --- | --- | --- |
| `llm_client.py` | Pipeline core | **Working** | Ollama wrapper. `gemma4:31b`, temp=0, seed=42, num_ctx=8192; `format:"json"` when `expect_json=True`. |
| `haldetect_pipeline.py` | Extraction pipeline | **Working, run** | generate → atomize → dedup(0.90) → drift(flag<0.50) → LLM classify → JSON extract → CSV. Run on 10 Qs → 125 claims. |
| `haldetect_claims_20260524_045439.csv` (also a `_1` variant) | Pilot dataset | **Partially gold-labeled** | 125 claims. Columns incl. `type`, `drift`, `subject/property/value/secondary`, blank `gold_type`/`gold_verdict`/`notes`. Annotation NOT finished. |
| `verifier_setup.py` | Infra check | **Passed (5/5)** | Wikidata SPARQL, opensearch, CrossRef, BART-MNLI, cache. |
| `temporal_verifier.py` | Verifier #1 | **Built, run, evaluated** | 27 TEMPORAL claims → 8 verifiable, 6 correct → **75% acc / 29.6% coverage.** |
| `citation_verifier.py` | Verifier #2 | **Built, spot-tested only** | Two-level (existence + NLI attribution). NOT yet evaluated on full gold set. |
| `verifier_cache.json` | Cache | **Has 3 stale keys** | Delete before re-running: `sparql__Q937__P577` (1900 placeholder), `sparql__Q121734997__P580` (net-zero wrong entity), `sparql__Q9366__P585` (Google has no point-in-time). |
| Phase 2 questions Q15–Q26 | Dataset expansion | **Designed, NOT run** | 12 questions; pipeline unchanged; output to separate CSV. |
| QUANTITATIVE / ENTITY_ATTRIBUTE / RELATIONAL verifiers | Verifiers #3–5 | **Not started** | Build order below. |
| Non-routed baseline | Ablation | **Not started** | The core comparison; spec is fixed (Wikipedia retrieval + BART-MNLI on every claim). |

---

## C. Key Findings — Ranked by Evidence Strength

1. **The extraction pipeline is complete and has actually run** (10 Qs → 125 claims). Highest-confidence item. LLM-based atomization + JSON extraction + classification, all on Gemma 4 31B, deterministic (temp=0, seed=42).
2. **TEMPORAL verifier real numbers: 75% accuracy on verifiable claims, 29.6% coverage** (8 of 27). These are honest, defensible, and low-coverage *by design*: Wikidata has no structured property for macroeconomic trends, geopolitical processes, or abstract entities, so those correctly return UNVERIFIABLE.
3. **Coverage is throttled by two separate things:** (a) ~12 of the 27 "TEMPORAL" claims are **misclassifications** that should be RELATIONAL/QUANTITATIVE (the LLM treats any claim containing a year as TEMPORAL), and (b) unmappable properties (`peak_year`, `trend_direction`, `growth_rate`, `spread_to`, etc.) have no Wikidata PID. Fix (a) in the CSV; (b) is correct behavior.
4. **Direct FActScore verdict comparison is invalid and has been abandoned** — live vs snapshot evidence + different models. The evaluation is **routed vs non-routed** on identical claims/labels/sources. This is methodologically stronger than chasing FActScore's numbers.
5. **Gemma 4 31B's hallucinations concentrate in RELATIONAL claims** — directional trade flows and causal/specific-statistic claims — while TEMPORAL/ENTITY_ATTRIBUTE on well-documented topics are mostly correct. Concrete FALSE examples found: "Global GDP contracted 0.1% in 2009" (actual ≈2%), "Merchants received horses from the Roman Empire" (came from Central Asia), "Merchants received grapes from the Roman Empire" (came from Central Asia/Persia). **Do not conclude "Gemma is accurate"** — conclude accuracy varies sharply by claim type.
6. **CITATION is genuinely rare in naturalistic LLM output.** LLMs almost never emit "Zhang et al. (2016)"; they say "According to the WHO…". The ~8.8% CITATION rate reflects source-directed questions; general-knowledge questions would be near zero. This is a real finding about LLM behavior, not a dataset flaw.
7. **Some claims are structurally UNVERIFIABLE regardless of verifier** — procedural/administrative ("providers use CDC guidelines for dosage"), vague causal ("rising fuel costs caused malnutrition"), and hyper-specific stats with no single authoritative source (5% purchasing-power drop; 10% food-insecurity rise). UNVERIFIABLE is the correct, reportable outcome.
8. **Low-parameter / web / RAG models slot in as claim *sources*, not new verifiers** — one extra column in the results table, no pipeline rebuild.

---

## D. Open Decisions — NOT YET MADE

- **Final dataset size:** 125 (Phase 1) vs ~275 (add Phase 2 Q15–Q26). Assistant recommends ~250–300; student leaned toward more but not committed. Annotation burden is the constraint.
- **Whether to fix the ~12 TEMPORAL misclassifications in the CSV before or after re-running metrics** — the fix is manual and quick, but not yet applied.
- **CITATION verifier's real accuracy/coverage** — unknown until run on the gold set. Expect many L1-TRUE / L2-UNVERIFIABLE cases (source exists, exact stat not entailed from page text).
- **TruthfulQA** as a secondary FALSE-stress set — deferred to Phase 2, not decided.
- **Lesser-known-entity questionnaire** — deferred to the automated phase (don't hand-annotate obscure claims). Not scheduled.
- **±1 year tolerance** in the TEMPORAL comparator — caused at least one wrong verdict; may need tightening.

---

## E. Standing Methodological Commitments

- **No model training anywhere** — LLM prompting + public APIs + similarity/NLI only.
- **The comparison is routed vs non-routed, never HalDetect-verdict vs FActScore-verdict.** Same claims, same gold labels, same evidence, only routing varies.
- **`gold_verdict` is human ground truth** (judgment/quick lookup), never the verifier's output. Never nudge a gold label toward a verifier result.
- **UNVERIFIABLE is a first-class, measurable outcome**, not a failure. A verifier that can't find structured evidence returns UNVERIFIABLE rather than rerouting to another verifier (rerouting would conflate failure modes and break the ablation).
- **Determinism:** Gemma 4 31B at temperature=0, seed=42, num_ctx=8192; `format:"json"` for extraction. Fixed model version. Report the settings.
- **Don't reinvent the wheel / free-tier only:** Ollama+Gemma local, sentence-transformers, `bart-large-mnli`, Wikidata SPARQL, Wikidata opensearch, CrossRef, Semantic Scholar. No paid/gated tools.
- **Cache every API call** (`verifier_cache.json`) to avoid rate limits; purge known-bad keys before re-runs.
- **Metrics:** Accuracy = correct / verifiable; Coverage = verifiable / total; Hallucination rate = FALSE / (TRUE + FALSE). Report overall and per claim type. Numbers will shift as more claims are added — state them as pilot figures until the full set is run.
- **Thesis authorship constraint:** acknowledge only *LLM response generation*. Present atomization, classification, and taxonomy design as the student's own work. Frame the questions as **intentional domain stratification**, never "I asked Gemma."

---

## F. What to Actually Do Next

1. **Finish gold-labeling the 125 Phase-1 claims** (`gold_type`, `gold_verdict`, `notes`). Fix the ~12 TEMPORAL misclassifications in the `type` column while you're in there.
2. **Compute classification accuracy** (`type` vs `gold_type`), overall and per type — an independent result, report it before any verifier.
3. **Run the CITATION verifier on the gold-labeled CITATION claims;** record accuracy + coverage; log every L1-TRUE / L2-UNVERIFIABLE split.
4. **Build the remaining verifiers in order: QUANTITATIVE → ENTITY_ATTRIBUTE → RELATIONAL.** ENTITY_ATTRIBUTE can reuse most of TEMPORAL's Wikidata logic; RELATIONAL uses the already-cached BART-MNLI over Wikipedia passages. Get each one end-to-end and measured before starting the next.
5. **Build the non-routed baseline** (Wikipedia retrieval + BART-MNLI on *every* claim) and run it on the same gold set. This is the core quantitative proof.
6. **(Optional) Phase 2 expansion** — run Q15–Q26 through the unchanged pipeline into a separate CSV, merge with pandas, re-check the type distribution before annotating.
7. **Aggregate results** (routed vs non-routed, per type) → thesis chapters 4–6.

Priority: 1 > 2 > 3 > 4 > 5 > (6) > 7.

---

## Key Files to Have for Context

- `haldetect_pipeline.py` + `llm_client.py` — the working extraction pipeline (local Ollama / Gemma 4 31B).
- `haldetect_claims_20260524_045439.csv` — the 125-claim pilot, mid-annotation.
- `temporal_verifier.py` — built/run/evaluated (75% / 29.6%).
- `citation_verifier.py` — built, spot-tested, awaiting gold evaluation.
- `verifier_setup.py` + `verifier_cache.json` — infra checks (5/5 pass) and the API cache (purge 3 stale keys).
- Phase 2 question list Q15–Q26 — lives only in this chat; promote when ready.
- **FActScore reference:** labeled subset = **183 examples/model**; prompts came from a systematic Wikipedia "people"-category crawl split by pageviews (popular vs rare), generated as "Tell me a bio of [name]"; the labor was human annotation, not prompt design. Paper: Min et al., EMNLP 2023.
- Model under test: **Gemma 4 31B** via Ollama.

---

## Files NOT to Trust Without Re-Checking

- **This is the local Ollama/Gemma code track, NOT the Colab/Gemini notebook** described elsewhere in the project memory (that notebook uses `gemini-3.x` + spaCy + SPARQLWrapper). A successor should NOT assume `temporal_verifier.py`/`citation_verifier.py` here are the same code as the notebook's Phase cells — verify which codebase is current before editing.
- **The gold verdicts given in-chat are provisional.** They are quick-lookup judgments, several explicitly flagged (Google 10,000-years → UNVERIFIABLE per IBM's 2.5-day rebuttal; Q12_C14 "cognitive decline is a causal pathway" → circular; various Q14 stats). Re-verify before treating any as final ground truth.
- **The TEMPORAL 75%/29.6% figures are pilot-only** on 27 claims and WILL change once misclassifications are fixed and more claims are added. Do not quote as final.
- **`verifier_cache.json` contains 3 known-bad entries** (listed in §B). Re-running without deleting them reuses wrong data.
- **The ~12 misclassification list and per-type percentages** (CITATION 8.8%, QUANT 12.8%, EA 6.4%) are from the revised pipeline run's diagnostics; recount from the final labeled CSV before quoting exact numbers in the thesis.
- **CITATION verifier has no real evaluation numbers yet** — any performance claim about it is a prediction, not a result.

---

## Tone Note

Keep it direct and dense: no filler, no "let me know if you need anything else," no praise-padding. Push back when the student is wrong and state uncertainty plainly — this session's most valuable moments were the assistant *correcting itself* (the rule-vs-LLM classification reversal; walking back "NLI handles numbers poorly" for lack of a citation). The student's thesis is literally about hallucination detection, so unearned confidence is the wrong failure mode. Prefer free/local tools; the student is on a free tier. **Do not produce a docx unless explicitly asked.**

And the morale point: the project is **past design and into working code**. The extraction pipeline runs, one verifier is fully evaluated, a second is built, the infrastructure passes all checks, and the evaluation design is settled and defensible. The remaining work — three more verifiers, the non-routed baseline, finishing annotation — is concrete, scoped, and unblocked.
