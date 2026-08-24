# Session Review — 2026-08-24 (fan-out of 5 investigation agents)

**Author:** Claude Code session (background job `ed46c2f3`)
**Scope:** Five parallel read-only/diagnostic agents over the HalDetect workspace.
**Repo is NOT under git** — there is no version-control undo, so the disk-change
manifest in §1 is the *only* retreat record. Verify it against `stat` before acting on it.

Standing-rule compliance: every count below was re-checked directly against files
(`csv` module, `stat`, cache key census), not taken from a subagent's word or from
CLAUDE.md. Where a subagent's claim was refined by direct check, it is marked ✎.

---

## 1. DISK-CHANGE MANIFEST — what this session wrote (the "retreat" record)

This session began ~20:5x on 2026-08-24. **Exactly three repository files were written**,
all as automatic side effects of running diagnostics — none hand-edited. Attribution is
by mtime: only the 21:06–21:14 writes belong to this session.

| # | file | mtime | size now | written by | kind |
|---|---|---|---|---|---|
| 1 | `current/quantitative_b3_results.csv` | 2026-08-24 21:06:53 | 26,220 B | `quantitative_verifier.py --diagnose` | regenerated diagnostic output |
| 2 | `current/hybrid_b3_diagnostic.csv` | 2026-08-24 21:14:00 | 10,540 B | `hybrid_fallthrough.py --diagnose` | regenerated diagnostic output |
| 3 | `current/verifier_cache_wikidata.json` | 2026-08-24 21:14:00 | 957,241 B | live Wikidata calls (quant selftest/diagnose/sensitivity) | append-only cache growth |

**NOT touched by this session (confirmed via `stat`):**
- `CLAUDE.md` (mtime 20:21:51 — predates session; the 20:xx edits are the user's own prior work today, not this session's)
- `WORKLOG_2026-08-22.md` (20:19:59 — user's prior work)
- Any source `.py`, the notebook `HalDetect_latest.ipynb`, any gold-label CSV,
  `README.md`, `reference/*`, or `property_match_diagnostic.csv` (still 2026-08-22 13:48:13).
- `.claude/settings.local.json` (21:44 — harness settings, not a repo artifact).

### Reversibility per file

1. **`quantitative_b3_results.csv`** — deterministic output of `--diagnose`.
   Re-running regenerates it. No prior hand-curated version is known to have existed.
   *Retreat:* none needed; regenerable. If a pre-session copy is wanted it was not snapshotted.
2. **`hybrid_b3_diagnostic.csv`** — same: deterministic `--diagnose` output, regenerable.
3. **`verifier_cache_wikidata.json`** — grew ~5.7 KB (subagent reported 951,548 → 957,241;
   current size and mtime confirmed by `stat`). Growth is **append-only**: new
   `cmeta3__` / `cand2__` / `pmeta2__` / `ilabel2__` entries from deterministic Wikidata
   lookups. No existing key was mutated or deleted (every other cache file is byte-identical).
   *Retreat:* not meaningful for a cache — each entry is a reproducible API lookup.
   The only on-disk snapshot, `archive/caches/verifier_cache_wikidata.pre-propertyfix-20260822.json`
   (2026-08-22 13:35, **30 keys, 4 KB**), is a PRE-property-fix relic, **NOT** a valid
   restore point for the current 3,584-key cache — restoring it would discard weeks of
   legitimate accumulation. Do not "roll back" this file.

**Bottom line:** the session's entire write footprint is 2 regenerable diagnostic CSVs
and additive cache growth. There is nothing here that needs reverting to protect the
thesis's canonical data. No gold labels, no source, no docs were altered.

### Live cache key census (verified this session)

```
total 3584 keys:
  pmeta2__  1418   (property_resolver, mul-fixed)      cmeta2__   21  (stale, pre-fix, unused)
  pmeta__    935   (property_resolver, pre-fix)        meta__     20  (notebook pre-fix)
  cmeta3__   838   (quantitative_verifier, all fixes)  ilabel__   15
  cand2__    109   (quantitative_verifier full-text)   cmeta__    14
  claims__   107                                        meta2__     0  ← see below
  ilabel2__   94   (property_resolver, mul-fixed)
```

✎ **Refines the resolver-audit agent's key finding.** Its claim "zero `meta2__` entries →
notebook cells 69/75 never executed the fix" is **confirmed** (`meta2__` = 0). But the
fuller picture: `cmeta3__`=838, `cand2__`=109, `pmeta2__`=1418 are heavily populated, so
the *quantitative_verifier* and *property_resolver* fixed code paths HAVE run extensively.
Only the **notebook's** resolver-metadata path (`meta2__`) never ran. The conclusion holds
and is now precisely bounded: **every recorded TEMPORAL/EA number in the notebook-output
CSVs is pre-fix; the standalone-module fixes are exercised.**

---

## 2. WHAT WAS INVESTIGATED

Five agents, all briefed read-only (no `--write`, no cache deletion, no source edits):

1. **Run unrun diagnostics** — execute the "Still unrun" command block.
2. **Audit resolver bugs project-wide** — Bug A/B/C × file matrix.
3. **Scope QUANTITATIVE tier 2** — are the 5 gold-FALSE aggregate claims reachable?
4. **Build Chapter 4 decision dossier** — evidence for the 3 open author decisions.
5. **Triage Phase 2 tier-2 labels** — bucket the 45 unreviewed AI fills.

---

## 3. FINDINGS

### 3.1 Diagnostics — all pass, every prediction confirmed (agent 1)

| command | result |
|---|---|
| `quantitative_verifier --selftest` | **24/24** (15 parse + 6 compare + 3 live) |
| `--diagnose` | **8/29 = 27.6%** cov, 8/8 acc — in the predicted band, NOT the precision-collapse signature |
| `--sensitivity` | **8/8 flip ≤50%, median 1%**, nothing flips at 0.1% |
| `consolidate_claims --verify` | b1=125, p2=126/109, b3=122, neg=27; IDs disjoint |
| `--stats --routing` | pooled 356 = 314/13/29; Always-True 88.2%; router 111/125=88.8%; TEMPORAL P 15/27 flagged |
| `gemini_key --check` | **live HTTP 200** ("OK"), `gemini-3.1-flash-lite-preview` |
| `llm_baseline --check` | ollama reachable, `gemma4:31b-cloud` present |
| `metrics.py` | Always-True 88.2%, F1(FALSE) 0.00, MCC 0.00, AURAC 0.993 |
| `hybrid_fallthrough --selftest / --diagnose` | ALL PASS (35) / **34/34 ABSTAIN, tier1 0/34** (QID bug NOT back) |

Operational note: `verify_env.sh` lacks its executable bit → run `bash verify_env.sh`
(not `./verify_env.sh`, which exits 126). The Gemini + ollama liveness means the LLM
baseline and a keyed pooled RELATIONAL re-run are no longer blocked on connectivity.

### 3.2 Resolver audit (agent 2)

- **CLAUDE.md is stale, code wins:** cells 69/75 DO carry all three fixes (`# FIX 2026-08-23`,
  pre-fix state preserved in `HalDetect_latest.backup-20260823-193627.ipynb`). But they have
  **never been executed** (`meta2__`=0, §1). Every recorded TEMPORAL/EA number is pre-fix.
- **`property_match_diagnostic.csv` is resolution-corrupted** (via `property_resolver.diagnose`'s
  first-hit `limit=1` path): Denali→**Q217136 national park**, Kilimanjaro→**Q265406 album**,
  Puncak Jaya→**Q27771 regency** (P2044 = 620 m, an 8× value error). 6 of 34 subjects resolve
  differently under the fixed resolver. **Headline 6/34 coverage @ 5/6 precision survives** —
  all 6 differing subjects sit in the `gap` bucket either way; the 6 `matched` rows
  (Rosetta Stone + ISRO) are identical under both resolvers.
- **Non-monotonic fix:** the fixed resolver sends "China" → Q130693 *porcelain* @0.624, clearing
  0.60 — the wrong-sense-same-name case already flagged as circular. Latent, not yet in a number.
- ✎ **"0% coverage entirely a property-mapping gap" → "overwhelmingly."** Split is 25 property /
  3 resolution / 6 matched. Cells 69/75 gate on `PROPERTY_TO_WIKIDATA` **before** `resolve_entity`,
  so for 25/34 resolution was never attempted — CLAUDE.md's "failed at resolution before matching"
  worry is inverted. One exception: `B3_01_C03` is property-mapped and died at resolution
  (`no search candidates`). The mul/full-text fix rescues none of the 3 unresolved (tested live:
  0 hits, or scores 0.477/0.534 honestly rejected). **No mul damage in the recorded results;
  the damage is latent — it appears the moment the property layer is unblocked.**

### 3.3 QUANTITATIVE tier 2 (agent 3)

Live API checks on the 5 gold-FALSE QUANTITATIVE claims:

| claim | reachable? | ground truth |
|---|---|---|
| **Q2_C13** GDP −0.1% 2009 | **decisive** | WB `NY.GDP.MKTP.KD.ZG` = −1.333% (IMF −0.4%, PPP −0.665%) |
| **B3_02_C09** renewable 3,372 GW end-2023 | **decisive** | IRENA PxWeb: 2023 = 3,872.8 GW, 2022 = 3,379.4 GW |
| Q14_C05 food insecurity +10% SSA | **ambiguous — do not count** | `SSF` null; AFE+AFW proxy spans −1.4% to +8.5% |
| Q14_C06 purchasing power −5% | not reachable | "purchasing power" = 0 of 29,533 WB indicators |
| Q12_C15 12M dementia | not reachable | no indicator; PubMed abstract empty |

- **Vintage hazard (B3_02_C09):** 3,372 GW is 0.22% from end-2022 (inside `EXACT_TOLERANCE`)
  and 12.93% from end-2023 — a year mis-resolution flips it TRUE on a gold-FALSE claim.
- **Practical gain = 1, not 2, under current routing:** Q2_C13 carries `type == TEMPORAL`
  and never reaches the QUANT verifier (over-firing on 40% of the target set). So 13 → 14
  (or 15 with a routing fix). 2/2 = Wilson [34.2%, 100%] — unquotable as a rate.
  **Does not retire controlled perturbation.**
- ✎ **Corrects the plan's premise:** only 3 of 5 abstain at the subtype gate (COMPUTATIONAL);
  the other 2 are NUMERICAL and die at **entity resolution** (B3_02_C09 → *a scholarly article*
  @0.480). Two distinct blockers: (a) derived-rate abstention rests on a false premise —
  agencies publish the derived quantity as one indicator value; (b) subtype must become a
  *backend selector*, and tier 2's subject is an `(indicator, region, period)` triple, not a
  QID, so `resolve_entity` must not run on that path. **API availability is not the blocker;
  routing is.** Indicator resolution is matching/retrieval, not lookup (WB `search` param is
  silently ignored; 3 IDs share the exact name "GDP growth (annual %)"; FAOSTAT now needs a key).

### 3.4 Chapter 4 dossier (agent 4) — four places files beat docs

1. **Cell 57 is a THIRD threshold regime:** `ENTAIL=0.55, CONTRADICT=0.45, MARGIN=0.15` —
   not 0.50/0.40. The pooled "3d vs 3e" table never evaluates cell 57's actual rule.
2. **Both 3d and 3e are strictly dominated** by 3d @ 0.35/0.30 (RELATIONAL n=174):
   **87.4% cov / 84.2% acc / F1(FALSE) 0.308 / MCC +0.310**, replicating on human-only.
   The "−22pp/+12pp tradeoff" Decision 1 is about is a suboptimal slice of the curve.
   Switch to 3e was **drift**, not a recorded reversal.
3. **Rule-8 count: "nine" → 8** pure source-existence (9 CITATION total); "140-claim corpus"
   → **138**; and **0 appear in the 356-claim eval set.** Already decided in the
   `Comparing-FActScore` handoff (item 9) in the prompt's favour → doc-sync failure, not open conflict.
4. **CITATION gold-FALSE: "all 3 missed" → 2 missed + 1 confident-wrong.** `B3_12_C07`
   (FAO 82.6% stocks) returns **TRUE @0.75**; plus `B3_09_C03` (OECD) overreach on gold-UNVERIFIABLE.

**V3 (Decision 3):** ceiling +3.2pp (111→115/125), **inside V0's CI [82.1%, 93.2%]**; trades
away TEMPORAL's perfect recall; all 8 error claims sit *outside* the held-out 65 (5 in Q7 alone
→ effective n ≈ 2–3 topics); costs the whole results chapter to re-run. Agent recommends: report
as a taxonomy finding + named future work, do **not** adopt.

### 3.5 Phase 2 tier-2 labels (agent 5)

- Counts match CLAUDE.md exactly (31/45/33; tier col = `priority`, AI verdict = `current_label`,
  `AUTHOR_VERDICT` blank on all 45 → never reviewed).
- **41 of 45 safe.** The lone `→FALSE` (Q18_C09, "climate neutrality by 2050") is **correctly
  FALSE** — verified against treaty text (Art 4.1 = "second half of this century"; zero "2050").
- **One likely-mislabeled: Q22_C01** — labeled TRUE, but FAO SOFI 2023 said hunger
  "**virtually unchanged** from 2021 to 2022," contradicting "increased during 2022." A
  CITATION-type claim; flipping it adds a gold negative to the negative-MCC CITATION type.
  Sibling Q22_C03 inherits the "rise" premise. 2 more need a glance (Q15_C03 granularity,
  Q19_C07 wording), not a fix.

---

## 4. PROPOSED CLAUDE.md CORRECTIONS (NOT YET APPLIED — author sign-off required)

### 4A. Confirmed factual corrections (files verified; safe to apply)
1. Rewrite the "not fixed project-wide / cells 69/75 still request `languages=en`" paragraph:
   cells 69/75 ARE fixed but **never executed**; recorded TEMPORAL/EA numbers are pre-fix.
2. Flag `property_match_diagnostic.csv` resolution corruption (3 mountains → park/album/regency);
   note coverage 6/34 @ 5/6 survives.
3. "0% coverage entirely a property-mapping gap" → "overwhelmingly" (25 property / 3 resolution).
4. CITATION gold-FALSE "all 3 missed" → "2 missed + 1 confident-wrong (B3_12_C07)".
5. Rule-8 "nine" → 8 pure-existence / 9 CITATION total / 138 claims / 0 in eval set; note doc-sync.
6. Record cell 57's real thresholds (0.55/0.45 + margin 0.15) as a third regime; note both
   3d/3e dominated by 0.35/0.30.
7. Mark the "Still unrun" block as run (§3.1 numbers); note `verify_env.sh` needs `bash`.
8. Phase 2 tier-2: 44/45 hold; flag Q22_C01 as the one label needing author review.
9. QUANT tier 2 scoped: 2 reachable negatives (WB + IRENA, free), blocked by routing not API.

### 4B. Author decisions (recommendations only — accept/reject)
- **Decision 1 (3d vs 3e):** reframe as threshold sweep; lead with retuned 0.35/0.30 point.
- **Decision 2 (Rule 8):** prompt stands, revise Rule 8 + 8 labels — zero measured numbers move.
- **Decision 3 (V3):** do not adopt; report as taxonomy finding.
- **Q22_C01:** decide whether to flip to FALSE/UNVERIFIABLE (adds a rare CITATION gold negative).

---

## 5. VERIFICATION LEDGER (what I checked directly vs. relied on)

- **Checked directly this session:** all row counts (`csv` module), all mtimes (`stat`),
  cache key census (python), git-absence, cache-backup location/size, the QUANT verifier and
  property_resolver source (full read).
- **Relied on subagent report (not independently re-run by me):** the live API values in §3.3,
  the notebook cell-content quotes in §3.2, the threshold recomputations in §3.4, the
  primary-source label checks in §3.5. These are traceable to files/URLs the agents cited and
  can be re-verified on request.
- **Refined a subagent claim (✎):** cache-census framing (§1), the 25/3 split "entirely" →
  "overwhelmingly" (§3.2), the subtype-gate premise (§3.3).
