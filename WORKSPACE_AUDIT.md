# HalDetect Workspace Audit Report
**Generated:** 2026-08-21 · **Reorganization executed 2026-08-21 — see "Execution Summary" at the bottom of this doc.**

## Method
For every file family, the row-count / grep-marker fingerprints from `haldetect_fingerprints.md` were checked against actual file content — not filenames, not `(1)/(2)/(3)` suffixes. Where the notebook (`latest/HalDetect_latest.ipynb`, 72 cells, 2.9 MB) was the more likely source of truth, its cells were parsed directly (not just full-text grep) to find which cell actually defines the live version of each verifier, using the notebook's own `## Phase N` markdown headers as the timeline. Two real discrepancies against `haldetect_fingerprints.md` turned up — flagged explicitly below rather than silently resolved.

---

## 1. RELATIONAL verifier — resolved

The notebook's "Relation Verifier" section (cells 28–57) contains **13 successive in-place edits** of the same functions, one per markdown phase header: Phase 1 → 2 → 3a → 3b → 3c → 3d → 3e → 3e(b) → 3e(c) → 3e(f) → 3e(g) → 3e(h) → **3e(i)**.

- **Live/current = cell 57**, under header `## Phase 3e (i)`. It is the *only* cell in this chain with a non-null `execution_count` (2), and it's the only one containing all three v2-final fingerprint markers together: `generationConfig: {"temperature": 0}`, `if data is None:` guards, and `"TRIED AND REVERTED"` in its docstring.
- **Root file `relation_verifier.py`** (268 lines) matches cell 30 / "Phase 1" — the original SBERT-ranking prototype (`run_phase1_test`), far behind current. No v2 markers present at all.
- **`latest/relational_verifier_phase3d.py`** matches cell 42 / "Phase 3d" exactly (contains `"PHASE 3D"`, nothing else) — a mid-pipeline snapshot, 7 phases behind the notebook's current cell 57.
- **Conclusion: the current RELATIONAL logic exists only inside the notebook (cell 57). No standalone `.py` file is up to date.**

## 2. TEMPORAL verifier — resolved, with a fingerprint-doc discrepancy

The notebook has only **one** Temporal cell (71, under `## Phase 1` — no Phase 2/3 sections exist here, unlike Relational/Entity-Attribute).

- Cell 71 contains **both** `"patent office"` (1 hit — the exact string `haldetect_fingerprints.md` calls an exclusive "v1, do not use" marker) **and** the full v2 machinery: `_get_with_retry` (5), `MAX_RETRIES`/`BASE_BACKOFF_SECONDS` (3 each), `P800` special-casing (4), and multi-candidate resolution (`candidates` × 9).
- **Discrepancy vs. `haldetect_fingerprints.md`:** that doc treats `"patent office"` as mutually exclusive with the retry/backoff v2 markers. In the actual file, they coexist — `"patent office"` is just a leftover domain-example string still present in the current, fully-upgraded cell. **Trust the file: cell 71 is current TEMPORAL, despite carrying the "v1" string.**
- **Root file `temporal_verifier.py`** (226 lines) has `"patent office"` but **lacks** `_get_with_retry`/`MAX_RETRIES`/`BASE_BACKOFF_SECONDS` entirely — so unlike the notebook cell, the root `.py` really is the older, pre-retry-logic version. It does already have P800 handling and the "two-step jump" comment, so it's not the original v1 either — it's an intermediate snapshot, superseded by notebook cell 71.

## 3. ENTITY_ATTRIBUTE verifier — resolved

Notebook section (cells 58–67): Phase 1 (60) → Phase 2 (62, then rewritten in-place at 65) → **Phase 3 "Slightly Updated" (67)**.

- Cells 65 and 67 both contain `_parse_secondary` and the 3-param `compare_attribute(claimed_val, wd_values, secondary=None)` — both look "v2-final" by the fingerprint doc's criteria alone. Diffing them directly shows cell 67 is a strict superset: it adds the full "SECONDARY-FIELD CONTEXT" fix (item 4 in its own changelog docstring) that cell 65 doesn't have, and it sits after the `## Phase 3` header.
- **Live/current = cell 67.**
- No standalone `.py` file for this verifier exists anywhere in the workspace (root or `latest/`) — it lives in the notebook only.

## 4. CITATION verifier

No "Citation Verifier" section exists anywhere in the notebook (72 cells fully enumerated). **`citation_verifier.py` (root, 23,394 bytes) is the only copy that exists**, standalone, matching audit.md's note "CITATION script (even if broken)." Nothing to reconcile — this file is unambiguously the one to keep.

## 5. Phase 2 gold-labeled CSV — resolved

| File | Rows | `gold_verdict` filled | Breakdown | Q18_C09 |
|---|---|---|---|---|
| `latest/haldetect_phase2_goldlabeled.csv` | 126 | 64 | RELATIONAL 64 only | n/a (blank) |
| `latest/haldetect_phase2_goldlabeled (1).csv` | 126 | 77 | RELATIONAL 64, EA 13 | n/a (blank) |
| `latest/haldetect_phase2_goldlabeled (2).csv` | 126 | **109** | RELATIONAL 64, EA 13, TEMPORAL 26, CITATION 6 | **FALSE ✓** |
| `latest/haldetect_phase2_goldlabeled (3).csv` | 126 | **109** | same as (2) | **FALSE ✓** |

`(2)` and `(3)` are **byte-identical** (`diff` returns nothing) — `(3)` (Aug 9) is a redundant duplicate save of `(2)` (Jul 25). Both match the fingerprint exactly (109/126, exact type split, Q18_C09=FALSE). **Current = `(3)` by mtime; `(2)` is an exact duplicate, not a separate version.** `.csv` (no suffix) and `(1)` are genuinely older/partial and should archive.

## 6. Batch 3 gold CSV — resolved, exact match

`latest/haldetect_claims_b3_gold.csv`: **122/122 filled**, breakdown **115 TRUE / 4 FALSE / 3 UNVERIFIABLE** — matches the fingerprint exactly. No conflicting copies found elsewhere. **Confirmed current, unique, no action needed.**

## 7. Negatives CSVs — ⚠️ REQUIRES USER DECISION, and contradicts `haldetect_fingerprints.md`'s row counts

Actual row counts (data rows, header excluded):

| File | Fingerprint doc said | Actual rows |
|---|---|---|
| `relational_negatives_batch3.csv` | 14 | **19** |
| `relational_negatives_batch3_expansion.csv` | 6 | **5** |
| `relational_negatives_batch3_round2.csv` | 8 | **8** (only one that matches) |
| `relational_negatives_batch3_merged.csv` | 20 | **27** |

None of the row counts match what `haldetect_fingerprints.md` describes except `round2.csv`. Per the ground-truth rule in `audit.md`, **the files win, not the doc** — but this means the merge state described in the fingerprint doc ("round 1 + your expansion = 20") is not what's on disk now. `merged.csv` (27 rows, mtime Aug 20 15:10) is *newer* than `round2.csv` (8 rows, mtime Aug 20 15:04) by only 6 minutes, suggesting `merged.csv` may already fold in round2 — but 19 + 5 + 8 = 32 ≠ 27, so it isn't a clean union of all three either, and there may be dedup or a partial merge involved. **I can't determine which negatives set is authoritative from file evidence alone — this needs you to confirm what `merged.csv` actually contains before I file it as current.**

## 8. Batch 3 verified-results duplicates (relational negatives)

`latest/relational_negatives_b3_merger_verified_results.csv` (Aug 20 15:43, 6.1KB→ wait 12,591 bytes) vs `relational_negatives_b3_merger_verified_results (1).csv` (Aug 20 16:14, 12,511 bytes) — nearly identical size, 31 min apart, `(1)` is slightly *smaller* despite being newer. Similarly `relational_negatives_b3_verified_results.csv` vs `(1).csv`. These look like re-runs against different negatives-file states (see #7) rather than simple re-saves — flagging as unresolved pending #7's answer, since these results files are downstream of whichever negatives file was live at each mtime.

## 9. Caches — resolved by mtime

Both cache pairs consistently pick the same winner:

- `relational_retrieval_cache (2).json` (Aug 20 16:14, 1.6MB) — newest, matches `relational_nli_cache (2).json` (Aug 20 16:14) exactly in mtime → **this pair is current**.
- `relational_retrieval_cache.json` (Aug 8, 2.8MB) and `(1).json` (Aug 9, 1.5MB) → older, archive.
- Root `relational_cache.json` (Jun 21, single-file design) predates the two-cache split entirely — belongs to the pre-Phase-3e(i) design. Archive.
- `latest/relational_cache.json` (Jul 13, 15KB) is yet another single-cache leftover from mid-pipeline — archive.
- `verifier_cache.json` (root, Jun 7) and `verifier_cache_temporal.json` (root, Jun 7) — both quite old (predate all the Aug work above) but no newer temporal-specific cache exists anywhere else in the workspace. **Uncertain whether still live** — likely stale given the big gap to the Aug 20 relational cache activity, but I can't confirm without knowing if the temporal notebook cell (71) was ever re-run against a fresh cache since June. Flagging rather than assuming.

## 10. Notebooks — resolved

- `latest/HalDetect_latest.ipynb` — **active**, confirmed above (contains all current verifier logic).
- `test.ipynb`, `llm_client.ipynb`, `Semantic_Embedding_Experiment.ipynb`, `haldetect_LLM_response_atomization_class.ipynb` — **none are referenced from HalDetect_latest.ipynb** (checked via full-text grep for filenames/imports — zero hits). These read as standalone drafts/experiments, safe to archive pending your confirmation of purpose.

## 11. Misc root files — resolved, all unnecessary/log artifacts

- `main` — despite the name, this is a **saved terminal transcript** (shell prompt + progress bars), not an executable/script. Log artifact.
- `currentcode.txt` — a text dump of an early "HalDetect Pipeline — Extraction, Deduplication, Classification" script; not referenced by the notebook (0 hits for `pipeline_results.json` or `embeddings_*.npy`, which this file's pipeline would have produced).
- `verifier_setup.txt` — early scaffolding using `transformers.pipeline`, superseded by the SBERT/Gemini/Wikidata approach used everywhere else.
- `test_results.txt`, `llm_client.txt` — terminal-output logs from early `main`/`llm_client` runs.
- `embeddings_1.npy`, `embeddings_2.npy`, `pipeline_results.json`, `similarity.py` — **zero references** anywhere in the current notebook. Confirmed orphaned experiment artifacts.
- `__pycache__/` — regenerated bytecode for `citation_verifier.py`/`temporal_verifier.py` (both stale versions per above) — safe to delete regardless.
- LaTeX build artifacts (`test.aux`, `test.fdb_latexmk`, `test.fls`, `test.log`, `test.pdf`, `test.synctex.gz`) — unrelated to HalDetect, standard build byproducts, `test.pdf` may be worth a glance before deleting in case it's a real document, but the rest are unambiguous build litter.
- `requirements.txt` — legitimate, keep.

## 12. Reference files — all present, no Thesis PDF found

All 5 handoff markdown files exist at root as expected:
`haldetect_starthere_2026-08-10.md`, `haldetect_session_handoff_2026-08-20.md`, `haldetect_decision_log__Evaluating_feasibility_of_hallucination_detection_project.md`, `haldetect_technical_config__Evaluating_feasibility_of_hallucination_detection_project.md`, `haldetect_fingerprints.md`.

**No `Thesis_Report_Sahib.pdf` found anywhere in the workspace** (only unrelated `sympy`/`torch` test files matched "thesis"-adjacent searches in `.venv`). If you have it, it's not in this directory tree.

---

## Proposed Current vs. Archive Classification

### → `current/`
- `latest/HalDetect_latest.ipynb` (contains all live verifier logic: RELATIONAL cell 57, TEMPORAL cell 71, ENTITY_ATTRIBUTE cell 67)
- `citation_verifier.py` (only copy, even if broken)
- `latest/haldetect_phase2_goldlabeled (3).csv` (109/126, confirmed current — `(2)` archived as exact duplicate)
- `latest/haldetect_claims_b3_gold.csv` (122/122, confirmed exact match)
- `latest/relational_retrieval_cache (2).json` + `latest/relational_nli_cache (2).json` (matching mtime pair, newest)
- Negatives file(s) — **pending your answer to #7**
- `verifier_cache_temporal.json` — pending confirmation it's still live (#9)

### → `archive/`
- `relation_verifier.py` (root — Phase 1 prototype)
- `temporal_verifier.py` (root — pre-retry-logic snapshot)
- `latest/relational_verifier_phase3d.py` (Phase 3d snapshot, 7 iterations behind current)
- `latest/haldetect_phase2_goldlabeled.csv`, `(1).csv`, `(2).csv` (superseded/duplicate)
- `relational_cache.json` (root), `latest/relational_cache.json` (both pre-split single-cache design)
- `latest/relational_retrieval_cache.json`, `(1).json`, `latest/relational_nli_cache.json`, `(1).json` (older cache generations)
- `verifier_cache.json` (root — stale, June)
- Older negatives/verified-results files — pending #7
- `latest/relational_verifier_test_runs.txt`, `latest/rel_verif_b3_code+output.txt` (run logs, not code)

### → `reference/`
- All 5 handoff `.md` files
- (no Thesis PDF found — nothing to move here)

### DELETE (safe, low-risk)
- `__pycache__/`
- LaTeX artifacts: `test.aux`, `test.fdb_latexmk`, `test.fls`, `test.log`, `test.synctex.gz` (recommend keeping `test.pdf` until you confirm it's disposable)
- `main`, `currentcode.txt`, `verifier_setup.txt`, `test_results.txt`, `llm_client.txt` (logs/dead scaffolding, unreferenced by current pipeline)
- `embeddings_1.npy`, `embeddings_2.npy`, `pipeline_results.json`, `similarity.py` (confirmed unreferenced)

### Archive, pending your confirmation of purpose
- `test.ipynb`, `llm_client.ipynb`, `Semantic_Embedding_Experiment.ipynb`, `haldetect_LLM_response_atomization_class.ipynb` (none referenced by the active notebook)
- Root-level dated claim CSVs (`haldetect_claims_2026*.csv` ×7, `haldetect_verified_temporal.csv`) — not cross-referenced against fingerprints yet; flag if you want these fingerprinted too before archiving

---

## Decisions — all resolved

1. **Negatives CSVs:** `merged.csv` (27 rows) confirmed authoritative by content inspection (not just row count) — preserves `base` B3N_01-20 intact, adds 7 non-colliding new claims B3N_21-27. `expansion.csv` is a pure subset/duplicate of `base` → archive. `round2.csv` has a confirmed ID collision with `base` (its B3N_15/16 reuse IDs for different content); 6 of its 8 claims are already folded into `merged.csv` under IDs 21-27 with verifier results already run, and the 7th (B3N_15, "Aral retained ~90%") is a reworded duplicate of `base`'s B3N_17 ("Aral lost <10%"). Nothing unverified or unique remains in `round2.csv` → archive as historical draft, not delete.
2. **Verified-results pairs:** keep `relational_negatives_b3_merger_verified_results (1).csv` as the "final" result (post temperature-fix, 66.67%); keep the no-suffix `relational_negatives_b3_merger_verified_results.csv` too, explicitly preserved in `archive/` as the pre-fix comparison point (60%) — this is reproducibility evidence, not superseded leftovers.
3. **`verifier_cache_temporal.json`:** keep in `current/` — still live, not archived.
4. **Draft notebooks** (`llm_client.ipynb`, `test.ipynb`, `Semantic_Embedding_Experiment.ipynb`, `haldetect_LLM_response_atomization_class.ipynb`): confirmed archive.
5. **`test.pdf`** and the rest of the LaTeX build artifacts: confirmed archive/delete along with `test.aux`/`.fdb_latexmk`/`.fls`/`.log`/`.synctex.gz`.
6. **Root-level dated CSVs — fingerprinted directly, not archived blind:**
   - `haldetect_claims_20260726_173737.csv` (124 rows) — bare `pair_id` (`citation_pair_01`), no `pair_incomplete` col → first/buggy Batch-3 raw run. Archive.
   - `haldetect_claims_20260731_173625.csv` (114 rows) — prefixed `pair_id` (`B3_02_...`), still no `pair_incomplete` → intermediate corrected run. Archive.
   - `haldetect_claims_20260731_175241.csv` (122 rows) — prefixed `pair_id` **and** has `pair_incomplete`; row count matches `haldetect_claims_b3_gold.csv` exactly → **the direct raw precursor `b3_gold.csv` was hand-labeled from.** → **`reference/`**, not archive (provenance evidence).
   - `haldetect_claims_20260524_043744.csv` (127 rows, 0% filled) and `haldetect_claims_20260524_045439.csv` (125 rows, 0% filled) — raw, superseded by `_1`/`_2`. Archive.
   - `haldetect_claims_20260524_045439_1.csv` / `_2.csv` (125 rows, 100% filled each, same type breakdown, differ by 24 diff-lines — not identical). `_2` is the hardcoded `INPUT_CSV` default in two *historical, superseded* notebook cells (34, 65) — not a live dependency. Archive both.
   - `haldetect_claims_phase2_20260607_185447.csv` (126 rows, 0% filled) — raw pre-labeling precursor to the `haldetect_phase2_goldlabeled*` family. Archive.
   - `haldetect_verified_temporal.csv` (125 rows, 100% filled, has `verified_verdict`/`wikidata_qid` cols) — fully-verified output from the pre-Phase2/B3 May/June lineage, unreferenced anywhere in the current notebook. Archive.
7. **`citation_verifier.py`:** stays in `current/`, not `archive/`. This is known, long-standing broken work (0% coverage on Batch 3, hardcoded org maps — documented in `haldetect_technical_config...md`'s CITATION section), intentionally not yet integrated into the active notebook because this cycle's focus was RELATIONAL/TEMPORAL/EA — deprioritized, not abandoned. Flagged explicitly as **"broken, unintegrated, rebuild scoped but not started."**

---

**Nothing has been moved, renamed, or deleted yet.** All decisions are now resolved — see the final move plan below for explicit approval before any filesystem changes.

---

## Execution Summary (2026-08-21)

All moves executed via `cp -p` (mtime-preserving) + verified `diff -q` clean, then originals removed. Two files were caught by the verification pass that had been missed in the original plan (root's own `relational_cache.json`, and a second, root-level copy of `haldetect_claims_20260524_045439_2.csv` distinct from the one in `latest/`) — both confirmed byte-identical to their already-archived copies before removal, no data lost.

**Final structure** (created directly at project root, not nested under a new wrapper folder):

- `current/` — 9 files + README.md
- `archive/scripts/`, `archive/csvs/`, `archive/caches/`, `archive/notebooks/`, `archive/experiments/` — 40 files total + README.md
- `reference/` — 6 files + README.md
- `latest/` — 10 files, intentionally held back (auto-classified by pattern, not individually fingerprinted; user asked to review before filing)
- `CLAUDE.md` generated at project root for future sessions
- No files were permanently deleted — everything questionable moved to `archive/` per this doc's own "do not delete without approval" rule, including `__pycache__/` and non-`test.pdf` LaTeX build byproducts.
- One rename pair (pre-approved, collision fix): `relational_cache.json` existed identically-named at both project root and `latest/` — archived as `relational_cache_root_2026-06-21.json` and `relational_cache_latest_2026-07-13.json` respectively.

**Outstanding:** the 10 files left in `latest/` (`entity_attribute_b3_verified_results.csv`, `entity_attribute_verified_results_v2.csv`, `relational_b3_verified_results.csv`, `relational_phase2_verified_results.csv`, `temporal_b3_verified_results.csv`, `temporal_verified_results_v2.csv`, `haldetect_claims_b3_triaged.csv`, `haldetect_claims_phase2_triaged.csv`, `rel_verif_b3_code+output.txt`, `relational_verifier_test_runs.txt`) still need a closer look before being filed into `current/` or `archive/`.

---

## Follow-up (2026-08-21, same day): remaining latest/ files filed

The 10 files held back pending review were confirmed for the originally-classified disposition (user had selected "review first" by mistake, corrected to "proceed as classified"):

- → `current/`: `entity_attribute_b3_verified_results.csv`, `relational_b3_verified_results.csv`, `temporal_b3_verified_results.csv`
- → `archive/csvs/`: `entity_attribute_verified_results_v2.csv`, `temporal_verified_results_v2.csv`, `relational_phase2_verified_results.csv`, `haldetect_claims_b3_triaged.csv`, `haldetect_claims_phase2_triaged.csv`, `rel_verif_b3_code+output.txt`, `relational_verifier_test_runs.txt`

All copies verified byte-identical via `diff -q` before originals were removed. `latest/` is now empty.

**Important correction to `rel_verif_b3_code+output.txt`'s status:** despite being filed in `archive/csvs/` for organizational consistency, this is **not** a routine log — it's the evidentiary source used to independently confirm RELATIONAL's headline Batch 3 numbers (80.77% acc / 55.32% cov). Flagged in `archive/README.md` as load-bearing; do not delete or overwrite.

---

## Corrections (2026-08-21, later same day)

1. **`CLAUDE.md` was stale** — it still said "10 files held back in `latest/`" after those files had already been filed (see the Follow-up section above). Fixed to state `latest/` is now empty.
2. **`haldetect_claims_20260731_175241.csv` was misfiled in `reference/`.** That folder is meant to hold only the 5 handoff/context docs, not claim data — this file is raw, pre-gold-labeled Batch 3 claims data and belongs with the rest of that lineage. Moved to `archive/csvs/` (mtime preserved via `cp -p`, verified byte-identical, original removed).
3. **Clarification on `current/haldetect_phase2_goldlabeled (3).csv`:** the *category* selection (109/126 filled, correct RELATIONAL/EA/TEMPORAL/CITATION split, Q18_C09=FALSE) was content-based and ruled out the plain `.csv` and `(1)` variants. But `(2)` and `(3)` are byte-identical to each other (`diff` returns nothing) — between those two specifically, there was no content signal to distinguish them, so `(3)` was picked by mtime (the more recent of two identical duplicate saves), not because the number `3` carried any meaning. Worth being explicit about this distinction: content decided the *category*, mtime (not the filename number) broke the tie *within* that category.
