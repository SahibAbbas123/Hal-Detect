---
name: edit-haldetect-notebook
description: Use before reading, editing, or executing any cell of current/HalDetect_latest.ipynb. Triggers on re-running cells 69/75 (TEMPORAL/EA), touching cell 57 (RELATIONAL Phase 3e), changing a threshold, or extracting notebook logic into a script. Encodes the raw-JSON-only rule, the cell map, and which cells are live versus superseded — the notebook holds live verifier logic that no standalone .py replicates.
---

# Editing the HalDetect notebook

**Hard rule: raw JSON only.** Read and write with `json.load` / `json.dump`. **Never install
jupyter, nbformat, or nbconvert** — the venv is pinned (torch 2.12 / transformers 5.9 /
sentence-transformers 5.5.1) and load-bearing for reproducibility.

```python
import json
nb = json.load(open("current/HalDetect_latest.ipynb"))
src = "".join(nb["cells"][69]["source"])          # cells is a list; 76 cells total
# ... edit ...
nb["cells"][69]["source"] = new_src.splitlines(keepends=True)
json.dump(nb, open("current/HalDetect_latest.ipynb","w"), indent=1, ensure_ascii=False)
```

## Cell map (verified 2026-08-24, 76 cells)

| cell | what | status |
|---|---|---|
| 46, 48, 50, 52, 54 | RELATIONAL phase progression | superseded |
| **57** | `## Phase 3e (i)` — **live RELATIONAL logic**, Wikipedia retrieval + BART-MNLI | **live** |
| 67 | EA Phase 3 | superseded |
| **69** | `## Phase 4` — **live ENTITY_ATTRIBUTE logic** | **live** |
| 73 | TEMPORAL Phase 1 | superseded |
| **75** | `## Phase 2` — **live TEMPORAL logic** | **live** |

Cells 69 and 75 are **self-contained** — each defines its own `CACHE_FILE`, `HEADERS`,
`PROPERTY_TO_WIKIDATA`, `resolve_entity_for_property`, SBERT loader and retry helper, so either
can be extracted and run as a standalone script without the earlier cells.

Cells 69/75 **already carry all three resolver fixes** and have **never been executed** —
`meta2__` = 0 keys. Every recorded TEMPORAL/EA number is therefore pre-fix. Pre-fix state is
preserved in `current/HalDetect_latest.backup-20260823-193627.ipynb`.

Verify the fixes by these markers (checked 2026-08-25, all present in both cells):

| fix | grep for | not |
|---|---|---|
| `mul` labels | `en\|mul` | — |
| full-text search | **`srsearch`** | `list=search` — params are a **dict**, so that URL string never appears |
| prominence tie-break | `RESOLUTION_TIE_BAND` | — |

## STALE CACHE PREFIXES — fix before re-running cells 69/75

Only `meta2__` was bumped. Cells 69/75 still share **three** prefixes with the superseded
cells 67/73, and those keys predate the fix:

| prefix | keys | shared with | caches |
|---|---|---|---|
| `entity_candidates__` | **5** | 67, 73 | the candidate **list** — the *output of the search that Bug B fixed* |
| `attr__` | 3 | 67 | EA property lookups |
| `sparql__` | 2 | 73 | TEMPORAL property lookups |

Those entries carry the **fingerprints of the original QID bug**: `attr__Q48584__P527 -> []`
is the Rosetta Stone fall-through to the punk band, `sparql__Q7350__P571 -> []` is the Panama
Canal fall-through to the Canal Zone. Subjects cached: `rosetta_stone`, `panama_canal`,
`french_effort_to_build_the_panama_canal`, `human_liver`, `lobules` — **the two flagship
examples of the entire QID-bug narrative are in that set.**

An empty `meta2__` means scoring is recomputed correctly, but **only over the old prefix-only
candidate set**, for ~5 of the 34 Batch 3 TEMPORAL+EA subjects. That is exactly the trap this
project already documented: *reusing a prefix preserves the bug while making the fix appear to
work.*

**Fix — in cells 69/75 only, so 67/73 keep their entries (never delete a cache):**
`entity_candidates__` -> `entity_candidates2__`, `attr__` -> `attr2__`, `sparql__` ->
`sparql2__`. Cost is 10 re-fetched keys. Do this **before** the re-run, or the re-run's numbers
are not attributable to the fix.

## Cell 57 runs a threshold regime that appears in no results table

```
ENTAIL_THRESHOLD      = 0.55   # raised from 0.50 — fewer marginal TRUE
CONTRADICT_THRESHOLD  = 0.45   # raised from 0.40 — fewer marginal FALSE
```
plus margin 0.15. The pooled "3d vs 3e" table evaluates **0.50/0.40**, so it never scores what
cell 57 actually does. This is a third, unreported regime — record it, don't silently pick one.

Cell 57 also calls `gemini-3.1-flash-lite-preview` for disambiguated query generation.
Uncached claims fall back to the bare subject, which measurably degrades coverage, so a pooled
re-run needs the key or its numbers carry an asterisk. Resolve the key via
`current/gemini_key.py` (env var → `geminiAPI.txt` → Colab); off-Colab imports need the
`google.colab` shim that `nonrouted_baseline.py` installs.

## Before any edit

1. `stat -f "%Sm %z %N" current/HalDetect_latest.ipynb` — record mtime and size.
2. Copy to `current/HalDetect_latest.backup-<UTC-stamp>.ipynb`.
3. Confirm the cell index by its **first line marker** (`## Phase 4`), never by position alone.
4. After writing, re-`json.load` the file to prove it still parses before running anything.

## Cache discipline when changing logic

- **Never delete a cache mid-experiment.**
- If retrieval logic changes, clear `title__` / `text__` / `llmquery__`; **preserve `nli__`**
  unless NLI logic itself changed.
- If a resolution or matching code path changes, **bump the key prefix** rather than reuse it.
  Reusing `meta__`/`cmeta__`/`search__` preserves the bug on every cached entry while making
  the fix appear to work. This discipline is what caught the cache-poisoning bug and proved
  cells 69/75 had never run.
- Never cache a failed API call.
