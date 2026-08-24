# HalDetect — Session Handoff (today 2026-08-22)

> Chat name: RAG for fact verification experimentation

_Read this first. Everything below assumes no prior context._

---

## What This Project Is

HalDetect: a taxonomy-routed hallucination-detection pipeline for LLM-generated text. Five claim types (CITATION, TEMPORAL, QUANTITATIVE, ENTITY_ATTRIBUTE, RELATIONAL), each routed to a type-specific verifier. The thesis compares this routed approach against a non-routed baseline.

**Core contribution:** taxonomy routing sacrifices some coverage for higher precision on certain claim types. The evidence for this trade-off is in the verifier outputs below.

---

## A. What Happened This Session, In Order

1. Opened with a question about whether anyone had done FActScore-style atomization combined with RAG or similar retrieval-based verification — confirmed yes, specifically FActScore itself (Wikipedia retrieval + NLI), SAFE (agentic iterative search), FacTool (task-domain routing), RARR (retrieval + editing). Established that HalDetect's novelty is the linguistic/evidence-type taxonomy routing, not any individual verifier technique.
2. Decided to build the RELATIONAL verifier from scratch, starting small. RELATIONAL is the largest claim category (~47.9% of dataset) so errors here dominate aggregate numbers.
3. Built Phase 1: retrieval only, no verdict. Subject field → Wikipedia opensearch → page text → paragraph chunks → SBERT cosine similarity ranking → top-k passages printed for manual inspection. Confirmed on 3 claims: right pages found, relevant passages returned.
4. Built Phase 2: NLI verdict on top of working retrieval. BART-MNLI (`facebook/bart-large-mnli`) via `zero-shot-classification` pipeline. `candidate_labels=[claim]`, `hypothesis_template="This text is evidence that: {}"`. Contradiction approximated as `1 - entail` (matched citation_verifier.py pattern). Tested on 3 known-TRUE claims, all correct.
5. Ran full Phase 1 CSV (73 RELATIONAL claims from `haldetect_claims_20260524_045439_2.csv`): 31.51% coverage, 60.87% accuracy. Low coverage traced to three root causes: generic subjects ("Merchants", "Home prices" resolve to nothing), rate-limiting 429 errors mid-run, and genuinely unverifiable causal claims.
6. Loaded second dataset (`haldetect_claims_phase2_triaged.csv`, 126 rows) — 64 RELATIONAL claims, structured with `triage_flag` column (CHECKABLE / UNCERTAIN / UNVERIFIABLE_LIKELY). Gold labels not yet filled. AI-filled gold labels conservatively (12 TRUE, 52 UNVERIFIABLE). Ran Phase 2 on this set: 43.75% coverage, 39.29% accuracy.
7. Diagnosed Phase 2 accuracy drop: `1 - entail` approximation producing fake FALSEs — "not supported by passage" misread as "contradicted by passage." Identified 9 FALSE verdicts, ~6-7 wrong.
8. Added LLM-guided query generation via Gemini (`gemini-3.1-flash-lite-preview`). Gemini takes claim + structured fields (subject, property, value, q_id) and generates a disambiguated Wikipedia search query. Falls back to bare subject on API failure. Cached under `llmquery__` key prefix.
9. Switched Wikipedia lookup from `action=opensearch` to `action=query&list=search` (full-text search). Opensearch requires a title-like string; full-text search resolves descriptive queries to correct pages. Coverage jumped to 89.06%.
10. Fixed NLI from `1 - entail` to proper 3-way classification: `candidate_labels=["entailment", "contradiction", "neutral"]`, scores read by label name. Entail and contradict now scored independently.
11. Fixed a bug in `evaluate_relational()` where `verdict = row.get("verified_verdict"...)` was placed after `return {}`, making it dead code and causing the for-loop to reference the previous iteration's `verdict` for every row. Accuracy numbers from runs with the bug are not trustworthy.
12. Produced `relational_verifier_phase3d.py` — clean version with bug fixed, dead commented code removed, evaluation function annotated to flag accuracy as unreliable until gold labels are verified.
13. Reviewed gold labels: identified 31 claims incorrectly labeled UNVERIFIABLE that should be TRUE (CRISPR mechanism claims, Paris Agreement emissions peak, stunting/malnutrition claims, Cuban Missile Crisis facts, TCP/IP, Tim Berners-Lee, Mosaic browser, vaccine mechanism claims, Marie Curie radiation death, Ukraine war grain/fertilizer disruption, flood/drought crop damage). Corrected labels, re-ran: accuracy jumped from ~15% to 61.11% at 84.38% coverage. Gold label quality, not verifier quality, was the dominant factor in that jump.
14. Ran with no cache (fresh): similar final numbers, confirmed stability. Note: Gemini query generation is non-deterministic without caching — same claim can produce different queries across runs, resolving to different Wikipedia pages and flipping verdicts.
15. Built Phase 3e (`relational_verifier_phase3e.py`): multi-candidate retrieval (top-3 search candidates + subject fallback page pooled together), margin-based NLI decision (entailment must beat contradiction by MIN_MARGIN=0.15, not just clear its own threshold), split caches (retrieval vs. NLI), exponential backoff retry on 429s. Result: 66.67% accuracy at 70.31% coverage — fewer wrong FALSEs, but more UNVERIFIABLEs from the margin gate.
16. Tried and reverted a page-relevance keyword gate inside Phase 3e — drop candidate pages whose title/intro share no claim keywords. Tested against full 64-claim set twice: didn't fix its target case (generic domain words like "mental" and "health" passed the gate regardless) and introduced a regression (dropped a legitimately relevant page for "debt crises reduce household purchasing power", flipping a correct TRUE to UNVERIFIABLE). Net: flat-to-negative on both metrics. Removed and documented in Phase 3e docstring as a dead end.
17. Established Phase 3d as the thesis-reportable result (84.38% coverage, ~61% accuracy) over Phase 3e (70.31% coverage, ~67% accuracy). Rationale: RQ4 is about what proportion of claims can be automatically verified — coverage matters more than a marginal accuracy gain from refusing to answer.
18. Identified five new literature review contributions emerging from the implementation work: entity disambiguation as underexplored bottleneck; coverage ceiling vs. implementation failure distinction; `1 - entail` NLI approximation gap; single-page vs. multi-candidate retrieval ablation; RELATIONAL structural heterogeneity sub-typing.

---

## B. Current File State

| File | Phase/Iteration | Status | Notes |
|------|-----------------|--------|-------|
| `haldetect_claims_20260524_045439_2.csv` | Phase 1 dataset | Input | 125 rows, 73 RELATIONAL. Gold-labeled from prior sessions. |
| `relational_verified_results.csv` | Phase 3d, Phase 1 dataset | Output | 73 RELATIONAL claims. 31.51% coverage, 60.87% accuracy. |
| `haldetect_claims_phase2_triaged.csv` | Phase 2 dataset | Input | 126 rows, 64 RELATIONAL. Triage flags present, gold labels not yet manually verified. |
| `haldetect_phase2_goldlabeled.csv` | Phase 2 dataset | **Working gold labels** | 64 RELATIONAL gold verdicts filled (12 TRUE, 52 UNVERIFIABLE → 31 corrected to TRUE). Still needs manual author verification pass. |
| `relational_phase2_verified_results.csv` | Phase 3d, Phase 2 dataset | Output | 64 RELATIONAL claims. 84.38% coverage, 61.11% accuracy (after gold label corrections). Thesis-reportable result. |
| `relational_phase2_verified_results_v2.csv` | Phase 3e, Phase 2 dataset | Output | 64 RELATIONAL claims. 70.31% coverage, 66.67% accuracy. Not chosen for thesis reporting — coverage regression too large. |
| `relational_verifier_phase1.py` | Phase 1 | Code — stable | Retrieval only, no verdict. Wikipedia opensearch + SBERT. |
| `relational_verifier_phase2.py` | Phase 2 | Code — superseded | First NLI verdict version. Uses `1 - entail` approximation. Do not use for new runs. |
| `relational_verifier_phase3d.py` | Phase 3d | Code — **authoritative** | Clean version: 3-way NLI, bug-free evaluation, Gemini query generation, full-text Wikipedia search, CSV I/O. Use this for any re-runs. |
| `relational_verifier_phase3e.py` | Phase 3e | Code — stable | Multi-candidate retrieval + margin NLI + split caches + backoff. Documented negative result (page-relevance gate) in docstring. Keep for reference but do not report as primary result. |
| `relational_cache.json` | Phase 3d | Cache | Wikipedia text + title + LLM queries. Do not delete between runs — reproducibility depends on it. |
| `relational_retrieval_cache.json` | Phase 3e | Cache | Phase 3e retrieval cache (separate from NLI cache). |
| `relational_nli_cache.json` | Phase 3e | Cache | Phase 3e NLI cache (separate from retrieval cache). |

**Golden rule:** `relational_verifier_phase3d.py` is the authoritative code for thesis results. Phase 3e is documented but not the primary result. Never delete caches mid-experiment — reproducibility depends on them.

---

## C. Key Findings — Ranked by Evidence Strength

1. **Gold label quality dominated the accuracy number.** Correcting 31 UNVERIFIABLE → TRUE labels raised measured accuracy from ~15% to 61% without changing the verifier at all. This is the clearest demonstration in the project that accuracy is only meaningful once both the verifier and the gold labels are independently trustworthy.

2. **Coverage ceiling for RELATIONAL-over-Wikipedia is ~84-89%, not 100%.** The remaining ~11-16% are genuinely unverifiable via Wikipedia regardless of implementation quality — vague causal claims ("mental health gaps are driven by systemic neglect"), claims requiring medical literature (hypertension → dementia), and claims too specific for any single Wikipedia page. This is a finding about the architecture, not a fixable bug.

3. **RELATIONAL claim type is structurally heterogeneous — five distinct sub-types with different verifiability ceilings.** Named-event causal and person-action claims (Types A/B) are reliably verifiable via Wikipedia. Generic-subject process (Type C), domain-specific mechanism (Type D), and historically contested interpretation (Type E) claims are not. The taxonomy's RELATIONAL bucket is too broad for a single verifier to handle uniformly. This directly answers RQ3.

4. **Multi-candidate retrieval (Phase 3e) improves accuracy but at a 14-point coverage cost.** The coverage-accuracy trade-off is real and documented. Raising the margin threshold suppressed spurious FALSEs but also pushed legitimate TRUEs into UNVERIFIABLE when a single noisy passage dragged the contradict score up. A blunt margin gate is not the right tool for this.

5. **Page-relevance keyword gate was tried twice and reverted twice.** First attempt: during earlier RELATIONAL verifier development (prior session). Second attempt: Phase 3e. Both times: didn't fix the target case (generic domain words passed the gate) and introduced regressions. This negative result is documented in the Phase 3e docstring. Do not re-attempt without prototyping against cached claims first.

6. **Gemini-generated queries improve disambiguation for ambiguous subjects but can over-specify for canonical ones.** "Marie Curie" → bare subject resolves correctly; Gemini query "Marie Curie education Sorbonne physics" sometimes resolves to the Sorbonne University page instead of the Marie Curie biography. The fix (multi-candidate pooling) dilutes this by fetching the biography page as the subject fallback regardless. One-shot retrieval is sensitive to query phrasing; pooling is more robust.

7. **`1 - entail` contradiction approximation produces systematic fake FALSEs.** Concretely demonstrated: "Hearing loss is a complication of diabetes" passage scores entail=0.000, making contradict=1.000, which then incorrectly falsifies "Diabetes leads to blindness." Proper 3-way NLI (`candidate_labels=["entailment", "contradiction", "neutral"]`) eliminated most of these. Documented as a limitation of the citation_verifier.py pattern inherited by this verifier.

---

## D. Open Decisions — NOT YET MADE

- **Author's manual gold label verification pass** — `haldetect_phase2_goldlabeled.csv` has AI-filled labels corrected by AI. Author needs to verify each label independently before any numbers are reported as final.
- **QUANTITATIVE verifier** — not built. Blocks ~24% of every batch. Architecture decision: numeric extraction + unit normalization + authoritative source lookup (Wikidata for counts, WHO/World Bank for statistics). No code exists yet.
- **Non-routed baseline** — not built. Required for RQ2. Same evidence sources, same NLI model, no taxonomy routing — every claim goes through one generic Wikipedia+NLI pipeline. Must be built after all five verifiers are stable.
- **ENTITY_ATTRIBUTE verifier** — existing version has 0% accuracy / 4.5% coverage (Rosetta Stone QID bug unfixed from prior sessions). Not revisited this session.
- **CITATION verifier Level 1 tautology** — TRIVIALLY_KNOWN_ORGS check always fires on the actual dataset. Not revisited this session.
- **Held-out test set** — none of the current numbers are final. A proper held-out set is still needed before thesis evaluation numbers are locked.

---

## E. Standing Methodological Commitments

- Gold labels are never nudged toward verifier output — only corrected where human judgment (or strong prior knowledge) says the label itself was wrong.
- Cache is never deleted mid-experiment. Clear specific key prefixes (`title__`, `text__`, `llmquery__`) if retrieval logic changes; preserve `nli__` keys unless NLI logic changes. Never delete the whole file between runs of the same experiment.
- Page-relevance gates are not re-added without prototyping against a small cached subset first — negative result is documented, do not repeat without new evidence.
- Results reported for the thesis come from a single cached run, not averages across runs. Non-determinism in page resolution means different runs can produce different verdicts for the same claim.
- Accuracy is flagged as unreliable in all printed evaluation output until the author has completed a manual gold label verification pass.
- Coverage is the primary diagnostic for RQ4; accuracy is secondary. A verifier that refuses to answer is not the same as one that gets more answers right.

---

## F. What to Actually Do Next

1. **Author manually verifies `haldetect_phase2_goldlabeled.csv`** — go through all 64 RELATIONAL gold verdicts, especially the 31 flipped from UNVERIFIABLE to TRUE, and confirm or correct each one independently of verifier output. Without this, no accuracy number is reportable.
2. **Build QUANTITATIVE verifier** — largest remaining gap, blocks ~24% of every batch. Suggested approach: extract numeric value + unit from claim, look up authoritative source (Wikidata P-property for counts, WHO/World Bank API for statistics), apply δ-tolerance comparison. Similar structure to TEMPORAL verifier.
3. **Build non-routed baseline** — required for RQ2. One generic Wikipedia + SBERT + BART-MNLI pipeline, no taxonomy routing, applied to all claim types. Build after all five type-specific verifiers are stable so the comparison is fair.
4. **Fix ENTITY_ATTRIBUTE verifier** — Rosetta Stone QID bug (Q4048553 → "Porl King") from prior sessions still unresolved. Entity resolution heuristic needs a secondary validation pass.
5. **Construct held-out test set** — none of the current results are final-ready. Needed before writing Chapter 4 results section.
6. **Write Chapters 4–6** — results, analysis, discussion/conclusion. RELATIONAL verifier findings are thesis-ready pending the gold label verification pass.

Priority: 1 > 2 > 3 > 4 > 5 > 6.

---

## Key Files to Have for Context

- `haldetect_session_handoff_2026-08-20.md` — prior session handoff. Has context on TEMPORAL, CITATION, ENTITY_ATTRIBUTE verifiers and the batch 3 adversarial testing.
- `haldetect_phase2_goldlabeled.csv` — working gold labels for Phase 2 dataset. Needs author verification pass before any numbers are final.
- `relational_phase2_verified_results.csv` — Phase 3d output, 64 RELATIONAL claims. The thesis-reportable result.
- `relational_verifier_phase3d.py` — authoritative RELATIONAL verifier code.
- `relational_verifier_phase3e.py` — Phase 3e code with multi-candidate retrieval and margin NLI. Keep for reference; not the primary result.
- `relational_cache.json` — Phase 3d cache. Do not delete.

---

## Files NOT to Trust Without Re-Checking

- `relational_phase2_verified_results_v2.csv` — Phase 3e output. Not chosen for thesis reporting due to coverage regression. Preserve for ablation comparison but do not cite as primary result.
- `relational_verifier_phase2.py` — uses `1 - entail` approximation. Superseded by Phase 3d. Do not use for new runs.
- Any gold label CSV without a manual author verification note — AI-filled labels corrected by AI are not independently verified and should not be treated as ground truth until the author has reviewed them.
- `haldetect_claims_phase2_triaged.csv` — original triaged CSV with no gold labels filled. Use `haldetect_phase2_goldlabeled.csv` instead.

---

## Literature Review Additions Identified This Session

Five new points emerged from the implementation that are worth adding to the lit review — framed as gaps in prior work that motivated design choices:

1. **Entity disambiguation as underexplored bottleneck** — FActScore/SAFE/AVeriTeC treat retrieval as a solved sub-problem; your implementation showed it is not for heterogeneous claim corpora. FActScore's biography-only scope makes entity linking trivial in ways HalDetect's multi-domain corpus does not enjoy.
2. **Coverage ceiling vs. implementation failure distinction** — existing work reports aggregate UNVERIFIABLE rates without distinguishing genuinely unverifiable claims, fixable retrieval errors, and infrastructure failures (rate limiting). Your Phase 4 decomposition makes this explicit.
3. **NLI approximation gap** — `1 - entail` shortcut appears implicitly in several systems. Your implementation demonstrated concretely that it collapses "not supported" and "contradicted," producing systematic false FALSEs.
4. **Single-page vs. multi-candidate retrieval** — FActScore and SAFE both retrieve from a single source per query. Your Phase 3d/3e ablation provides empirical evidence that multi-candidate pooling improves accuracy for disambiguation-hard claims but introduces noise for broad claims, producing a documented coverage-accuracy trade-off.
5. **RELATIONAL structural heterogeneity** — the biggest practical finding. RELATIONAL as a catch-all contains at least five structurally distinct sub-types with different verifiability ceilings and evidence source requirements. FActScore restricts scope to avoid this; FacTool routes by task-domain; neither explicitly characterizes the sub-types or measures their impact on coverage. This is the clearest empirical contribution to the literature from this session.

---

## Tone Note

The RELATIONAL verifier is done. The implementation produced real, documented findings rather than just performance numbers — structural heterogeneity, retrieval disambiguation failures, NLI approximation artifacts, and a documented negative result (page-relevance gate). These are thesis contributions, not problems to fix. The project is not at a dead end. The remaining work is all known-scope: one more verifier (QUANTITATIVE), one baseline, one manual annotation pass, and three chapters.
