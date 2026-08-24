# Claim-set inventory and routing measurement — 2026-08-22

Purpose: the authoritative account of **which gold claim data exists**, what each file's
schema actually is, and which measurements the data can and cannot support. Written
because the project had been evaluating on 122 claims while 356 labeled claims existed.

Everything below was verified by **grepping the files directly** (per the CLAUDE.md
standing rule), not from any prior doc. No code execution was available when this was
written — the Bash safety classifier was down — so every number here comes from `grep -c`
/ `grep -oP | sort | uniq -c` and hand arithmetic. Re-derivation commands are given so
each figure can be re-checked independently.

---

## 1. The four claim sets

All four are **mutually disjoint** by claim ID. There is no overlap to deduplicate.

| Set | ID range | File | rows | labeled | TRUE | FALSE | UNVERIF |
|---|---|---|---|---|---|---|---|
| Batch 1 | `Q1`–`Q14` | `archive/csvs/haldetect_claims_20260524_045439_2.csv` | 126 | **125** | 112 | 8 | 5 |
| Phase 2 | `Q15`–`Q26` | `current/haldetect_phase2_goldlabeled (3).csv` | 126 | **109** | 87 | 1 | 21 |
| Batch 3 | `B3_01`–`B3_12` | `current/haldetect_claims_b3_gold.csv` | 122 | **122** | 115 | 4 | 3 |
| Negatives (synthetic) | `B3N_01`–`B3N_27` | `current/relational_negatives_batch3_merged.csv` | 27 | **27** | 0 | 27 | 0 |
| **Total** | | | 401 | **383** | 314 | 40 | 29 |

**Real (non-synthetic) gold = 356 claims: 314 TRUE / 13 FALSE / 29 UNVERIFIABLE.**

> **Batch 1 was hiding in `archive/`.** The bare-named `haldetect_claims_20260524_045439.csv`
> carries **no** gold labels; only the `_1` and `_2` variants do. The 2026-08-21 reorg filed
> `_1`/`_2` as `(1)`/`(2)` browser-download duplicates — but they are the *only* labeled
> copies of Batch 1. A textbook instance of the standing rule: the suffix was treated as
> provenance when it was not.

### Per-type totals (real gold only, n = 356)

| gold_type | Batch 1 | Phase 2 | Batch 3 | **Total** | FALSE | UNVERIF |
|---|---|---|---|---|---|---|
| RELATIONAL | 73 | 64 | 47 | **184** | 4 | 26 |
| TEMPORAL | 15 | 26 | 12 | **53** | 1 | 0 |
| QUANTITATIVE | 17 | 0 | 29 | **46** | 5 | 1 |
| ENTITY_ATTRIBUTE | 9 | 13 | 22 | **44** | 0 | 1 |
| CITATION | 11 | 6 | 12 | **29** | 3 | 1 |
| **Total** | 125 | 109 | 122 | **356** | 13 | 29 |

Phase 2 contributes **zero** QUANTITATIVE claims. ENTITY_ATTRIBUTE still has **zero gold
negatives across all 44 claims** — controlled perturbation is the only route to
discrimination there, exactly as for QUANTITATIVE (§4).

Re-derive any row with:

```
grep -o ',\(TEMPORAL\|RELATIONAL\|ENTITY_ATTRIBUTE\|CITATION\|QUANTITATIVE\),\(TRUE\|FALSE\|UNVERIFIABLE\),' <file> \
  | sort | uniq -c | sort -rn
```

### Why this matters statistically

Pooling drops the degenerate **Always-True** baseline from **94.3%** (Batch 3 alone) to
**88.2%** (356 real claims), or **82.0%** including the synthetic negatives. A weaker
degenerate baseline is a *better* evaluation, because it leaves more headroom for a real
system to demonstrate skill.

The bigger gain is interval width. RELATIONAL goes 47 → 184 raw claims; at its measured
55.3% coverage that is ~102 covered rather than 26:

| Quantity | Point | 95% Wilson CI | ± |
|---|---|---|---|
| RELATIONAL accuracy, Batch 3 only (21/26) | 80.8% | [62.1%, 91.5%] | ±14.7pp |
| RELATIONAL accuracy, pooled (≈82/102 projected) | 80.8% | **[72.1%, 87.3%]** | **±7.6pp** |

The Batch-3-only interval **cannot separate 80% from 65%**; the pooled one can. This is the
single largest evaluation improvement available **with no new annotation** — the labels
already exist. (Projection assumes coverage and accuracy hold on the new batches; it is a
sample-size projection, not a result. Verify by actually running the verifiers on the
pooled set.)

---

## 2. Four different schemas — and two silent value-encoding traps

| Set | cols | header |
|---|---|---|
| Batch 1 | 14 | `q_id,claim_id,claim,type,drift,flagged,subject,property,value,secondary,gold_type,gold_verdict,notes,source_q` |
| Phase 2 | 15 | `…,gold_verdict,notes,triage_flag,triage_reason` |
| Batch 3 | 19 | `q_id,claim_id,claim,type,drift,flagged,pair_id,pair_incomplete,subject,property,value,secondary,extraction_failed,classification_fallback_used,gold_type,gold_verdict,notes,triage_flag,triage_reason` |
| Negatives | 12 | `claim_id,claim,type,subject,property,value,secondary,synthetic,injection_type,gold_type,gold_verdict,notes` |

**Common core (10 columns) present in all four:**
`claim_id, claim, type, subject, property, value, secondary, gold_type, gold_verdict, notes`

`q_id`, `drift` and `flagged` are absent from the negatives set. Batch 3 interleaves
`pair_id`/`pair_incomplete` *between* `flagged` and `subject`, so **column position is not
stable across sets** — never index these files by position.

### Trap 1: `flagged` has three encodings

| Set | encoding |
|---|---|
| Batch 1 | `TRUE` / `FALSE` (upper) |
| Phase 2 | `True` / `False` (title) |
| Batch 3 | `True` / `False` (title) |
| Negatives | column absent |

Verified: `grep -coP ',(?:RELATIONAL\|…),[0-9.]*,(?:True\|False),'` returns **0** on Batch 1
and **122** on Batch 3. A naive `pd.concat` produces a `flagged` column mixing `bool` and
`str`, which silently breaks any `flagged == True` filter on part of the data.

### Trap 2: `TRUE`/`FALSE` is overloaded across two columns

`flagged` (Batch 1, uppercase) uses the same tokens as `gold_verdict`. Any regex counting
verdicts must anchor on `gold_type` immediately preceding `gold_verdict`
(`,<TYPE>,<VERDICT>,`) or it will double-count. This produced a wrong labeled-row count
once already in this project before being caught.

### Which Batch 1 pass is authoritative: `_2`

`_1` and `_2` differ in exactly 8 rows, all in `gold_type`, verdicts identical. Router
disagreement count is **6 in `_1`** vs **14 in `_2`**, i.e. `_2` contains 8 *additional*
type corrections. **`_2` is the later, more-corrected pass and is authoritative.**

```
grep -cP ',(RELATIONAL|TEMPORAL|ENTITY_ATTRIBUTE|CITATION|QUANTITATIVE),[0-9.]*,(?i:true|false),.*,\1,(TRUE|FALSE|UNVERIFIABLE),' <file>
```

### Proposed unified schema

Add three columns that no existing file has, then left-join everything else as nullable:

```
batch, q_id, claim_id, claim, type, drift, flagged, subject, property, value,
secondary, gold_type, gold_verdict, gold_type_independent, synthetic,
injection_type, notes,
  # batch-specific, nullable:
  pair_id, pair_incomplete, extraction_failed, classification_fallback_used,
  triage_flag, triage_reason, source_q
```

1. **`batch`** (`b1` / `p2` / `b3` / `b3neg`) — mandatory, because the sets differ in
   *labeling protocol*, not just content (§3). Any pooled result must be sliceable by it.
2. **`gold_type_independent`** (bool) — `true` for Batch 1 only. **The single most important
   new column**: it is what prevents anyone, including a future session, from computing a
   circular routing accuracy off Phase 2 / Batch 3 (§3).
3. **`synthetic`** / **`injection_type`** — `false` / empty for the three real sets; carried
   through from the negatives set. Keeps synthetic rows poolable but always excludable.
4. Normalise `flagged` to a single lowercase `true`/`false`.
5. Leave `q_id` empty for negatives. Their `notes` field records a base claim
   (`"Base: B3_10_C17 pattern"`) but this is prose, not a parsed key — do not infer an ID
   from it.

---

## 3. `gold_type` is NOT an independent label in Phase 2 or Batch 3

Measured router agreement (classifier `type` vs human `gold_type`):

| Set | agreement | rate |
|---|---|---|
| Batch 1 (`_2`) | 111 / 125 | **88.8%** |
| Phase 2 | 109 / 109 | **100%** |
| Batch 3 | 122 / 122 | **100%** |

100% over 231 claims is not a result, it is an artifact. Confirmed independently: Batch 3's
classifier `type` distribution is **identical** to its `gold_type` distribution
(RELATIONAL 47, QUANTITATIVE 29, EA 22, TEMPORAL 12, CITATION 12). `gold_type` was seeded
from `type` and the human review touched **verdicts only, never types**.

**Consequences — treat as hard constraints:**

1. **Router / classifier accuracy can be measured only on Batch 1.** Any figure from
   Phase 2 or Batch 3 is 100% by construction. Never report it; never let it into thesis text.
2. Batch 1's own types went through **two** review passes (`_1` → `_2`), so they are the only
   types with evidence of genuine independent scrutiny.
3. The FEVER experiment in `paper_findings_2026-08-22.md` §6 — run our classifier over
   untyped FEVER claims to isolate router accuracy from verifier accuracy — is **not a
   "bonus experiment."** It is the only route to an independent routing measurement at
   scale, because our own gold set cannot provide one outside Batch 1's 125 rows.
4. If Phase 2 / Batch 3 types are ever needed as gold, they must be **re-labeled blind**.

---

## 4. Router accuracy and the TEMPORAL over-firing defect

**Batch 1 router accuracy = 111/125 = 88.8%, 95% Wilson CI [82.1%, 93.2%].**

All 14 errors, as `classifier type → gold_type`:

| n | Confusion |
|---|---|
| 8 | TEMPORAL → RELATIONAL |
| 3 | TEMPORAL → QUANTITATIVE |
| 1 | TEMPORAL → ENTITY_ATTRIBUTE |
| 2 | QUANTITATIVE → RELATIONAL |

**12 of 14 errors are the classifier over-predicting TEMPORAL.** Derived per-route figures
(counts reconstructed from the gold-type totals in §1 plus the confusion table above; they
sum to 125):

| Route | Classifier n | Correct | Precision | Recall |
|---|---|---|---|---|
| **TEMPORAL** | 27 | 15 | **55.6%** [37.3%, 72.4%] | 100% |
| QUANTITATIVE | 16 | 14 | 87.5% | 82.4% |
| RELATIONAL | 63 | 63 | 100% | 86.3% |
| ENTITY_ATTRIBUTE | 8 | 8 | 100% | 88.9% |
| CITATION | 11 | 11 | 100% | 100% |

### Root cause

The classifier routes on **presence of a temporal expression**, not on
**temporal-predicate-hood**. In every one of the 12 cases the date is a *modifier* and the
asserted predicate is something else:

* *"Buddhism spread from India to China **during the 1st century CE**"* → `spread_to`, a relation.
* *"Genghis Khan led Mongol conquests **in the 13th century**"* → `led_conquests`, a relation.
* *"Maritime trade routes replaced land travel **after 1453**"* → `replaced`, a relation.
* *"Infants receive their first dose **within 24 hours of birth**"* → a schedule attribute (EA), not a calendar date.
* *"The global GDP contracted by 0.1% **in 2009**"* → `growth_rate`, a quantity.

The fix is a routing rule, not a verifier change: **route on the predicate, and treat a
date as TEMPORAL evidence only when the date is the asserted value** — i.e. when the
extracted `value` (not `secondary`) is itself the time expression.

### Why this matters beyond the router

TEMPORAL's headline is 0% coverage / 0% accuracy on Batch 3, attributed in CLAUDE.md
entirely to a `PROPERTY_TO_WIKIDATA` mapping gap. This measurement shows **part of that gap
is a routing artifact**: if router precision on TEMPORAL is ~56%, then roughly **44% of the
claims the TEMPORAL verifier is asked to check are not temporal claims at all** and can
*never* resolve against a `time`-datatype property, no matter how good the property matcher
gets. Some fraction of "unmapped property" is really "misrouted claim."

The router precision figure above is measured on **Batch 1**, while the 0%-coverage figure
is from **Batch 3**, whose `gold_type` cannot supply an independent check (§3). So the
inference was tested a different way — by asking, of Batch 3's 12 TEMPORAL-routed claims,
how many actually assert a date in the extracted `value`.

### Confirmed independently on Batch 3: 4 of 12 are misrouted

| Claim | property | `value` | Asserts a date? |
|---|---|---|---|
| B3_01_C01 / C03 / C05 / C10 | construction_start_year, dissolution_year, took_over_project_year, inception_date | 1881, 1889, 1904, "August 15, 1914" | yes |
| B3_06_C02 / C05 / C10 | discovery_year, publication_year, decipherment_year | 1799, "196 BC", 1822 | yes |
| B3_08_C01 | diversion_start_date | 1960s | yes |
| **B3_02_C03** | solar_capacity_installed | *"more than the entire world in 2022"* | **no** — comparative quantity |
| **B3_06_C13** | duration_of_unreadability | *"1,500 years"* | **no** — a duration, which Wikidata stores as `quantity` (P2047), never as `time` |
| **B3_07_C02** | best_time | *"9.58 seconds"* | **no** — date is in `secondary` only |
| **B3_07_C05** | record_time | *"10.49 seconds"* | **no** — date is in `secondary` only |

**8/12 genuine → 33% misrouted on Batch 3**, against ~44% predicted from Batch 1's 55.6%
precision. Two independent batches, two independent methods, same conclusion. The inference
in this section is **established, not merely suggestive.**

Note the duration case specifically: even a claim that *feels* temporal (`1,500 years`) is
unreachable by this verifier by construction, because the TEMPORAL verifier filters
candidate properties to the `time` datatype and durations are `quantity`. Routing
"time-flavoured" claims to TEMPORAL is not the same as routing *date* claims there.

### The minimal pair — a natural experiment already in the data

Question `B3_07` yields 8 claims about the same two athletes and the same two records. The
router splits them across **two different verifiers**, and the discriminating feature is not
semantic:

| Claim | subject | property | value | adjunct in `secondary` | Routed |
|---|---|---|---|---|---|
| **B3_07_C05** | Florence Griffith-Joyner | `record_time` | 10.49 seconds | `{"date": "July 16, 1988"}` | **TEMPORAL** |
| **B3_07_C06** | Florence Griffith-Joyner | `record_time` | 10.49 seconds | `{"event": "Olympic Trials", "location": "Indianapolis"}` | **QUANTITATIVE** |

**Identical subject, identical property, identical value — different verifier.** The only
difference is that C05's adjunct is a *date* and C06's is a *place*. (The Bolt pair
C02/C03 shows the same split, slightly less cleanly, as the property names differ.)

This is the cleanest available demonstration that routing keys on **incidental temporal
expressions** rather than on the asserted predicate, and it needs no new annotation to
show — it is a controlled pair the dataset already contains. Use it as the worked example
in the thesis.

### Knock-on: the sprint gap is 8 claims, not 6, and no single verifier's diagnostics show it

`WORKLOG_2026-08-22.md` records a sprint-records **data-model gap** in the QUANTITATIVE
desk-trace — Wikidata stores records on the event/record item, not on the athlete, so 6 of
29 QUANTITATIVE claims are unreachable. Verified: exactly 6 (`B3_07_C01/C03/C04/C06/C08/C09`).
But B3_07_C02 and B3_07_C05 are **the same claim class sitting in TEMPORAL's bucket.**

So the gap really spans **8 claims across two verifiers**, both failing for the identical
reason, and **neither verifier's diagnostics will ever report more than part of it.** This is
a concrete instance of why action item #8 — log routing separately from verification —
is not bookkeeping: a defect split across two routes is systematically under-counted by
per-verifier evaluation.

**This is an independent, own-data instance of FinGround's central claim** (quoted in
`paper_findings_2026-08-22.md` §4): *"the bottleneck is routing rather than verification
difficulty."* Reaching that conclusion from our own confusion matrix, rather than only
citing it, is a materially stronger thesis position — and it makes action item #8 ("log
routing separately from verification") a measurement we can now partly report.

---

## 5. The QUANTITATIVE negatives are structurally unreachable — a real limitation finding

Pooling raises QUANTITATIVE gold negatives from 1 to 5. **None of the 5 is reachable by a
Wikidata-grounded verifier.** All five pair an *abstract-aggregate subject* with a
*derived-rate property*:

| Claim | subject | property | Why unreachable |
|---|---|---|---|
| `Q2_C13` global GDP contracted 0.1% in 2009 | `global GDP` | `growth_rate` | not a Wikidata item; per-year rate not a stored `quantity` |
| `Q12_C15` 12 million dementia cases preventable | `modifiable risk factors for dementia` | `preventable_cases` | not an entity; figure originates in a Lancet report |
| `Q14_C05` 10% rise in food insecurity | `food insecurity` | `increase_percentage` | not an entity; derived statistic |
| `Q14_C06` purchasing power −5% | `households in low-income countries` | `reduction_in_purchasing_power` | not an entity; derived statistic |
| `B3_02_C09` renewable capacity 3,372 GW | `renewable capacity` | (capacity) | IRENA statistic, no Wikidata home |

Plus the one gold-UNVERIFIABLE (`Q9_C09`, Sycamore *"10,000 years"*), which is comparative
against a hypothetical classical supercomputer — unverifiable in principle.

### This is systematic, not bad luck

**LLMs hallucinate numbers precisely where no grounded fact existed to recall.** Derived
statistics from institutional reports (World Bank, Lancet, IRENA) have no canonical
structured home, so the model interpolates. Conversely, the quantities Wikidata *does*
store — mountain elevations, populations — are high-frequency, heavily-attested facts that
models reproduce correctly. The result is an **anti-correlation between hallucination
likelihood and knowledge-graph presence**:

> The claims most likely to be hallucinated are the least likely to be in a knowledge graph.

This generalises past HalDetect — it is a limitation of KG-grounded verification as a
class, and it is worth stating as a finding rather than hiding as a coverage number.

### Three consequences

1. **Pooling does not fix QUANTITATIVE's evaluation problem.** 5 negatives, 0 reachable, so
   measured accuracy on gold data still reports the base rate. **Controlled perturbation
   (`quantitative_verifier.py --sensitivity`) is not a fallback — it is the only available
   discrimination measurement.** This retroactively justifies that design decision.
2. **It names tier 2 precisely.** The reachable evidence for these claims is
   *report-document numeric retrieval* (find the World Bank/IRENA/Lancet source, locate the
   figure) — which is substantially the **CITATION** backend. QUANTITATIVE tier 2 and the
   CITATION rebuild share a retrieval component and should be scoped together, not as two
   independent work items.
3. **It predicts where coverage can and cannot go.** Wikidata tier 1 can reach concrete
   physical/administrative quantities (the 7 Batch-3 mountain elevations via `P2044`) and
   essentially nothing else. The desk-traced ~24% predicted coverage is therefore close to
   a *structural ceiling* for tier 1, not an implementation shortfall.

### Precedent already in the repo for perturbation

`current/relational_negatives_batch3_merged.csv` is an existing, reviewed synthetic-negatives
set — 27 RELATIONAL claims, all gold FALSE, with a typed `injection_type`:

| injection_type | n |
|---|---|
| temporal_condition | 9 |
| magnitude | 8 |
| entity_swap | 3 |
| negation | 3 |
| directional | 3 |
| comparative | 1 |

So the project **already has a validated controlled-perturbation methodology**, including a
`magnitude` class that is exactly the QUANTITATIVE perturbation `--sensitivity` performs.
Reuse this taxonomy and the `synthetic`/`injection_type` column convention rather than
inventing a second one; it also gives the thesis a single consistent story about synthetic
negatives across verifiers.

---

## 6. Action list this inventory implies

| # | Action | Driven by |
|---|---|---|
| 1 | Consolidate all four sets into one schema with `batch`, `gold_type_independent`, `synthetic` | §1, §2 |
| 2 | Re-run RELATIONAL on the pooled 184 claims — largest CI win available, no new annotation | §1 |
| 3 | Never report routing accuracy off Phase 2 / Batch 3; mark it unmeasurable | §3 |
| 4 | Report Batch-1 router accuracy 88.8% [82.1, 93.2] + the per-route precision table | §4 |
| 5 | Fix routing to key on the predicate / on `value` being the date, not on date presence | §4 |
| 6 | ~~Check Batch-3 TEMPORAL-routed claims for non-date `value`~~ **DONE — 4/12 misrouted, inference confirmed** | §4 |
| 6b | Re-route the 2 sprint claims out of TEMPORAL; treat durations as `quantity`, not `time` | §4 |
| 7 | Treat `--sensitivity` as the primary QUANTITATIVE evidence, not a supplement | §5 |
| 8 | Scope QUANTITATIVE tier 2 together with the CITATION rebuild — shared retrieval | §5 |
| 9 | Reuse the `injection_type` taxonomy for all future synthetic negatives | §5 |
| 10 | Normalise `flagged`; never index these CSVs by column position | §2 |

Related: `paper_findings_2026-08-22.md` (literature), `WORKLOG_2026-08-22.md` (build log),
`../CLAUDE.md` §"Read this before quoting any accuracy number".
