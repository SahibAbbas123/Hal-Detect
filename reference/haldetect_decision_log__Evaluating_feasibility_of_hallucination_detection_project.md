# HalDetect — Decision Log
*Extracted from: "Evaluating feasibility of hallucination detection project" chat*
*Date range: 2026-08-09 to 2026-08-20 (approximate)*

---

## Decision 1: Audit Prior Handoff Docs Against Raw Files

**Decision:**
Do not take prior transfer/handoff docs at face value; independently verify their claims against raw CSVs and execution logs before accepting any numbers or status.

**Why it was chosen:**
Author expressed crisis-level doubt about project viability. Rather than reassure, the right move was to verify the factual ground. Multiple docs claimed different things about the same files (RELATIONAL "not yet run" vs. verifier outputs showing it had been; Phase 2 gold labels "all filled" vs. CSV showing TEMPORAL/CITATION blank).

**Alternatives considered:**
- Accept docs at face value, move forward.
- Skim the CSVs casually without computational audit.

**Why alternatives were rejected:**
File-version confusion had already caused rework and lost context in prior sessions (sandbox resets). Casual inspection would miss subtle contradictions (e.g., "32 labels added" vs. actual 32 rows changed). Computational diff and row-by-row audit took 2 hours but prevented weeks of working with stale assumptions.

**Impact on future work:**
Established as a standing rule: cross-file consistency is checked first, not assumed. This prevents silent mismatches between docs and actual data. Every future claim about "which CSV is authoritative" now requires verification, not trust.

---

## Decision 2: Designate haldetect_phase2_goldlabeled__3_.csv as Authoritative

**Decision:**
Of three versions of the Phase 2 gold-labeled CSV, use `__3_` as the single source of truth for all downstream work. Retire the earlier versions from active use.

**Why it was chosen:**
Three versions existed; two had contradictory fill-states (TEMPORAL/CITATION columns blank vs. filled). Audit via superset-diff (`32 additions, 0 overwrites`) confirmed `__3_` was a strict superset of the original, with no silent label changes. This satisfies the project's own standing rule: corrections only from human judgment, never silent overwrites.

**Alternatives considered:**
- Merge all three versions by taking the union of all filled cells.
- Use the original (simpler, but missing 32 labels).
- Request the author re-export a fresh version.

**Why alternatives were rejected:**
Union merge would create ambiguity if the three versions disagreed on the *same* label (they didn't, but the risk was real). Original version was clearly incomplete. Re-export would have been correct but slow; we had the data already and the superset audit proved `__3_` was trustworthy.

**Impact on future work:**
All Phase 2 results now use a single, audited CSV, eliminating version-mismatch confusion. File labeling convention: append `__N_` to versioned files; the highest `N` is assumed newest unless the filename explicitly states otherwise.

---

## Decision 3: Independently Source-Verify Q18_C09 Against UNFCCC Article 4.1

**Decision:**
Do not rely on the prior chat's self-report that Q18_C09 (Paris Agreement / 2050) was deliberately marked FALSE. Web-search the actual UNFCCC treaty text to confirm.

**Why it was chosen:**
The prior chat's reasoning was specific and plausible, but "I marked this FALSE because the treaty says X" is a claim that needs verification, not trust. This is a thesis example; if cited, it must be defensible against scrutiny.

**Alternatives considered:**
- Accept the prior chat's reasoning at face value.
- Skip this claim as too low-priority to verify.

**Why alternatives were rejected:**
Thesis examples carry higher evidentiary standards than routine claims. A single verified example is worth more than three unverified ones. The web search took 10 minutes and returned six corroborating sources (NewClimate, WRI, ScienceDirect, UK gov, UNFCCC NDC, CLARA) all confirming Article 4.1 says "second half of this century," not 2050.

**Impact on future work:**
Q18_C09 is now a fully source-verified, citable example of "widely-repeated shorthand mistaken for primary source." Future examples should receive the same treatment: at least one primary source, no exceptions.

---

## Decision 4: Build Adversarial Negative-Injection Test for RELATIONAL After B3_10_C17 Miss

**Decision:**
Do not treat the glycogen-reversal miss (B3_10_C17 verified TRUE despite gold FALSE) as an isolated anecdote. Instead, build a controlled minimal-pair test to see if the error pattern is systematic or random.

**Why it was chosen:**
A single miss could be noise. But the miss was mechanistically explicable (BART-MNLI doesn't penalize directional reversals well). This suggested a specific failure mode, not random error. Adversarial testing at n=14-20 claims would either confirm the pattern or falsify it.

**Alternatives considered:**
- Log the miss and move on to other verifiers.
- Run a quick rerun on Batch 3 to see if the miss was reproducible.

**Why alternatives were rejected:**
Moving on would leave an unconfirmed mechanism. A rerun wouldn't answer the question "is this a RELATIONAL-specific NLI failure or a general problem?" Adversarial testing is the standard method for diagnosing systematic weaknesses.

**Impact on future work:**
Result: every dangerous TRUE (false positive on a FALSE claim) clustered in `temporal_condition` and `magnitude` injection types; zero from `negation`, `entity_swap`, `directional`, `comparative`. This pattern replicated across three independent runs. Finding is now publication-ready; need to write it up in thesis Chapter 5.

---

## Decision 5: Fix Cache-Poisoning Bug Before Re-Running RELATIONAL

**Decision:**
Do not run the expanded negative test without first patching the cache-poisoning bug in `_get_with_retry()` → `resolve_wikipedia_titles()` and `fetch_page_text()`.

**Why it was chosen:**
The bug was found during code review: both functions cached an empty result `[]` or `""` when retries were exhausted, indistinguishable from a genuine "no results" response. This poisons all future runs for the same query. If B3N_01 (glycogen) had hit this bug, the third run would silently trust the poisoned cache instead of retrying.

**Alternatives considered:**
- Ignore the bug; it's probably rare and will show up as noise in the results.
- Document the bug and file it for later fixing.
- Patch only one of the two functions (partial fix).

**Why alternatives were rejected:**
Rate-limiting hits (429s) are not rare; they happen regularly in Wikipedia retrieval. Leaving the bug unfixed would mean every future rate-limit event poisons the cache. Documenting-for-later is how bugs persist. Both functions must be patched symmetrically, not one.

**Impact on future work:**
All RELATIONAL runs going forward use the patched functions. Results are more trustworthy. Standing rule: verify cache behavior is correct before interpreting verdict changes across runs — they may reflect cache poisoning, not actual algorithm changes.

---

## Decision 6: Add Gemini API temperature=0 Pinning

**Decision:**
Patch the `generate_search_query()` function to include `"generationConfig": {"temperature": 0}` in the Gemini API call, matching the determinism principle used elsewhere (Ollama seed pinning).

**Why it was chosen:**
B3N_02 flipped from UNVERIFIABLE → TRUE → UNVERIFIABLE across runs. Investigation showed the Gemini query string itself was changing: `'Glycogen glycogenesis'` vs. `'glycogenolysis and glycogenesis'`. Different queries fetch different Wikipedia pages, producing different NLI verdicts. Temperature=0 is the standard LLM lever for reproducibility.

**Alternatives considered:**
- Accept that query generation is non-deterministic; document it as a limitation.
- Use a fixed prompt template instead of Gemini, avoiding the issue entirely.
- Cache the Gemini responses so the same query always gets the same answer.

**Why alternatives were rejected:**
Accepting non-determinism is reasonable for many tasks but not for reproducibility testing. Fixed templates lose the benefit of Gemini's adaptive query generation (it generates different queries for different claims). Response caching would work but doesn't fix the root cause (temperature variance); temperature=0 is more direct.

**Impact on future work:**
Query generation is now reproducible *given the same evidence pool*. However, the third run revealed retrieval-input instability persists even with temperature=0 (B3N_02 flipped again due to different Wikipedia pages being returned). This is a deeper instability that temperature=0 alone cannot fix. Standing rule: reproducibility requires both query pinning AND retrieval pinning (caching or deterministic ranking).

---

## Decision 7: Shift Priority from RELATIONAL to Entity-Resolution Bug

**Decision:**
After closing RELATIONAL (negative-injection test is done, findings are clear), the next task is NOT QUANTITATIVE or CITATION but entity-resolution bug fix (Panama Canal / Rosetta Stone QID mismatches).

**Why it was chosen:**
Both TEMPORAL and EA have confirmed bugs from the same root cause: the "prefer first non-empty candidate" QID-resolution heuristic is wrong. Panama Canal (opened 1914) resolved to Q498979 (1903 date). Rosetta Stone resolved to Q4048553, fetching wrong value "Porl King." These are high-confidence errors producing wrong verdicts, not just low coverage.

**Alternatives considered:**
- Finish QUANTITATIVE first (blocks 24% of Batch 3).
- Do CITATION rebuild (structurally broken, all hardcoded orgs).
- Continue with Phase 2 analysis.

**Why alternatives were rejected:**
QUANTITATIVE and CITATION are important but affect fewer claims; entity-resolution affects TEMPORAL and EA, which together cover ~30% of all batches. The bug produces actively wrong answers, not just gaps. Fixing it will likely raise both verifiers' accuracy by 10-15 percentage points.

**Impact on future work:**
Entity-resolution becomes the critical path for improving overall accuracy. Fix needs either (a) better QID-disambiguation scoring, or (b) secondary validation pass (e.g., check if fetched property makes sense for the claim). Work on this should begin before final thesis numbers are run.

---

## Decision 8: Do NOT Re-Add RELATIONAL's Page-Relevance Gate

**Decision:**
Explicit standing commitment: the page-relevance gate (drop candidate pages if title/intro shares no keywords with claim) is NOT to be re-attempted without full prototyping first. This decision overrides any future impulse to add it back.

**Why it was chosen:**
The gate was tried twice in prior sessions, both times with net-negative effect on accuracy and coverage. First attempt missed its target (generic domain words like "mental" and "health" passed the gate regardless), introducing new regressions (debt-crisis claim flipped from correct TRUE to UNVERIFIABLE). Second attempt had similar results.

**Alternatives considered:**
- Try a third time with tweaked heuristics.
- Accept that page-relevance filtering is necessary and iterate on it.

**Why alternatives were rejected:**
Two independent runs with net-negative results is strong evidence the approach itself has a ceiling. Adding more heuristics (stricter keywords, semantic matching, etc.) would make the code harder to debug without improving results. Better to live with some tangential pages in the pool than filter out legitimate pages.

**Impact on future work:**
If ranking instability persists and manifests as tangential pages dominating the passage pool, the correct fix is to improve SBERT ranking, not to add a gate. This principle extends to similar "filter early" temptations: do not filter at architecture level without evidence that filtering solves the problem.

---

## Decision 9: Treat Retrieval-Input Instability as Structural, Not Query-Variance

**Decision:**
After B3N_02 flipped on run 3 despite temperature=0 pinning, interpret this as evidence that retrieval-input instability is structural (Wikipedia search results themselves are non-deterministic), not merely a Gemini variance issue.

**Why it was chosen:**
The fact that temperature=0 did *not* stop the flip is the key evidence. If query variance was the root cause, pinning temperature should have fixed it. But different passages were retrieved, suggesting the Wikipedia search API itself returns different results across calls, or SBERT ranking is sensitive to small differences in input (model initialization, device state, etc.).

**Alternatives considered:**
- Assume the temperature=0 fix didn't actually work; try pinning it more aggressively.
- Accept that some run-to-run variance is inevitable and report results with confidence intervals.

**Why alternatives were rejected:**
The temperature=0 code change was correct and confirmed in the API call. The flip happened anyway. The most parsimonious explanation is that retrieval, not query generation, is the unstable layer. Trying to pin temperature more aggressively would not fix Wikipedia's own non-determinism.

**Impact on future work:**
Reproducibility at the RELATIONAL level requires either (a) freezing the cache (every run reads from a fixed cache, no fresh fetches), or (b) accepting that verdict precision has a floor due to retrieval variance. For final thesis numbers, use frozen cache runs. For generalization testing, document the variance as a limitation.

---

## Decision 10: Accept Phase 2 Gold Set Despite TRUE-Skew (109 labels, 1 FALSE)

**Decision:**
Use `haldetect_phase2_goldlabeled__3_.csv` as the Phase 2 working set despite heavy TRUE-skew (only Q18_C09 is FALSE across RELATIONAL, EA, TEMPORAL, CITATION combined).

**Why it was chosen:**
109 labels is a meaningful dataset size for development. The TRUE-skew is a real limitation but is documented and flagged for future work (injected negatives needed). Holding the Phase 2 set until perfect label balance exists would delay progress indefinitely.

**Alternatives considered:**
- Wait and add more hand-labeled FALSE examples to Phase 2 before using it.
- Use only Batch 3 (which has better balance: 115 TRUE, 4 FALSE, 3 UV) for all Phase 2 work.

**Why alternatives were rejected:**
Hand-labeling more Phase 2 examples would be slow; the author is sole annotator. Using only Batch 3 would discard 126 claims. The right approach is proceed with Phase 2 as-is, but plan for injected negatives in a separate step (planned for task 4 in F).

**Impact on future work:**
Phase 2 results are usable for development but may overestimate precision on TRUE claims. Final thesis results must use a separate, balanced held-out test set before reporting accuracy/coverage numbers.

---

## Summary of Standing Rules Derived From Decisions

1. **Verify before trust:** Cross-check doc claims against raw data. File versions are never trusted without audit.
2. **Specificity matters:** Single-example anecdotes are cited only if independently verified against primary sources.
3. **Mechanism > pattern:** When a failure is mechanistically explicable, build an adversarial test to confirm it's systematic, not noise.
4. **Don't patch symptoms:** Bugs get fixed at root cause. Filtering queries (page-relevance gate) is a symptom; improving ranking is the root.
5. **Reproducibility is layered:** Pinning one layer (query temperature) is necessary but not sufficient; retrieval and ranking are also layers.
6. **Gold labels are sacred:** No silent overwrites, no nudging toward verifier output. Only human judgment corrects labels.
7. **Gaps are tolerable; errors are not:** TRUE-skew (missing FALSE examples) is acceptable if flagged. Active hallucinations (wrong verdicts) from the verifier are priority fixes.

