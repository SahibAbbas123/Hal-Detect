---
name: track-changes-safely
description: Use before writing, editing, deleting, or overwriting ANY file in the HalDetect repo, and again when reporting what a session changed. Encodes what git does and does NOT protect here — caches, credentials and large data are deliberately untracked, so a checkout will not restore them — plus the worklog manifest convention and the author's standing rule to ask before running any large verifier job.
---

# Tracking changes safely

**The repo IS under git as of 2026-08-25** (`main`, initial commit `6458249`, **no remote —
local only**). That is new; anything older describing this as an untracked workspace is stale.

So `git diff`, `git checkout -- <file>` and `git stash` now work. But git covers **140 of the
repo's files, deliberately not all of them**, and the gaps are exactly the load-bearing ones.

## What git will NOT restore

| untracked | why it is excluded | what that means for you |
|---|---|---|
| `*_cache.json`, `verifier_cache*.json` | machine-local; thesis numbers come from a **single cached run** | a checkout cannot bring a cache back — **back it up by hand** |
| `.venv/`, `.venv-pdf/` | pinned torch 2.12 / transformers 5.9 | rebuild from `requirements.txt`, don't expect a restore |
| `data/`, `factscore-repo/` | 54M, re-downloadable; the latter is an embedded git clone | re-fetch, don't recover |
| `geminiAPI.txt`, `.geminiAPI`, `.zshrc` | **live credentials** | never stage; see below |

**Caches are the dangerous case.** They are not in git, growth is append-only, and every entry
is a reproducible API call — so deleting one is unrecoverable *and* silently changes results.

- **Never delete a cache mid-experiment.**
- Clear `title__` / `text__` / `llmquery__` only if retrieval logic changed; preserve `nli__`
  unless NLI logic changed. **Bump prefixes rather than reuse them** — reusing one preserves the
  bug on every cached entry while making the fix appear to work.
- `archive/caches/verifier_cache_wikidata.pre-propertyfix-20260822.json` is **NOT a restore
  point** — 30 keys / 4 KB against the live cache's 3,584 keys. Restoring it would discard weeks
  of legitimate accumulation. Leave it alone.
- Gemini query generation is **non-deterministic without its cache**, so thesis numbers come
  from one cached run, never an average.

## Before any write

1. `stat -f "%Sm  %z bytes  %N" <file>` — record mtime and size.
2. Tracked file? `git diff` is your record. Untracked and hand-curated (a cache, a credential,
   anything in the ignore list)? **copy first**: `<name>.backup-<UTC-stamp><ext>`.
3. Decide the reverse command **now** and write it into the worklog.

## The worklog is still the narrative record

`WORKLOG_2026-08-22.md` carries numbered steps (`Step 29`, …), each with what changed, why, and
an explicit **reverse command**. Git records *what* bytes moved; the worklog records *why*, and
that is the part a commit diff cannot reconstruct. Keep both.

Classify every write:
- **regenerable** — deterministic `--diagnose`/`--selftest` output; no revert needed
- **additive** — append-only cache growth; must NOT be rolled back
- **deliberate** — hand edit; needs an explicit reverse command
- **canonical** — gold labels, authoritative CSVs, source, CLAUDE.md, the notebook; back up first

## Credentials — three files, one key, and it nearly went into history

`geminiAPI.txt` **and** `.geminiAPI` hold the *same* 53-char Gemini key; `.zshrc` holds a live
`ANTHROPIC_AUTH_TOKEN`. All three are now gitignored, and all three were **caught staged** on
2026-08-25 before the first commit. Nothing entered history.

- **Never print, echo, or log a key** — not in chat, a commit message, or script output. Use
  `current/gemini_key.describe()`, which emits only `AQ.Ab8...ipHQ (len=53)`.
- The key had also leaked into **cached notebook cell outputs** (a request URL printed with
  `?key=` in a traceback, 15× per notebook). Redacted 2026-08-25. **Re-check after any notebook
  run that errors**, because a fresh traceback can reintroduce it.
- Run this before **every** commit, not just the first:
  ```bash
  git diff --cached --name-only | grep -iE "gemini|zshrc|bashrc|profile|\.env|\.key$|\.pem$"
  ```
  Then scan staged *content* for the literal value, since a filename check cannot catch an
  embedded key. If anything appears: `git reset` before committing.

## Don't run large jobs unasked

The author's standing instruction: verifiers are not to be run over 500/1000 rows on a whim —
work in blocks, and **ask before running any large script or task**. A 30-claim diagnostic is
routine; a pooled 356-claim re-run with live API calls is not.
