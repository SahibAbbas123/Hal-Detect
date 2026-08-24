# HalDetect Workspace Audit & Organization Prompt
## For Claude Code CLI

You are auditing an active research codebase with 73 files across 3 directories.

### Objective
Use file metadata (mtime) and fingerprint patterns to:
1. Identify true current versions (not just "latest/" folder position)
2. Detect file lineage and relationships
3. Separate necessary from unnecessary files
4. Propose clean reorganization
5. **ASK FOR APPROVAL BEFORE EXECUTING**

---

### Step 1: Initial Audit (Non-Destructive, Read-Only)

Run these commands and analyze output:
```bash
ls -lR
# For each .csv, .py, .json file, extract:
find . -type f \( -name "*.csv" -o -name "*.py" -o -name "*.ipynb" -o -name "*.json" \) -exec ls -lh {} \; | sort -k6,7
```

### Step 1b: Locate Handoff Reference Files

Before fingerprinting, check if these 5 files exist in the workspace:
- `haldetect_starthere_2026-08-10.md`
- `haldetect_session_handoff_2026-08-20.md`
- `haldetect_decision_log__Evaluating_feasibility....md` (may have different suffix)
- `haldetect_technical_config__Evaluating_feasibility....md` (may have different suffix)
- `haldetect_fingerprints.md`

If they exist, note their location for later moving to `reference/` folder (Step 3).

Also check for:
- `Thesis_Report_Sahib.pdf` (if present, also moves to `reference/`)

---

### Step 2: File Fingerprinting

Cross-reference your files against these patterns from `haldetect_fingerprints.md` (one of the files you're looking for):

**CSV Fingerprints:**
- Phase 2 gold current: look for exactly 109/126 rows with `gold_verdict` filled (26 TEMPORAL, 64 RELATIONAL, 13 EA, 6 CITATION, 0 QUANTITATIVE). This row-count check is the source of truth.
- **IMPORTANT — do NOT infer version age from `(1)`/`(2)`/`(3)` suffixes in filenames.** These numbers reflect save/download order on the user's machine, not content age, and the direction is not guaranteed (a higher number is *usually* more recent, but this must be confirmed via `mtime`, never assumed from the number alone). For every numbered variant of `haldetect_phase2_goldlabeled*.csv`, check `mtime` AND row-count/fill-pattern independently — do not rely on either signal alone.
- Batch 3 gold: `haldetect_claims_b3_gold.csv` — 122/122 labeled (115 TRUE, 4 FALSE, 3 UV) — unique, no duplicates
- Negatives: `relational_negatives_batch3_merged.csv` (n=20, merged) OR separate `batch3.csv` (n=14) + `expansion.csv` (n=6) unmerged — verify actual row count, do not assume from filename

**Script Fingerprints — IMPORTANT CAVEAT:**
Most of the user's actual working code may now live inside notebook cells (`HalDetect_latest.ipynb` or similar), not the standalone `.py` files. **Do not assume the standalone `.py` files are stale just because a notebook exists.** Before making any archive decision about a `.py` file:
1. Open the notebook and check which cells actually define/run the relevant verifier logic.
2. Check whether the notebook's version of that logic matches, is older than, or is newer than the standalone `.py` file — a notebook can easily contain a stale copy-pasted cell from weeks ago that's actually behind the `.py` file, not ahead of it.
3. If the notebook has multiple cells defining the same function (e.g. edited-in-place across a session), note this explicitly in the audit report as "notebook contains N versions of this function across cells" rather than picking one silently.
4. Only propose archiving a `.py` file if you've confirmed — from actual cell content, not assumption — that its logic is superseded by what's currently live in the notebook.

Specific things to check for, once you've confirmed where the real logic lives (notebook or `.py`):
- RELATIONAL current: contains both `"generationConfig": {"temperature": 0}` in the Gemini call AND `if data is None:` guards (not caching on retry-exhaustion) in both `resolve_wikipedia_titles()`-equivalent and `fetch_page_text()`-equivalent functions
- TEMPORAL v2: check for multi-candidate entity resolution + any P800 special-casing
- ENTITY_ATTRIBUTE v2: check for a `PROPERTY_TO_WIKIDATA`-style mapping dict

**Cache Fingerprints:**
- Do not infer age from `(1)`/`(2)` suffixes — same caveat as CSVs above. Use `mtime` only.
- Larger file size generally correlates with more accumulated cache entries, but confirm with `mtime` before treating a smaller/larger file as newer.

**Ground truth priority — applies to ALL fingerprinting above:**
These fingerprint patterns are informed guesses based on a prior conversation, not verified facts about this specific workspace. If actual file content, mtime, or structure contradicts what's described here, **trust the file, not this document.** Report the discrepancy explicitly in the audit ("expected X per fingerprint notes, found Y instead") rather than silently forcing a match or silently trusting the fingerprint over the file.

**Notebook Fingerprints:**
- Active: `HalDetect_latest.ipynb` in `latest/` subfolder
- Draft/test: `test.ipynb`, `llm_client.ipynb`, `Semantic_Embedding_Experiment.ipynb` → likely unnecessary

**Unnecessary Files (Safe to Archive):**
- `__pycache__/` — regenerated on import, safe to delete
- `embeddings_*.npy` — experiment artifacts, check if still referenced
- LaTeX artifacts: `test.aux`, `test.fdb_latexmk`, `test.fls`, `test.log`, `test.pdf`, `test.synctex.gz`
- `pipeline_results.json` — check if duplicated in cache or results
- `currentcode.txt`, `verifier_setup.txt`, `test_results.txt` — assess if these are documentation or stale logs

---

### Step 3: Build Audit Report

Create `WORKSPACE_AUDIT.md` with this structure:

```markdown
# HalDetect Workspace Audit Report

## Timeline: Files by Modification Date (Oldest → Newest)

| File | mtime | Size | Status | Phase/Notes | Superseded By | Action |
|---|---|---|---|---|---|---|
| ... | | | | | | |

## File Relationships & Lineage

### RELATIONAL Scripts
- `relation_verifier.py` → `temporal_verifier.py` → `relational_verifier_phase3d.py` → [CURRENT?]
  - Check which has temperature=0 + cache fix

### TEMPORAL Scripts
- `temporal_verifier.py` [VERSION?] → `temporal_verifier.cpython-313.pyc` in __pycache__
  - Check for multi-candidate resolution

### CSVs: Batch 3 Gold
- Single authoritative: `haldetect_claims_b3_gold.csv` (122 rows)
- Verified result files: `relational_b3_verified_results.csv`, `temporal_b3_verified_results.csv`, `entity_attribute_b3_verified_results.csv`
- Check for duplicates with parentheses: `entity_attribute_b3_verified_results.csv` vs. `entity_attribute_verified_results_v2.csv`

### CSVs: Phase 2 Gold
- TARGET CURRENT: `haldetect_phase2_goldlabeled__3_.csv` (109/126 labeled)
- Older versions to archive: `haldetect_phase2_goldlabeled.csv`, `haldetect_phase2_goldlabeled (1).csv`, `(2).csv`, `(3).csv`
- Check row counts to confirm

### CSVs: Negatives (UNRESOLVED CONFLICT)
- Original (n=14): `relational_negatives_batch3.csv`
- Expansion 1 (n=6): `relational_negatives_batch3_expansion.csv`
- Expansion 2 (n=6): `relational_negatives_batch3_round2.csv` [different from expansion.csv?]
- Merged (n=20): `relational_negatives_batch3_merged.csv` [is this actually merged, or a placeholder?]
- STATUS: **REQUIRES USER DECISION** — which expansions are official?

### Caches
- Retrieval: `relational_retrieval_cache.json`, `relational_retrieval_cache (1).json`, `relational_retrieval_cache (2).json`
  - PICK LATEST by mtime; archive older numbered versions
- NLI: `relational_nli_cache.json`, `relational_nli_cache (1).json`, `relational_nli_cache (2).json`
  - PICK LATEST by mtime; archive older
- Temporal: `verifier_cache_temporal.json`

## Unnecessary/Uncertain Files

| File | Status | Reason | Recommendation |
|---|---|---|---|
| `Semantic_Embedding_Experiment.ipynb` | Uncertain | User flagged as unnecessary | Archive or delete |
| `embeddings_1.npy`, `embeddings_2.npy` | Uncertain | Experiment artifacts; check if referenced | Audit for references |
| `__pycache__/` | Unnecessary | Auto-generated | Delete (regenerate on next import) |
| LaTeX build artifacts (`test.*`) | Unnecessary | Unrelated to HalDetect | Delete |
| `llm_client.txt`, `llm_client.ipynb` | Uncertain | Likely early experiment | Archive or clarify |
| `test.ipynb` | Uncertain | Generic name; unclear purpose | Archive or clarify |

## Current vs. Archive Classification

### MUST STAY IN `current/` (for experiments)
- `HalDetect_latest.ipynb`
- `haldetect_phase2_goldlabeled__3_.csv`
- `haldetect_claims_b3_gold.csv`
- `relational_negatives_batch3_merged.csv` (if resolved)
- RELATIONAL script with temperature=0 + cache fix
- TEMPORAL v2 script
- ENTITY_ATTRIBUTE v2 script
- CITATION script (even if broken)
- Latest frozen caches (by mtime)

### SHOULD MOVE TO `archive/`
- Older goldlabeled versions
- Phase 3e scripts without patches
- Older cache versions (numbered)
- Older negatives expansions (if merged)

### SHOULD MOVE TO `reference/`
- The 5 handoff markdown files
- `Thesis_Report_Sahib.pdf`

### DELETE (Safe)
- `__pycache__/`
- LaTeX artifacts

### REQUIRES USER DECISION
- Which negatives expansion is official? `expansion.csv`, `round2.csv`, or `merged.csv`?
- Is `llm_client.ipynb` still used? If not, archive.
- Purpose of `Semantic_Embedding_Experiment.ipynb`? Archive if unused.

---

## Proposed Directory Structure

```
haldetect_thesis/
├── current/
│   ├── HalDetect_latest.ipynb
│   ├── [RELATIONAL script with Phase 3e.i patches]
│   ├── [TEMPORAL v2 script]
│   ├── [ENTITY_ATTRIBUTE v2 script]
│   ├── citation_verifier.py (even if broken)
│   ├── haldetect_phase2_goldlabeled__3_.csv
│   ├── haldetect_claims_b3_gold.csv
│   ├── relational_negatives_batch3_merged.csv [or clarified]
│   ├── relational_retrieval_cache__LATEST.json
│   ├── relational_nli_cache__LATEST.json
│   ├── verifier_cache_temporal.json
│   └── README.md (auto-generated: what's here and why)
│
├── archive/
│   ├── scripts/
│   │   ├── relation_verifier.py (superseded)
│   │   └── relational_verifier_phase3d.py (if not current)
│   ├── csvs/
│   │   ├── haldetect_phase2_goldlabeled.csv (older)
│   │   ├── haldetect_phase2_goldlabeled\ (1).csv
│   │   ├── haldetect_phase2_goldlabeled\ (2).csv
│   │   ├── haldetect_phase2_goldlabeled\ (3).csv
│   │   ├── relational_negatives_batch3.csv (unmerged, n=14)
│   │   ├── relational_negatives_batch3_expansion.csv (unmerged, n=6)
│   │   ├── relational_negatives_batch3_round2.csv (unmerged, n=6)
│   │   └── [other old claim CSVs]
│   ├── caches/
│   │   ├── relational_retrieval_cache\ (1).json
│   │   ├── relational_retrieval_cache\ (2).json
│   │   ├── relational_nli_cache\ (1).json
│   │   └── relational_nli_cache\ (2).json
│   ├── notebooks/
│   │   ├── llm_client.ipynb
│   │   ├── test.ipynb
│   │   ├── Semantic_Embedding_Experiment.ipynb
│   │   └── haldetect_LLM_response_atomization_class.ipynb
│   ├── experiments/
│   │   ├── embeddings_1.npy
│   │   ├── embeddings_2.npy
│   │   ├── pipeline_results.json
│   │   └── similarity.py
│   └── README.md (auto-generated: what's here and why)
│
├── reference/
│   ├── haldetect_starthere_2026-08-10.md
│   ├── haldetect_session_handoff_2026-08-20.md
│   ├── haldetect_decision_log__Evaluating_feasibility....md
│   ├── haldetect_technical_config__Evaluating_feasibility....md
│   ├── haldetect_fingerprints.md
│   ├── Thesis_Report_Sahib.pdf
│   └── README.md (auto-generated: what's here)
│
└── README.md (main entry point for new chats)
```

---

## User Approval Checklist

**STOP HERE. Do not proceed until user approves the following:**

1. ✅/❌ Move all files in `latest/` back to root and re-organize (consolidate the mess)
2. ✅/❌ Archive `__pycache__/` and LaTeX artifacts
3. ✅/❌ Archive older goldlabeled CSV versions
4. ✅/❌ Archive older cache files (numbered variants)
5. ✅/❌ **CONFLICT DECISION:** Which negatives CSV is current?
   - Option A: Keep `relational_negatives_batch3_merged.csv` (n=20, if truly merged)
   - Option B: Keep both unmerged: `batch3.csv` (n=14) + pick one expansion (n=6)
   - Option C: Clarify which is which and merge manually
6. ✅/❌ Archive experimental notebooks (`llm_client.ipynb`, `test.ipynb`, `Semantic_Embedding_Experiment.ipynb`)
7. ✅/❌ Confirm which RELATIONAL script is current (check for temperature=0 + cache fix)
8. ✅/❌ Move handoff markdown files (5x `haldetect_*.md` + `Thesis_Report_Sahib.pdf` if present) to `reference/`
   - Files to move: `haldetect_starthere_*.md`, `haldetect_session_handoff_*.md`, `haldetect_decision_log*.md`, `haldetect_technical_config*.md`, `haldetect_fingerprints.md`
9. ✅/❌ Generate `README.md` files in each subdirectory

**Answer format:**
```
1. Yes
2. Yes
3. Yes
4. Yes
5. Option [A/B/C] with clarification:
6. Yes
7. [Script name]
8. Yes
9. Yes
```

Once approved, I will:
- Move files into clean subdirectories
- **Preserve modification times on move** (use `cp -p` / equivalent, not a plain move that resets mtime)
- **Do NOT rename any file currently in active use** (i.e., anything staying in `current/`, or referenced by a live notebook cell via `pd.read_csv(...)`, `open(...)`, etc.) without first showing the exact old-name → new-name mapping and getting explicit approval — renaming a file referenced inside a notebook silently breaks that notebook.
- Files moving into `archive/` MAY be renamed with a date suffix for clarity (e.g. `haldetect_phase2_goldlabeled_2026-07-xx.csv`), but only after showing the proposed rename list for approval — do not rename silently even for archived files.
- Generate README files explaining each folder
- **Generate a `CLAUDE.md` file in the workspace root** (see new Step 6 below) so future `claude code` sessions in this directory load project context automatically
- Output final `ls -R` to confirm
- Append summary to WORKSPACE_AUDIT.md

---

### Step 6: Generate CLAUDE.md (Persistent Project Context)

Claude Code automatically reads a `CLAUDE.md` file at the start of every session in this directory, if one exists. Create one now so future sessions don't need to re-explain the project.

Contents should be a condensed version of `reference/haldetect_starthere_2026-08-10.md` plus `reference/haldetect_session_handoff_2026-08-20.md`, specifically:
- One paragraph: what HalDetect is and its core research question
- The 5 claim types and their verifiers, one line each on current status
- The critical standing rule: never trust a filename or (1)/(2)/(3) suffix — always verify row counts / mtime / content directly
- Pointer: "Full context lives in `reference/` — read `haldetect_starthere_*.md` first if you need more than this summary."
- Current highest-priority open bug (entity-resolution QID mismatch, Panama Canal/Rosetta Stone) so a new session doesn't have to rediscover it

Keep this under ~50 lines — it's meant to be a fast-loading summary, not the full context. The full docs in `reference/` remain the authoritative source.

---

### Additional Notes for Auditor

- Do NOT delete anything without approval, even "obvious" junk
- If a file's purpose is unclear, flag it and ask the user
- When moving files, preserve `mtime` using `cp -p` or `shutil.copy2` (Python)
- Generate a `CONFLICTS.md` if multiple versions of the same file exist with unclear purpose
- Output final state clearly so user can verify before cleanup is permanent
