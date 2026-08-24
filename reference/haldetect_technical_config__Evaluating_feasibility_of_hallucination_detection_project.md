# HalDetect — Technical Configuration Sheet
*Extracted from: "Evaluating feasibility of hallucination detection project" chat*
*Date range: 2026-08-09 to 2026-08-20 (approximate)*

---

## Environment

**Execution:**
- Platform: Google Colab (with local Ollama access)
- Python: 3.x (version unspecified, assume 3.9+)
- Fallback: Ubuntu 24 Linux container (for bash tool tasks)

**LLM Inference:**
- Local: Ollama + Gemma 4 31B (for code generation, fact extraction in earlier phases)
- API: Gemini 3.1 Flash Lite Preview (`gemini-3.1-flash-lite-preview`) via Colab userdata secrets

**Libraries & Models:**
- Sentence embeddings: `sentence-transformers` / `all-MiniLM-L6-v2` (384-dim embeddings)
- NLI: `transformers` / `facebook/bart-large-mnli` (zero-shot classification for entailment/contradiction/neutral)
- Wikipedia retrieval: `requests` library, Wikipedia API v1 (en.wikipedia.org/w/api.php)
- Knowledge source: Wikidata SPARQL endpoint, CrossRef API (for CITATION verifier, not yet fully built)
- Data: `csv` (standard library), `json` (for caching)

---

## Project Structure

| File/Module | Purpose | Status | Notes |
|---|---|---|---|
| `haldetect_pipeline.py` | Main extraction pipeline (v1) | Superseded | Silent-failure bugs; replaced by v2 |
| `haldetect_pipeline_v2.py` | Main extraction pipeline (v2) | Stable | User has copy locally; applies 5 fixes to v1 |
| `temporal_verifier_v2.py` | TEMPORAL claim verifier | Partial | 75% acc / 15.4% cov on Phase 2; P800 two-hop bug unfixed |
| `entity_attribute_verifier_v2.py` | EA claim verifier | Stable | 87.5% acc / 61.5% cov on Phase 2 (unconfirmed via execution); 0% on held-out |
| `relational_verifier_phase2.py` | RELATIONAL verifier (snapshot) | Stale | Check against `rel_verif_latest.txt` for current code |
| `rel_verif_latest.txt` | RELATIONAL verifier Phase 3e (h) | Code template | Contains cache-poisoning bug in both functions; apply patches before use |
| `citation_verifier.py` | CITATION verifier | Broken | Hardcoded org maps; 0% coverage on Batch 3 |
| `taxonomy_rules.md` | Claim extraction/classification rules | Reference | Specifies 5 types, dual-emit tagging, property vocabularies |

**Data Files (CSVs):**

| File | Rows | Gold Labels | Type | Status |
|---|---|---|---|---|
| `haldetect_phase2_goldlabeled__3_.csv` | 126 | 109/126 | Phase 2 working set | **Authoritative** (superset-audited) |
| `haldetect_claims_b3_gold.csv` | 122 | 122/122 | Batch 3 gold | Confirmed (MD5, row-by-row verified) |
| `relational_negatives_batch3.csv` | 14 | 14/14 | RELATIONAL adversarial | Minimal-pair negative injections |
| `relational_negatives_batch3_expansion.csv` | 6 | 6/6 | RELATIONAL adversarial | Extended minimal-pairs (3+3) |
| `relational_negatives_b3_merger_verified_results.csv` | 20 | 20/20 | RELATIONAL output (run 2) | 60% acc / 40% cov (cached) |
| `relational_negatives_b3_merger_verified_results__1_.csv` | 20 | 20/20 | RELATIONAL output (run 3) | 66.67% acc / 33.33% cov (fresh cache) |

**Caches:**

| File | Content | Size | Notes |
|---|---|---|---|
| `relational_retrieval_cache.json` | Wikipedia titles, page texts, Gemini queries | 447+ lines | Freeze after validation; clear only specific prefixes for logic changes |
| `relational_nli_cache.json` | NLI scores (entail/contradict) per passage | 885+ lines | Separate from retrieval; safe to iterate on NLI thresholds alone |
| `verifier_cache.json` | Small reference cache | — | Contains Panama Canal (Q498979) and Rosetta Stone (Q4048553) entries |

---

## Data

**Input Corpus:**
- Phase 1: 125 cross-domain claims (Einstein/quantum/CDC vaccines, held-out for generalization testing)
- Phase 2: 126 LLM-generated claims (prompts from FActScore-priv dataset, domain-specific)
- Batch 3: 122 LLM-generated claims (FActScore-priv, synthesized for diversity)
- Adversarial set: 20 minimal-pair injections (natural RELATIONAL claims with 1 element inverted per pair)

**Preprocessing:**
- Atomization: LLM-generated paragraph → sentence-level claims
- Deduplication: duplicate-detection filter on extracted claims
- Drift detection: flagged claims with suspicious atomization patterns (known: 17/122 in Batch 3, likely false positives)
- Type classification: LLM + heuristic rules (taxonomy_rules.md)
- Structure extraction: subject, property, value, secondary fields

**Features:**
- Claim text (raw)
- Claim ID (q_id + claim_id within paragraph)
- Type (CITATION / TEMPORAL / QUANTITATIVE / ENTITY_ATTRIBUTE / RELATIONAL)
- Subject, property, value, secondary (structured extraction; optional fields)
- Synthetic flag (True if injected, False if natural)
- Injection type (only for synthetic: temporal_condition, magnitude, negation, entity_swap, directional, comparative)
- Gold verdict (TRUE / FALSE / UNVERIFIABLE; only for labeled data)

---

## Implementation Details

### RELATIONAL Verifier (Phase 3e, Latest)

**Retrieval:**
- Query source: LLM-generated via Gemini (`generate_search_query()`)
- Query generation: uses Gemini 3.1 Flash Lite with `temperature: 0`
- Candidates: SEARCH_CANDIDATES = 3 pages per query
- Fallback: also fetch page for raw `subject` field if different from query

**Ranking:**
- Model: Sentence-BERT (`all-MiniLM-L6-v2`)
- Passages pooled: TOP_K_PASSAGES = 5 (after similarity ranking)
- Threshold: MIN_PASSAGE_SCORE = 0.45 (passages below this are dropped)
- Deduplication: identical passages from different pages are merged

**NLI Verdict:**
- Model: BART-MNLI (`facebook/bart-large-mnli`)
- Thresholds: ENTAIL_THRESHOLD = 0.55, CONTRADICT_THRESHOLD = 0.45
- Margin requirement: MIN_MARGIN = 0.15 (entail must beat contradict by this much)
- Decision rule: 
  - TRUE if `entail >= 0.55` AND `margin >= 0.15`
  - FALSE if `contradict >= 0.45` AND `margin <= -0.15`
  - UNVERIFIABLE otherwise

**Retry/Backoff:**
- MAX_RETRIES = 4
- BASE_BACKOFF_SECONDS = 2.0 (exponential: 2s, 4s, 8s, 16s)
- Rate limit: respects Wikipedia 429 errors

**Caching:**
- Retrieval cache: `relational_retrieval_cache.json` (titles, texts, Gemini queries)
- NLI cache: `relational_nli_cache.json` (entail/contradict scores)
- Separate caches allow freezing retrieval while iterating on NLI thresholds

**Cache Poisoning Fix (Phase 3e.i):**
- Bug: `_get_with_retry()` returns None on retry exhaustion; calling functions cached empty `[]` or `""` anyway
- Fix: check `if data is None:` before caching; return empty without cache save
- Both `resolve_wikipedia_titles()` and `fetch_page_text()` require patching

### TEMPORAL Verifier (v2)

**Thresholds:**
- Entity resolution: multi-candidate (top 3)
- Date parsing: regex + Wikidata property lookup (P585 "point in time", P580 "start time", P582 "end time")

**Known Bugs:**
- P800 ("notable work") two-hop lookup only special-cased for publications (P577), not inventions
- Missing property mappings: ~81% unmapped on Phase 2 own gold set
- Einstein/Patent-Office fuzzy-synonym handler only fires on "intellectual property" string

### ENTITY_ATTRIBUTE Verifier (v2)

**Property Mapping:**
- PROPERTY_TO_WIKIDATA: hardcoded dict of claim-property strings to Wikidata property IDs
- Unmapped properties: return UNVERIFIABLE (no fallback)
- Known ceiling: 0/8 coverage on cross-domain held-out test (property generalization limit)

**Matching:**
- Entity resolution: multi-candidate resolution via SBERT semantic matching
- Secondary field context folding: uses secondary_field column to disambiguate

**Known Bugs:**
- QID resolution: "prefer first non-empty candidate" heuristic is wrong
  - Panama Canal: should resolve to Q1529 (the canal itself), resolves to Q498979 (1903 treaty)
  - Rosetta Stone: should resolve to Q6463, resolves to Q4048553 (wrong value "Porl King")

### CITATION Verifier (v1)

**Status:** Broken, not fixed this session.

**Issues:**
- ORG_URL_MAP: one hardcoded URL per org regardless of claim topic
- TRIVIALLY_KNOWN_ORGS: static ~15-org list (IEA/OECD/FAO/UNESCO/World Athletics all absent)
- Dual-emit pairing: ~9% success rate (1/11 tagged groups in Batch 3 actually matched)

**Proposed fix (not built):** dynamic search-based source confirmation (same multi-candidate retrieval as RELATIONAL)

### QUANTITATIVE Verifier

**Status:** Does not exist. Blocks ~24% of all batches from being CHECKABLE.

**Design decision pending:** text+NLI fallback vs. stay UNVERIFIABLE architecture.

---

## Current Errors / Issues

| Issue | Scope | Priority | Status |
|---|---|---|---|
| Entity-resolution QID mismatch (Panama Canal Q498979, Rosetta Stone Q4048553) | TEMPORAL, EA | **CRITICAL** | Unfixed; produces actively wrong verdicts |
| TEMPORAL P800 two-hop date lookup | TEMPORAL | High | Unfixed; false negatives on invention dates |
| Retrieval-input instability (even with temperature=0) | RELATIONAL | High | Documented; inherent to non-deterministic Wikipedia/ranking |
| CITATION verifier broken (0% coverage) | CITATION | High | Needs rebuild with dynamic source confirmation |
| QUANTITATIVE verifier nonexistent | QUANTITATIVE | Medium | Blocks analysis, but lower priority than entity-resolution |
| Phase 2 gold set TRUE-skew (only 1 FALSE / 109 labels) | Evaluation | Medium | Planned: injected negatives for balanced testing |

---

## Reproduction Steps

### Run RELATIONAL Verifier (Phase 3e.i, After Fixes)

**Prerequisites:**
1. Apply cache-poisoning fix to `rel_verif_latest.txt` (patch both `resolve_wikipedia_titles()` and `fetch_page_text()`)
2. Apply Gemini temperature=0 fix to `generate_search_query()` API call
3. Prepare input CSV (e.g., `relational_negatives_b3_merger_verified_results.csv` — 20 rows, RELATIONAL type)
4. Colab secrets: GEMINI_API_KEY must be set

**Steps:**
1. `retrieval_cache = load_json_cache(RETRIEVAL_CACHE_FILE)`
2. `nli_cache = load_json_cache(NLI_CACHE_FILE)`
3. For each row in CSV:
   - Call `verify_relational(row, retrieval_cache, nli_cache)`
   - Populate `verified_verdict`, `verified_evidence`, `verified_conf`
4. `evaluate_relational(all_rows)` — prints accuracy/coverage breakdown
5. Write output CSV with verdicts

**Cache management:**
- For reproducibility testing: use existing frozen cache (both files)
- For fresh runs: delete both cache files before running
- For NLI-only iterations: freeze retrieval cache, delete NLI cache only

### Extract Phase 2 Claims

1. Use `haldetect_pipeline_v2.py` with FActScore-priv questions as input
2. Output: `haldetect_claims_phase2_20260607_185447.csv` (126 unlabeled rows)
3. Triage: filter to `haldetect_phase2_annotation_ready.csv` (69 CHECKABLE rows)
4. Gold-label: use `haldetect_phase2_goldlabeled__3_.csv` (109/126 labeled)

---

## Parameter Summary (For Quick Reference)

| Parameter | Value | Module | Notes |
|---|---|---|---|
| SEARCH_CANDIDATES | 3 | RELATIONAL retrieval | pages per query |
| TOP_K_PASSAGES | 5 | RELATIONAL ranking | final passage pool |
| MIN_PASSAGE_SCORE | 0.45 | RELATIONAL ranking | similarity threshold |
| ENTAIL_THRESHOLD | 0.55 | RELATIONAL NLI | decision threshold |
| CONTRADICT_THRESHOLD | 0.45 | RELATIONAL NLI | decision threshold |
| MIN_MARGIN | 0.15 | RELATIONAL NLI | entail must beat contradict by this |
| MAX_RETRIES | 4 | Retrieval retry | Wikipedia API backoff |
| BASE_BACKOFF_SECONDS | 2.0 | Retrieval retry | exponential backoff base |
| SBERT_MODEL | all-MiniLM-L6-v2 | Ranking | embedding model |
| NLI_MODEL | facebook/bart-large-mnli | Verdict | entailment classifier |
| GEMINI_MODEL | gemini-3.1-flash-lite-preview | Query generation | LLM for adaptive queries |
| Gemini temperature | 0 | Query generation | reproducibility pinning |

