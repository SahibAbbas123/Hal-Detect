# HalDetect — Session Handoff (2026-08-09 to 2026-08-20 approximate)

> Chat name: Evaluating feasibility of hallucination detection project

_Read this first. Everything below assumes no prior context._

---

## What This Project Is

HalDetect: a taxonomy-routed hallucination-detection pipeline for LLM-generated text. Five claim types (CITATION, TEMPORAL, QUANTITATIVE, ENTITY_ATTRIBUTE, RELATIONAL), each routed to a type-specific verifier. The thesis compares this routed approach against a non-routed baseline.

**Core contribution:** taxonomy routing sacrifices some coverage for higher precision on certain claim types. The evidence for this trade-off is in the verifier outputs below.

---

## A. What Happened This Session, In Order

1. Inherited a project at a crisis point: author worried it was all broken/not feasible. Audited two prior handoff docs (transfer_2026-08-02 + log_2026-08-02_batch3-gold-labeling) against raw CSVs and execution logs.
2. Found: transfer doc had stale claim (RELATIONAL "not yet run" when it had been); CSV had real contradictions (Phase 2 gold labels claimed filled but actually blank in one version).
3. Resolved via direct file audit: got three versions of Phase 2 goldlabeled CSV, identified which was authoritative (\__3_ version, only one with TEMPORAL/CITATION filled + Q18_C09 correctly FALSE).
4. Independently source-verified Q18_C09 (Paris Agreement / 2050 claim) against UNFCCC Article 4.1 — claim is FALSE, label is correct. Added primary citation.
5. Found: RELATIONAL verifier had one real miss (B3N_10_C17, glycogen inversion) that was called TRUE despite being gold FALSE. Led to adversarial testing.
6. Built minimal-pair negative-injection test: 14 natural RELATIONAL claims + 6 deliberately false claims (temporal_condition and magnitude inversions). Ran, got 50%/40% accuracy/coverage.
7. Found cache-poisoning bug: `_get_with_retry()` returns None when retries exhausted, but calling functions cached empty result anyway, poisoning future runs. Fixed both functions.
8. Ran expanded test again (20 rows after fix), same cache: 60%/40%. Pattern held — every dangerous TRUE (false verdict of TRUE on a FALSE claim) clustered in temporal_condition and magnitude only; zero from negation/entity_swap/directional/comparative.
9. Found: Gemini query generation had no temperature pinning, causing retrieval-input variance. Added `"generationConfig": {"temperature": 0}` to the API call.
10. Ran third time (fresh cache, temperature=0): B3N_02 flipped UNVERIFIABLE (different passages retrieved). Confirmed retrieval-input instability is real and structural, not just query-variance.

---

## B. Current File State

| File                                                           | Phase/Iteration      | Status            | Notes                                                                                                                                                                                         |
| -------------------------------------------------------------- | -------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `temporal_b3_verified_results.csv`                             | Phase 1 (original)   | Confirmed         | 26 rows, 75% acc / 29.6% cov. Known bug: Panama Canal wrong QID.                                                                                                                              |
| `entity_attribute_b3_verified_results.csv`                     | Phase 1              | Confirmed         | 22 rows, 0% acc / 4.5% cov. Rosetta Stone wrong QID (Q4048553→"Porl King").                                                                                                                   |
| `relational_b3_verified_results.csv`                           | Phase 3e             | Confirmed         | 47 rows (Batch 3 natural claims), 80.77% acc / 55.32% cov.                                                                                                                                    |
| `haldetect_phase2_goldlabeled__3_.csv`                         | Phase 2, gold labels | **Authoritative** | 126 rows, 109 labeled (RELATIONAL 64, EA 13, TEMPORAL 26, CITATION 6, QUANTITATIVE 0). Superset-audited: no silent overwrites. TRUE-skewed (only 1 FALSE across 109 labels).                  |
| `relational_negatives_batch3.csv`                              | Phase 3e, synthetic  | Input             | 14 adversarial FALSE claims on natural RELATIONAL topics.                                                                                                                                     |
| `relational_negatives_batch3_expansion.csv`                    | Phase 3e, synthetic  | Input             | 6 additional minimal-pair negatives (3 temporal_condition, 3 magnitude).                                                                                                                      |
| `relational_negatives_b3_merger_verified_results.csv`          | Phase 3e (i), run 2  | Output            | 20 rows (14+6), 60% acc / 40% cov. Danger pattern: all 4 dangerous TRUEs in temporal_condition+magnitude.                                                                                     |
| `relational_negatives_b3_merger_verified_results__1_.csv`      | Phase 3e (i), run 3  | Output            | Same 20 rows, fresh cache, temperature=0. 66.67% acc / 33.33% cov. Danger pattern holds: 1 temporal_condition + 2 magnitude. B3N_02 flipped to UV, confirming retrieval instability persists. |
| `rel_verif_latest.txt` (uploaded file)                         | Phase 3e (h)         | Code              | Template for phase 3e; includes cache-poisoning bug in both functions.                                                                                                                        |
| `relational_verifier_phase2.py` (from earlier in conversation) | Phase 3e (g)         | Code              | NLI verdict logic; may be stale relative to latest. Check against `rel_verif_latest.txt` before trusting.                                                                                     |

**Golden rule:** always cross-check code against the most recent `.txt` upload, not earlier `.py` files. The `.py` files are snapshots; `.txt` files in this session are the working reference.

---

## C. Key Findings — Ranked by Evidence Strength

1. **RELATIONAL's NLI failure is clustering and repeatable.** Adversarial testing at n=6/category (temporal_condition, magnitude) produced dangerous TRUEs in both, zero in negation/entity_swap/directional/comparative. Replicated across three independent runs with different cache states. Pattern holds. Ready for thesis chapter.

2. **Retrieval-input instability is structural, not just query-generation variance.** Even with Gemini `temperature=0` pinned, B3N_02's verdict flipped between runs due to different passages being retrieved and ranked. Root cause: Wikipedia search results and passage ranking are themselves non-deterministic. This is a real, citable limitation of the current architecture.

3. **Q18_C09 (Paris Agreement / 2050) is a clean, source-verified example of "widely-repeated shorthand mistaken for primary source."** UNFCCC Article 4.1 specifies "second half of this century," not 2050. The year was adopted by individual Parties post-treaty. Good thesis example.

4. **Phase 2 Phase 2 gold set is heavily TRUE-skewed.** Across 109 labeled claims (RELATIONAL 64, EA 13, TEMPORAL 26, CITATION 6), only Q18_C09 is FALSE. All other types have zero FALSE examples. This was diagnosed and flagged but not yet fixed via injected-negative-example work.

5. **Entity-resolution QID bugs are real and active.** Panama Canal (1914 opening) resolved to Q498979 (1903 date), Rosetta Stone resolved to Q4048553 (wrong value "Porl King"). Both confirmed in verifier outputs. Root cause: "prefer first non-empty candidate" heuristic, affects TEMPORAL and EA. Unfixed, highest-priority code bug.

---

## D. Open Decisions — NOT YET MADE

- **QUANTITATIVE verifier architecture:** text+NLI fallback vs. stay UNVERIFIABLE. Unbuilt, blocks ~24% of every batch.
- **CITATION rebuild (Level 1):** dynamic bibliographic verification. Scoped, not started.
- **Injected-negative-example completion:** how many per type, hand-written vs. synthetic, for final evaluation set. Scoped, not executed.
- **Held-out test set for thesis numbers:** none of the current numbers should be reported as final. Still needed.
- **Entity-resolution bug fix:** Panama Canal / Rosetta Stone QID mismatch. Highest-priority unfixed bug. Affects TEMPORAL accuracy directly.

---

## E. Standing Methodological Commitments

- Gold labels are never nudged toward verifier output — only corrected where human judgment says the label itself was wrong.
- Cross-file consistency: always verify a doc's claims against raw data, not just accept the doc's self-report.
- Don't re-add RELATIONAL's page-relevance gate without prototyping first (tried twice, reverted twice, net-negative effect both times).
- Don't expand static property/org maps claim-by-claim as failures surface — only structural/architectural fixes.
- Temperature pinning is necessary but not sufficient for reproducibility — retrieval fragility is the next layer of instability.

---

## F. What to Actually Do Next

1. **Shift to entity-resolution bug fix** (not RELATIONAL anymore). Panama Canal / Rosetta Stone both have wrong QIDs. Affects TEMPORAL and EA accuracy directly. Diagnosis: "prefer first non-empty candidate" heuristic is wrong. Needs: either fix the QID-resolution scoring, or add a secondary validation pass to catch mismatches.
2. **Build QUANTITATIVE verifier** — still doesn't exist, blocks analysis of ~24% of all batches.
3. **Rebuild CITATION Level 1** — currently tautological on the dataset (all claims cite well-known orgs that are hardcoded TRUE).
4. **Design and execute injected-negative examples** for Phase 2 — currently 109 labeled claims but only 1 FALSE across all types except TEMPORAL.
5. **Construct held-out test set** — none of the current results are final-ready.

Priority: 1 > 2 > 3 > 4 > 5.

---

## Key Files to Have for Context

- `haldetect_discrepancies_handoff.md` — lists every ambiguity/bug found in earlier sessions.
- `haldetect_log_2026-08-09_consolidated.md` — the prior session's findings and contradictions (this session resolved most).
- `haldetect_phase2_goldlabeled__3_.csv` — the authoritative Phase 2 gold set (109 labels, TRUE-skewed).
- `relational_negatives_b3_merger_verified_results__1_.csv` — the final Phase 3e adversarial test output (20 claims, 3 runs).
- `1786277765077_Claude_chat-Verifying_factual_claims_across_multiple_domains-20260809-1815.md` — excerpt from prior chat that built the original 14-claim negative set and the initial findings.

---

## Files NOT to Trust Without Re-Checking

- `rel_verif_latest.txt` in the uploaded folder — contains the cache-poisoning bug unfixed. Use as a code template but apply both patches before running.
- Any `relational_verifier_phase2.py` without a date — the code may be stale relative to `rel_verif_latest.txt`.
- `haldetect_transfer_2026-08-02.md` — parts of it are now stale (RELATIONAL marked "not yet run" when it had been, CSV gold-fill status inaccurate).

---

## Tone Note

This project is **not** broken or at a dead end. It has real, replicated findings backed by deliberate adversarial testing. The author's earlier crisis-anxiety ("am I doing fake work?") was warranted as a gut-check but the answer is no — the work is sound. The next tasks are all buildable, known-scope work, not theoretical blockers.
