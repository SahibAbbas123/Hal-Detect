# archive/

Superseded, duplicate, or historical-draft files, moved here 2026-08-21 after direct content fingerprinting (not filename guessing). Nothing here was deleted — everything is fully reversible. See `../WORKSPACE_AUDIT.md` for the evidence behind each disposition.

## scripts/
Standalone `.py` verifiers, all confirmed superseded by logic that now lives inside `../current/HalDetect_latest.ipynb`:
- `relation_verifier.py` — the original Phase 1 SBERT-ranking prototype (`run_phase1_test`).
- `temporal_verifier.py` — an intermediate TEMPORAL snapshot; has P800 handling but lacks the retry/backoff logic (`_get_with_retry`, `MAX_RETRIES`, `BASE_BACKOFF_SECONDS`) present in the notebook's current cell.
- `relational_verifier_phase3d.py` — matches notebook cell 42 (`## Phase 3d`) exactly, 7 phase-iterations behind the current cell 57 (`## Phase 3e (i)`).

## csvs/
- `haldetect_phase2_goldlabeled.csv`, `(1).csv`, `(2).csv` — older/partial Phase 2 gold labeling (64, 77, and 109-but-duplicate-of-current fill counts respectively). `(2)` is byte-identical to the current `(3)`.
- `relational_negatives_batch3.csv` (the "base" set, 20 rows, IDs B3N_01–20) — archived as input; its content is fully preserved inside `relational_negatives_batch3_merged.csv` in `../current/`.
- `relational_negatives_batch3_expansion.csv` — pure subset/duplicate of `base` (same IDs B3N_15–20, same content).
- `relational_negatives_batch3_round2.csv` — historical draft from a separate chat session with a confirmed ID collision against `base` (B3N_15/16 reused for different content). 6 of its 8 claims are already folded into the current merged set under new IDs 21–27 with results already run; the 7th (B3N_15, "Aral retained ~90%") is a reworded duplicate of `base`'s B3N_17. Nothing unverified or unique remains here — kept for audit trail only.
- `relational_negatives_b3_verified_results.csv` / `(1).csv` — earlier verified-results runs (14 and 20 rows) against the negatives set before it reached its final 27-row merged state.
- `relational_negatives_b3_merger_verified_results.csv` — **explicitly preserved** pre-temperature-fix result (60% accuracy) against the final 27-row merged set. Its post-fix sibling (66.67%) is the current one, in `../current/`. Kept intentionally as reproducibility-comparison evidence, not a superseded leftover.
- `haldetect_claims_20260524_043744.csv`, `haldetect_claims_20260524_045439.csv`, `haldetect_claims_20260524_045439_1.csv`, `haldetect_claims_20260524_045439_2.csv` — an early May/June extraction-batch lineage, unrelated to the current Phase 2/Batch 3 gold system. `_1`/`_2` are 100%-filled but predate the phase-based methodology entirely.
- `haldetect_claims_20260726_173737.csv` (124 rows) — first, buggy Batch 3 raw pipeline run (bare `pair_id`, no `pair_incomplete` column, per the fingerprint rule).
- `haldetect_claims_20260731_173625.csv` (114 rows) — intermediate corrected Batch 3 raw run (prefixed `pair_id`, still no `pair_incomplete`).
- `haldetect_claims_phase2_20260607_185447.csv` — raw, pre-labeling precursor to the `haldetect_phase2_goldlabeled*` family.
- `haldetect_verified_temporal.csv` — a fully-verified output from the pre-Phase2/B3 May/June lineage; not referenced anywhere in the current notebook.

- `haldetect_claims_20260731_175241.csv` — the final corrected Batch 3 raw pipeline run (122 rows, prefixed `pair_id`, has `pair_incomplete`, no `gold_verdict` filled). Row count matches `haldetect_claims_b3_gold.csv` exactly — almost certainly the direct raw precursor the gold set was hand-labeled from. Briefly misfiled in `../reference/` (which is meant to hold only handoff/context docs, not claim data) — moved here where the rest of the claims-data lineage lives.

- `entity_attribute_verified_results_v2.csv`, `temporal_verified_results_v2.csv`, `relational_phase2_verified_results.csv` — older Phase 2-era verified-results runs, superseded by the current Batch 3 results in `../current/`.
- `haldetect_claims_b3_triaged.csv`, `haldetect_claims_phase2_triaged.csv` — mid-pipeline triage states (`triage_flag`/`triage_reason` present, `gold_verdict` still blank), not final.
- **`rel_verif_b3_code+output.txt` — ⚠️ NOT just a run log.** This is the evidentiary source used to independently confirm RELATIONAL's headline Batch 3 numbers (80.77% acc / 55.32% cov). **Do not delete or overwrite this file.** Archived for organization only — treat it as load-bearing for any thesis claim citing those numbers.
- `relational_verifier_test_runs.txt` — ordinary run log, no special status.

## caches/
- `relational_cache_root_2026-06-21.json` / `relational_cache_latest_2026-07-13.json` — two same-named `relational_cache.json` files (one from the project root, one from `latest/`) from the pre-split single-cache design, renamed with a source+date suffix to avoid collision. Superseded by the two-cache (retrieval + NLI) split used by the current verifier.
- `relational_retrieval_cache.json` / `(1).json`, `relational_nli_cache.json` / `(1).json` — older generations of the current cache pair (`(2)` versions, in `../current/`), superseded by mtime.
- `verifier_cache.json` — stale, June-dated, predates all the August relational work.

## notebooks/
`test.ipynb`, `llm_client.ipynb`, `Semantic_Embedding_Experiment.ipynb`, `haldetect_LLM_response_atomization_class.ipynb` — none referenced anywhere inside `HalDetect_latest.ipynb` (checked via full-text search for filenames/imports). Draft/experimental notebooks, archived at user's confirmation.

## experiments/
Orphaned experiment artifacts (confirmed zero references in the current notebook), old run logs, and build byproducts — archived rather than deleted, per the project's own audit instructions ("do not delete anything without approval, even obvious junk"):
- `embeddings_1.npy`, `embeddings_2.npy`, `pipeline_results.json`, `similarity.py` — unreferenced anywhere in the current pipeline.
- `main`, `currentcode.txt`, `verifier_setup.txt`, `test_results.txt`, `llm_client.txt` — early scaffolding/terminal-transcript logs, unrelated to the current SBERT/Gemini/Wikidata approach.
- `test.aux`, `test.fdb_latexmk`, `test.fls`, `test.log`, `test.pdf`, `test.synctex.gz` — LaTeX build artifacts; no `.tex` source exists anywhere in this workspace, so `test.pdf` is not regeneratable and was archived rather than treated as pure build litter.
- `__pycache__/` — regenerated bytecode for the (now-archived) stale `citation_verifier.py`/`temporal_verifier.py` snapshots.
