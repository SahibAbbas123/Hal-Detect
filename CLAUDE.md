# HalDetect

Thesis project (CSE 700, University of Chittagong): a taxonomy-routed post-hoc hallucination detection system for LLM-generated text. Claims are extracted from LLM output, classified into 5 types, and each type is checked by a purpose-built verifier rather than one generic "ask an LLM if this is true" step. Core research bet: structured, evidence-grounded verification trades some coverage for much higher reliability than open-ended LLM self-checking, in the domains where routing can reach.

## The 5 claim types and current verifier status

| Type | Method | Status |
|---|---|---|
| **RELATIONAL** | Wikipedia passage retrieval + NLI entailment (BART-MNLI) | Best performer. 80.77% acc / 55.32% cov on held-out Batch 3. Live logic = `current/HalDetect_latest.ipynb` cell 57 (`## Phase 3e (i)`) — no standalone `.py` is current. |
| **TEMPORAL** | Wikidata SPARQL lookup | **STILL ZERO in the live path — the "moved off zero" row was MISLABELED. Corrected 2026-08-26; see the correction note below this table.** Live logic = notebook cell 75 (`## Phase 2`); cell 73 is the superseded Phase 1. Verified from the output file itself: `current/temporal_b3_verified_results_phase2.csv` → TEMPORAL **0/12 covered, 12/12 UNVERIFIABLE, zero confident-wrong.** The `1/12 = 8.3%` figure is the **pre-fix** file (`temporal_b3_verified_results.csv`, 11 UNVERIFIABLE + 1 FALSE) and that single covered claim **is** the confident-wrong Panama Canal FALSE — so 8.3% was never a *correct* 8.3%. The `1/12` + `5/22` + `17.6% @ 5/6` triple describes the **unintegrated** `current/temporal_ea_verifier.py` + `property_resolver.py` path (1+5 = 6/34 = 17.6%, matching the 6/34 @ 5/6 recorded for `property_resolver.py` below) — **no results file for that run exists on disk, so it is unquotable until re-run.** |
| **ENTITY_ATTRIBUTE** | Wikidata SPARQL lookup | **STILL ZERO in the live path — same mislabeling as TEMPORAL. Corrected 2026-08-26.** Live logic = notebook cell 69 (`## Phase 4`); cell 67 is the superseded Phase 3. Verified from the file: `current/entity_attribute_b3_verified_results_phase4.csv` → EA **0/22 covered, 22/22 UNVERIFIABLE.** Pre-fix `entity_attribute_b3_verified_results.csv` is 1/22 = 4.5%, and that one covered claim **is** the confident-wrong Rosetta-Stone-as-*British-punk-band* FALSE. **`5/22 = 22.7%, all 5 correct` is reproduced by no file on disk** — it belongs to the unintegrated `property_resolver.py` path. The `P186=granodiorite` / `P407=Ancient Greek` / `P282=Egyptian Demotic` lookups are real (that is what the QID fix returns for Q48584), but "5 covered, all correct" is **not a measured result.** |
| **CITATION** | **Three** levels: does the source exist (L1), do the work's own properties contradict the claim (**L1b**), does it actually say this (L2, unbuilt) | **Level 1 rebuilt and off zero 2026-08-23.** `current/citation_l1_verifier.py`: **75.9% coverage (22/29), 90.9% accuracy (20/22), AURAC 0.934** — was 0/12. Replaced both hardcoded dicts (`ORG_URL_MAP`, `TRIVIALLY_KNOWN_ORGS`) with Wikidata resolution via the fixed resolver. **Level 1 can never return FALSE** — a source that fails to resolve is UNVERIFIABLE, not fabricated — so F1(FALSE)=0.00 by construction and all 3 gold-FALSE CITATION claims are missed. **Level 1b BUILT 2026-08-26** and it is the first thing in the project to return CITATION FALSE: `current/citation_l1b_verifier.py`, `--selftest` ALL PASS, **TPR 9/25 = 36.0% on the negatives against FPR 0/25 on the gold-TRUE natural claims → J = +0.360 vs the baseline's +0.128** on the same type. Caveat that must travel: **8 of the 9 detections come from one Wikidata item (Q103843442, IPCC AR6) — one work working, not CITATION working**, and the TPR CIs overlap the baseline's. Level 2 (attribution) is still unbuilt: it needs NLI, which SIGBUSes locally, and NLI contradiction precision caps at 0.20 anyway. Old `current/citation_verifier.py` retains the tautology; do not use it. Full analysis `reference/citation_l1b_result_2026-08-26.md`. |
| **QUANTITATIVE** | Structured extract-and-compare vs. Wikidata `quantity` statements (**not** NLI) | **WORKING, and as of 2026-08-25 the one type where routing BEATS the baseline on a prior-independent metric.** `current/quantitative_verifier.py`; selftest **24/24**. Measured on gold negatives at last: **14/14 correct across 14 covered claims with BOTH classes present, 0 confident errors, MCC +0.378 vs the baseline's best +0.202.** On 4 claims both systems answer confidently and disagree — routed 4/4, baseline 0/4. Batch 3 alone: 8/29 = 27.6% cov, 8/8. Negatives alone: 6/24 = 25.0% cov, 6/6. Full analysis `reference/rq2_quantitative_negatives_2026-08-25.md`; reproduce with `current/rq2_quantitative_table.py` (offline). NUMERICAL works; COMPARATIVE + COMPUTATIONAL abstain by design. |

### Correction 2026-08-26 — the TEMPORAL/EA "moved off zero" rows were mislabeled, and the stale numbers ESCAPED THIS FILE

Verified directly from the four result CSVs, not from any doc:

| file | TEMPORAL | EA | confident verdicts |
|---|---|---|---|
| `temporal_b3_verified_results.csv` (**pre**-fix) | 1/12 = 8.3% | — | 1 FALSE — **the Panama Canal confident-wrong** |
| `temporal_b3_verified_results_phase2.csv` (**post**-fix, live) | **0/12** | — | none |
| `entity_attribute_b3_verified_results.csv` (**pre**-fix) | — | 1/22 = 4.5% | 1 FALSE — **the Rosetta-Stone-punk-band confident-wrong** |
| `entity_attribute_b3_verified_results_phase4.csv` (**post**-fix, live) | — | **0/22** | none |

**This file already said so, two sections down** — *"coverage moved 8.3%→0% (TEMPORAL) and
4.5%→0% (EA) because the only 'covered' claims had been the wrong ones."* The summary
table contradicted its own QID-bug section for three days. When two parts of this file
disagree, **the section with a named file and a row count wins over the summary table.**

**The numbers were not invented, they were misattributed.** `1/12` + `5/22` = `6/34` =
17.6%, exactly the `6/34 @ 5/6` recorded for the **unintegrated** `property_resolver.py`.
So the triple describes a real design — just not the live notebook cells, and **no results
file for that run exists on disk.** `temporal_ea_hybrid_b3.csv` (34 rows) is a *different*
run: 28/34 = 82.4% coverage, 6 FALSE, and **all 34 rows are gold TRUE, so all 6 are
wrong** — the third occurrence of coverage-up/precision-down, and unquotable per WORKLOG.

**Why this correction was worth making immediately: the stale numbers left the project.**
An external technique catalog (`~/.gemini/.../modern_techniques_for_haldetect.md`, read
2026-08-26) states TEMPORAL 8.3% and EA 22.7% in its "Your Current Stack" table and ranks
its recommendations against them. A wrong number in this file became a wrong premise in a
roadmap that would have driven architectural decisions. **Correct stale rows when found,
not when convenient.**

Note on `mtime`: all files under `current/` in this worktree share `2026-08-25 02:40`, the
worktree copy time. **`mtime` is uninformative here** — the standing rule's other two
signals (row counts, content markers) are the ones that worked.

## The standing rule

**Never trust a filename, a `(1)`/`(2)`/`(3)` suffix, or a doc's description of a file — always verify row counts, `mtime`, and specific content markers directly against the file itself.** This has been the single biggest source of wasted effort across the project. The 2026-08-21 workspace reorganization (`WORKSPACE_AUDIT.md`) found two cases where even `reference/haldetect_fingerprints.md` itself didn't hold up against actual file content — verify, don't assume, even against prior docs.

## Entity-resolution QID bug — FIXED 2026-08-21

The "accept first candidate with a non-empty property result" heuristic used `has a value for this PID` as a proxy for `is the right entity`. Replayed against live Wikidata, that premise **inverts**: in both confirmed cases the correct entity was already search hit #1 and was *discarded* for lacking the property, promoting a wrong-sense homonym that had it.

- Panama Canal: Q7350 (correct) has no P571 → fell through to Q498979 *Panama Canal Zone*, P571=1903 → FALSE @0.8 on a gold-TRUE claim. Truth was one property away: Q7350 **P1619** = 1914-08-15.
- Rosetta Stone: Q48584 (correct) has no P527 → fell through to Q4048553, a *British punk rock band*, P527=['Porl King'] → FALSE @0.8 on gold TRUE. Truth: Q48584 **P186** = granodiorite.

**Fix:** `resolve_entity(subject, ctx, cache)` now scores candidates on their own label/alias/description (lexical tier + SBERT similarity, `RESOLUTION_THRESHOLD = 0.60`), commits, *then* queries the property. Empty property → honest UNVERIFIABLE naming the mapping gap. New `resolution_score`/`resolution_detail` columns make resolution auditable. Failed API calls are never cached (the cache-poisoning bug fixed earlier in RELATIONAL).

Calibrated over all 34 Batch 3 TEMPORAL+EA subjects: at 0.60, **15/15 accepted resolutions are correct**; every wrong one falls below (Denali→"album by Denali" 0.590, SpaceX Starlink→a journal article 0.547, China 0.510, "Egyptian texts"→a Wikimedia category 0.483, "Nominations" 0.355). One correct-but-weak rejection: "United States" 0.447 (its claims are unmapped anyway).

**Both confident-wrong verdicts are now honest gaps; zero remain on Batch 3.** Accuracy was already 0% on both verifiers, so nothing correct was lost — coverage moved 8.3%→0% (TEMPORAL) and 4.5%→0% (EA) because the only "covered" claims had been the wrong ones. Results: `current/temporal_b3_verified_results_phase2.csv`, `current/entity_attribute_b3_verified_results_phase4.csv` (originals kept for comparison).

### A SECOND resolution failure mode — FOUND 2026-08-22 evening, FIXED 2026-08-23

The 2026-08-21 fix removed *property-gated* selection. It did not add any notion of **prominence**, and `quantitative_verifier.py --selftest` exposed the gap: 6/6 offline comparison cases passed, **0/3 live Wikidata cases passed, and all three failed at resolution rather than property matching.**

    ST_everest      -> Q19977041 @0.797   "entity has 6 properties but none of datatype ['quantity']"
    ST_denali       -> Q554469   @0.74     best property candidate P2045 (orbital inclination)
    ST_everest_bad  -> Q19977041 @0.804    same wrong entity

Three distinct bugs, all now fixed in `current/quantitative_verifier.py`. **Selftest 21/24 → 24/24.**

**Bug A — identity score cannot break ties.** `score = 0.5*TIER_NORM + 0.5*sim` gives tier 3 to *any* entity whose label is literally "Mount Everest", so the real mountain (Q513) and a stub both land near 0.5+0.5·sim and the sort picked whichever was higher by a hair. Fixed with a **prominence tie-break on sitelink count** (`RESOLUTION_TIE_BAND = 0.10`), applied only among candidates within the band of the leader. **Prominence never enters the number compared to `RESOLUTION_THRESHOLD`** — that is the safety property, and it means the 2026-08-21 calibration is arithmetically untouched: a famous wrong entity still cannot be promoted past 0.60 by being famous ("China" 0.510, SpaceX Starlink 0.547, Denali-the-album 0.590 all still fail). The band is also below 0.17 = 0.5·(TIER_NORM[3]−TIER_NORM[2]), so a tier difference can never be tied away. Live proof: Q513 (237 sitelinks) now beats a **band** called Mount Everest that scored *higher* (0.835 vs 0.806).

**Bug B — `wbsearchentities` is prefix-only.** Searching `"Denali"` returns 8 items and **omits Q130018, whose English label is literally "Denali"**, while `"Mount McKinley"` returns it as hit #1; `"Denali mountain"` returns **nothing**, because a descriptive phrase is not a label prefix. **This is the same bug class the RELATIONAL verifier already fixed** by moving `action=opensearch` → `action=query&list=search` (coverage 31.51% → 89.06%). Candidates now come from prefix search **unioned with** full-text search on the subject and on subject+context.

**Bug C — Wikidata labels under `mul`, and this is the significant one.** Wikidata stores language-agnostic labels under the pseudo-language `mul`, and a large, growing class of items has **no `en` label at all**:

    Q130018 (Denali)       en=None             mul='Denali'
    Q554469 (6194 Denali)  en=None             mul='6194 Denali'
    Q513  (Mount Everest)  en='Mount Everest'  mul=None

Requesting `languages=en` returned an **empty label** for Denali, so the lexical tier could only match its aliases — `['Mount Denali', 'Mt. Denali', 'Bolshaya Gora']`, none of which equals "Denali". **The correct entity was scored as though it were not even named Denali, and lost to an asteroid.** This is the worst case, not an edge case: **proper nouns are the class most likely to live in `mul`**, since a proper noun is the same string in every language — and proper nouns are exactly what entity resolution resolves. Fixed with `languages=en|mul` and en-preferred fallback (labels, descriptions and aliases).

**Cache prefixes were bumped (`cmeta3__`, `cand2__`).** Reusing `cmeta__`/`cmeta2__`/`search__` would have preserved each bug while making the fix appear to work — the same discipline that caught the earlier cache-poisoning bug.

**`mul` and full-text are NOT yet fixed project-wide.** `property_resolver.py` and notebook cells 69/75 still request `languages=en` and still resolve via prefix search, on the same proper nouns. **This means TEMPORAL/EA's recorded "0% coverage, entirely a `PROPERTY_TO_WIKIDATA` gap" diagnosis may be partly wrong** — some of those claims may have failed at resolution, with the entity silently unnamed, before property matching was ever reached. Re-measure rather than assume.

### A THIRD resolution failure mode — editions of a serial publication (found 2026-08-25, FIXED 2026-08-26)

The 08-21 fix removed property-gated selection; the 08-23 fixes added prominence,
full-text search and `mul` labels. **Neither addresses this, and it is live.** Found
by `current/citation_negatives_analysis.py --reachability`; full account in
`reference/citation_negatives_headroom_2026-08-25.md`.

Asked for `Lancet Commission on dementia prevention`, the resolver **accepted**:

    Q92676744  @0.605  'The Lancet Commission on Dementia Prevention, ... a call
                        for action'          (2019 article, 0 sitelinks)  <- CHOSEN
    Q139937996 @0.597  '... 2024 report of the Lancet standing Commission'
    Q98186330  @0.595  '... 2020 report of the Lancet Commission'  <- THE RIGHT WORK

Three scores spanning **0.010**, covering the 2019 / 2024 / 2020 works, and the
correct one is **rejected by one hundredth of a point**. The accepted item's
`P577 = 2019-06-01` would falsify the gold-TRUE claim *"The 2020 Lancet Commission
identified 12 modifiable risk factors…"* — **a confident-wrong FALSE, the exact
class the QID fix drove to zero.** `Poverty and Shared Prosperity` shows it twice
over: the accepted item is the **2020** edition, `P577` is **absent**, and two
byte-identical duplicate items tie at exactly **0.654**.

**Why the existing fixes cannot touch it.** Every candidate has **0 sitelinks**, so
the prominence tie-break is inert by construction — it breaks ties on fame, and no
edition of a serial is famous *as an edition*. Editions share nearly all of their
label, and the token that discriminates them is **the year, which is the value under
test**. Resolving the edition therefore uses the claimed value to pick the entity
that will judge the claimed value.

**The non-circular design:** resolve the **series**, enumerate edition years from
`P577` across its members, and test the claimed year against the **span** of those
years — the year then tests and never selects. On the Lancet rows this detects 3
of 5 with no confident-wrong risk, versus 5 of 5 with it. **Take the 3.** Any
CITATION or TEMPORAL work-date check must do this before it ships.
*(This paragraph originally said "membership in the series". That contradicted the
"Use a span rule, not set-membership" ruling two sections down, which is the correct
one and is now what shipped — see below. Corrected 2026-08-26.)*

#### BUILT 2026-08-26 — `current/series_resolver.py`, `--selftest` ALL PASS (commit `1849791`)

**Non-circularity is enforced by the interface, not by discipline.**
`resolve_edition_span(subject, cache, ctx)` **has no year parameter at all**; only
`test_year_in_span(claimed_year, span_result)` ever sees a claimed year, and a selftest
asserts via `inspect.signature` that no parameter name contains `"year"`. A rule you can
break by editing one line is not a guarantee; a signature that cannot express the
violation is.

**Widen, don't re-pick.** Tie-band membership decides *who is in the comparison set*,
never *how to rank it*. The span is taken across **all** competing editions, so a FALSE
verdict holds under **any** resolution of the edition ambiguity — it survives the very
ambiguity that caused the bug. (My first rationale for this was wrong: I claimed label
clustering fails to separate the editions. It does not — all three Lancet works cluster
at J ≥ 0.75, because `_STOP` strips `report`/`of`/`the`. The real reason is the one just
given.)

**No TRUE verdict, by design.** Inside the span means *"not refutable from publication
dates"*, never *"confirmed"*.

**Three guards. Two of them exist only because the module was run against live Wikidata —
reasoning about it would not have found either, and both bugs were the exact confident-wrong
class the task was written to remove.**

| guard | what it fixes |
|---|---|
| **1 — harvest years from labels too** | Q139937996 *is* the real 2024 Lancet report and its `P577` is simply **absent**, so the span closed at 2020 and `year 2024 → FALSE`. Years are read off the **entity**, never the claim (so no circularity), and can only ever **widen** a span — a spurious hit costs coverage, not correctness. |
| **2 — an undated member is a HOLE, not a zero** | No `P577` *and* no label year → hole of unknown position → FALSE outside the observed range is unsound in **both** directions → `INCOMPLETE_SPAN`, `span=None`, abstain. |
| **3 — a degenerate span is the most AGGRESSIVE rule, not the most conservative** | **Guard 1 caused this one.** Two byte-identical duplicates of the *2020* World Bank edition both yielded `label_years=[2020]`, so guard 2 didn't fire and the span collapsed to `(2020, 2020)` — making `year 2023`, **the gold-TRUE original value**, read FALSE. A SERIAL covering fewer than **2 distinct years** is now `INCOMPLETE_SPAN`. Distinct *years*, not member count, precisely because duplicates were how it got through. |

**Reusable lesson from guard 3: a span rule is conservative only while the span is WIDE.
Narrow it enough and the same rule becomes the most aggressive detector in the system. The
conservatism was a property of the data, not of the rule.** That bug is also the **fourth**
recorded coverage-up/precision-down event (`property_resolver.py` first pass · `--variant
hybrid` · `temporal_ea_hybrid_b3.csv` · this).

**Measured ceiling on the 12 CITATION `year_shift` negatives: 8/12.** Tallies are computed
from `collections.Counter` over the live probes and **asserted**, not printed as literals —
I nearly shipped `World Bank 0/2` as a hardcoded string, which is how a prediction becomes
a "result".

| source | detected | mode | span |
|---|---|---|---|
| IPCC Sixth Assessment Report | **5/5** | `SINGLE_WORK` | (2021, 2023) |
| Lancet Commission on dementia prevention | **3/5** | `SERIAL` | (2019, 2024) |
| Poverty and Shared Prosperity | **0/2** | `INCOMPLETE_SPAN` | `None` |

Lancet 3/5 is asserted as **exactly 3**: with the 2024 hole present all five perturbations
read FALSE — that is the headroom doc's *"5 of 5 **with** confident-wrong risk"* — so 5/5
reappearing means guard 1 regressed. **CONCENTRATION CAVEAT, which must travel with the 8:
detections come from two works, so this is two works working, not "CITATION working"** —
the same caveat QUANTITATIVE's 6/6-from-P2044 carries. Regression guards cover all three
gold-TRUE base values (IPCC 2023, Lancet 2020, World Bank 2023) plus the membership trap
(IPCC 2022 must abstain).

`quantitative_verifier.py` (validated 24/24) and `property_resolver.py` are **imported,
never edited**; existing cache prefixes reused for their intended purpose, additive writes
only.


### The independent resolution check has first evidence, and it fired immediately

The audit below downgraded the resolver's 72/72 to *"0% refusal, correctness
unverified by an independent signal"* and named the fix as future work: check the
resolved entity's **other** properties against the claim's context. That check ran
incidentally during the 08-25 probe and **caught a wrong resolution scoring *above*
threshold**: Q92676744's `P1433` (published in) is **Q15751849 = *Irish Journal of
Psychological Medicine***, not *The Lancet*. The label-based check passes this entity
— its label really does read "The Lancet Commission on Dementia Prevention…" — and
the property-consistency check rejects it. **The caveat was not theoretical, the
proposed fix works, and it is nearly free** (the claims fetch is already being made).

**BUILT 2026-08-26 — `current/source_consistency.py`, `--selftest` 12/12 ALL PASS.**
The safety half of the serial-edition fix, deliberately shipped *before* series
resolution because it **removes** a confident-wrong verdict rather than adding
coverage. A separate module, so QUANTITATIVE's validated 24/24 is untouched.

    Q92676744 vs 'The Lancet' -> CONFLICT   P1433 = 'Irish Journal of Psychological Medicine'
    Q103843442 vs 'IPCC'      -> CONSISTENT P123  = 'Intergovernmental Panel on Climate Change'
    Q103843442 vs 'WHO'       -> CONFLICT   P123  = 'Intergovernmental Panel on Climate Change'

The third case is the one that converts the CITATION *analysis* into a *detection*: it
is exactly the `SYN_CITA_075/076/077` fabricated-composite-title route ("The WHO Sixth
Assessment Report"), and it is caught with **no NLI at all.**

Four design decisions, each load-bearing:

1. **Only `P1433`/`P123` can veto.** They answer *"who put this work out"*, which is
   what a citation names. `P50`/`P179`/`P361`/`P31` are printed for context but never
   decide — **an author is not a publisher**, so a mismatch there is not a provenance
   conflict. (Q92676744 carries two `P50` values; neither is consulted.)
2. **Any match wins.** A co-published report legitimately carries several provenance
   values, so one genuine hit is confirmation, not a tie.
3. **`NO_EVIDENCE` must never reject.** Most Wikidata items have no `P123` at all;
   making absence reject would delete coverage while detecting nothing. Same asymmetry
   Level 1 already encodes — *a source that fails to resolve is UNVERIFIABLE, not
   fabricated.*
4. **Both error directions are safe, which is why it can ship ahead of the hard half.**
   A wrong CONSISTENT → no veto → status-quo behaviour. A wrong CONFLICT → veto →
   honest UNVERIFIABLE. **The check only ever removes a verdict**, so neither direction
   can manufacture a confident-wrong one. The name matcher is therefore deliberately
   lenient (bidirectional acronym *prefix* match: `FAO` matches "Food and Agriculture
   Organization of the United Nations" via FAOUN, while `CDC` vs "World Health
   Organization" still fails).

**#17b shipped 2026-08-26 — `current/series_resolver.py`, commit `1849791`** (details in
the *A THIRD resolution failure mode* section above). That module does not *find* the right
edition either; it **stops needing to**, by spanning all of them so the year tests without
ever selecting. The two modules are complementary and both preconditions for #18:
`source_consistency.py` vetoes a wrong *publisher*, `series_resolver.py` removes the wrong
*edition*'s ability to decide a date.

### #18 SHIPPED 2026-08-26 — CITATION Level 1b returns FALSE, and beats the baseline on its own weakest type

`current/citation_l1b_verifier.py`, `--selftest` ALL PASS, `--diagnose` → 54 rows in
`current/citation_l1b_results.csv`. Full analysis
`reference/citation_l1b_result_2026-08-26.md`. Consumes both preconditions above.

| | TPR on the 25 negatives | FPR on the 25 gold-TRUE natural | **J** |
|---|---|---|---|
| **Level 1b** | **9/25 = 36.0%** [20.2, 55.5] | **0/25** [0.0, 13.3] | **+0.360** |
| baseline, CITATION | 5/24 = 20.8% [9.2, 40.5] | 2/25 = 8.0% [2.2, 25.0] | +0.128 |

By route: `year_shift` **5/12** via `P577`, `source_swap` **4/11** via a `P123` conflict.
J nearly triples on the type CLAUDE.md already named *"the reachable gap"* — and **with
no NLI at all**, which was the whole bet of the headroom analysis.

**Three caveats, all mandatory wherever the 9 is quoted:**

1. **8 of 9 detections come from ONE Wikidata item** (Q103843442, IPCC AR6; the ninth is
   Q29876135, SOFI). **One work working, not CITATION working** — the same caveat
   QUANTITATIVE's *6/6-from-P2044* carries.
2. **The TPR CIs overlap heavily** ([20.2, 55.5] vs [9.2, 40.5]); n = 25 cannot separate
   36% from 21%. The clean, prior-independent part is **FPR 0/25 vs 2/25** and the
   confident-error count **0**, not the TPR gap.
3. **Ceiling ≠ end-to-end.** `series_resolver`'s 8/12 was measured from hand-curated
   subject strings; extracting from claim text gives **5/12**. Report both. The gap is
   entirely Lancet and is **candidate generation, not ranking** — `'Lancet Commission'`
   returns 4 candidates and none is a dementia work, so no threshold or tie-band change
   recovers them.

**The natural set could only ever have lost here: max TP on it is 0 by construction.**
All 3 gold-FALSE natural CITATION claims are *content* falsities (`Q12_C11` wrong
largest-reduction factor; `B3_05_C02` the ten criteria — and its **1972 is the correct
year**; `B3_12_C07` wrong percentage), which no property check reaches. So all value is
on the negatives and all risk was false alarms. **0/25.**

**Unlike `source_consistency`, 1b EMITS FALSE**, so it can manufacture the confident-wrong
class — hence precision-gated at the front, and **no TRUE verdict exists in the module**
(a year inside the span returns UNVERIFIABLE; Level 1 owns TRUE, and `--selftest` asserts
no `TRUE` assignment in production code *plus* that the assertion has not gone vacuous).

**Two general lessons, both bought by finding real bugs:**

- **`SUBJECT_OVERLAP_MIN` is a symmetric Jaccard, and that is the defect.** It gets *more*
  permissive as the requested title gets shorter: `jaccard({lancet,commission},
  {lancet,commission,value,death}) = 0.50`, clearing the 0.25 bar. End-to-end extraction
  therefore produced a **FALSE on gold-TRUE `Q12_C01`** off a span of 2014–2018 built
  from three unrelated Lancet Commissions — **misplaced, not merely narrow**, which
  guards 2 and 3 cannot see because the members are dated, distinct and plural. Fixed by
  **guard 4 (topical anchoring)**: keep a member only if the content its label adds beyond
  the subject is empty or intersects the claim's anchor terms. Asymmetric, independent of
  the selection signal, can only ever DROP members (so a drop abstains, never decides),
  and `anchors=None` leaves the committed 8/12 untouched — re-verified ALL PASS.
- **A detection off a wrong span is luck, not evidence, and only base-pairing exposes it.**
  `SYN_CITA_071` (2030) had been "detected" off that bogus span — while its gold-TRUE twin
  `Q12_C01` (2020) was read FALSE off the *same* span. Guard 4 removes both. A
  negatives-only run would have scored it a win. **Pair every detection with its
  unperturbed base claim.**
- **Non-circularity must be closed in every channel, not just the signature.** The
  year-free signature proves no year can be *passed* in; `ctx` feeds full-text search and
  SBERT, so an unstripped claim *leaks* one. Measured: the Lancet leader score moved
  **0.566 → 0.553** once ctx was year-stripped. And **the invariance test that proves this
  was itself vacuous at first** — run on the Lancet claim it compared `NO_TOPICAL_MATCH`
  to `NO_TOPICAL_MATCH`, passing while testing nothing. It now runs on AR6 and asserts
  three things: span identical across 2021/2022/2033/2133, span **non-empty**, and the
  **verdict still varies** (2022 → UNVERIFIABLE, 2133 → FALSE). Evidence invariant, answer
  not — invariance alone is also satisfied by a verifier that never decides anything.

**The corpus `subject` column is CONTAMINATED — never resolve from it.** The perturbation
harness rewrote the claim and left `subject` holding the **original, un-perturbed** year:
`SYN_CITA_071`'s claim says 2030, its `subject` says `'2020 Lancet Commission'`. Resolving
from it hands the verifier the exact value the negative exists to hide, so every
"detection" would measure the harness. The negatives file also carries `original_value` /
`corrupted_value` outright. Extraction reads **claim text only, uniformly across both
populations** — using different inputs for natural and synthetic rows would invalidate the
comparison even if neither leaked.

### QUANTITATIVE now has real, validated coverage (2026-08-23)

`--diagnose` on Batch 3's 29 QUANTITATIVE claims: **coverage 8/29 = 27.6%** (was 0), accuracy **8/8 = 100%**. 27.6% sits in the predicted ~24% band, so this is **not** the property-resolver pattern where coverage jumped and precision collapsed. Covered set = the 7 mountain elevations via P2044, plus Florence Griffith-Joyner's 10.49 s personal best (P2415). Denali verifies 6190 = 6190; before the fix it was checking a mountain's elevation against an asteroid's *orbital inclination*.

**The 100% is uninformative on its own** — zero gold negatives among the covered set, so it cannot be distinguished from an unconditional "TRUE". The valid measurement is `--sensitivity` (controlled perturbation), and it passes cleanly:

    Flipped within 50%: 8/8       Median flip point: 1%
    nothing flips at 0.1% (inside the 0.5% tolerance)

**Every covered claim flips TRUE→FALSE when the claimed value moves by ≤1%, and none flips inside the tolerance.** That is genuine discrimination, and it is the first validated detection result in the project. All 21 abstentions are honest gaps with named reasons: 6 COMPUTATIONAL + 1 COMPARATIVE abstain by design, and `world_record_time` correctly rejects the near-miss P2415 (sprint records are separate award items in Wikidata, not entity properties).

## RQ1 IS MEASURED — routing accuracy 93.8–95.4%, contamination-free (2026-08-24)

**The project's own classifier, on 65 held-out Batch 1 claims:**

| | accuracy | CITATION | TEMPORAL | QUANT | EA | RELATIONAL |
|---|---|---|---|---|---|---|
| deployed classifier (recorded `type` column) | **93.8%** [85.2, 97.6] | F1 1.00 | **P 0.57** | 0.84 | 0.91 | 0.99 |
| reproduction (`current/original_classifier.py`) | **95.4%** [87.3, 98.4] | — | — | — | — | — |
| my zero/few-shot rebuild (do NOT use) | 83.1% [72.2, 90.3] | 0.89 | 0.75 | 0.95 | **0.46** | 0.90 |

Reproduction agrees with the recorded output **62/65 = 95.4%**, so it is faithful enough
to stand in for the deployed classifier. It parses both prompts **verbatim** out of
`archive/experiments/currentcode.txt` at import time and raises rather than
approximating — retyping a prompt is how a "faithful reproduction" silently stops being
faithful.

**Why the split is legitimate:** exemplars from Q1/Q2/Q5/Q7/Q9, tested on Q10–Q14.
Split **by question, not by claim** — two claims from one question share subject matter
and phrasing, so a claim-level split still leaks. Batch 1 is the **only** set with
independently labelled `gold_type`; Phase 2 and Batch 3 seeded theirs from classifier
output, and FActScore/FEVER have no type labels at all. **Correction to an earlier
note: FEVER cannot measure routing.** It has no claim types.

**TEMPORAL over-firing is confirmed and now reproduced three independent times** —
precision **0.56 at recall 1.00** on all 125 (15/27). See the next section: the cause is
**not** the prompt omission it looked like.

### TEMPORAL over-firing is a TAXONOMY GAP, not a prompt bug (ablation 2026-08-24)

The obvious hypothesis was that the prompt's *"apply top-down, stop at first match"*
overrides §4's most-contestable-element rule, letting TEMPORAL (rank 2) beat
QUANTITATIVE (rank 3) whenever a date appears. **Tested and refuted**
(`current/router_ablation.py`, worklog Step 27):

| | overall | TEMPORAL P | TEMPORAL R |
|---|---|---|---|
| V0 deployed | 111/125 = 88.8% | 15/27 = **55.6%** [37.3, 72.4] | 1.00 |
| V1 + §4 override | 111/125 = **88.8%** | 13/21 = **61.9%** [40.9, 79.2] | 0.87 |

**Zero change in overall accuracy.** 7 claims re-typed — 3 errors fixed, 3 created, 1
wrong→wrong. The +6.3pp precision has near-total CI overlap and was **bought with
recall**, discarding two genuinely-TEMPORAL claims.

**On the held-out 65 the same fix looked excellent** — TEMPORAL P 0.67 → 1.00, overall
95.4% → 96.9%. That rested on **4 gold TEMPORAL claims** (4/4 = [51%, 100%]) and was
noise pointing the wrong way. Best in-project illustration of the bare-100% rule above.

**The actual defect: 8 of 14 errors are TEMPORAL-predicted / human-RELATIONAL** — the
dominant class, untouched by V1. All are narrative process claims carrying a date
("Home prices fell after 2006", "Buddhism spread from India to China during the 1st
century CE", "Maritime trade routes replaced land travel after 1453"). Process verb →
human says RELATIONAL; date present → classifier says TEMPORAL.

**§4 enumerates five conflicts — TEMPORAL vs EA, QUANTITATIVE vs TEMPORAL, EA vs
RELATIONAL, QUANTITATIVE vs RELATIONAL, and "CITATION vs any type". With 5 types there
are 10 possible pairs, and CITATION-vs-any covers 4, so §4 covers 8 of 10. The two it
never mentions are TEMPORAL vs RELATIONAL and QUANTITATIVE vs EA.**

**8 of V0's 14 errors (57%) fall in TEMPORAL vs RELATIONAL — one of the only two pairs
the taxonomy leaves unaddressed.** The remaining 6 spread across pairs §4 does cover
(3 TEMPORAL/QUANTITATIVE, 2 QUANTITATIVE/RELATIONAL, 1 TEMPORAL/EA). So the taxonomy's
coverage gap predicts the classifier's error distribution: 57% of errors concentrate in
20% of the pairs, and specifically the unaddressed ones.

The taxonomy does not under-specify this tie; it never records that the tie exists. No
prompt variant can fix that, which is why V1 could not and V2 (EA vs RELATIONAL — a
*covered* pair, 1 of 14 errors, ceiling +0.8pp) will not.

**Report this as a taxonomy finding, not a bug.** Untested proposal (V3): *"RELATIONAL
beats TEMPORAL when the dominant verb describes a process and the date is when it
occurred."* Adopting it edits the taxonomy and re-types the column every downstream
number rests on — author's decision.

### The deployed classifier CONTRADICTS the taxonomy rules — decide before Chapter 4

The classifier prompt states: *"'WHO exists' is NOT a CITATION claim."* The rule
document says the opposite — **Rule 8 (dual-emit)** extracts *"The World Health
Organization exists. [CITATION]"*, §3.2 lists pure source-existence claims as CITATION,
and the 140-claim corpus contains **nine** of them all labelled CITATION.

**Dual-emit manufactures one such claim per citation-wrapped statement**, so this is a
systematic class, not an edge case. Either Rule 8 stands and the prompt needs fixing, or
the prompt stands and Rule 8 plus nine corpus labels need revising. No measurement
resolves it.

Two undocumented refinements in the prompt, both apparently useful: it asks for **one
bare word** rather than JSON (zero parse failures, where a JSON rebuild lost 2 of 65
claims), and it adds *"vague quantities ('millions', 'many') do NOT qualify"* for
QUANTITATIVE, which appears nowhere in the rule document.

## NEVER WRITE A BARE 100% — every one of them audited 2026-08-24

Wilson CIs on every 100% figure reported this cycle:

| claim | k/n | 95% CI | verdict |
|---|---|---|---|
| RELATIONAL precision (deployed classifier) | 36/36 | [90.4%, 100%] | **holds** |
| entity resolution "correct" | 72/72 | [94.9%, 100%] | **circular — see below** |
| resolution, very-rare tier | 18/18 | [82.4%, 100%] | defensible |
| QUANTITATIVE accuracy | 8/8 | [67.6%, 100%] | n too small |
| QUANTITATIVE sensitivity flips | 8/8 | [67.6%, 100%] | n small, but flips are the real evidence |
| CITATION F1 (deployed classifier) | 8/8 | [67.6%, 100%] | n too small |
| tier-1 Wikidata, Batch 3 | 5/5 | **[56.6%, 100%]** | meaningless as "100%" |
| tier-1 Wikidata, negatives | 2/2 | **[34.2%, 100%]** | meaningless |

**`tier1 = 5/5` has a lower bound of 56.6%** — barely better than a coin flip. It had
been quoted as the strongest evidence for the tiering argument and **cannot carry that
weight.** Write `5/5 [56.6%, 100%]`, never "100%".

### The resolution 100% is partly CIRCULAR — downgraded

The resolver searches Wikidata with the subject string, then picks the candidate whose
**label** best matches that string. The audit "verified" correctness by checking that the
chosen entity's **label** matches the subject string. **The check uses the same signal as
the selection**, so it cannot fail — it proves the resolver did not return something with
an unrelated name, not that it picked the right *person*.

Two things it cannot catch, and the second is the original QID bug: same-name ambiguity
(two people called "Desmond Luke"), and wrong-sense-same-name ("Rosetta Stone" the punk
band has the label "Rosetta Stone").

**Report as "0% refusal, correctness unverified by an independent signal."** The rarity
finding (resolution does not degrade with obscurity) survives as *suggestive*, since
refusal rate genuinely did not move across tiers, but it is no longer backed by a
correctness check. An independent test would check the resolved entity's *other*
properties for consistency with the claim's context — information the resolver never
consulted.

## Claim-set inventory — CONFIRMED four distinct sets, nothing missing (2026-08-24)

| set | authoritative file | rows |
|---|---|---|
| Batch 1 | `archive/csvs/haldetect_claims_20260524_045439_2.csv` | 125 |
| Phase 2 | `current/haldetect_phase2_goldlabeled (3).csv` | 126 / 109 labeled |
| Batch 3 | `current/haldetect_claims_b3_gold.csv` | 122 |
| Negatives | `current/relational_negatives_batch3_merged.csv` | 27 |

All four are wired into `consolidate_claims.py` with hardcoded `expect` counts that pass.
Everything else is a superseded ancestor.

`archive/csvs/haldetect_phase2_annotation_ready.csv` (69 rows) is an **annotation
worksheet**, not a fifth set: `gold_verdict` blank on all 69, and every claim_id is a
strict subset of the authoritative `(3)` file, which also has the labels it lacks.

Two naming traps: `__3_.csv` / `__1_.csv` are the same files as `(3).csv` / `(1).csv`
with characters sanitised, so a file list can double-count them. And
`relational_negatives_b3_merger_verified_results (1).csv` holds **27 rows, not 20** — a
prior inventory recorded it as 20. Verify against the file, always.

## The non-routed baseline (RQ2) — RUN AND MEASURED 2026-08-23

**Status: complete. 356/356 claims, 0 failures, Colab T4.** Full analysis: `reference/nonrouted_baseline_result_2026-08-23.md`. Results: `current/nonrouted_baseline_results.csv`.

| | coverage | selective accuracy | F1(FALSE) | MCC |
|---|---|---|---|---|
| **3d-style** | **77.2%** [72.6, 81.3] | **69.8%** [64.2, 74.9] | 0.170 | +0.180 |
| **3e-style** (margin ≥0.15) | 53.7% | 81.2% [75.0, 86.1] | 0.174 | +0.144 |
| *Always-True* | 100% | **88.2%** | 0.00 | 0.000 |

**Four findings that change how results must be reported:**

1. **The baseline scores 18pp BELOW Always-True on accuracy.** Accuracy is the wrong headline for this project — with 314/13/29 it rewards never saying FALSE. **Lead with F1(FALSE) and MCC**; quote accuracy only next to Always-True. Any table leading with accuracy is trivially attacked.
2. **Of 81 FALSE predictions, 8 are correct — precision 0.099.** 67 are gold-TRUE false alarms. Uniform retrieval+NLI manufactures hallucination alarms at ~9:1. Same failure class as the `1 - entail` proxy: proper 3-way NLI reduced it but `CONTRADICT_THRESHOLD = 0.40` still reads "unsupported" as "contradicted". The margin gate does not fix it (halves recall for +2pp precision; MCC gets *worse*).

   **⚠ CORRECTED 2026-08-25 — this was recorded as "the strongest empirical motivation for the taxonomy the project has." It is not, because it is a PRIOR ARTIFACT.** `negatives_cache_audit.py` measures the baseline's TPR on the 85 gold-FALSE negatives (53.6%) against its FPR on the natural set's gold-TRUE claims (21.3%). Substituting those into `P = πT/(πT+(1−π)F)` at π = 13/356 = 0.0365 **predicts precision 0.0870 against the observed 0.0988 — a gap of 0.012.** The base rate alone reproduces the figure. At this π a detector needs a TPR/FPR ratio of **26.4:1** for 50% precision and 6.6:1 for 20%; the measured ratio is 2.5:1, so ~9:1 alarms is what the arithmetic *requires*. **Youden's J = +0.323, which is not zero** — at a balanced prior the same detector shows precision 0.715. Always pair the precision figure with the base rate and J. Full analysis: `reference/negatives_cache_audit_2026-08-25.md`.
3. **RELATIONAL's Batch-3 number reproduces on the pooled set.** Recorded 80.77% acc @ 55.32% cov on ~26 covered claims; pooled 174 gives **79.1% @ 52.3% on 91 covered**. CI tightens from ±14.7pp to ≈±8pp. The biggest open statistical risk in the project — that "80.77%" was an artifact of 26 claims — **is closed.** (3d on the same 174: 66.4% @ 77.0%.)
4. **Phase 2's AI-filled labels are NOT driving the result.** All-labeled 69.8% vs human-only b1+b3 71.6%; coverage 77.2% vs 76.9%. The robustness check built to catch this passed.

**The honest RQ2 verdict, which must not be softened:** routing currently **loses** to not-routing on four of five types — because four routed verifiers are non-functional (TEMPORAL 0%/0%, EA 0%/0%, QUANTITATIVE never run, CITATION 0/12), while the baseline reaches 67–81% accuracy with real coverage on all five. The defence is the error profile, not fairness: the baseline is wrong 90% of the time it says FALSE, whereas post-QID-fix TEMPORAL/EA produce zero confident-wrong verdicts. But a verifier at 0% coverage detects nothing and ties Always-True on the FALSE class, so **that is currently an argument about design intent, not a measured win.** Turning RQ2 into a result requires non-zero routed coverage, which makes the resolver prominence prior the critical path.

> **PARTIALLY SUPERSEDED 2026-08-25 — QUANTITATIVE is no longer in the losing set.** Measured on gold negatives, routed QUANTITATIVE is **14/14 correct across 14 covered claims with both classes present, MCC +0.378 vs the baseline's best +0.202, and 0 confident errors against the baseline's 19**; on the 4 claims where both answer confidently and disagree, routed is 4/4 and the baseline 0/4. So for one type this *is* a measured win on a prior-independent metric, not an argument about design intent. **The verdict above still stands verbatim for TEMPORAL, EA and CITATION.** Caveat that must travel with the number: all 6 negative detections come from a single property (P2044 elevation), so this is one property working rather than "QUANTITATIVE working", and coverage is 25–26%. `reference/rq2_quantitative_negatives_2026-08-25.md`.

Per-type 3d/3e (cov, acc): RELATIONAL 77.0/66.4 → 52.3/79.1 · TEMPORAL 90.8/67.8 → 61.5/82.5 · QUANTITATIVE 82.2/73.0 → 55.6/84.0 · **EA 74.4/81.2 → 60.5/80.8 (the one type where 3d dominates)** · CITATION 44.8/76.9 → 31.0/88.9. The 3d→3e trade is a stable −22pp coverage for +12pp accuracy.

Read the rest of this section for the spec and what this must not be confused with.

### The baseline's per-type discrimination, measured on gold negatives (2026-08-25)

`current/negatives_cache_audit.py` — offline, ~1 s. TPR on the 85 synthetic
gold-FALSE negatives (strict tier, cache collisions removed) against FPR on the
natural set's gold-TRUE claims. Same code path, same operating point, so the
difference is discrimination. Rows use the **`type`** column, i.e. what the
verifier receives.

| type | TPR on negatives | FPR on gold-TRUE | **J = TPR−FPR** |
|---|---|---|---|
| **CITATION** | 5/24 20.8% | 2/25 8.0% | **+0.128** ← weakest, and prior-independent |
| ENTITY_ATTRIBUTE | 5/5 100% | 5/42 11.9% | +0.881 (n=5, do not quote) |
| QUANTITATIVE | 8/14 57.1% | 9/41 22.0% | +0.352 |
| TEMPORAL | 19/26 73.1% | 19/62 30.6% | +0.424 |
| **ALL** | **37/69 53.6%** | **67/314 21.3%** | **+0.323** |

**Detection rate on the negatives is never quotable alone** — every row there is
gold FALSE, so an unconditional "FALSE" scores TPR 1.00 and the baseline's 53.6%
is *worse* than the degenerate strategy. That is the exact mirror of Always-True
scoring 88.2% on the natural 356. **Pair it with FPR, or report J**, which is 0
for Always-True and Always-False alike.

**Bounding caveat:** the negatives are synthetic perturbations (a swapped number
or date), plausibly easier to refute than a naturally-hallucinated causal claim.
Every TPR here is an **upper** estimate and every J an upper bound.

**Also settled here:** the `nli__{claim[:60]}__{passage[:40]}` cache key affects
**16 of 85 negatives (18.8%)** in three classes — 12 fabricated (exclude), 10
duplicate reads (discount), 3 *partial* inheritance where entail is inherited but
contradict is fresh. QUANTITATIVE is untouched by the third class, so
`reference/rq2_quantitative_negatives_2026-08-25.md` stands unchanged. TEMPORAL's
recorded 75.0% on 28 clean rows was correct (→ 73.1% strict, not material). Both
previously-hardcoded id lists are gone: importers now call
`negatives_cache_audit.Audit`, and `--selftest` asserts the computed sets still
reproduce the legacy ones.

### CITATION is the reachable gap, but not where the docs said (2026-08-25)

Follows directly from CITATION's **J = +0.128** above. `current/citation_negatives_analysis.py`
(`--composition` offline, `--reachability` ~15 calls, `--selftest` 12 checks);
full account `reference/citation_negatives_headroom_2026-08-25.md`.

**Not one of the 25 CITATION negatives perturbs source existence** — the only
question Level 1 asks. 12 shift the **year** on a correctly-named work, 11 swap the
organisation **for another real one** (WHO in 10 of 11), 2 swap the content. So the
recorded framing understates the gap: **even a Level 1 that *could* return FALSE
would still detect 0/25.** Changing L1's FALSE policy — the tempting fix — buys
nothing here, and `source_swap` is worse than a miss, since an existence check
resolves WHO successfully and thereby *vouches for* the fabricated citation. It also
carries the QUANTITATIVE `cross_substitute` control property: the injected org is
real, so no surface-form or plausibility signal exists.

**But 17 of 25 (68%) need no NLI at all** — 12 via publication date (`P577`), 5 via
a publisher (`P123`) conflict on a fabricated *composite* title ("WHO Sixth
Assessment Report"). The 12 year-shifts are neither existence nor attribution; they
need a **third** check, structurally `quantitative_verifier.py` with the datatype
filter changed from `quantity` to `time`. The CITATION FALSE class is not blocked on
Level 2 to the degree assumed.

**Reachable today: 8 of 25 — and all 8 through one Wikidata item** (Q103843442, IPCC
AR6: `P577 = {2021-08-09, 2023-03-20}`, `P123 = Q171183` = IPCC, verified not
assumed). Same concentration warning as *"6 of 6 QUANTITATIVE detections are P2044
mountain elevations"* — **one work working, not CITATION working**, and it must be
stated wherever the 8 is quoted. The Lancet rows (5) are blocked by the serial-edition
failure mode above; the World Bank rows (2) resolve to the wrong edition with `P577`
absent; `World Mental Health Report` misses at 0.530; FAO's `P123` evidence exists but
resolution is rejected at 0.585.

**Use a span rule, not set-membership, for publication dates.** AR6 is multi-part
across 2021–2023 and Wikidata lists only two `P577` values, so membership would mark
*"published in 2022"* FALSE though WG2/WG3 genuinely appeared in 2022 — a manufactured
confident-wrong verdict. FALSE only outside `[min, max]`, abstain inside. It costs
nothing here: all five claimed years (2024–2123) are after 2023, so span detects 5/5
too, and the matched pair is 6/6 either way.

**Author decision before any build** — this is a new verifier component, not a fix.
Weigh 8/25 with a single-entity dependency against the baseline's J = +0.128, and
require the three preconditions in §6 of that doc (series resolution, the
property-consistency check, span-not-membership).

> **All three preconditions are now MET (2026-08-26):** series resolution =
> `current/series_resolver.py` (`1849791`), property-consistency = `current/source_consistency.py`
> (`504f51b`), span-not-membership = encoded in `test_year_in_span`. **Two numbers in the
> paragraphs above are superseded by measurement.** The 12 `year_shift` rows were recorded as
> reachable only via IPCC (5); the built span rule measures **8/12** — IPCC 5/5 **plus Lancet
> 3/5**, because harvesting years from labels recovers the 2024 report whose `P577` is absent.
> And the World Bank rows are **0/2 by an explicit abstention** (guard 3), not merely
> "blocked": their span degenerates to a single year, and a narrow span is *more* dangerous
> than none. The single-entity dependency is therefore now a **two**-work dependency; the
> concentration caveat stands unchanged.
>
> **#18 IS NOW BUILT AND MEASURED (2026-08-26) — and the 8/12 above is a CEILING, not the
> shipped number.** `current/citation_l1b_verifier.py` scores **9/25 negatives at 0/25 false
> alarms, J = +0.360** (see the #18 section above). Two corrections to the paragraph
> immediately above:
>
> - The **8/12** was measured from **hand-curated subject strings** taken from this very
>   doc during design. End-to-end extraction from claim text gives **5/12** — the Lancet 3
>   are lost because `'Lancet Commission'` retrieves 4 candidates and **none is a dementia
>   work**. That is candidate *generation*, not ranking, so no threshold move recovers them.
>   **Quote 8/12 only as a ceiling, always beside the 5/12.**
> - So the "**two**-work dependency" reverts to **one** on the shipped path: 8 of the 9
>   detections come from Q103843442 alone. The concentration caveat is therefore *stronger*
>   than recorded here, not weaker.
>
> The 4 extra detections that lift 5 → 9 are `source_swap` rows caught by the **publisher**
> route, which this doc had estimated at 5. **Do not try to close the Lancet gap with the
> corpus `subject` column** — it holds the un-perturbed original year (see #18).

### Threshold sweep, 2026-08-23 — the shipped operating point is a strawman, and contradiction NLI has no good threshold

`current/threshold_sweep.py` recomputes the whole threshold surface from the cached `entail`/`contradict` scores — **zero model calls**. Full analysis: `reference/threshold_sweep_result_2026-08-23.md`.

| point | coverage | accuracy | F1(FALSE) | P(FALSE) | MCC |
|---|---|---|---|---|---|
| shipped (0.50/0.40) | 77.2% | 69.8% | 0.170 | 0.099 | +0.180 |
| **best (0.35/0.30)** | **90.2%** | **84.7%** | **0.292** | 0.200 | **+0.288** |

1. **The shipped point is strictly dominated — every metric improves at once** (+13pp coverage, +14.9pp accuracy, +0.12 F1(FALSE), +0.108 MCC), and it replicates on human-only labels (90.7% / 86.6% / 0.308 / +0.283). **So RQ2 must be reported against the baseline at (0.35/0.30) — ON THE NATURAL 356 ONLY. See the scope qualifier below; do not carry this threshold to a set with a different class prior.** Using phase3d's untuned defaults would credit routing with a ~15pp gap that is really one badly set constant — a strawman, which the committed spec explicitly forbids. No re-run needed; it is recomputable from the CSV.

   **SCOPE QUALIFIER, added 2026-08-25 — the "optimum" is a class-prior fit.** On the 24 gold-FALSE QUANTITATIVE negatives, (0.35/0.30) is *far worse* than shipped: F1(FALSE) 0.488 → 0.200, MCC +0.202 → +0.083, and on the clean 15 it detects 2/15 while confidently asserting **13** hallucinations are true. Mechanism: the entail threshold is a knob on how often the system says TRUE, and rows with `entail ∈ [0.35, 0.50)` become TRUE under tuning — **92 such rows on the natural 356 split 81 helpful / 3 harmful (27:1), versus 0 helpful / 9 harmful on the negatives.** The sweep found a better fit to a 24:1 class imbalance, not a better discriminator. This is the project's own class-imbalance trap operating on hyperparameter *selection* rather than metric *reporting*. Verified not an artifact: the 9 flipping rows are disjoint from the 9 cache-corrupt rows (overlap 0). **Rule: quote the baseline at whichever operating point is stronger on the population being reported, and name both the point and the population's class prior. Carrying the tuned point onto a negatives-enriched set is a *reverse* strawman, equally inadmissible.** The routed verifier has no threshold at all, so there is no operating point in it to fit to a prior — an architectural difference that is now measured rather than asserted. Detail: `reference/rq2_quantitative_negatives_2026-08-25.md` §6.
2. **The bigger finding: contradiction precision never leaves 0.08–0.12 across the whole sweep and caps at 0.20 over all 225 grid points.** Raising the threshold destroys recall while precision stays flat — by ct=0.65 it catches **0 of 13** negatives while accuracy climbs to 92.5% purely by abstaining. This is the `1 - entail` defect surviving the 3-way fix — an architectural limit, not a hyperparameter. It also explains why folding NEI into False (Factcheck-Bench, OpenFactCheck) hides this, and why we don't frame against them.

   **⚠ RESTATED 2026-08-25 — the conclusion drawn here was too strong.** It read: *"BART-MNLI's contradiction score over retrieved passages **cannot separate** 'refutes this' from 'does not mention this' at any operating point"*, and called that *"the strongest available motivation for structured verification."* **Every number in the sweep is a precision figure, and precision at π = 0.037 is arithmetically forced low even for a competent discriminator** — see the correction on the baseline's 0.099 above. Measured on gold negatives the same code path has **TPR 53.6% vs FPR 21.3%, J = +0.323**. The defensible version: **the ROC never reaches a high-precision regime at this base rate — the best TPR/FPR ratio available anywhere on it is ~6.6:1, where ~26:1 is needed for even coin-flip precision.** That is a real finding about the ROC's *shape*; it is not "cannot separate," and must not be written that way. The prior-independent motivations that survive are the **confident-error count** (routed QUANTITATIVE 0 vs baseline 19), **MCC** (+0.378 vs +0.202), the **same-number control**, and **CITATION's J = +0.128** — the baseline's genuinely weakest type, which is a better motivation for structured citation checking than the aggregate precision figure ever was.
3. **Coverage 90.2% is at the ceiling** — NLI scored 322/356 (90.4%); the other 34 abstained pre-NLI. Lifting that is **retrieval**, not thresholds.
4. **Per-type optima differ, but the values are overfit — do not quote them.** Tuned on the evaluation rows with only 13 negatives total; RELATIONAL/TEMPORAL optima move between label sets. Three findings *are* stable: **QUANTITATIVE wants strict contradiction (0.50), CITATION permissive (0.30)**; **CITATION has NEGATIVE MCC at the shipped threshold** (−0.115 pooled, −0.150 human-only — worse than chance at detecting false citations, alongside 44.8% coverage and "FAO" → *Aquaculture* retrieval failures); and **EA's MCC is 0.000 everywhere because it has essentially no gold negatives**, so its 97.4% accuracy is uninformative by construction.
5. **13 gold negatives across 356 claims is now the binding constraint on every detection claim in the thesis.** Controlled perturbation is not optional polish.

**Never quote accuracy without coverage and effective n.** The ct≥0.65 rows show accuracy reaching 92.5% on a system that detects nothing.

Read `old-chats-handoffs/` before planning any experiment. Five exported session handoffs live there, and **all three build-phase handoffs independently name the same missing deliverable as the central result** — while this file had it nowhere:

> "Task 6 — **the core quantitative proof:** ablation of taxonomy-routed verifiers vs a single generic (uniform) verifier." — *Taxonomy-based hallucination detection*
> "Non-routed baseline | Ablation | **Not started** | The core comparison; spec is fixed." — *Comparing systems against FActScore's dataset*
> "**Non-routed baseline — not built. Required for RQ2.**" — *RAG for fact verification experimentation*

**The spec has been fixed since May and never changed:** every claim, regardless of type → top-k Wikipedia passage retrieval → `facebook/bart-large-mnli` 3-way NLI → threshold → TRUE/FALSE/UNVERIFIABLE. Same claims, same gold labels, same evidence sources; **routing is the only variable.** This is essentially what FActScore does, which is why it is the natural non-strawman baseline rather than a rigged one.

**Why this outranks everything else in the queue: the machinery already exists.** Cell 57 (RELATIONAL / Phase 3e) *is* Wikipedia retrieval + BART-MNLI. Run it over all claims with the type filter removed and you get the non-routed baseline nearly free — and simultaneously RELATIONAL's pooled-184 number on the subset routing sends it to. The two highest-value experiments in the project are the same run.

**Do not confuse this with `current/llm_baseline.py`.** That is a *secondary* baseline (ask-an-LLM, gemma4:31b-cloud) and it answers a different question. The methodology's committed comparison is routed-vs-non-routed, both using identical evidence and identical NLI. Building only the LLM baseline would leave RQ2 unanswered.

**Blocker:** cell 57 calls `gemini-3.1-flash-lite-preview` (via `GEMINI_API_KEY`, `userdata.get`) for disambiguated query generation. Uncached claims fall back to the bare subject, which measurably degrades coverage — so a pooled re-run needs the key, or its numbers carry an asterisk.

### How `current/nonrouted_baseline.py` implements it (2026-08-22 evening)

**It does not reimplement retrieval or NLI.** It imports `archive/scripts/relational_verifier_phase3d.py` — the code the RAG handoff calls *"the authoritative code for thesis results"* — and calls its `verify_relational()` on every claim. That function already applies **no type filter**; routing was always imposed by the *caller*, never by the verifier. Sharing one code path is what makes the ablation defensible: a reviewer cannot argue the measured gap comes from implementation drift in chunking, ranking, thresholds or the NLI prompt template, because there is only one implementation.

Two honest consequences: the baseline should look **good** on RELATIONAL (same code path, so routed and non-routed should nearly agree there), and the interesting slices are TEMPORAL / EA / QUANTITATIVE / CITATION where routing sends claims elsewhere. **A gap there is the thesis result; no gap is also a result and must be reported rather than tuned away.**

- **The Colab coupling is fixed, not worked around.** `current/gemini_key.py` resolves the key env var → `geminiAPI.txt` → real Colab, and `nonrouted_baseline.py` installs a `google.colab` shim so phase3d imports off Colab. Before this, that "authoritative" script **could not be imported on this machine at all** — which is why it had sat unrun since July.
- **Both variants come from one run.** phase3d caches raw `{entail, contradict}` per (claim, passage), so the Phase-3e margin rule is recomputed post-hoc at zero model cost. `--dry-run` / `--check` are offline; `--limit N` stratifies across types so a smoke test still exercises every route.
- **Every result prints twice** — all labeled claims, and Batch 1 + Batch 3 only — because Phase 2's 109 verdicts are AI-filled. If the two diverge, the pooled figure is not quotable.
- **Cache safety:** it runs against a *copy* of the retrieval cache, seeded from the original so shared claims see byte-identical evidence, but never mutating the routed run's reproducibility.
- **Reporting decision (settled 2026-08-22):** report Phase 3d and 3e **side by side as a coverage-accuracy tradeoff table**, not one or the other. Coverage is what RQ4 measures, accuracy is what RQ2 compares, and the shape of the tradeoff is itself a finding. This resolves the code-vs-decision conflict below rather than hiding it.

**Also settled in those handoffs and not previously recorded here:**
- **RQ4 is a coverage question** ("what proportion of claims can be automatically verified"), which is why Phase **3d** (84.38% cov / ~61% acc) was chosen as thesis-reportable **over** Phase 3e (70.31% / 66.67%). But cell 57 — the live code — **is Phase 3e.** The notebook is running the variant that was explicitly *not* chosen. That decision predates Batch 3 and may have been reversed deliberately; **resolve it before writing Chapter 4, do not silently pick one.**
- **RELATIONAL is structurally heterogeneous — five sub-types (A–E) with different verifiability ceilings.** Named-event causal and person-action claims verify reliably via Wikipedia; generic-subject process, domain-specific mechanism, and historically contested interpretation do not. This answers RQ3 and is called the clearest empirical contribution to the literature from that session.
- **Wikipedia's coverage ceiling for RELATIONAL is ~84–89%, not 100%** — an architectural finding, not a fixable bug.
- **Negative result, do not re-attempt:** the page-relevance keyword gate was tried and reverted **twice**. Generic domain words pass it, and it regressed a legitimate TRUE. Documented in the Phase 3e docstring.
- **`1 - entail` is a known-broken contradiction proxy** that manufactures false FALSEs — already the reason `citation_verifier.py` is untrustworthy, since it inherits that pattern.
- **Cache discipline:** never delete a cache mid-experiment. Clear `title__` / `text__` / `llmquery__` prefixes if retrieval logic changes; preserve `nli__` unless NLI logic changes. Gemini query generation is **non-deterministic without the cache**, so thesis numbers come from a single cached run, never an average.
- **Thesis authorship constraint (stated in two separate handoffs):** acknowledge only *LLM response generation*. Atomization, classification, and taxonomy design are presented as the author's own work; frame the question set as intentional domain stratification.

## Next highest-priority work

**The `PROPERTY_TO_WIKIDATA` structural fix has been built** — `current/property_resolver.py` (2026-08-22). It replaces the static-map gate with `wbgetentities props=claims` retrieval + a datatype prior + structural guards (directional veto, superlative-containment veto, TEMPORAL core-term guard). Root cause it fixes: **predicate mapping was treated as a LOOKUP problem when it is a MATCHING/RETRIEVAL problem.** Batch 3: 6/34 covered at 5/6 precision, up from 0/34.

**It is deliberately NOT integrated into cells 69/75 yet.** Its first pass reached 47.1% coverage at ~31% precision — i.e. it re-introduced ~11 confident-wrong verdicts, the exact class the 2026-08-21 QID fix drove to zero. The guards fixed that, but the matcher should be reviewed before it touches live cells. **Coverage is not correctness** — this is now the second time on this project that a coverage jump masked a precision collapse.

## The evaluation set is 356 claims, not 122 (established 2026-08-22)

There are **four** gold claim sets, all with disjoint ID spaces. The project had been evaluating on Batch 3 alone. Full evidence trail: `reference/claim_set_inventory_2026-08-22.md`; consolidate with `current/consolidate_claims.py`.

| Set | IDs | rows | labeled | T / F / U | `gold_type` independent? |
|---|---|---|---|---|---|
| Batch 1 | `Q1`–`Q14` (10 questions; **Q3/Q4/Q6/Q8 deliberately absent**) | 125 | 125 | 112 / 8 / 5 | **yes — the only one** |
| Phase 2 | `Q15`–`Q26` | 126 | 109 | 87 / 1 / 21 | no (seeded) |
| Batch 3 | `B3_01`–`B3_12` | 122 | 122 | 115 / 4 / 3 | no (seeded) |
| Negatives | `B3N_01`–`27` | 27 | 27 | 0 / 27 / 0 | n/a (synthetic) |

**Real gold = 356: 314 TRUE / 13 FALSE / 29 UNVERIFIABLE.** Per type: RELATIONAL 184, TEMPORAL 53, QUANTITATIVE 46, ENTITY_ATTRIBUTE 44, CITATION 29.

### Batch/version census, verified 2026-08-22 late

**Four batches — 3 real + 1 synthetic negative set — and that is all there are.** Each has several versions on disk; the authoritative one is bolded.

| Batch | questions | rows | versions present | authoritative |
|---|---|---|---|---|
| Batch 1 | **10** (Q1, Q2, Q5, Q7, Q9–Q14) | 125 | `20260524_043744`, `20260524_045439`, `_1`, `_2` | **`_2`** (only labeled copy) |
| Phase 2 | 12 (Q15–Q26) | 126 | `phase2_20260607_185447`, `phase2_triaged`, `phase2_goldlabeled`, `(1)`, `(2)`, `(3)` | **`(3)`** |
| Batch 3 | 12 (B3_01–B3_12) | 122 | `20260726_173737`, `20260731_173625`, `20260731_175241`, `b3_triaged`, `b3_gold` | **`b3_gold`** |
| Negatives | n/a | 27 | `relational_negatives_batch3` (20), `_expansion`, `_round2`, `_merged` | **`_merged`** (20 original + 7 added) |

**Batch 1's missing q_ids are deliberate, not data loss.** Q3/Q4/Q6/Q8 were dropped and source-directed Q11–Q14 (WHO / Lancet / CDC / World Bank) swapped in to lift a CITATION rate that had been ~3.8%; recorded in the *Comparing systems against FActScore's dataset* handoff.

The three July files are Batch 3 *re-extractions* (124 → 114 → 122 rows as triage ran), not a fifth set — all three carry `B3_01`–`B3_12`. Dumping Batch 1's first column also prints a stray `IBM's rebuttal: 2.5 days with optimized Summit…` fragment, which is a `notes` field bleeding into column 1: direct confirmation of the embedded-newline rows behind the 125-vs-126 row count.

**Those per-type counts are by `gold_type`, and the routed system does not see them (measured 2026-08-22 evening).** `nonrouted_baseline.py --dry-run` loads the same 356 claims by the **`type`** column — what the router actually assigned — and gets a different mix:

| type | by `gold_type` | by `type` (what verifiers receive) | delta |
|---|---|---|---|
| RELATIONAL | 184 | **174** | −10 |
| TEMPORAL | 53 | **65** | **+12** |
| QUANTITATIVE | 46 | **45** | −1 |
| ENTITY_ATTRIBUTE | 44 | **43** | −1 |
| CITATION | 29 | **29** | 0 |

Both sum to 356. **The +12 on TEMPORAL is the router over-firing, and it reproduces the Batch 1 confusion matrix exactly** (12 of 14 routing errors over-predict TEMPORAL: 8 → RELATIONAL, 3 → QUANTITATIVE, 1 → EA). This is now measured on the pooled set, not just Batch 1.

Two consequences: **"the pooled 184" is wrong for any routed experiment — the RELATIONAL verifier is handed 174.** And the TEMPORAL verifier is handed **65** claims, 12 of which are not temporal assertions at all, so part of its 0% coverage is misrouting rather than a `PROPERTY_TO_WIKIDATA` gap. Always state which column a per-type count came from.

Batch 1's labels live **only** in `archive/csvs/haldetect_claims_20260524_045439_1.csv` and `_2.csv` — the 2026-08-21 reorg filed them as `(1)`/`(2)` download duplicates, but the bare-named file has no labels, so those "duplicates" are the only labeled copies of 125 claims. **`_2` is authoritative:** it and `_1` differ in exactly 8 rows, all `gold_type` (verdicts identical), and `_2` holds 8 more type corrections.

**Two things this changes:**

1. **Re-running RELATIONAL on the pooled claims is the highest-value experiment now available, and needs no new annotation.** The right number is **174** (claims *routed* to RELATIONAL), not 184 (claims whose `gold_type` is RELATIONAL) — see the table above. At its measured 55.3% coverage that is ~96 covered instead of ~26 → Wilson CI narrows from [62.1%, 91.5%] (±14.7pp) to roughly ±7.8pp, finally able to separate 80% from 65%. The Always-True baseline also drops 94.3% → 88.2%.
2. **Pooling does not rescue QUANTITATIVE.** All 5 gold-FALSE QUANTITATIVE claims across all batches pair an abstract-aggregate subject with a derived-rate property (global GDP growth, food-insecurity increase, purchasing-power reduction, preventable dementia cases, IRENA renewable capacity) and are all **Wikidata**-unreachable. This is systematic: **the claims most likely to be hallucinated are the least likely to be in a knowledge graph** — LLMs invent numbers precisely where no grounded fact existed to recall.

   **REVISED 2026-08-23: "unreachable by Wikidata" is not "unreachable."** Tested live, no API key required: the **World Bank API** returns world GDP growth for 2009 as **−1.333%** (`api.worldbank.org/v2/country/WLD/indicator/NY.GDP.MKTP.KD.ZG`), which falsifies the gold-FALSE claim "global GDP contracted 0.1% in 2009" *automatically*. **WHO GHO OData** (`ghoapi.azureedge.net/api/`), **PubMed E-utilities** and **Crossref** also answered 200 with no key. So the derived-rate aggregates that Wikidata cannot model are exactly what statistical agencies publish as their primary product.

   Three consequences: (a) `--sensitivity` is no longer the *only* discrimination measurement available — some real gold negatives become checkable; (b) QUANTITATIVE tier 2 has a concrete, free backend and no longer needs to be scoped jointly with CITATION; (c) **this strengthens the thesis rather than weakening it** — "route to the source that models this kind of fact" is a stronger claim than "route to Wikidata", and the Wikidata-unreachability finding survives as a statement about knowledge *graphs* specifically, which is the more interesting version.

   Still true and unchanged: QUANTITATIVE tier 2 needs building, and no number from it exists yet.

### `gold_type` is not a label in Phase 2 or Batch 3 — never score routing on them

Both show 100% agreement with the classifier's own `type` column (109/109 and 122/122), and Batch 3's `type` distribution is *identical* to its gold_type (47/29/22/12/12). It was seeded from classifier output and never reviewed. **Any routing accuracy from those batches is 100% by construction.** `consolidate_claims.py --routing` refuses them rather than trusting a reader to remember.

**Correction 2026-08-22 (evening): Batch 3's verdicts are sound, but Phase 2's are NOT.** An earlier version of this section said "verdict labels are unaffected and sound" for both. That is wrong for Phase 2, and the error inflates any pooled figure. Per `old-chats-handoffs/haldetect_session_handoff_RAG-for-fact-verification-experimentation_2026-08-22.md`, Phase 2's `gold_verdict` column was **AI-filled** conservatively (12 TRUE / 52 UNVERIFIABLE on the RELATIONAL slice), then an AI **flipped 31 UNVERIFIABLE → TRUE**. That relabel alone moved measured RELATIONAL accuracy **~15% → 61.11% with no change to the verifier** — the single clearest demonstration in this project that label quality, not verifier quality, can dominate a headline number. That handoff's own standing rule: *"AI-filled labels corrected by AI are not independently verified and should not be treated as ground truth until the author has reviewed them."*

So of the 356 pooled claims, **109 rest on labels that are not independent ground truth**, and the 31 flipped rows are the highest-risk subset. Until the author reviews them: report pooled results **both with and without Phase 2**, and never quote a pooled figure that leans on it. Batch 1 (`_2`, human-labeled) and Batch 3 are unaffected.

**RESOLVED 2026-08-23 for the highest-risk tier.** The exact 31 flipped rows were recovered by diffing `archive/csvs/haldetect_phase2_goldlabeled.csv` (the pre-flip state: 12 TRUE / 52 UNVERIFIABLE) against `current/haldetect_phase2_goldlabeled (3).csv` (43 TRUE / 21 UNVERIFIABLE). All 31 were then reviewed against primary sources — WHO fact sheets, UNFCCC Article 4, PMC/PubMed, JFK Library, W3C, NIAID, Nobel Prize, IDF Diabetes Atlas — and **all 31 confirmed TRUE. The AI flips were justified.** Verdicts and per-claim citations are recorded in `current/phase2_labels_for_review.csv`.

**The diff also surfaced 45 changes the handoff never documented:** 44 `(blank) → TRUE` and 1 `(blank) → FALSE`. Those are *fills*, not flips — the pre-flip file had only the 64-row RELATIONAL slice labeled, and 45 more were filled later (64 + 45 = 109 ✓). They are still AI-origin and unreviewed, so the review file carries three tiers: **1-HIGHEST (31, now done)**, **2-HIGH (45 fills, open)**, **3-MEDIUM (33 AI-filled-unchanged, open)**.

**Six claims where the label is right but the wording outruns the source** — worth a thesis footnote, because a verifier that marks these FALSE is not straightforwardly wrong, it is disagreeing about granularity:

| claim | issue |
|---|---|
| `Q21_C08` | sources say diabetes *"increases risk of"* heart failure; the claim says *"leads to"* |
| `Q24_C15` | Nobel source says Curie's anemia was *"likely caused by"* radiation; the claim asserts causation |
| `Q23_C09` | true, but the Turkey missile removal was a **secret** understanding, not a public term |
| `Q17_C08` | designed *insertions* require a donor template (HDR), not repair alone |
| `Q20_C10` | *"prevent"* is stronger than the sources' *"cannot afford"* |
| `Q20_C09` | debt→purchasing-power is an indirect pathway, and has the weakest citation of the 31 |

Consequence: the FEVER routing experiment is not a bonus — it is the only route to independent routing measurement at scale.

#### First tier-2 finding — `Q22_C01` FLAGGED, NOT FLIPPED (2026-08-26)

`Q22_C01` — *"The FAO reported in 2023 that global food insecurity increased during 2022"* —
is gold **TRUE**, and it looks wrong. **SOFI 2023 reports moderate-or-severe food insecurity
as *virtually unchanged* 2021 → 2022;** the rise it headlines is the 2019 → 2022 horizon
(+122 M), a different comparison than *"during 2022"*.

**It was NOT flipped, and the reason is the rule, not the evidence.** `Q22_C01` sits at
`priority='2-HIGH'`, `why='AI filled a blank; never reviewed'` — so flipping it is *an AI
overwriting an AI-filled label*, exactly what this file exists to prevent. The precedent is
recorded above: relabelling Phase 2 once moved measured RELATIONAL accuracy **~15% → 61.11%
with no change to the verifier.** A verdict I cannot cite is not better than a blank.

**Recorded via two new machine-origin columns, `FLAG` and `FLAG_EVIDENCE`.** They are
additive — 109 rows and all 13 original columns byte-identical, **0 `AUTHOR_*` cells
written** (the 31 tier-1 verdicts are untouched). `AUTHOR_VERDICT` stays blank because it is
the author's column. `Q22_C03` is flagged `PREMISE-DEPENDENT`, not false: *"the rise"* has a
defensible 2019 → 2022 reading and may stand as TRUE even if `Q22_C01` flips.

**`EVIDENCE: UNVERIFIED IN SESSION.`** `WebSearch` is unsupported on this model
(`400 tool type 'web_search_20250305' is not supported`) and FAO / WHO / UNICEF launch pages
returned 403/404, so this rests on model knowledge, not a checked citation. **Author must
confirm against SOFI 2023 before changing anything.**

**Blast radius if it does flip** — computed offline, so the decision is costed:

| effect | detail |
|---|---|
| files containing the id | **18 CSVs** |
| `SYN_CITA_083` (base `Q22_C01`, source_swap FAO→WHO) | its gold FALSE stays *correct*, but it stops being a **clean controlled perturbation** — the base would already be false for an unrelated reason, so a detector could score it right for the wrong reason. Drop from the `source_swap` slice or re-base. |
| `SYN_CITA_002`, `SYN_CITA_084` | based on `Q22_C03`, which inherits the *"the rise"* premise |
| Level 1b | **immaterial.** `Q22_C01` is gated out (`work title 'FAO' has 0 content word(s)`), so FPR moves 0/25 → 0/24 and a 4th missed gold-FALSE natural claim appears. **The 9/25 negatives figure is unchanged.** If `SYN_CITA_083` is also dropped, `source_swap` reads 4/10 = 40.0% and overall TPR 9/24 = 37.5% — quote those only *after* the author decides. |

### The router over-fires TEMPORAL — measurable only on Batch 1

**111/125 = 88.8% [82.1%, 93.2%]** overall, but 12 of 14 errors over-predict TEMPORAL (8 → RELATIONAL, 3 → QUANTITATIVE, 1 → EA). Per route: **TEMPORAL precision 15/27 = 55.6% [37.3%, 72.4%]** at 100% recall; QUANTITATIVE 87.5%/82.4%; RELATIONAL 100%/86.3%; EA 100%/88.9%; CITATION 100%/100%. Cause: it routes on **temporal-expression presence**, not temporal-predicate-hood.

Confirmed independently on Batch 3, where gold_type can't be used: only 8 of 12 TEMPORAL-routed claims assert a date → **33% misrouted**. Two are sprint times whose date sits in `secondary` only; one is a *duration* ("1,500 years"), which is **unreachable by construction** because the TEMPORAL verifier filters to the `time` datatype while Wikidata stores durations as `quantity` (P2047).

A minimal pair already in the data: `B3_07_C05` and `B3_07_C06` share subject, property (`record_time`) and value (10.49 seconds) but route to TEMPORAL vs QUANTITATIVE — the only difference is a date adjunct vs a place adjunct. Also note the sprint-records gap spans **8 claims across two verifiers**, so no single verifier's diagnostics can report all of it; log routing separately from verification.

### Read this before quoting any accuracy number

Pooled real gold is **314 TRUE / 13 FALSE / 29 UNVERIFIABLE of 356**, so an unconditional "TRUE" scores **88.2%** (on Batch 3 alone it scores 94.3%). TEMPORAL and EA have **zero negatives across Batch 3's 34 claims**; QUANTITATIVE has one, and it is unverifiable in principle (no Wikidata home). Use `current/metrics.py` — it implements all four rules below and prints the baselines next to every result, so the comparison can't be skipped. Citations in `reference/paper_findings_2026-08-22.md`:

- Report **per-class F1** plus Random / Always-True / Always-False baselines, never accuracy alone (Factcheck-Bench's Always-True scores F1 = 0.88 on the True class and 0.00 on False).
- **NO metric is safe across class priors — check the degenerate rows every time (2026-08-25).** On the natural 356 (88% TRUE) accuracy is the gamed metric: Always-True scores 88.2% while F1(FALSE) correctly reads 0.00, which is why the rule above says lead with F1(FALSE). But on a negatives-enriched set the trap **mirrors**: on the 53-row QUANTITATIVE positives+negatives population (28 TRUE / 25 FALSE), **Always-False scores F1(FALSE) = 0.641 — beating every real system including ours.** So "lead with F1(FALSE)" is itself prior-dependent. **MCC is the only figure that no degenerate strategy games in either direction** (Always-True, Always-False and Always-UNVERIFIABLE all score exactly 0.000), which is why it carries the QUANTITATIVE headline. Always print the degenerate rows next to the result — `metrics.report()` does this automatically — and never move a metric or a threshold between populations without restating the class prior.
- Report **Wilson CIs**. RELATIONAL's "80.77%" rests on ~26 covered claims → 95% CI [62.1%, 91.5%], which **cannot separate 80% from 65%.**
- Effective n for an accuracy claim is `coverage × dataset n`, far below the dataset size.
- Where gold negatives don't exist, measure discrimination by **controlled perturbation** (`quantitative_verifier.py --sensitivity`), not by accuracy.
- Never merge **gold** UNVERIFIABLE (not checkable in principle) with **predicted** UNVERIFIABLE (couldn't reach evidence). A confident verdict on a gold-UNVERIFIABLE claim is an error, not a hit.

## Where things live

- `current/` — verified-current files only (see `current/README.md` for exactly why each one qualifies).
- `archive/` — superseded/duplicate/historical-draft files, nothing deleted, all reversible (see `archive/README.md`). **One exception to "superseded":** `archive/csvs/haldetect_claims_20260524_045439_2.csv` holds Batch 1's 125 gold labels and is live evaluation data, not a leftover.
- `reference/` — handoff/context docs only, no claim data. `reference/haldetect_starthere_2026-08-10.md` is the fullest single account if this file isn't enough; `reference/paper_findings_2026-08-22.md` is the literature index and metrics rationale; `reference/claim_set_inventory_2026-08-22.md` is the claim-set audit. `reference/external_catalog_assessment_2026-08-26.md` assesses three externally-supplied technique documents — **read it before acting on any external roadmap**, because it shows one built on a three-day-old snapshot of these diagnostics and ranking its recommendations against two numbers that had already been corrected.
- `latest/` — empty; the 10 files originally held back here have all been filed into `current/` or `archive/csvs/`.
- `old-chats-handoffs/` — **five exported session handoffs, added to this file's awareness 2026-08-22. Read these before planning experiments.** They are the only record of decisions made before the notebook era, and three of them independently name the non-routed baseline as the core missing result. Also the only place holding: the RQ numbering, the Phase 3d-vs-3e reporting decision, the RELATIONAL A–E sub-typing, the page-relevance-gate negative result, the cache-prefix discipline, and the thesis authorship constraint. Chronological order is *Taxonomy-based* (Feb–Apr) → *Comparing systems against FActScore's dataset* (May–Jul) → *RAG for fact verification* → *LLM verification capabilities* (literature) → *Reading files from GitHub repository* (FActScore-priv).

## Execution status — 4 of 6 scripts VALIDATED 2026-08-22 evening; 2 bugs found and fixed

The Bash safety classifier was unavailable across two full sessions, so these were built by reading source and desk-tracing data. The author ran them manually on 2026-08-22 evening. **Results below are real output, not predictions.** Anything still marked unrun stays unquotable.

| command | status | result |
|---|---|---|
| `metrics.py` | **PASS** | Always-True **88.2%** [84.4%, 91.2%], F1(FALSE) **0.00**, MCC **0.00**, Macro-F1 0.312, AURAC 0.993. Exactly as predicted — the trap is real and now demonstrated on our own gold. |
| `llm_baseline.py --selftest` | **PASS** | 10/10 parser cases; the synthetic Always-True demo reproduces 88.0% / F1(FALSE) 0.00; cache keys stable and binary-flag-sensitive. |
| `hybrid_fallthrough.py --selftest` | **PASS** | **ALL PASS**, all 35 checks, including both date-adjacency gates and the shape-preserving perturbations. |
| `hybrid_fallthrough.py --diagnose` | **PASS** | **34/34 ABSTAIN** — the inverted expectation held. All 34 report `no resolver supplied — tier 1 skipped by design`. The QID bug has **not** crept back. Also correctly printed `!! THAT ACCURACY IS NOT EVIDENCE` for the zero-negative slice. |
| `consolidate_claims.py --verify` | **bug found → fixed** | Reported `b1: expected 126 rows, got 125` and refused to write. **The expectation was wrong, not the loader.** See below. |
| `quantitative_verifier.py --selftest` | **bug found → fixed** | `SyntaxError` at line 489 — the file had never been parsed by anything. See below. |

### Bug 1 — `quantitative_verifier.py:489` SyntaxError (fixed)

`save_cache(cache)    if not hits:` — two statements collapsed onto one line, so **the module never parsed at all**. Fixed by splitting them and dedenting `if not hits:` out of the `else:` branch, because an empty hit list must return the same honest gap whether it came from the cache or a fresh search. A grep for the same collapse pattern across all of `current/` found no other instance. `--diagnose` and `--sensitivity` still need to run; its ~24% coverage prediction is still unverified.

### Bug 2 — the Batch 1 row count was 125 all along, not 126 (fixed)

`consolidate_claims.py` hardcoded `expect: {rows: 126}` for Batch 1 and aborted. Verified directly rather than trusting either number: `wc -l` = 127, but `grep -c "^Q[0-9]"` = **125**, the file has **no trailing newline**, and **two rows carry embedded newlines inside quoted fields**. So 127 newlines describe 125 logical rows — `csv.DictReader` was right and the hardcoded expectation was derived from `wc -l` minus one, which is *precisely* the multiline-quoted-field trap the script was written to guard against. A textbook instance of the standing rule, caught by the script's own integrity check.

**The pooled 356 total is unaffected** — it is built from *labeled* counts (125 + 109 + 122), and 125 labeled was always correct. Only the row-count expectation and the Batch 1 table row changed.

### Still unrun

    .venv/bin/python current/consolidate_claims.py --stats --routing --write
    .venv/bin/python current/quantitative_verifier.py --diagnose   # expect coverage ~24%; MUCH higher = warning
    .venv/bin/python current/quantitative_verifier.py --sensitivity
    .venv/bin/python current/gemini_key.py --check                 # new: removes the Colab userdata coupling
    .venv/bin/python current/llm_baseline.py --check               # then --mode closed, then --force-binary

Or just run `./verify_env.sh`, which chains the syntax check, both bug fixes, the Gemini live call and the ollama check in one go.

The remaining inverted expectation: `quantitative_verifier.py --diagnose` reporting coverage far above ~24% is a **warning**, not a win; that is the exact shape of the property-resolver precision regression.

Reverse commands for everything built in that window are in `WORKLOG_2026-08-22.md`.
