# Task #21 — `P31` type-consistency check: closing the resolution circularity

**Date:** 2026-08-27 · **Module:** `current/type_consistency.py` · **Selftest:** `24/24`, exit 0 (§8)
**Status:** built, self-tested, **no corpus-wide audit run** (§9 — that needs author go-ahead)

This document is the authority on *how* the module's constants were derived. `CLAUDE.md` wins on
rules and numbers; this file wins on the derivation. Every QID below was read off live Wikidata
during the build, never recalled from memory (R1).

---

## 1. Why the module exists

`CLAUDE.md` §6 records that the resolver's **"72/72 correct" is partly CIRCULAR**: the audit
verified correctness by checking the chosen entity's **label** against the subject string — the
same signal `resolve_entity()` uses for **selection**. A test that reuses the selection signal
cannot fail. That number is therefore downgraded to *"0% refusal, correctness unverified by an
independent signal."*

The specific thing a label check cannot catch is **wrong-sense-same-name**, which is exactly the
class of both recorded resolution bugs:

- **Panama Canal → *Panama Canal Zone*** (Q7350 → Q498979). The label check passes: "Panama Canal"
  really is in "Panama Canal Zone".
- **Rosetta Stone → a British punk band** (Q48584 → Q1703969). The label check passes perfectly —
  the band is *called* Rosetta Stone.

`P31` typing is independent of the label, so it is a genuinely different signal. `source_consistency.py`
was the first independent evidence (`P1433`/`P123` publisher veto); **this is the type-level
version**, which is what reaches the punk-band class.

**Citable precedent:** `P31`/`P279` fine-grained typing is how **ReFinED (Ayoola et al. 2022)**
scores its own candidates — so this is the mechanism a SOTA entity linker relies on, not a local
heuristic.

---

## 2. Both motivating bugs are now caught

Measured, live, in Arm B of the selftest:

- `Q498979` Panama Canal Zone, expected `WATERWAY` → **CONFLICT** (`P31` = *unincorporated
  territory of the United States*; families = ADMIN_TERRITORY)
- `Q1703969` Rosetta Stone, expected `PHYSICAL_ARTIFACT` → **CONFLICT** (`P31` = *musical group*;
  families = ORGANIZATION)

…while the **correct** entities pass:

- `Q7350` Panama Canal → **CONSISTENT** (families = STRUCTURE/WATERWAY)
- `Q48584` Rosetta Stone → **CONSISTENT** (families = PHYSICAL_ARTIFACT/WRITTEN_WORK)

…and the safety case abstains rather than vetoing:

- `Q68487022` human liver, expected `PERSON` → **NO_EVIDENCE** (*no `P31` statements at all*)

**These four are only evidence because the verdict tracks the expectation, not the entity.**
Re-asked under the expectation that fits them, both CONFLICT entities return CONSISTENT
(`Q498979`/ADMIN_TERRITORY, `Q1703969`/ORGANIZATION). Without that pair the check could be
detecting "this entity is unusual". Both are now permanent Arm B rows labelled `SPECIFICITY`.

---

## 3. The safety model — three states, and CONFLICT needs positive evidence

| verdict | condition |
|---|---|
| `CONSISTENT` | the type closure meets an expected family |
| `CONFLICT` | **every** entity family is explicitly disjoint from **every** expected family |
| `NO_EVIDENCE` | anything else — no `P31`, no recognised family, or any pair not declared disjoint |
| `NO_EXPECTATION` | no expectation supplied, and none is guessed |

The `every…every` rule is the load-bearing part. **One unlisted or non-disjoint pair defeats a
CONFLICT**, so a gap in the curated table, an unusual Wikidata class, or a truncated closure
degrades to `NO_EVIDENCE`. **Never-reached is not disjoint.**

**Both error directions are safe, for the same structural reason as `source_consistency.py`: the
check only ever REMOVES a verdict.** A missed conflict leaves today's behaviour unchanged; a
spurious `CONSISTENT` cannot manufacture a confident-wrong verdict, only fail to prevent one.
Nothing here can create a FALSE.

---

## 4. Measured constraint 1 — depth 2 is an optimum, not a guess

`MAX_DEPTH = 2` over `P279`, measured with `p279_closure_probe.py`.

- **Depth 1 is too shallow** — it misses the fine-to-coarse lift that makes families work at all:
  `ship canal` → `canal`, `waterway`; `stele` → `monument`, `archaeological artefact`.
- **Depth 2 already collides across domains.** A **ship canal (Q949819)** and a **stele
  (Q178743)** both reach **`architectural structure` (Q811979)**. Two entities from families one
  would want to separate meet at depth 2.
- Therefore **depth 3+ imports the upper ontology and the DISJOINT table stops meaning anything.**

This independently **validates `citation_l1_verifier.py:76`'s refusal of unbounded `P279*`** —
that comment says a broad subclass walk "lets almost anything qualify, which would rebuild the
tautology in a new shape." Measured here at the smallest depth where it starts to bite.

---

## 5. Measured constraint 2 — union classes, and an honest note on the filter

**Wikidata's upper ontology contains UNION classes that silently merge families.** Measured:

- `organization` (Q43229) reaches **`person or organization` (Q106559804)**
- `human` (Q5) reaches **`legal person` (Q3778211)**
- `sovereign state` (Q3624078) reaches **`juridical person` (Q155076)**

Without explicit exclusion a closure comparison concludes **a person IS an organization**. All
such classes are in `HUB_CLASSES` (24 entries) and excluded from every family. Also excluded:
`architectural structure` (Q811979), reached by both a canal and a stele; `work` (Q386724),
reached by the Rosetta Stone and every publication; and `animal`/`omnivore`/`consumer`, which
would admit non-persons to `PERSON`.

### The part that must be stated precisely, because the obvious phrasing is wrong

**The runtime hub filter in `families_of_closure()` is INERT BY CONSTRUCTION.** Selftest check #1
asserts no hub QID is a family anchor; if no hub is an anchor, then dropping hubs from a closure
**cannot change which anchors it intersects**. Measured rather than argued: emptying `HUB_CLASSES`
changes the families of **0 of the 13** `INVARIANT_QIDS`.

That is **defence in depth, not redundancy** — check #1 *detects* a hub wrongly added as an
anchor, and the filter *neutralises* the same mistake — so both are kept, and the selftest now
exercises one each.

**This was a real defect in my own selftest, found by proving it non-vacuous rather than by
reading its PASS.** The original pair of checks asserted *"hub exclusion works: organization +
`person or organization` is not PERSON"* and *"Q106559804 is in HUB_CLASSES"*. The first **cannot
fail** while check #1 holds, because Q106559804 was never a PERSON anchor — so nothing would put
it in PERSON with or without the filter. The second is a **tautology over two constants**. Both
printed PASS in the 22/22 run and neither tested anything. Replaced by: (a) inject the hub into
`PERSON` and assert the filter still keeps PERSON out — the only scenario where the filter can
matter; (b) assert the inertness relationship directly.

The same lesson as #20, where a selftest destroyed a quoted result while printing 11/11: **a
test's own PASS is not evidence.**

---

## 6. Negative result — Wikidata's own type constraints CANNOT supply the expectation side

The obvious way to avoid curating `PROPERTY_EXPECTATION` by hand is to read each property's
declared subject-type constraint from Wikidata itself: `P2302` → `Q21503250` (subject type
constraint), classes in qualifier `P2308`, relation in `P2309`. **Measured with
`constraint_probe.py` over 11 PIDs, and it does not work.** Three independent reasons:

1. **It contains the very hub classes that must be excluded.** `P2044` (elevation) lists
   **`object` (Q488383)**; `P577` and `P1433` both list **`work` (Q386724)**. Intersecting an
   entity's closure against those makes almost everything CONSISTENT — **the L1 tautology
   objection arriving from the other direction.**
2. **It is simply absent for some properties** — `P571` (inception) and `P2046` (area) both
   returned **n = 0** class-bearing constraints.
3. **It mixes constraint kinds, and reading the wrong one is silent.** `P186`'s first
   class-bearing constraint is **`Q21510865` value-type**, describing what the *value* may be,
   not the *subject*. **My first probe made exactly this mistake** and reported material classes
   (`material`, `food`, `chemical element`) as though they constrained the subject. Filtering on
   `Q21503250` is mandatory; `_probe_constraints()` now does it and records the error so it
   cannot recur silently.

**Where the constraints *are* clean they corroborate the curated map**, which is the useful
outcome: `P569` → `human`; `P610` → `geographic location` / `geographical feature`; `P1082` →
`region` / `territory` / `human settlement`. So the curated `PROPERTY_EXPECTATION` is not at odds
with Wikidata's own modelling — it is a **hub-free subset** of it.

---

## 7. The curated part, and how its failure mode differs from L1's

`FAMILIES` (8 families) and `DISJOINT` (21 pairs) are hand-curated, and **this project has been
bitten by a curated class list before.** `citation_l1_verifier`'s first version required `P31` ∈
`SOURCE_CLASSES` and **downgraded 4 of 4 correctly-resolved entities** because Wikidata used
classes the list had not anticipated: IPCC AR6 → Q103843442, CDC → Q583725, World Bank → Q7164,
IEA → Q826700. The fix was to prefer a **structural** signal (`P856`) over a curated one.

**The failure mode here is less severe, and the difference is the point.** An unanticipated class
means no family matches, which yields **`NO_EVIDENCE`** — a **coverage** loss, not a wrong
verdict. L1's curated list produced an actively wrong *downgrade*; this one produces an
abstention. That is a consequence of §3's safety model, not luck.

**The honest expectation that follows: the CONFLICT rate in the wild will be LOW.** Do not read a
low rate as the check not working — read it as the cost of curation, and **measure it** (§9).

### Three DISJOINT pairs that live data refuted before they became bugs

Each was about to be declared disjoint on intuition, and a real entity disproved it. All three are
now in `NOT_DISJOINT`, marked `MEASURED`:

- **`PHYSICAL_ARTIFACT` × `WRITTEN_WORK`** — the **Rosetta Stone (Q48584)** is a *stele* **and** a
  *bilingual inscription*. Declaring these disjoint would have made the project's own canonical
  correct resolution a CONFLICT.
- **`STRUCTURE` × `PHYSICAL_ARTIFACT`** — a stele reaches `architectural structure`.
- **`WATERWAY` × `STRUCTURE`** — a **ship canal** is a *waterway* **and** a *hydraulic structure*,
  which is why `Q7350` legitimately carries both families.

This is what Arm C tests, and it is the reusable technique: **a DISJOINT table can be falsified
empirically — one entity occupying two families declared disjoint disproves that pair.**

---

## 8. Selftest structure, and the vacuity proofs

`python type_consistency.py --selftest` → **three arms**. `families_of_closure()` and `decide()`
are pure and network-free, which is what lets most of it run offline.

- **Arm A — offline logic (14).** Structural invariants (no hub is an anchor; no QID anchors two
  families; DISJOINT and NOT_DISJOINT do not overlap; every family named anywhere is defined) plus
  the whole verdict rule, including *one non-disjoint pair defeats CONFLICT*, *no `P31` →
  NO_EVIDENCE*, *no expectation → NO_EXPECTATION*, and *an unmapped PID returns `None` rather than
  a guess*.
- **Arm B — live Wikidata (9).** The 5 cases in §2 plus the 2 `SPECIFICITY` rows and the safety
  row. Cached, so it re-runs in seconds.
- **Arm C — the DISJOINT table vs 13 real entities (1).** No entity may occupy two families
  declared disjoint.

### Vacuity proofs — `python type_consistency.py --vacuity`, 4/4

Because the arms above report their own PASS, each load-bearing check was separately shown to be
**capable of failing**. This lives in the module rather than in a scratch script, so it stays
reproducible; every mutation is restored before the next proof runs.

- **V1 — Arm C is not vacuous.** Injecting the (false) pair `PHYSICAL_ARTIFACT × WRITTEN_WORK`
  into `DISJOINT` makes Arm C report **1 violation**, correctly naming `Q48584`. Restored to 21
  pairs afterwards.
- **V2 — CONFLICT is expectation-specific.** 5/5: the same two entities flip CONFLICT ↔ CONSISTENT
  purely by changing the expectation. Promoted into Arm B as permanent rows.
- **V3 — the hub-leak check is not vacuous.** Injecting `Q106559804` into `PERSON` makes check #1
  report the leak; removing it returns the table to clean.
- **V4 — the hub filter's inertness, measured.** 0 of 13 entities change families when
  `HUB_CLASSES` is emptied. This is the finding written up in §5, and it is what exposed the two
  bogus checks.

---

## 9. What has NOT been measured — read this before quoting anything

- **No corpus-wide audit has been run.** How many of the recorded **72** resolutions this check
  independently corroborates, and how many it flags, is **unmeasured**. Doing it means live
  Wikidata calls across the corpus and **needs author go-ahead**, exactly like
  `property_resolver.py --resolver validated` and task #19.
- **The 72/72 figure is not yet repaired**, only *repairable*. Until that audit runs, `CLAUDE.md`
  §6's wording stands: *"0% refusal, correctness unverified by an independent signal."* This
  module supplies the missing signal; it has not yet been applied at scale.
- **Nothing is integrated.** Built as a **sibling** of `source_consistency.py` per `CLAUDE.md` §7,
  not as an edit to a validated verifier. No cache prefix bumped, no verifier touched, no measured
  number in the thesis changes.
- **Coverage, when measured, must not be read as correctness (R8).** A high CONFLICT rate would be
  as suspicious as a low one — the pattern of a coverage jump masking a precision collapse has
  misled this project four times.

---

## 10. Reproduce

Offline-plus-cached, seconds, zero model calls. `24/24`, exit 0 as of 2026-08-27:

```
cd current
../../../../.venv/bin/python type_consistency.py --selftest        # 3 arms, 24 checks
../../../../.venv/bin/python type_consistency.py --demo            # worked examples
../../../../.venv/bin/python type_consistency.py --probe-constraints  # §6's negative result
```

The venv lives **only in the main checkout** (`ThesisCode_copy/.venv/bin/python`) — four levels up
from `current/` inside this worktree, not three (verified, not counted from memory). This worktree
also refuses compound Bash commands, so drive it from `python3 -c` with `subprocess.run(...,
cwd=current)` if you need the `cd` and the exit code in one step.

**Related:** `CLAUDE.md` §6 (the circularity, failure modes #1 and #2) · `current/source_consistency.py`
(the sibling pattern, `P1433`/`P123`) · `current/citation_l1_verifier.py:76` and its `SOURCE_CLASSES`
incident (§4, §7) · `reference/property_resolver_bugB_2026-08-27.md` (task #20).
