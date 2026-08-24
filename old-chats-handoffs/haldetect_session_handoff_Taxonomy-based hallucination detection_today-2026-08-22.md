# HalDetect — Session Handoff (today, 2026-08-22)

> Chat name: Taxonomy-based hallucination detection
> Source chat span: created 2026-02-21, last updated 2026-04-05, exported 2026-08-22

_Read this first. Everything below assumes no prior context._

---

## What This Project Is

HalDetect: a taxonomy-routed claim-verification pipeline for detecting hallucinations in LLM-generated text (BSc thesis, CSE 700). An LLM response is atomized into claims; each claim is classified into one of five types and routed to a type-specific verifier that queries a public knowledge source in real time and returns TRUE / FALSE / UNVERIFIABLE.

**Five types, in priority order:** CITATION > TEMPORAL > QUANTITATIVE > ENTITY_ATTRIBUTE > RELATIONAL.

**Core contribution:** taxonomy-guided routing instead of one uniform verifier for every claim. The closest prior work, FActScore (Min et al., EMNLP 2023), applies uniform Wikipedia retrieval + NLI to all claims; HalDetect picks the right verification strategy per claim type. Nothing is trained — it is rule-based classification + public APIs + similarity/NLI.

**This chat covers the foundational phase:** Task 1 (taxonomy rules) start-to-finish, the FActScore dataset study, selection of the 30-claim pilot, and the first TEMPORAL verifier. It predates the Colab verifier notebook built in later sessions.

---

## A. What Happened This Session, In Order

1. **Cold start.** Student opened with "have we been discussing a taxonomy-based hallucination detection mechanism?" and shared an anonymized thesis PDF (`Thesis_Report_Sahib_anonymous_copy.pdf`). Resolved the central misconception up front: verifiers query public APIs/knowledge bases **by entity/topic in real time** — there is no pre-built "evidence set" to assemble, and the claim type does **not** filter the corpus; it selects the verification *strategy*.
2. **Unified the plan.** Merged Claude + ChatGPT guidance into one sequence and established two evaluation modes: **Mode A** (FEVER-style, pre-labeled → measures verifier accuracy cleanly) and **Mode B** (TruthfulQA-style generate → extract → verify → measures coverage & hallucination rate in the wild). Both intended.
3. **Subtask 1.1 — taxonomy rules.** Wrote the priority hierarchy + rule doc (`taxonomy_rules.md`): 10 extraction rules, five type definitions with near-misses, tie-breaking rules, the dual-emit policy, and a decision checklist.
4. **Subtask 1.2 — collect responses.** 10 questions × 6 LLMs (DeepSeek, Grok, ChatGPT, Minimax, Perplexity, Gemini), each constrained to 5–7 plain sentences. Chose **ChatGPT's 10 responses** to atomize (keeps manual work manageable); the rest are held in reserve in `tenQuestionsLLM_Responses.txt`. Flagged that **DeepSeek ≡ Grok** were identical on most questions — not independent data points.
5. **Reviewed a completed reference thesis** (the shared PDF) as a structural template — confirmed the small-custom-dataset + results-table framing is acceptable for the department.
6. **Subtask 1.3 — atomize.** Atomized ChatGPT's 10 responses → **109 claims** after fixes (merged over-decomposed claims; the IPCC dual-emit case was reduced 14 → 8 = 1 CITATION + 7 embedded).
7. **Conceptual Q&A resolved:** dual-emit independence + shared-ID linking (`citation_pair_XX`); the aggregation report; a plain-English "trust score" deferred to future work; why routing beats uniform retrieval (fabricated-citation example); how HalDetect differs from FActScore; how to treat post-cutoff claims.
8. **Subtask 1.4 — classify.** Classified all 109. Main systematic error: **EA vs RELATIONAL** (what an entity *is/has* vs what it *does/causes*). Corrections applied; hard cases logged for 1.5.
9. **CITATION rework.** Realized conversational LLM output rarely uses "X et al. (20XX)" — only **1 genuine CITATION** in the first 109. Added a **CITATION specificity threshold** (named **and** independently lookable; "scientists say" / "many scientists" → RELATIONAL). Added 8 citation-targeted questions → Gemini + Grok → **31 new claims**. Corpus → **140**.
10. **Subtask 1.5 — finalize.** Chose **option A** (clean standalone doc) → produced `taxonomy_rules.docx`. **Task 1 COMPLETE.**
11. **FActScore deep-dive.** Dataset layout (labeled / unlabeled / unlabeled-predictions); fields (topic, category, human vs model atomic facts, is-relevant, S/NS/IR labels); verification = local Wikipedia dump + retrieval + LLM-as-NLI (**not** free-recall); training (FActScore's NPM retrieval is fine-tuned, FEVER trains classifiers, **HalDetect trains nothing**); label mapping **S→TRUE, NS→FALSE, IR→exclude** (not UNVERIFIABLE). Noted modern models (ChatGPT 5.2 etc.) are far stronger than FActScore's 2022–23 models — motivation for why detection still matters.
12. **Task 2 prep.** Selected **30 balanced pilot claims** (6 per type, 3 dual-emit pairs), each with a selection justification.
13. **Verifier design deep-dive.** Per-type pipeline sketches; entity linking via Wikidata `wbsearchentities` (confirmed standard, widely-used — not invented); normalization via `dateparser` + `rapidfuzz`; fallback hierarchies; RELATIONAL via Sentence-BERT passage similarity with an optional `bart-large-mnli` NLI upgrade; thresholds to be tuned on the pilot.
14. **First TEMPORAL verifier.** Wrote the 5-step pipeline (NER → entity link → date-property inference → SPARQL → normalize + compare) returning TRUE/FALSE/UNVERIFIABLE. Separated library calls (spaCy `nlp`, `dateparser`) from custom functions still to write (`wikidata_search` ~10 lines, `sparql_query` ~15 lines via SPARQLWrapper, `infer_date_property`: born→P569, died→P570, founded→P571). Subject picked via `nsubj` dependency; low-confidence disambiguation → UNVERIFIABLE.
15. **Interaction style guide** produced for successor chats (direct, dense, push back, no docx unless asked, free-tier-aware).

---

## B. Current File / Artifact State

| Artifact | Stage | Status | Notes |
| --- | --- | --- | --- |
| `taxonomy_rules.docx` | Subtask 1.5 output | **Authoritative** | Clean standalone (option A). 10 extraction rules, 5 type definitions w/ real examples, tie-breaks, CITATION threshold, dual-emit policy, outcome defs, aggregation format, distribution reference. Supersedes `taxonomy_rules.md`. |
| `tenQuestionsLLM_Responses.txt` | Subtask 1.2 | Input / reserve | 10 Qs × 6 LLMs raw. Only ChatGPT's 10 were atomized; rest are reserve. DeepSeek ≡ Grok flagged. |
| 109-claim atomized + classified list | Subtask 1.3–1.4 | Confirmed | ChatGPT responses, fully classified with corrections. |
| 31 citation-targeted claims | CITATION rework | Confirmed | Gemini + Grok, from 8 citation-cue questions. |
| all-140 classified-claims table (claim / class / justification) | Post-1.5 | Confirmed | Requested as a table, "no docx". The working corpus. |
| `HalDetect (1)/(2)/(4)/(5).txt` | Peer review | Input — treat with care | Grok/DeepSeek/Minimax remarks on the student's classification. Contains sycophancy and over-reach (see below). |
| `ChatGPT.jsonl` (421 lines) | FActScore study | Reference | From `factscore-unlabeled-predictions`; sample used to understand the dataset. |
| 30-claim pilot selection | Task 2 prep | **Selected, NOT verified** | Lives only in this chat. 6/type, 3 dual-emit pairs. Promote to a CSV in Task 2. |
| TEMPORAL verifier | Task 3 start | **Sketch only** | 5-step pipeline written; custom functions unwritten; not a committed script. |
| `Thesis_Report_Sahib_anonymous_copy.pdf` | Context | Input | Prior/reference thesis used as a structural template. |

_Note: most verifiers can run locally; the **RELATIONAL** verifier (Sentence-BERT + `bart-large-mnli`) is the one suited to **Colab/Kaggle** GPU. 140 claims on CPU is manageable if needed._

---

## C. Key Findings — Ranked by Evidence Strength

1. **Task 1 is genuinely complete and battle-tested.** The taxonomy rules were validated against 140 real LLM claims, not toy examples. Highest confidence item in this handoff.
2. **The corpus distribution is realistic, not a defect.** Across 140 claims: RELATIONAL 47.9%, ENTITY_ATTRIBUTE 17.1%, TEMPORAL 16.4%, QUANTITATIVE 11.4%, CITATION 7.1%. RELATIONAL dominance and CITATION/QUANT scarcity reflect how LLMs actually write. Do not artificially balance the corpus.
3. **The biggest conceptual unblock:** verification queries evidence by entity/topic in real time; the claim type routes the *strategy*, it does not filter the corpus, and there is no evidence set to pre-build. This was the student's central worry — now resolved.
4. **EA vs RELATIONAL is the main classification fault line.** Rule of thumb: dominant assertion = what the entity *is/has* → ENTITY_ATTRIBUTE; what it *does/causes/enables* → RELATIONAL.
5. **CITATION needs a specificity threshold: named AND independently lookable.** "Scientists say" / "many scientists" is RELATIONAL, not CITATION. Only 1 true CITATION appeared in the first 109 claims.
6. **Dual-emit is a real contribution over uniform verification.** Splitting a citation-wrapped claim into a source-existence CITATION + an embedded fact (linked by `citation_pair_XX`) distinguishes *fabricated-source-but-true-fact* from *real-source-but-wrong-fact* — a failure mode FActScore's uniform pipeline cannot isolate.
7. **FActScore is the baseline, not a duplicate.** It applies uniform Wikipedia retrieval + NLI to every claim; HalDetect routes by type. Querying live APIs also avoids FActScore's static-dump staleness. Both are citable thesis advantages.
8. **IR → exclude, not UNVERIFIABLE.** Conflating "not worth verifying" with "tried but found no evidence" corrupts the Coverage metric. Keep them distinct.

---

## D. Open Decisions — NOT YET MADE

- **Task 2 (manual gold-labeling of the 30 pilot claims)** — not started. This is the immediate next action.
- **RELATIONAL similarity threshold θ and QUANTITATIVE tolerance δ** — tune on the pilot, do not hardcode.
- **RELATIONAL method:** plain Sentence-BERT similarity vs `bart-large-mnli` NLI — undecided.
- **Entity disambiguation policy** when multiple entities appear (subject via `nsubj`; low confidence → UNVERIFIABLE) — sketched, not implemented.
- **Post-cutoff claims** (e.g., sea-level / 2026-dated items from Gr10, DeepSeek) — lean toward excluding from the pilot; not finalized.
- **Whether to run Mode A (FEVER / FActScore facts) in addition to Mode B** — both planned; sequencing not fixed.

---

## E. Standing Methodological Commitments

- **No model training anywhere** — rule-based classifier + public APIs + similarity/NLI. Deliberate design choice and a talking point vs FEVER/NPM.
- **Don't reinvent the wheel** — spaCy (NER / dependency / segmentation), sentence-transformers, dateparser, rapidfuzz, SPARQLWrapper, and the Wikidata / DBpedia / Semantic Scholar / CrossRef / Wikipedia APIs.
- **UNVERIFIABLE is a legitimate, measurable outcome**, not a failure.
- **Don't artificially balance the real corpus.** The 30-claim pilot IS intentionally balanced because it is a validation set, not a representative sample.
- **The thesis will not credit AI for classification/atomization/rule-writing** — only LLM *response generation* is acknowledged. Present the taxonomy work as the student's own.
- **Tune thresholds on the pilot and report the tuning;** never nudge a gold label toward verifier output.
- **Metrics:** Precision, Recall, F1, Coverage = (TRUE + FALSE) / Total, Hallucination Rate = FALSE / (TRUE + FALSE).

---

## F. What to Actually Do Next

1. **Task 2 — manually verify the 30 selected claims → gold CSV** (`claim_id, claim_text, claim_type, ground_truth, evidence_source, notes, citation_pair`). Exclude post-cutoff claims.
2. **Task 3 — build verifiers** in order **TEMPORAL → ENTITY_ATTRIBUTE → CITATION → RELATIONAL → QUANTITATIVE**. Start from the TEMPORAL sketch; fill in `wikidata_search`, `sparql_query`, `infer_date_property`, `parse_date`, `dates_match`. Get one verifier end-to-end and measured before starting the next.
3. **Task 4 — programmatic extraction + classification** (the 10 rules in spaCy, replacing manual atomization).
4. **Task 5 — evaluation:** Mode A (FActScore atomic facts vs S/NS) + Mode B (own 140-corpus responses vs the 30 gold labels).
5. **Task 6 — the core quantitative proof:** ablation of taxonomy-routed verifiers vs a single generic (uniform) verifier.
6. **Task 7 — write the thesis.**

Priority: 1 > 2 > 3 > 4 > 5 > 6.

---

## Key Files to Have for Context

- `taxonomy_rules.docx` — authoritative Task 1 output.
- all-140 classified-claims table (claim / class / justification) — the working corpus.
- `tenQuestionsLLM_Responses.txt` — raw 6-LLM responses (ChatGPT atomized, rest reserve).
- The 30-claim pilot selection — currently only in this chat; promote to CSV in Task 2.
- `Thesis_Report_Sahib_anonymous_copy.pdf` — reference thesis / structural template.
- **FActScore:** paper `arxiv.org/abs/2305.14251`; upstream repo `github.com/shmsw25/FActScore`; private working copy `github.com/SahibAbbas123/FActScore-priv.git`; sample studied `ChatGPT.jsonl` (421 lines, `factscore-unlabeled-predictions`).
- LLM versions used for response generation: ChatGPT 5.2, Gemini 3, DeepSeek v3.2, Claude Sonnet 4.6, Grok 3, Minimax M2.7.

---

## Files NOT to Trust Without Re-Checking

- **`HalDetect (1)/(2)/(4)/(5).txt` (peer-review remarks)** — contain sycophancy (e.g., DeepSeek "excellent") and over-reach (Minimax proposing DEFINITIONAL / COMPARATIVE types). Reviewed and **rejected** — do not resurrect those type suggestions; ENTITY_ATTRIBUTE already covers them.
- **Any verdicts on the 30 pilot claims** — NONE are ground truth yet. The "likely TRUE" notes in the selection table are guesses, not labels. Verify manually in Task 2.
- **Post-cutoff claims** — exclude until the cutoff policy is finalized.
- **The TEMPORAL verifier sketch** — the 5-step logic is sound but the custom functions are unwritten and disambiguation + `infer_date_property` coverage need completing before trusting at scale.
- **The "~" counts in the distribution** (TEMPORAL ~23, QUANT ~16, EA ~24, RELATIONAL ~67) — approximate. Recount from the final 140-claim table before quoting exact per-type numbers in the thesis. (The percentages in §C are the figures given in the chat.)

---

## Tone Note

The interaction style that worked in this chat, to keep: direct, dense, no filler, no "let me know if you need anything else," push back when the student is wrong, admit uncertainty instead of guessing, and **do not produce a docx unless explicitly asked** (student repeatedly said "no docx"). Keep it efficient — the student is on a free tier.

And the morale point: this project is **on track**. Task 1 is genuinely finished and validated on real data, the FActScore relationship is understood, and the pilot is chosen. The next steps are concrete, buildable, known-scope work — no theoretical blockers remain.
