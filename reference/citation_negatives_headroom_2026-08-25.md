# CITATION headroom: what the 25 negatives actually attack, and what Wikidata can reach

**Date:** 2026-08-25
**Reproduce:** offline composition — `current/citation_negatives_analysis.py --composition`
(zero network, ~1 s) · live reachability — `--reachability` (~15 Wikidata calls).
**Inputs:** `current/synthetic_negatives.csv` (85 rows, 25 CITATION),
`current/quantitative_verifier.resolve_entity` (the only resolver carrying all
three 2026-08-23 fixes), `current/property_resolver.fetch_entity_claims`.

This was scoped as "run routed CITATION Level 1 on its 25 gold negatives, the way
Step 33 did for QUANTITATIVE." **The run was not worth making, and finding out why
is the result.** Two further findings came out of the reachability check, one of
which is a new resolution failure mode.

---

## 1. Not one of the 25 negatives perturbs source existence

Level 1 asks a single question: *does the cited source exist?* Every one of the 25
CITATION negatives names a **real** source.

| injection | n | what it perturbs | does the source still exist? |
|---|---|---|---|
| `year_shift` | 12 | the publication/edition **year** | yes — name untouched |
| `source_swap` | 11 | the publishing **organisation**, replaced by another real one (**WHO in 10 of 11**, CDC in 1) | yes — WHO and CDC both exist |
| `cross_substitute_categorical` | 2 | what the report **says** | yes — source and title both correct |

So Level 1 detects **0 of 25**, and *not because Level 1 is broken*: it answers its
own question correctly every time. CLAUDE.md currently records the gap as

> *"Level 1 can never return FALSE — a source that fails to resolve is
> UNVERIFIABLE, not fabricated — so F1(FALSE)=0.00 by construction."*

That is true but understates it. **Even a Level 1 that *could* return FALSE would
still detect 0/25**, because non-resolution is never the signal here. Changing L1's
FALSE policy — the tempting fix, and the risky one — would buy exactly nothing on
the only gold-FALSE CITATION set we have.

`source_swap` also carries the same control property that makes the QUANTITATIVE
`cross_substitute` result strong: because the injected organisation is *real*, there
is no implausibility, surface-form, or LLM-prior signal to exploit. An existence
check does not merely miss these — it resolves WHO successfully and thereby
**vouches for the fabricated citation**.

## 2. Where the headroom is, and 17 of 25 need no NLI at all

| n | shape | detectable by | needs NLI? |
|---|---|---|---|
| 12 | wrong year on a correctly-named work | publication date (**P577**) | no |
| 5 | fabricated *composite title* — "WHO Sixth Assessment Report", "CDC World Mental Health Report 2022", "Food and Agriculture Organization (WHO)" | real title resolves, its **publisher (P123) conflicts** with the claimed one | no |
| 6 | org-only attribution swap — "The WHO reported in 2023 that the global extreme poverty rate remained stagnant at 8.4%" | does WHO actually assert this | **yes** |
| 2 | content swap between two real reports | does this report assert this | **yes** |

**17 of 25 (68%) are reachable by structured lookups with no inference step.** That
matters specifically because NLI is the component that SIGBUSes locally *and* whose
contradiction precision caps at 0.20 across all 225 sweep grid points. The CITATION
FALSE class is not blocked on Level 2 to the degree the project has assumed.

Note the split is not L1-vs-L2. The 12 year-shifts are neither *existence* nor
*attribution* — they need a **third** check, a property comparison on the work
itself, structurally identical to what `quantitative_verifier.py` already does with
`quantity` but filtered to `time`.

---

## 3. Live reachability: 8 of 25 today, all through one entity

| target | resolved | score | evidence found |
|---|---|---|---|
| `IPCC Sixth Assessment Report` | **Q103843442** | **0.946** ✓ | `P577 = {2021-08-09, 2023-03-20}`, `P123 = Q171183` |
| `Sixth Assessment Report` (bare) | **Q103843442** | **0.946** ✓ | same item — the composite-title route lands here |
| `Lancet Commission on dementia prevention` | Q92676744 | 0.605 ✓ | **WRONG WORK — see §4** |
| `Poverty and Shared Prosperity` | Q139955780 | 0.654 ✓ | wrong edition; **P577 absent**; 5 properties |
| `World Mental Health Report` | — | 0.530 ✗ | best candidate is a 2002 article about the 2001 report |
| `The State of World Fisheries and Aquaculture` | — | 0.585 ✗ | `P123 = Q82151` (FAO) **exists but is out of reach** |

Publisher QIDs verified independently rather than assumed: **Q171183 =
Intergovernmental Panel on Climate Change**, **Q82151 = Food and Agriculture
Organization of the United Nations**.

**Reachable today: 8 of 25.**

- **5** IPCC `year_shift` rows (claiming 2024 / 2025 / 2028 / 2033 / 2123) against
  `P577 = {2021, 2023}`.
- **3** IPCC `source_swap` rows ("The WHO Sixth Assessment Report…") against
  `P123 = IPCC ≠ WHO`.

**All 8 run through a single Wikidata item, Q103843442.** That is the same
concentration warning as *"6 of 6 QUANTITATIVE detections are mountain elevations
via P2044"* — **one work working, not CITATION working** — and it must be stated
wherever the 8 is quoted.

### The safe date rule loses nothing here, and there is a trap in the obvious one

AR6 is a multi-part work published across 2021–2023; Wikidata lists only two P577
values. A **set-membership** test ("is the claimed year one of the P577 values")
would mark *"published in 2022"* FALSE — yet WG2 and WG3 genuinely appeared in 2022.
That is a manufactured confident-wrong verdict.

A **span** test — FALSE only when the claimed year falls outside `[min P577, max
P577]`, abstain inside — is the lenient, defensible version. Here it costs nothing:
all five claimed years (2024–2123) are strictly after 2023-03-20, so the span rule
detects **5/5 as well**. Prefer the span rule; the trap only shows up on a year the
current negatives happen not to use.

Matched-pair check, computed from the same P577: base `Q5_C01` ("published in
2023", gold TRUE) → 2023 is in range → TRUE; its five perturbations → FALSE. **6/6
on a matched pair, under either rule.**

---

## 4. A THIRD resolution failure mode: editions of a serial publication

The 2026-08-21 fix removed property-gated selection. The 2026-08-23 fixes added
prominence, full-text search and `mul` labels. **Neither touches this, and it is
live right now.**

Asked for `Lancet Commission on dementia prevention`, the resolver **accepted**:

```
Q92676744  @0.605  'The Lancet Commission on Dementia Prevention, Intervention,
                    and Care: a call for action'   (2019 article, 0 sitelinks)
Q139937996 @0.597  'Dementia prevention, intervention, and care: 2024 report of
                    the Lancet standing Commission'
Q98186330  @0.595  'Dementia prevention, intervention, and care: 2020 report of
                    the Lancet Commission'         <-- THE CORRECT WORK
```

Three near-identical scores spanning **0.010**, covering the **2019**, **2024** and
**2020** works, and the correct one is **rejected by one hundredth of a point**. The
accepted item's `P577 = 2019-06-01` would have falsified the gold-TRUE base claim
*"The 2020 Lancet Commission identified 12 modifiable risk factors…"* — **a
confident-wrong FALSE**, the exact class the QID fix drove to zero.

Every candidate has **0 sitelinks**, so the prominence tie-break is inert by
construction: it breaks ties on fame, and no edition of a serial is famous as an
edition. `Poverty and Shared Prosperity` shows the same shape twice over — the
accepted item is the **2020** edition (claims reference 2023), `P577` is **absent
entirely**, and two *byte-identical duplicate items* (Q139955780, Q139954726) tie at
exactly **0.654**, which no tie-break can separate because they are the same item
twice.

**Why this mode is different from the previous two.** Editions of a serial share
nearly all of their label; the token that discriminates them is **the year** — which
is *the value under test*. Resolving the edition therefore means using the claimed
value to select the entity that will judge the claimed value. That is circular, and
it fails in the worst direction: a wrong year selects a wrong edition whose real
year then "refutes" a true claim.

**The non-circular design.** Resolve the **series**, not the edition; enumerate
edition years from `P577` across its members; test the claimed year for
**membership in the series**. The year is then used to *test* and never to *select*.
On the Lancet set (editions 2017 / 2020 / 2024) this detects the 2025 / 2030 / 2120
rows outright; under the span rule 2021 and 2022 fall inside `[2017, 2024]` and
abstain — **3 of 5, honestly, with no confident-wrong risk**, versus 5 of 5 with it.
Take the 3.

## 5. The independent resolution check works — first evidence, and it caught one

`reference/negatives_cache_audit_2026-08-25.md` downgraded the resolver's "72/72
correct" to **"0% refusal, correctness unverified by an independent signal"**,
because the audit checked the chosen entity's **label** against the subject string —
the same signal the selection used, so the check could not fail. It named the fix as
future work:

> *An independent test would check the resolved entity's other properties for
> consistency with the claim's context — information the resolver never consulted.*

This probe ran that check incidentally, and **it fired on the first serial
publication it saw.** Q92676744's `P1433` (published in) resolves to **Q15751849 =
*Irish Journal of Psychological Medicine*** — not *The Lancet*. The label-based
check passes this entity (its label really does read "The Lancet Commission on
Dementia Prevention…"); the property-consistency check rejects it immediately.

So the caveat was not theoretical. **A one-property consistency test on `P1433` /
`P123` against the source named in the claim catches a wrong resolution that scored
*above* threshold**, and it is cheap — the claims fetch is one call already being
made. This should be built before any CITATION verifier ships.

---

## 6. What to do with this

**Do not change Level 1's FALSE policy.** It buys 0 of 25 (§1) and it is the
epistemically wrong move: failure to resolve genuinely is not evidence of
fabrication.

**A CITATION "Level 1b" — work-property comparison — is the reachable route**, and
it is close to existing machinery: the fixed resolver plus a `time` datatype filter
is `quantitative_verifier.py` with one constant changed, plus a `P123`-conflict
check. Realistic yield **8 of 25** on this set.

**Three preconditions, in this order.** Shipping without them repeats a
documented regression rather than risking a new one:

1. **Series-level resolution** for serial publications (§4). Without it the Lancet
   and World Bank rows contribute confident-wrong verdicts, not coverage.
2. **The property-consistency check** (§5), which is nearly free and demonstrably
   catches the §4 failure.
3. **Span, not membership**, for multi-part publication dates (§3).

**State the concentration.** 8 of 25 through one Wikidata item is thin, and the
honest headline is *"one work working"*. Weighed against the baseline's CITATION
**J = +0.128** — its weakest type on a prior-independent measure — routing has real
room here, but 8/25 with a single-entity dependency is not yet a result.

**Author decision required before any build**: this is a new verifier component,
not a fix to an existing one. The 8/25 ceiling and the single-entity concentration
are the numbers to weigh it against.
