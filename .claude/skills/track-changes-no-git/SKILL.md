---
name: track-changes-no-git
description: Use before writing, editing, deleting, or overwriting ANY file in the HalDetect repo, and again when reporting what a session changed. This repo is not under version control, so there is no `git checkout` undo — the worklog manifest is the only retreat record. Triggers on any edit to source, CSVs, CLAUDE.md, the notebook, or caches, and on the author's standing request to "keep track in case we need to take a few steps back".
---

# Change tracking without git

**`git rev-parse` returns `fatal: not a git repository`.** There is no version-control undo.
Every change must be reversible by a command written down *before* the change is made.

## Before any write

1. Record current state so a diff is possible later:
   ```bash
   stat -f "%Sm  %z bytes  %N" <file>
   ```
2. For anything hand-curated (gold labels, source, CLAUDE.md, the notebook), copy first:
   `<name>.backup-<UTC-stamp><ext>`.
3. Decide the reverse command **now**, and write it into the worklog.

## After the change: append to the worklog

`WORKLOG_2026-08-22.md` is the running record; entries are numbered steps (`Step 27`, …). Each
entry carries what changed, why, and an explicit **reverse command**, e.g.

```
Reverse: rm -f current/router_ablation.py current/router_ablation_results.csv
```

Then report a disk-change manifest: file, mtime, size, how it was written, and whether it needs
reverting. Attribute by mtime — it distinguishes this session's writes from earlier ones.

Classify every write as one of:
- **regenerable** — deterministic output of a `--diagnose`/`--selftest` run; no revert needed
- **additive** — append-only cache growth; must NOT be rolled back
- **deliberate** — hand edit; needs an explicit reverse command
- **canonical** — gold labels, authoritative CSVs, source, CLAUDE.md; back up before touching

## Caches are not revertible, and one "backup" is a trap

`current/verifier_cache_wikidata.json` is ~3,584 keys / ~957 KB of deterministic Wikidata
lookups. Growth is append-only; each entry is a reproducible API call.

**`archive/caches/verifier_cache_wikidata.pre-propertyfix-20260822.json` is NOT a restore
point** — it holds **30 keys / 4 KB**. Restoring it would silently discard weeks of legitimate
accumulation. Leave that file alone.

- **Never delete a cache mid-experiment.**
- Clear `title__` / `text__` / `llmquery__` only if retrieval logic changed; preserve `nli__`
  unless NLI logic changed. Bump prefixes rather than reuse them.
- Gemini query generation is **non-deterministic without the cache**, so thesis numbers come
  from a single cached run, never an average across runs.

## Don't run large jobs unasked

The author's standing instruction: verifiers are not to be run over 500/1000 rows on a whim —
work in blocks, and **ask before running any large script or task**. A 30-claim diagnostic is
routine; a pooled 356-claim re-run with live API calls is not.

## The credential

`geminiAPI.txt` sits in the repo root in plaintext (`.gitignore` covers it). **Never print,
echo, or log the key** — in chat, in a commit message, or in a script's output. Use
`current/gemini_key.describe()`, which emits only a masked fingerprint
(`AQ.Ab8...ipHQ (len=53)`).

If version control is ever initialised here, confirm `geminiAPI.txt` is ignored **before** the
first `git add`, or the key enters history permanently.
