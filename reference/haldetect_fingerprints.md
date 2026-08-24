# Chat: Verifying factual claims across multiple domains

**Created:** 7/19/2026 13:12:45  
**Updated:** 8/20/2026 14:36:27  
**Exported:** 8/20/2026 14:39:59  
**Link:** [https://claude.ai/chat/f1b941ab-8251-48c1-9d14-deb409b2c52c](https://claude.ai/chat/f1b941ab-8251-48c1-9d14-deb409b2c52c)  
**Chat Name:** Verifying factual claims across multiple domains

## User:

> 8/20/2026 14:35:26

i keep forgetting which versions of a file i have. e.g: which csv is of phase 2, which is of phase 3, which script of rel_verif is of phase 2 - and so on. can you point out unique parts/attributes which when i see (or say, an llm sees) can say that this is latest, or belongs to 'x-th' iteration etc

## Assistant:

> 8/20/2026 14:36:27

> Synthesized version markers across scripts and CSVs for instant identification.
>
> - Synthesized version markers across scripts and CSVs for instant identification.
> - **Done**

Good instinct — here's a fingerprint table you (or a fresh LLM) can use to identify any file in seconds, without needing to read the whole thing.

## Verifier scripts

| File family          | Version                                          | Grep for this (presence = this version)                                                          | Also check                                                                                               |
| -------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| **RELATIONAL**       | Original/Phase 3d                                | `"PHASE 3D"` in docstring                                                                        | Single cache file `relational_cache.json`, no `MIN_MARGIN` constant                                      |
|                      | v2 with the reverted gate (**do not use**)       | `page_is_relevant` function                                                                      | Has `STOPWORDS` set, `_claim_keywords` function                                                          |
|                      | v2 final/correct                                 | `"TRIED AND REVERTED"` in docstring                                                              | Two cache files: `relational_retrieval_cache.json` + `relational_nli_cache.json`                         |
| **ENTITY_ATTRIBUTE** | v1 (original)                                    | Absence of `SentenceTransformer` import                                                          | `INPUT_CSV` hardcoded string, no `sys.argv`                                                              |
|                      | v2, pre-secondary-fix (**do not use — 50% acc**) | `def compare_attribute(claimed_val, wd_values):` — exactly 2 params                              | No `_parse_secondary` function anywhere                                                                  |
|                      | v2, final/correct (**87.5% acc**)                | `_parse_secondary` function present                                                              | `compare_attribute(..., secondary=None)` — 3 params                                                      |
| **TEMPORAL**         | v1 (original, **do not use**)                    | `"patent office"` string literal anywhere in the file                                            | Bare `except: return None` style (no retry logic)                                                        |
|                      | v2 final/correct                                 | `_get_with_retry` function present                                                               | `MAX_RETRIES` / `BASE_BACKOFF_SECONDS` constants defined                                                 |
| **Pipeline**         | v1 (original)                                    | `atomize()` returns bare strings — check: does the function have a return type hint `list[str]`? | Few-shot examples mention "Einstein"/"Tesla"/"Lehman Brothers"                                           |
|                      | v2, before pair_id fix (**collision bug**)       | `"pair_id": pair_id or ""` (no q_id prefix)                                                      |                                                                                                          |
|                      | v2, current/correct                              | `"pair_id": f"{q_id}_{pair_id}"`                                                                 | `pair_incomplete` field present; few-shot examples mention "Berlin Wall"/"Amazon River"/"Saturn" instead |

## CSVs — check row counts and fill patterns, not filenames (filenames get renamed/reused)

| File family                     | Fingerprint check                                                                           | What it tells you                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 2 gold-labeled**        | Count non-blank `gold_verdict` cells, broken down by `type`                                 | **109/126 filled, exact split RELATIONAL 64/64, EA 13/13, TEMPORAL 26/26, CITATION 6/6, QUANTITATIVE 0/17 = current correct version.** Anything less (esp. TEMPORAL=0 or CITATION=0) = stale.                                                                                                                                                        |
|                                 | Check `Q18_C09`'s `gold_verdict` specifically                                               | Should be `FALSE` (deliberate exception). If blank or `TRUE` → stale/pre-fix copy.                                                                                                                                                                                                                                                                   |
| **Batch 3 raw pipeline output** | Search any `pair_id` value — does it lack a `B3_XX_` prefix (e.g. bare `citation_pair_01`)? | If yes → first, buggy run (124 rows). If all prefixed → corrected run (122 rows).                                                                                                                                                                                                                                                                    |
|                                 | Column list: is `pair_incomplete` present?                                                  | Presence = corrected/current run.                                                                                                                                                                                                                                                                                                                    |
| **Batch 3 triaged**             | Has `triage_flag`/`triage_reason` columns, but `gold_verdict` still blank                   | Mid-pipeline state, not final.                                                                                                                                                                                                                                                                                                                       |
| **Batch 3 gold**                | Count filled `gold_verdict`: should be exactly 122/122                                      | Breakdown should be exactly 115 TRUE / 4 FALSE / 3 UNVERIFIABLE. Any other count = incomplete or wrong copy.                                                                                                                                                                                                                                         |
| **Negatives CSV**               | Row count: 14, or 20, or 8 (separate file)?                                                 | 14 = my round 1 only. 20 = round 1 + _your_ independent expansion (B3N_15-20, Panama->100yrs / coral-shortest / Aral-<10% / OECD-same-fiscal-year content). A separate 8-row file = _my_ round 2 (different B3N_15-22 content: Aral-90%-retained / OECD-Gini-2-of-34 / etc.) — **these two round-2 sets are still unmerged as of the last session.** |

## The one universal rule, if you remember nothing else

**Never trust a filename or a doc's description of a file — always check the file's own row count + a specific fill pattern or grep hit.** This exact confusion (stale scripts re-uploaded, CSVs a doc claimed were complete but weren't) has been the single biggest source of wasted effort across this whole project — it's already written into the standing methodological commitments in the start-here doc for exactly this reason.

Want this saved as its own reference file (`haldetect_fingerprints.md`) so it travels with the project the same way the other logs do?

Powered by Claude Exporter (https://www.ai-chat-exporter.net)
