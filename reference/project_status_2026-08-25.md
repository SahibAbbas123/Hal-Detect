# Project status, 2026-08-25 — verifier health, and a cache bug found today

Answers the question *"verifiers doing fine, got worse, or still need testing and
consolidation?"* with what the code does **today**, not what earlier docs recorded.
Everything below was re-run or re-derived on 2026-08-25; nothing is quoted from
CLAUDE.md without checking it against a file.

**One-line answer: nothing regressed, all five verifiers are off zero, and the
binding constraint has moved from *coverage* to *trustworthy negatives*. One new
bug found today (§3) partially invalidates the synthetic-negative measurements
but leaves the main RQ2 result intact.**

---

## 1. Health check — nothing has gotten worse

| check | result |
|---|---|
| `current/*.py` parse (19 files) | **19/19 ok**, 0 syntax errors |
| `metrics.py --selftest` | **PASS** — Always-True still 88.2%, F1(FALSE) 0.00, MCC 0.00 |
| `quantitative_verifier.py --selftest` | **PASS 24/24** |
| `hybrid_fallthrough.py --selftest` | **PASS**, all checks |
| `consolidate_claims.py --verify` | **PASS** — all 4 sets' row counts, labeled counts and verdict distributions match; all claim_ids disjoint |
| `llm_baseline.py --selftest` | **PASS** — 10/10 parser, cache keys stable and flag-sensitive |

The two bugs fixed on 2026-08-22 (the `quantitative_verifier.py:489` SyntaxError
and the Batch-1 126-vs-125 row expectation) have stayed fixed. `rq2_comparison.py`
reports MISSING against the main checkout only because it lives on the
`worktree-rq2-batch3-table` branch and is not merged yet.

## 2. Per-verifier status, with the trust level of each number

"Detection evidence" is the column that matters. Coverage and selective accuracy
on an all-positive slice cannot distinguish a working verifier from one that says
TRUE unconditionally.

| verifier | coverage | acc | detection evidence | trust |
|---|---|---|---|---|
| **QUANTITATIVE** | 27.6% (8/29 B3) | 8/8 | `--sensitivity` **8/8 flips at ≤1%**, none inside the 0.5% tolerance | **highest in the project.** Controlled perturbation, not accuracy |
| **RELATIONAL** | 55.3% (B3) / 52.3% (pooled 174) | 80.8% / 79.1% | 3 FALSE calls on B3, **0 correct** | coverage/accuracy solid and replicated; **detection unproven** |
| **CITATION L1** | 75.9% (22/29) | 90.9% | **structurally none** — L1 cannot emit FALSE | honest by construction; F1(FALSE)=0.00 is a *design* fact |
| **TEMPORAL** | 8.3% tier 1 → 91.7% hybrid | 90.9% hybrid | 30/33 on 36 TEMPORAL+EA negatives | **the number is a fall-through result** — tier 1 answered 2 of 36 |
| **ENTITY_ATTRIBUTE** | 22.7% (5/22 B3) | 5/5 | folded into the 36 above | zero gold negatives in B3; see §3 |

Two things this table makes visible that a coverage-only view hides:

- **QUANTITATIVE is the only verifier with a validated detection result**, and it
  got there by perturbation rather than by finding gold negatives.
- **CITATION's F1(FALSE)=0.00 is not a failure to fix.** Level 1 asks "does this
  source exist"; a source that fails to resolve is UNVERIFIABLE, not fabricated.
  Emitting FALSE there would be the confident-wrong class the QID fix eliminated.
  Scoring CITATION on fabrication needs Level 2, which is unbuilt.

## 3. NEW BUG (2026-08-25) — the NLI cache key truncates the claim to 60 chars

`archive/scripts/relational_verifier_phase3d.py:194`:

```python
cache_key = f"nli__{claim[:60].replace(' ', '_')}__{passage[:40].replace(' ', '_')}"
```

Two claims agreeing in their first 60 characters share one cache entry, and the
second silently inherits the first's `entail`/`contradict`. For synthetic
negatives this is close to a worst case: they are perturbations of claims that
were **all already scored in the 356-run**, both runs share
`nonrouted_cache.json`, and the perturbed value frequently sits *past* character
60.

**The smoking gun.** Three negatives inherit the score of the true claim they
were built to contradict:

| negative | claimed | inherits from | its gold | entail |
|---|---|---|---|---|
| `SYN_QUAN_027` | $707 billion | `Q2_C11` "$700 billion" | TRUE | 0.7222 |
| `SYN_QUAN_028` | $735 billion | `Q2_C11` "$700 billion" | TRUE | 0.7222 |
| `SYN_QUAN_032` | **$7000 billion** | `Q2_C11` "$700 billion" | TRUE | 0.7222 |

`claim[:60]` stops at `...provided $7`, so a 10× error and a 1% error produce the
same key. Likewise `SYN_QUAN_033`–`037` (1.2 / 1.4 / 1.7 / 2.2 / **11.0** °C
against a true 1.1) all carry entail 0.6139 / contradict 0.1117, inherited from
`Q5_C04`.

**Correction to a reading I nearly recorded:** those identical scores across a
10× change look like proof that BART-MNLI ignores numbers outright. They are not
— they are one cached score reused five times. The weaker claim does survive on
clean keys: `SYN_QUAN_010`–`013` have distinct keys and are still called TRUE,
including *"Mount Everest reaches 6,961 meters"* against 8,848.86 — a 21% error
scored entail 0.5272. NLI misses large numeric errors; it is not provably blind
to them.

### Blast radius — bounded, and the main result survives

| set | claims on a value-differing collision | effect |
|---|---|---|
| synthetic negatives (85) | 16 cross-file + intra-file → **18 rows** | material per-type |
| main 356-claim run | **8 of 356 = 2.2%** | not material |

- Of the **23** confident-wrong misses on negatives: **11 artifact, 12 genuine.**
- Of the **43** catches: 7 on collided keys, **36 clean.**
- Pooled recall barely moves: reported 43/85 = 50.6% → **clean-key-only 36/67 =
  53.7%.**
- Per type it moves a lot: **9 of QUANTITATIVE's 24 negatives are collided**, so
  the "baseline catches 9/24, is confidently wrong on 13/24" figure is not usable
  as stated.
- **RQ2's headline (77.2% cov / 69.8% acc) and the whole threshold sweep stand
  — verified by recomputation, not asserted.** Dropping all 8 collided rows and
  recomputing on the remaining 348:

  | | coverage | sel. acc | F1(FALSE) | MCC |
  |---|---|---|---|---|
  | 3d, all 356 (as reported) | 77.2% | 69.8% | 0.170 | **+0.180** |
  | 3d, collision-free (348) | 77.9% | 70.1% | 0.172 | **+0.180** |
  | 3e, all 356 | 53.7% | 81.2% | 0.174 | +0.144 |
  | 3e, collision-free | 53.7% | 81.8% | 0.178 | +0.147 |

  **Largest movement in any headline figure: 0.67pp**; 3d's MCC does not move at
  all. The threshold sweep recomputes from these same cached scores, so it
  inherits exactly this. (The recomputation also reproduced the recorded
  77.2/69.8/0.170/+0.180 exactly, which independently re-validates the stored
  verdict columns.)

### Fix

Key on a hash of the **full** claim + passage, not a prefix. Cheap to write, but
the affected rows need rescoring, and **BART-MNLI SIGBUSes locally** — so the
re-score is a Colab run of ~18 negative rows plus 8 positive rows, not a local
one. Bump the prefix to `nli2__` rather than reusing `nli__`; reusing it would
preserve the collisions while making the fix appear to work, which is the same
trap the `cmeta3__`/`cand2__` bumps were introduced to avoid.

## 4. What the negatives now make measurable — and the one gap left

There are **85 synthetic negatives, not 27** (`current/synthetic_negatives.csv`,
built by `make_negatives.py`): TEMPORAL 31, CITATION 25, QUANTITATIVE 24, EA 5,
all gold FALSE. The baseline has been scored on all 85
(`nonrouted_negatives_results.csv`). This is a **fifth claim set** and CLAUDE.md's
claim-set inventory does not list it.

Baseline recall on negatives, Phase 3d, **with the §3 caveat on QUANTITATIVE and
the 2 collided CITATION rows**:

| type | n | caught | recall | 95% CI | conf. wrong | abstain |
|---|---|---|---|---|---|---|
| TEMPORAL | 31 | 24 | 77.4% | [60%, 89%] | 4 | 3 |
| QUANTITATIVE | 24 | 9 | 37.5% | [21%, 57%] | 13 | 2 |
| CITATION | 25 | 5 | 20.0% | [9%, 39%] | 6 | 14 |
| ENTITY_ATTRIBUTE | 5 | 5 | 100% | **[57%, 100%]** | 0 | 0 |
| **POOLED** | **85** | **43** | **50.6%** | [40%, 61%] | 23 | 19 |

Phase 3e collapses to 14/85 = 16.5% — the margin gate abstains its way out of
detection, consistent with the threshold sweep's finding that contradiction
precision caps at 0.20 at every operating point.

EA's 5/5 is written **[57%, 100%]** and must never be quoted as "100%".

**Routed coverage of these 85:**

| slice | status |
|---|---|
| TEMPORAL + EA (36) | **measured** — routed 30/33 vs baseline 29/33. **+2.7pp, i.e. a tie**, and tier 1 answered only 2 of 36, so the routed system *is* the baseline on ~94% of them. Correctly recorded as a fall-through result, not a routing win. |
| QUANTITATIVE (24) | **NOT MEASURED — the highest-value gap in the project.** |
| CITATION (25) | **NOT MEASURED, and 0/25 is knowable a priori** — L1 cannot emit FALSE. Level 2 is what would score here. |

### Why QUANTITATIVE × 24 negatives is the highest-ROI experiment left

It is the one slice where routed and non-routed use genuinely different
machinery: structured numeric comparison at 0.5% tolerance versus sentence-pair
entailment. The baseline's clean-key misses (`SYN_QUAN_010`–`013`, 21% elevation
errors called TRUE) are precisely the cases a numeric comparator cannot miss, and
those four mountains are inside the P2044 coverage `--sensitivity` already
validated 8/8 on. It would convert the perturbation proxy into a real
gold-negative detection number on 24 claims — a small block, not a large run.

It is also the one place a routing win looks *likely* rather than hoped-for,
which is worth stating plainly given that on Batch 3 routing beats the baseline
on no measurable axis (`reference/rq2_routed_vs_nonrouted_batch3_2026-08-25.md`).

## 5. Consolidation debt — what is inconsistent right now

1. **CLAUDE.md's verifier table conflicts with the files.** It records TEMPORAL
   1/12 = 8.3% and EA 5/22 = 22.7% post-fix. **No file on disk yields EA 5/22**,
   and the 8.3% traces to the *pre*-fix file. CLAUDE.md's own QID-fix section says
   8.3% → 0% and names the phase2/phase4 files, which match. Author decision:
   correct the table row to 0%, or produce the run that yields 5/22.
2. **The claim-set inventory is missing the 85 synthetic negatives.** It lists
   four sets totalling 356; `synthetic_negatives.csv` is a fifth, and
   `external_negatives.csv` (75 rows) is a sixth that nothing has scored.
3. **Phase 3d vs 3e is still unresolved** as the reportable operating point. The
   negatives data adds a strong argument for 3d: 3e's recall on negatives is
   16.5% against 3d's 50.6%. A margin gate that abstains on 51 of 85 planted
   errors is not a better operating point for a *detector*.
4. **`rq2_comparison.py` and the RQ2 doc are unmerged**, on
   `worktree-rq2-batch3-table`.

## 6. Author decisions still open

Unchanged from the previous cycle, none of them resolvable by measurement:
RELATIONAL's headline operating point · the CITATION / Rule 8 contradiction
(prompt says source-existence is not CITATION, Rule 8 dual-emit says it is, nine
corpus labels agree with Rule 8) · the V3 taxonomy rule for TEMPORAL vs
RELATIONAL (**recommend not adopting** — it re-types the column every downstream
number rests on, for a ceiling of +0.8pp) · `Q22_C01` · plus §5.1 above.

## 7. Do not quote without the caveat

- EA negatives **5/5 → [57%, 100%]**.
- Baseline QUANTITATIVE recall on negatives — **9 of 24 rows are cache-collided**
  (§3). Recompute on clean keys or re-score before use.
- The TEMPORAL/EA hybrid's 91.7% / F1 0.91 — **a fall-through result**; tier 1
  reached 2 of 36 claims.
- Any routed-vs-baseline gap on Batch 3 — **4 gold negatives**; no CI separates
  anything.
