# Task #20 — `property_resolver.py`: Bug B removed, not ported

**Date:** 2026-08-27
**Module:** `current/property_resolver.py`
**Reproduce:** `.venv/bin/python current/property_resolver.py --selftest` (Arm A offline,
Arm B two live Wikidata property fetches)
**Model calls:** zero. Arm A is fully offline; Arm B hits the Wikidata API only.

---

## 0. The short version

CLAUDE.md recorded #20 as *"`action=wbsearchentities` still at L612, i.e. Bug B is LIVE, and no
`sitelinks`, no `RESOLUTION_TIE_BAND`"* with the instruction *"Must be fixed before any
integration, with another prefix bump."* Four things in that framing needed correcting before the
fix could be designed, and each was verified rather than reasoned about:

| CLAUDE.md said | measured | consequence |
|---|---|---|
| Bug B is live at **L612** | the call spans **L611–616**, and it is **not in a resolver** — it is an inline fallback inside the `--diagnose` loop | changes what "fix Bug B" means |
| it is a *fallback* | `haldetect_claims_b3_gold.csv` has **no `resolved_qid` column at all**, so it ran on **34/34 rows — the sole resolver** | the recorded 17.6% was measured *through* it |
| Bug B (prefix-only search) | the path is **unscored**, `limit=1`: it lacks fix **#1** (score, commit, *then* query) as well as #2 and #3 | worse than recorded, and the older fix is the more serious omission |
| fix it "with another prefix bump" | the removed call goes through `_get_with_retry`, which **takes no cache argument and writes nothing** | **no bump is required**; a bump here would be cargo-culting R14 |

The fix is to **delete the path and inject resolution**, not to port a fourth copy of the
resolver. `quantitative_verifier.py:84` imports *from* `property_resolver`, so this module cannot
import `resolve_entity` back — that is a circular import, and it is why "just call the validated
resolver" is unavailable in the obvious direction.

**Also found, and it is not part of #20:** the module's `--selftest` is **1/2, and was already
1/2 before this task**. CLAUDE.md §2 lists it as *"`--selftest` passing"*. That claim is stale.

**And one self-inflicted near miss worth reading before the rest:** the first working draft of the
new selftest **overwrote `property_match_diagnostic.csv`** — the 34-row file behind the 17.6% in
the table above — with its own 1-row output, while printing `11/11 passed`. Caught by
`git status`, restored from git, verified back to 34 rows / 6 matched, and the cause fixed in
`diagnose()`'s signature with a byte-identical assertion that is itself proven to fail when the
defect returns (§3).

---

## 1. Why "Bug B is live here" understated it

Bug B is *prefix-only search* — `wbsearchentities` is a prefix matcher, so it omits `Q130018`
whose label **is** "Denali", and `"Denali mountain"` returns nothing. The fix was prefix search
**unioned with** full-text `action=query&list=search`.

**So the mere presence of `wbsearchentities` is not evidence of Bug B.** The validated resolver in
`quantitative_verifier.py` calls it too, at L572 — as one arm of a union. A grep for the string
cannot distinguish the bug from the fix, which is worth stating because that grep is what produced
the "L612" record.

What made this instance a defect was everything around it:

```python
        if not qid:
            # Resolution is the notebook's job; here we only measure the
            # property layer. Resolve by exact search hit for the diagnostic.
            data = _get_with_retry({
                "action": "wbsearchentities", "search": subj, "language": "en",
                "format": "json", "limit": 1, "type": "item",
            })
            hits = (data or {}).get("search", [])
            qid = hits[0]["id"] if hits else ""
```

`limit: 1`, and the first hit is taken **unconditionally**. There is no score, no
`RESOLUTION_THRESHOLD`, no `RESOLUTION_TIE_BAND`, no sitelinks prominence, and no `en|mul` on the
search arm. That means it is missing **failure mode #1's fix** — *score candidates on their own
label/alias/description, commit, and only then query the property*, the 2026-08-21 change that
drove Batch 3's confident-wrong verdicts to zero. #1 is the older and more consequential omission,
and the "Bug B" label obscured it.

### It was the sole resolver, not a fallback

```
haldetect_claims_b3_gold.csv:  122 rows, 34 TEMPORAL+EA
has a `resolved_qid` column:   False
rows with a non-empty one:     0 / 34
```

The guard is `qid = (r.get("resolved_qid") or "").strip()`, and the column does not exist, so the
branch fired on every row.

**One near-miss worth recording.** The CSV *does* have a `q_id` column, populated on all 34 rows,
which reads like the missing QID field. It is not: its values are `B3_01`, `B3_02`, … — the
**question** id. Feeding it to Wikidata as a QID would have produced 34 silent resolution failures
that looked like a coverage result. Checked before use, per R1.

### What that does to the 17.6%

CLAUDE.md §7 uses this module's **6/34 = 17.6%** as one of the two recorded precedents that make a
high #19 coverage figure a *warning* rather than a win (R8). That number was produced with every
QID coming from the unscored `limit=1` path.

So **17.6% is a floor depressed by resolution failure, not a measurement of the property layer** —
which is the one thing the module claims to isolate. It remains usable as a precedent in the
direction R8 needs it (a real property-layer figure can only be ≥ it once resolution is fixed),
but it should not be quoted as "the property layer reaches 17.6%". The `--resolver validated` path
added here is what would measure it properly, and that run has not been made — it calls the
Wikidata API for 34 subjects and needs author go-ahead, like #19.

---

## 2. Why the fix is injection

Three candidate fixes, and the reasons two were rejected:

**(A) Move `resolve_entity` down into `property_resolver`, and have `quantitative_verifier` import
it from here.** Architecturally the cleanest end state — one resolver, in the lower layer. Rejected
for now: it edits `quantitative_verifier.py`, the module carrying the project's only
prior-independent win (selftest 24/24, MCC +0.378 vs +0.202, 14/14 with zero confident errors).
CLAUDE.md's discipline for #21 is explicit — *"build as a sibling, not an edit to a validated
verifier"* — and it applies with more force here, because the beneficiary is a module that is
**deliberately unintegrated and not on the critical path**. Bad risk for the reward.

**(B) Port a fourth copy of the three fixes into this module.** No circularity, no validated
verifier touched. Rejected because a fourth divergent copy of a calibrated component is precisely
the drift that created this task: #9 ported the fixes to three places, #12 bumped two of them, and
this module lagged for days without anything noticing.

**(C) Delete the path; inject the resolver.** Adopted. `diagnose()` takes a `resolver` callable
with `resolve_entity`'s signature — `(subject, cache, ctx) -> {"qid", "score", "detail", ...}` —
and given none it records `no_resolver` and abstains. The dependency now points the right way: the
lower layer declares the hook, the upper layer supplies the implementation.

This **removes** the defect rather than patching it. A module that does not search cannot have a
prefix-only-search bug, and it cannot acquire one by drifting out of sync with a fix applied
elsewhere.

`--resolver validated` wires in `quantitative_verifier.resolve_entity` with a **call-time** import
inside the `__main__` block. That is not circular — by then this module is fully loaded — but it
does instantiate a second `property_resolver` module object and therefore a second SBERT, which is
why it is opt-in rather than the default. The cost is stated in the CLI help rather than hidden.

### Two distinctions the routes now preserve

`no_resolver` and `unresolved` are deliberately different strings:

- **`no_resolver`** — no resolver was supplied. The row is **UNMEASURED**.
- **`unresolved`** — a resolver ran and declined. The row is a genuine resolution gap.

Collapsing them would let unmeasured rows read as negative ones, which is the same error class as
R8's coverage-vs-correctness confusion and R7's two kinds of UNVERIFIABLE. The summary block prints
the caveat explicitly when any `no_resolver` rows exist, rather than reporting a coverage
percentage whose denominator silently includes rows nothing was tried on.

### R12 is now enforced, not just documented

The loop reads the **`subject`** column (`subj = (r.get("subject") or "").strip()`). On this
population — natural Batch 3 — that is clean, because R12's contamination is a property of the
*perturbation harness*, which rewrote `claim` and left `subject` holding the original un-perturbed
value. There is no live leak.

But it is a landmine: pointed at `synthetic_negatives.csv`, this loop would resolve from the exact
column that holds the value the negative exists to hide. So `diagnose()` now **aborts** if the CSV
carries any of `original_value`, `corrupted_value`, `base_claim_id`, `injection_type`,
`perturbation`. Six lines, and it converts a documented rule into an enforced one.

The injected resolver also receives **claim text** as `ctx`, never the `subject` column, so its
scoring sees the same input the pipeline sees. A selftest asserts both halves.

### No cache-prefix bump, and this was checked

R14 mandates bumping a prefix — never reusing one — when stale cached values would otherwise
preserve a bug while making its fix appear to work. That does not apply here:

```python
def _get_with_retry(params: dict) -> dict | None:
    """GET with backoff. Failed calls are NEVER cached (cache-poisoning bug)."""
```

It takes no cache argument and writes nothing, and the deleted call site passed no cache. **The
removed path never produced a cache entry.** `pmeta2__` and `ilabel2__` remain correct as they are.

CLAUDE.md §7's *"with another prefix bump"* is over-broad on this point. Worth recording, because
an unnecessary bump is not free — it silently discards valid cached work and, on a module that
shares `verifier_cache_wikidata.json` with the notebook verifiers, would have cost re-fetches
nothing in this change required.

---

## 3. The selftest gap that let this rot

The old `_selftest` ran two cases, both with **hardcoded QIDs** (`Q7350`, `Q48584`) passed straight
into `resolve_property_values`. It never called search. **A test that cannot reach the defect is
not evidence it is absent** — and this is the mechanical reason cells 69/75 were fixed under #12
while this module lagged.

The new **Arm A** is structural and offline, 14 checks:

| check | what it prevents |
|---|---|
| no `{"action": "wbsearchentities", …}` dict literal in the module | the bug returning verbatim |
| no indirect live reference to the token outside the selftest | the bug returning via an assembled params dict |
| the token still appears in prose | **the check itself going vacuous** |
| `diagnose()` takes a `resolver` parameter | the hook existing |
| …defaulting to `None` | the module never guessing an entity again |
| `diagnose()` takes an `out_path` parameter | the test having somewhere else to write |
| an injected resolver is actually called | the wiring |
| …and receives claim text as `ctx`, not `subject` | R12 |
| resolver present + `qid` None → `unresolved` | the measured-vs-unmeasured distinction |
| no resolver → `no_resolver` | same, other direction |
| …and the summary says **UNMEASURED** | a floor not being read as a result |
| a CSV with harness columns raises `SystemExit` | R12, enforced |
| `property_match_diagnostic.csv` is byte-identical across the arm | **R19 — the test destroying a quoted result** |
| …and the arm's own CSV went to a tempfile | same, positive form |

Two design points carried from elsewhere in the project:

1. **The first draft of the token check failed by flagging itself.** Its own check-name string and
   its own AST predicate are live string constants containing `wbsearchentities`, so a
   docstring-exclusion pass reported three hits. It now checks the **call pattern** — a dict
   literal with key `"action"` and a value containing the token — which cannot be confused with a
   mention anywhere, plus a bare-reference check scoped to exclude the selftest's own body.
   Comments never enter the AST, so they are excluded for free.

2. **The check is proven non-vacuous.** The same predicate was run against the deleted code and
   against a prose-only mention:

   ```
   OLD code (the deleted fallback): predicate reports [5]
   PROSE-ONLY mention:              predicate reports []
   ```

   It fires on the real call and stays silent on a mention. This project has already shipped one
   test that passed while testing nothing (`series_resolver`'s invariance test comparing
   `NO_TOPICAL_MATCH` to `NO_TOPICAL_MATCH`), which is worse than no test because it reads as
   evidence. Same guard applied here.

The stub resolver keeps Arm A offline: it records its arguments and returns `qid=None`, so the
wiring, the `ctx` contract and both route strings are all exercised without a network call.

### The test destroyed the number this task is about

**The first working draft of Arm A clobbered `current/property_match_diagnostic.csv`.** It called
`diagnose()` with a 1-row temp CSV, but `out_path` did not exist yet — the destination was
hardcoded to the module directory — so the arm overwrote the recorded **34-row** artifact with its
own **1-row** output. That file is the source of the **6/34 = 17.6%** figure this very document
spends §1 analysing, and which CLAUDE.md §7 quotes as an R8 precedent.

**How it was caught:** `git status --short` listed `current/property_match_diagnostic.csv` as
modified when nothing in the task should have written to it, and `git diff --stat` read
`2 insertions(+), 35 deletions(-)`. Restored with `git checkout --`, then verified rather than
assumed: 34 rows, routes `{gap: 25, unresolved: 3, matched: 6}`, `matched 6/34 = 17.6%`.

**The fix is in the writer's signature, not the caller's care.** `diagnose()` now takes
`out_path=None`, the selftest passes a tempfile, and two checks make it self-enforcing: the
recorded file's bytes are snapshotted before the arm and asserted byte-identical after
(`18163 bytes before, 18163 after`), and the arm's own CSV must exist at the tempfile path. A
comment saying *be careful not to overwrite this* would have been worth nothing; the assertion
fires on its own.

**That assertion was then proven non-vacuous the same way the token check was** — by reproducing
the defect on purpose against the real file, with the bytes held in memory *and* `git show HEAD:`
as an independent second restore path:

```
recorded file  : 18163 bytes  sha=a6f3b323a488d2cb
git HEAD copy  : 18163 bytes  sha=a6f3b323a488d2cb
after out_path-omitted call:   170 bytes  sha=e16ef0e46a574af6   <- clobbered
restored       : 18163 bytes  sha=a6f3b323a488d2cb   == git HEAD
                 34 rows, 6 matched = 17.6%
```

So the check fails when the defect returns, which is the only thing that makes it evidence.

**Two lessons worth keeping.** First, R19 (*never overwrite a result CSV that is currently quoted*)
was written about experiment output and it applies just as much to **test** output — a selftest is
a program that writes files, and its default destination is part of its contract. Second, the near
miss was silent: the arm printed `11/11 passed` while having destroyed a quoted number, so **the
test's own PASS was not evidence the test was harmless.** `git status` was the only thing standing
between this and a commit that quietly replaced 34 measured rows with one synthetic one.

---

## 4. `--selftest` is 1/2, and it was 1/2 before this task

Arm B fails one of the two founding cases:

```
FAIL  Q7350 'inception_date' -> None (want P1619) @0.569
      core-term guard: 'inception' vs 'official opening' =0.194 < 0.35
      — P1619 (date of official opening) is a different kind of date, not this claim's
PASS  Q48584 'consists_of' -> P186 @0.686
```

**Verified pre-existing, not a regression.** The unmodified main-checkout copy produces a
byte-identical failure — same `@0.569`, same guard message, same `1/2 passed`. My edits touch the
docstring, `diagnose()`, `_selftest`, two imports and the `__main__` block; none touches
`match_property` or the guard.

**How the stale claim survived:** the old `_selftest` printed `1/2 passed` and **exited 0**. Any
scripted or remembered check reading the exit code called it green. It now exits 1.

```
OLD (main checkout) exit code: 0
NEW (worktree)      exit code: 1
```

**So CLAUDE.md §2's *"all `--selftest` passing"* is wrong for this module and is corrected to
1/2.** This is the R1 pattern again: a document's description of a file, believed rather than
checked.

### The failure is the core-term guard working as designed

The guard exists because every TEMPORAL predicate and every time-valued property label shares the
same scaffolding — *year*, *date*, *time*, *of* — which dominates the embedding and makes unrelated
dates look alike. It stopped 7 confident-wrong matches on Batch 3, including
`decipherment_year → P569 (date of birth)`, comparing 1790 against a claimed 1822 and flipping a
gold-TRUE claim to FALSE.

Here it rejects `P1619 (date of official opening)` for `inception_date` at 0.194 < 0.35. But
`P1619 = 1914-08-15` **is** the Panama Canal's inception for this claim's purposes, so the guard
costs coverage on one of the two bugs the module was built to fix and names in its own docstring.

**Precision up, coverage down — the exact mirror of the four recorded coverage-up/precision-down
events (R8).** That makes it a real trade, not obviously the wrong one, and the reason it must be
measured rather than nudged: lowering 0.35 to buy back one coverage case risks the 7 confident-wrong
matches the guard prevents. Logged as **task #25**, out of scope for #20. The likelier fix is a
synonym set for date-kind terms (inception / founding / opening / establishment) rather than a
threshold move, since the defect is that SBERT scores *inception* against *official opening* at
0.194 while they denote the same event class here.

---

## 5. What changed, what did not

**Changed** — `current/property_resolver.py` only:

- docstring records the contract, the four corrections, and the no-bump finding
- `diagnose(csv_path, limit=None, resolver=None)`; inline `wbsearchentities` block deleted
- `no_resolver` vs `unresolved`, and an UNMEASURED caveat in the summary
- R12 abort on harness columns; `ctx` is claim text
- `out_path` parameter, so a test can redirect the CSV away from the recorded one (§3)
- `resolution_detail` column added to `property_match_diagnostic.csv`
- Arm A (14 offline structural checks); `_selftest` now exits non-zero on failure
- `--resolver none|validated`; `ast` and `tempfile` imports

**Not changed, deliberately:**

- **No measured number moves.** This module is unintegrated; nothing in RQ1, RQ2, the threshold
  sweep, the per-type J table, QUANTITATIVE's 14/14 or CITATION L1b reads from it.
- **`current/property_match_diagnostic.csv` is byte-identical to `HEAD`** —
  `sha256[:16] = a6f3b323a488d2cb`, 34 rows, 6 matched, 17.6%. It was clobbered mid-task and
  restored (§3); the commit contains no change to it, which `git status` confirms rather than
  this sentence.
- `quantitative_verifier.py` untouched — the validated verifier, still 24/24.
- No cache prefix bumped (§2).
- The core-term guard untouched (§4, task #25).
- `--resolver validated` **has not been run**. It is 34 live subject resolutions; that needs author
  go-ahead, and its coverage figure carries R8's warning — a number far above 17.6% is a warning,
  not a win, and the 17.6% it would be compared against is itself a depressed floor (§1).

**Reverse:** `git revert` the commit. Nothing imports `diagnose`, and the module writes only
`property_match_diagnostic.csv`.
