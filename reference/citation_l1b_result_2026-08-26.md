# CITATION Level 1b — measured, 2026-08-26

> **SUPERSEDED IN PART, same day.** Written before task #23 dropped `SYN_CITA_083` from the
> negatives (WHO co-published SOFI 2023, so the FAO→WHO `source_swap` injected no falsity), and
> before the `Q22_C01` flip left the gold-TRUE pool. **Denominators only — every numerator below
> stands.** Current: TPR **9/24 = 37.5%** [21.2, 57.3] (J **+0.375**), `source_swap` **4/10**,
> baseline CITATION **5/23 = 21.7%** [9.7, 41.9] (J **+0.134**), FPR **0/24** on 24 gold-TRUE
> natural claims. **Unchanged and load-bearing:** FPR 0, **0 confident errors**, `year_shift`
> 5/12, the 8-of-9 Q103843442 concentration, the overlapping CIs, and **4** gold-FALSE natural
> CITATION claims (was 3 — the flip added one, and L1b abstained on it, so true positives on the
> natural set stayed 0). Authority: `reference/syn_cita_083_drop_2026-08-26.md` and `CLAUDE.md` §3.
>
> **REFRAMED, 2026-08-26 by task #22 — the head-to-head with the baseline is the wrong comparison,
> and the reason is structural.** McNemar's exact test (`current/mcnemar.py`,
> `reference/mcnemar_rq2_2026-08-26.md`) finds **one** discordant pair across all 53 CITATION rows
> (`SYN_CITA_075`) and **zero** on the natural 29 — not small-sample bad luck but **coverage
> disjointness**: L1b answers 9 rows, the baseline 23, **union 28, intersection 4**. L1b reads
> Wikidata `P577`/`P123`; the baseline reads BART-MNLI over Wikipedia passages. Their reachability
> sets barely meet, so *no* convention supports "which is better" — C2 is inadmissible (L1b emits no
> TRUE by design, so exact-match forfeits every gold-TRUE row) and C3 is gamed (Always-UNVERIFIABLE
> ties its `p = 0.0039`). **What replaces it is stronger, not weaker:** L1b answers **5 rows the
> baseline abstains on and is correct on 5/5** (`SYN_CITA_063/064/067/076/077`), while the baseline
> uniquely answers 19 at **11 right / 8 wrong**, and neither reaches 25. **That is the first
> quantitative case for composition (#3), and the J comparison below should be read as the marginal
> summary it is — a paired test cannot corroborate it on this corpus.** The 8-of-9 Q103843442
> concentration (R11) travels with the 5 unchanged.

`current/citation_l1b_verifier.py` (~600 lines, `--selftest` ALL PASS, `--diagnose`
writes `current/citation_l1b_results.csv`, 54 rows). Built on the two preconditions
shipped first: `series_resolver.py` (#17b) and `source_consistency.py`.

Answers the gap named in `reference/citation_negatives_headroom_2026-08-25.md`:
**17 of 25 CITATION negatives need no NLI at all** — 12 via publication date (`P577`),
5 via a publisher conflict (`P123`) on a fabricated composite title. Level 1 asks only
*does the source exist*, which none of the 25 perturbs.

---

## 1. The headline, and the two numbers that must travel with it

| | TPR on the 25 negatives | FPR on the 25 gold-TRUE natural | **J = TPR − FPR** |
|---|---|---|---|
| **Level 1b (end-to-end)** | **9/25 = 36.0%** [20.2, 55.5] | **0/25 = 0.0%** [0.0, 13.3] | **+0.360** |
| non-routed baseline, CITATION | 5/24 = 20.8% [9.2, 40.5] | 2/25 = 8.0% [2.2, 25.0] | +0.128 |

J nearly triples on **the type the baseline is weakest at** — CITATION's +0.128 was the
lowest row in `negatives_cache_audit.py` and the reason CLAUDE.md names it "the
reachable gap". J is the right metric here for the reason recorded project-wide: every
row in the negatives set is gold FALSE, so an unconditional "FALSE" scores TPR 1.00,
and J is 0 for Always-False and Always-True alike.

**Two honesty constraints on that table.**

1. **The TPR confidence intervals overlap heavily** ([20.2, 55.5] vs [9.2, 40.5]).
   n = 25 cannot separate 36% from 21%. The *TPR* comparison is suggestive, not
   established. What is clean is the **FPR: 0/25 against 2/25**, and the confident-error
   count — **0 confident-wrong verdicts**, where the baseline produces 2 on the same
   gold-TRUE claims. That is the same prior-independent shape that carries the
   QUANTITATIVE result (0 confident errors vs 19).
2. **8 of the 9 detections come from ONE Wikidata item.**

       Q103843442  (IPCC AR6)                          8
       Q29876135   (State of World Fisheries and Aq.)   1

   **State this wherever the 9 is quoted: one work working, not CITATION working.**
   Identical in kind to QUANTITATIVE's *"all 6 negative detections come from a single
   property (P2044)"*. A single item's `P577`/`P123` being well-populated is not
   evidence that Wikidata models citations generally.

By injection type: `year_shift` **5/12** [19.3, 68.0] (date route), `source_swap`
**4/11** [15.2, 64.6] (publisher route), `cross_substitute_categorical` 0/2.

---

## 2. Ceiling ≠ end-to-end, and the gap is retrieval

| year_shift negatives | detected |
|---|---|
| **ceiling** — hand-curated subject strings, `series_resolver.py --selftest` | **8/12** = 66.7% [39.1, 86.2] |
| **end-to-end** — subject extracted from claim text, this module | **5/12** = 41.7% [19.3, 68.0] |

The 3-claim gap is entirely Lancet, and it is a **candidate-generation limit, not a
ranking one**. The ceiling was measured with `'Lancet Commission on dementia
prevention'`, taken from the headroom doc during design. End-to-end extraction yields
`'Lancet Commission'`, which returns **4 candidates and not one is a dementia work** —
so no threshold move, tie-band change or re-pick can recover them. Abstention is
correct.

**Report both. Neither substitutes for the other**, and a reader given only the 8/12
would over-estimate what the built system does on text it has not been handed help
with.

### The `subject` column is contaminated — do not close the gap with it

The obvious fix is the corpus `subject` field. It cannot be used:

    SYN_CITA_068   claim "The 2021 Lancet Commission ..."   subject '2020 Lancet Commission'
    SYN_CITA_071   claim "The 2030 Lancet Commission ..."   subject '2020 Lancet Commission'

The perturbation harness rewrote the claim and **left `subject` holding the original,
un-perturbed year**. Resolving from it would hand the verifier the exact value the
negative exists to hide, and every "detection" would be measuring the harness. The
negatives file also carries `original_value` / `corrupted_value` outright. Extraction
reads claim text only, uniformly across both populations — using different inputs for
natural and synthetic rows would invalidate the comparison even if neither leaked.

---

## 3. Guard 4 (topical anchoring) — added to `series_resolver` for a live confident-wrong verdict

End-to-end extraction produced a **FALSE on gold-TRUE `Q12_C01`**, the exact class the
2026-08-21 QID fix drove to zero. `'Lancet Commission'` resolved to three unrelated
Lancet Commissions — Editor's note 2015, Value of Death 2018, UK nursing 2014 — giving
span **2014–2018**. That span is **misplaced, not merely narrow**, so the claimed 2020
fell outside it.

**Guards 2 and 3 cannot see this.** Guard 2 fires on an undated member; guard 3 on a
SERIAL with fewer than 2 distinct years. Here the members are dated, distinct and
plural — the span is well-formed and about the wrong works.

**Root cause: `SUBJECT_OVERLAP_MIN` is a symmetric Jaccard, and that is the defect.**
It gets *more* permissive as the requested title gets shorter, because a short title is
a subset of many longer ones:

    jaccard({lancet, commission}, {lancet, commission, value, death}) = 0.50   > 0.25

The discriminating direction is **asymmetric**: how much of the *label* the subject
fails to explain. Guard 4 encodes that — a member is kept iff the content its label
introduces beyond the subject is either empty (exact-ish title match) or intersects the
claim's anchor terms.

Four properties, each load-bearing:

1. **Independent by construction.** It reads only label content the subject did *not*
   supply, so it is not the selection signal used twice — the circularity that got the
   resolver's 72/72 downgraded to *"0% refusal, correctness unverified by an
   independent signal"*.
2. **It can only ever DROP members.** A narrowed span is then re-tested by guards 2
   and 3, so a drop can convert SERIAL → `INCOMPLETE_SPAN` → abstain, never into a new
   confident verdict.
3. **Strict, not inert, when the claim is nothing but the title.** AR6 survives via the
   empty-extra branch; a hypothetical *"The Lancet Commission was published in 2024"*
   drops every intruder and abstains.
4. **`anchors=None` is the default**, so every pre-existing caller and the committed
   8/12 ceiling are untouched — re-verified: `series_resolver.py --selftest` still
   ALL PASS at IPCC 5/5, Lancet 3/5, World Bank 0/2.

Anchor terms exclude years, bare numerals, function words and reporting verbs. **Every
exclusion makes guard 4 stricter**, which is the safe direction for a check that can
emit FALSE: a missing anchor costs coverage, a spurious one buys a confident-wrong
verdict.

### A detection off a wrong span is luck, not evidence

`SYN_CITA_071` (claimed 2030) returned FALSE **using the bogus 2014–2018 span** — and
its gold-TRUE twin `Q12_C01` (2020) returned FALSE off the same span. Guard 4 removes
both. That is a detection **deliberately given up**, and the `LIVE_CASES` entry now
records why. Pairing every detection with its unperturbed base claim is what exposed
it; a negatives-only run would have scored it as a win.

---

## 4. Non-circularity is closed in both channels, and the second one was leaking

`series_resolver`'s year-free signature proves no year can be **passed** in. It does not
prove none **leaks** in: `ctx` feeds full-text search and SBERT similarity, so an
unstripped claim carries the claimed year into candidate selection.

**Measured, not asserted:** the Lancet leader score moved **0.566 → 0.553** once ctx was
year-stripped. The claimed year *had* been influencing selection.

Fixes: `strip_years()` on ctx, numerals stripped from anchors, and a live test asserting
span/mode/anchors are identical across four claimed years.

**That test was initially vacuous and had to be re-pointed.** Run on the Lancet claim it
compared `NO_TOPICAL_MATCH` to `NO_TOPICAL_MATCH` — passing while testing nothing, which
is worse than no test because it reads as evidence. It now runs on AR6, which yields a
real span, and carries two extra assertions:

    span invariant across 2021/2022/2033/2133 : '2021-2023'   (identical)
    span non-empty, mode in SINGLE_WORK/SERIAL               (not vacuous)
    verdict still varies: {2022: UNVERIFIABLE, 2133: FALSE}  (not inert)

The evidence is invariant to the value under test; the answer is not. Both halves are
needed — invariance alone is also satisfied by a verifier that never decides anything.

---

## 5. The gate — three grammatical positions of a year, and only two license a date test

The extractor's whole job. Testing an unlicensed year against a publication span is a
category error that manufactures false alarms.

| role | example | licensed? |
|---|---|---|
| PUBLICATION | *"was published in 2024"* | **yes** |
| EDITION | attributive: *"The 2021 Lancet Commission"* | **yes** |
| REPORTING | *"reported in 2024 that…"* — when the org **spoke** | no |
| PREDICATE | `SYN_CITA_082`: *"…suffered from stunting in 2022"* — when the **fact** happened | no |

Second gate half: `MIN_WORK_CONTENT = 2` content words, which separates *"Sixth
Assessment"* from a bare organisation reference (`'WHO'`, `'FAO'`, `'OECD'`, `'CDC'`)
and from a one-word title (`'Renewables'`). **The two halves reject independently** — a
licensed year must not rescue a bare org reference, and `--selftest` asserts it.

Gate disposition: natural `{NONE: 20, DATE: 4, PUBLISHER: 4, BOTH: 1}`, negatives
`{NONE: 9, DATE: 5, PUBLISHER: 5, BOTH: 6}`. 12 offline gate cases on real corpus
strings, including the two traps: `SYN_CITA_082` (predicate year, gated out twice over)
and `B3_05_C02` (gold FALSE but its **1972 is correct**, so the date route must abstain
and leave it to Level 2).

---

## 6. Why the natural set can only ever lose here

**Max TP on the natural set is 0, by construction.** All 3 gold-FALSE natural CITATION
claims are **content** falsities, which no property check reaches:

| claim | falsity |
|---|---|
| `Q12_C11` | wrong largest-reduction factor |
| `B3_05_C02` | the ten criteria — and its 1972 is the *correct* year |
| `B3_12_C07` | wrong percentage |

So all measurable value is on the negatives and **all risk is false alarms on the 25
gold-TRUE claims**. Result: **0/25**. That was the pass condition, and it is the only
outcome the natural set could have contributed.

Two design consequences follow, and both are already in force:

- **1b EMITS FALSE**, unlike `source_consistency`, which only ever removes a verdict and
  is therefore safe in both error directions. 1b can manufacture the confident-wrong
  class, so it is precision-gated at the front — the four recorded coverage-up /
  precision-down events on this project are why.
- **No TRUE verdict exists in the module.** Consistent provenance, or a year inside the
  span, returns UNVERIFIABLE; Level 1 owns TRUE. `--selftest` asserts no `TRUE`
  assignment in production code, plus a meta-check that the assertion has not gone
  vacuous by scanning past `verify_l1b`.

---

## 7. What is NOT built

- **Level 2 (attribution).** Still needs NLI, still SIGBUSes locally, and NLI
  contradiction precision caps at 0.20 anyway.
- **The 12 `year_shift` negatives are not an attribution problem** — that was the point
  of the headroom doc. 5 of 12 now fall to `P577`. The remainder are Lancet (retrieval,
  above) and World Bank (guard 3 abstains rather than risk 2023).
- **Series-level resolution for serials.** `source_consistency` catches the wrong
  edition; nothing yet *finds* the right one.
- **Span-not-membership is in force and it costs nothing here.** AR6 is multi-part
  across 2021–2023 with only two `P577` values, so membership would mark *"published in
  2022"* FALSE though WG2/WG3 genuinely appeared then — a manufactured confident-wrong
  verdict. All five claimed years are after 2023, so the span rule detects 5/5 too.

## Reproduce

    python current/citation_l1b_verifier.py --selftest    # 12 gate + 7 live + invariance
    python current/citation_l1b_verifier.py --diagnose    # 54 rows -> citation_l1b_results.csv
    python current/series_resolver.py      --selftest     # the 8/12 ceiling
