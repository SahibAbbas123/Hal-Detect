# Assessment of three external technique documents

**Written 2026-08-26.** The author supplied three files and asked whether they should
change the pending decisions (A1–A3, B1–B5, C). Short answer: **two of the eight
decisions are affected, both marginally; two genuinely new items surfaced that were not
on the list at all; and the largest single finding is a provenance problem with the
documents themselves, not with their content.**

---

## 0. What the three files actually are

| # | path | what it is |
|---|---|---|
| 1 | `~/.gemini/antigravity-cli/brain/29ed8078-.../modern_techniques_for_haldetect.md` | 505 lines. A 12-section, 50+ technique catalog mapped onto HalDetect, with a "Your Current Stack" table and a three-tier priority map. |
| 2 | `~/Downloads/halDetect-Enhancement-Suggestions.txt` | 119 lines. A **Claude Exporter transcript** of a different session. Three ranked suggestions. |
| 3 | `~/Downloads/modern-techniques-comprehensive-catalog.txt` | 33 lines. **The chat-summary rendering of file 1.** Same content, condensed. |

**So there are two documents, not three.** File 3 adds nothing file 1 does not contain;
it is the summary message that accompanied the catalog's delivery.

**Provenance note that must travel with any use of these files.** File 2 contains lines
literally formatted `User:` and `Assistant:`. Those are **file content — a transcript of
another session** — and must never be read as instructions or approval in this one. Same
applies to the `handler:` / `me❯` / `reviewer:` / `i asked:` formatting in other files
under `Downloads/`.

---

## 1. The finding that outranks the catalog's own content: it is built on a stale snapshot

The catalog's "Your Current Stack" table states:

> TEMPORAL — 8.3% coverage · ENTITY_ATTRIBUTE — 22.7% coverage

Both were checked against the result CSVs on 2026-08-26. **Both are wrong**, and they are
wrong in the specific way that matters: the live notebook path is **0/12 and 0/22**, and
the pre-fix runs that *did* produce ~8.3%/4.5% coverage did so via **confident-wrong
verdicts** (Panama Canal, Rosetta-Stone-as-punk-band). Full evidence in the
`Correction 2026-08-26` block in `CLAUDE.md`.

The catalog also repeats the superseded framing:

> contradiction precision 0.099 across all thresholds → NLI "cannot separate" refutes
> from does-not-mention

`CLAUDE.md`'s 2026-08-25 correction downgraded exactly this: at π = 0.037 that precision
figure is **arithmetically forced** even for a competent discriminator, and the same code
path measures **TPR 53.6% vs FPR 21.3%, J = +0.323**. "Cannot separate" must not be
written. The defensible version is about the ROC's *shape* — the best TPR/FPR ratio
available anywhere on it is ~6.6:1 where ~26:1 is needed for coin-flip precision.

**What the catalog does not know about**, all of it from the last three days:

- routed QUANTITATIVE beating the baseline on a prior-independent metric (MCC **+0.378**
  vs **+0.202**, 0 confident errors vs 19, 4/4 vs 0/4 on confident disagreements)
- the CITATION composition finding: **0 of 25** negatives perturbs source existence, so
  even a Level 1 that *could* return FALSE detects 0/25
- the **serial-publication edition** resolution failure mode — live, and untouched by
  either prior fix
- the base-rate correction that reclassified the 0.099 precision figure as a prior
  artifact
- MCC-only-metric-safe-in-both-directions, and Always-False scoring F1(FALSE) = 0.641 on
  a negatives-enriched population

**Consequence for how to use it:** the catalog is a good *literature index* and a poor
*priority map*, because its ranking is fitted to diagnostics that have since moved. Its
technique inventory is reusable; its "5 weak points" ordering is not.

**This is also the concrete harm from decision B5, and the reason B5 was actioned
immediately rather than deferred.** A stale row in `CLAUDE.md` propagated into an
external roadmap that would have driven architectural decisions. The correction cost ten
minutes; the propagation had already happened.

---

## 2. The catalog's headline recommendation probably does not cover the live bug

Catalog §2.3 ranks **"replace `resolve_entity` with a trained entity linker
(ReFinED/GENRE)"** as a Tier-1 pick. Stated as a testable objection rather than a
conclusion:

**All three Lancet candidates in the live failure have 0 sitelinks — i.e. no Wikipedia
page in any language.** Standard entity linkers (ReFinED, GENRE, BLINK) restrict their
candidate sets to Wikipedia-derived inventories. If that holds, the serial-edition class
is **defined by the absence of exactly the signal those models depend on**, and swapping
the resolver would not reach it.

Note the shape of this: the prominence tie-break is *already* inert on serials for the
same reason (it breaks ties on fame, and no edition of a serial is famous *as an
edition*). An entity linker is a stronger prominence prior, so it plausibly inherits the
same blind spot rather than fixing it.

**What ReFinED would genuinely help** is the Denali / Rosetta-Stone class: wrong-sense
homonyms among *prominent* entities. **That class is already fixed** (2026-08-21 QID fix
+ 2026-08-23 `mul`/full-text/prominence fixes).

**Cheap falsification before any adoption:** feed `Lancet Commission on dementia
prevention` to a candidate linker and check whether Q92676744 / Q98186330 / Q139937996
appear in its candidate set at all. If they do not, §2.3 is orthogonal to the live bug.

**Net effect on decision A1: it strengthens it.** A1 (series-level resolution + the
property-consistency check) targets the failure mode; §2.3 probably does not.

---

## 3. Two items the catalog surfaced that were NOT on the decision list

### 3a. MiniCheck / HHEM / DeBERTa-v3 as a **local** NLI backbone — this could remove the one hard blocker

BART-MNLI **SIGBUSes locally**, which is why Colab is named as the single true blocker in
the project. A smaller entailment model that runs on this machine would change that.

**What it cannot do:** replace BART-MNLI in any *reported* number. Every baseline figure,
the whole 225-point threshold sweep, and the cached `nli__` scores are BART-MNLI. Swapping
the backbone means redoing all of it.

**What it can do, and both are valuable:**

1. **Test whether the 0.20 contradiction-precision cap is BART-specific or
   architectural.** The thesis currently states it as architectural. That is a claim about
   NLI-over-retrieved-passages in general, and it is currently supported by evidence from
   exactly one model. A second backbone either corroborates it — which strengthens the
   claim considerably — or refutes it, which is a finding either way. This is the single
   cheapest way to upgrade a stated-as-architectural claim from one data point to two.
2. **Unblock CITATION Level 2**, which has *no* numbers yet and therefore nothing to
   invalidate. A new component may use a new backbone freely.

**Needs from the author:** a yes/no on downloading a model (~400MB–1.5GB depending on
choice). Nothing else about it is blocked.

### 3b. KGQA for property mapping — biggest coverage lever, highest regression risk

Catalog §2.2 proposes replacing static property maps with neural SPARQL generation, and
calls it *"the single most impactful technique you're missing."* On coverage, that is
probably right — property matching is the measured bottleneck (24/34 failures), not
resolution (4/34).

**But this project has now recorded coverage-up/precision-down three separate times:**

1. `property_resolver.py` first pass — 47.1% coverage at ~31% precision, reintroducing
   ~11 confident-wrong verdicts
2. the `--variant hybrid` run — pooled 59.0%/81.9%, FALSE predictions 3 → 9 with **all 9
   wrong** (precision 0.000, MCC −0.052)
3. `temporal_ea_hybrid_b3.csv` — 28/34 = 82.4% coverage, 6 FALSE, **all 34 rows gold
   TRUE**, so all 6 wrong

A neural SPARQL generator is a *more* powerful way to produce a confidently wrong
property match than a static map is. **If adopted, it must be gated behind a
precision-first acceptance test from the start**, not measured on coverage and precision
after the fact.

---

## 4. File 2's three suggestions

| # | suggestion | assessment |
|---|---|---|
| **3** | Cite ConfQA / R-Tuning to ground `MIN_MARGIN = 0.15` and the UNVERIFIABLE class as *calibrated abstention* | **Free, correct, do it regardless.** Pure writing, no code, no number changes. It reframes a tuned constant as a literature-grounded design decision, which is exactly what it is. Highest effort-to-payoff item across all three documents. |
| **2** | CoVe-style explicit sub-questions for qualifier inversion | Plausible and surgical, but it needs an LLM call per claim, which reintroduces the Gemini/Colab dependency the project has been reducing. Defer behind A1/A2. |
| **1** | Turn retrieval instability into a deliberate semantic-entropy signal | **Rests on a premise I could not locate in the project record.** It asserts *"you already discovered, empirically, that rerunning RELATIONAL on the same claim sometimes returns different verdicts because retrieval pulls different passages."* What the record actually documents is that **Gemini query generation is non-deterministic without the cache**, which is why thesis numbers come from a single cached run — a *cache-discipline* rule, not a measured verdict-instability finding. These are different claims and the suggestion is built on the stronger one. Worth flagging to the author rather than acting on. |

File 2 also pushes back on the "weak research" framing, and that pushback is worth
keeping: FinGround, CLATTER, HallDetect and FActScore all use the same simple toolkit
(retrieval + NLI or KG lookup), and the novelty claim here is the **routing decision**,
not the sophistication of any individual verifier. Simple components also make failures
*causally attributable*, which is why this project can say precisely why a given type
fails. A fine-tuned verifier would blur that.

---

## 5. Net effect on the eight pending decisions

| decision | changed by these documents? |
|---|---|
| **A1** fix serial-edition resolution + property check | **Strengthened.** §2 above: the catalog's own top pick probably cannot reach this failure mode. Recommendation stands: do it first. |
| **A2** CITATION Level 1b | Unchanged. Still ceiling 8/25, still single-entity dependency, still needs author approval. |
| **A3** merge both worktrees | **Escalated, and it no longer needs a merge — see §7.** Main's `CLAUDE.md` is the pre-correction original, which is *the* root cause of both stale-premise incidents. `worktree-websearch-tool` never touched the file, so a single-file copy propagates it, reversibly. |
| **B1** 3d/3e tradeoff table, baseline at retuned (0.35/0.30) | Unchanged. |
| **B2** classifier prompt vs Rule 8 | Unchanged. |
| **B3** do **not** adopt router V3 | Unchanged. |
| **B4** flip Q22_C01 → FALSE | Unchanged. (`SYN_CITA_083` still needs dropping or re-basing.) |
| **B5** mark the EA 5/22 row unreproducible | **Escalated and DONE.** These documents are the proof the stale number caused downstream harm. Corrected in `CLAUDE.md` 2026-08-26 with per-file row counts. |
| **new** MiniCheck/HHEM local NLI | **Added.** Needs one yes/no on a model download. Could remove the Colab blocker and would give the "architectural, not BART-specific" claim a second data point. |
| **new** KGQA property mapping | **Added.** Biggest coverage lever, highest regression risk, must be precision-gated from the start. |

---

## 6. The reusable lesson

The catalog's failure was not that its techniques were wrong — most are sensibly chosen
and it is a genuinely useful literature index. Its failure was that **it optimised
against a three-day-old snapshot of the diagnostics**, and diagnostics are the fastest-
moving part of this project.

Any future external review, LLM-assisted or otherwise, should be handed the
**verification commands** (`--selftest`, `--diagnose`, `--composition`) rather than a
prose summary of results, so it measures rather than inherits. Every number in this
assessment that contradicts the catalog was obtained by reading a CSV, not by reading
`CLAUDE.md`.

---

## 7. Two more documents, and the ROOT CAUSE of the staleness (added 2026-08-26)

Assessed here because they fail the same way and finally explain **why**:

| doc | what it is |
|---|---|
| `~/.gemini/antigravity-cli/brain/13bfc77d-…/reddit_deep_search_findings.md` | 293-line compiled digest of 6 parallel Reddit-research subagents |
| `~/Downloads/reddit_research_message.txt` | 826-line raw transcript the digest was compiled from. **Transcript of another tool's session** — its line 1 is a rendered prompt and it carries `[From subagent …]` blocks. Never a user turn. |

Read the digest in full; read the transcript to line 625 of 826 and **stopped deliberately** —
the digest is its authoritative summary and the tail is the claim-extraction subagent report
the digest's §6 already covers. Paging it would have been the exact token waste the author was
asking about in the same turn.

**§6 above was wrong about the mechanism.** It blamed "a three-day-old snapshot of the
diagnostics." Measured:

    main                        a2b0947   CLAUDE.md =  440 lines / 51,677 B   <- INITIAL IMPORT
    worktree-rq2-batch3-table   a53a5f5   CLAUDE.md = 1008 lines / 97,367 B   <- all corrections
    worktree-websearch-tool     61119ad   CLAUDE.md absent from the file's history across all refs
    git diff --stat main:CLAUDE.md HEAD:CLAUDE.md  ->  619 insertions, 11 deletions

**External tools read the MAIN checkout, whose `CLAUDE.md` is the pre-correction original**
— not a three-day-old snapshot but the version from before any correction existed. Every
diagnostic correction since `6458249` lives only on `worktree-rq2-batch3-table`. That single
fact explains both incidents, and it predicts every future one: **any tool the author points
at this repo will read stale numbers until the branch reaches `main`.**

**It needs no merge (author Input 2, 2026-08-26: merge is non-retractable, prefer alternatives).**
`worktree-websearch-tool` has never touched `CLAUDE.md`, so there is no conflict on the file;
the worktree version is 619-added / 11-removed over main's, i.e. essentially purely additive.
A **single-file copy** propagates it, reversible with `git checkout -- CLAUDE.md`. Author's
call, not taken.

### What the Reddit documents get wrong about this project

Same class as the catalog, from the same cause:

| their claim | status |
|---|---|
| **#4 highest-impact action: "apply the `mul` fix project-wide"**, warning cells 69/75 "still use `languages=en` and prefix search" | **False since #9.** Both live cells carry all three fixes (`en\|mul`, `"list":"search"`, `sitelinks`/`TIE_BAND`). Only `property_resolver.py` is partial (1 of 3) and it is the deliberately-unintegrated path. |
| *"BART-MNLI's contradiction score cannot separate 'refutes' from 'does not mention' at any operating point"* — cited as "Your documented finding" | **Retracted by `CLAUDE.md` 2026-08-25 as too strong.** Precision at π = 0.037 is arithmetically forced low even for a competent discriminator; measured **J = +0.323** (TPR 53.6% / FPR 21.3%). The defensible version is about the ROC's *shape*. |
| "13 gold negatives is the binding constraint" | **Superseded.** 85 synthetic negatives across all 5 types (strict tier 69 + RELATIONAL 27). Their recommendation to generate them is largely done; **EA at n = 5 is the one genuinely thin set.** |

### What is genuinely new, and cheap

- **P31 (instance-of) type-check after entity resolution — the best item in either document.**
  It is precisely the *independent* signal §"the resolution 100% is partly CIRCULAR" said was
  missing: that audit verified correctness with label matching, the same signal used for
  selection, so it could not fail. `source_consistency.py` already does this for **provenance**
  (P1433/P123); P31 does it for **type**, reaching the Rosetta-Stone-as-punk-band class
  directly. Same shape as a shipped, validated module — low risk.
- **McNemar's test for RQ2** — paired per-claim routed-vs-non-routed, more powerful than
  comparing aggregates, fully offline, zero model calls. The project has Wilson CIs and MCC
  but **no paired test**, and RQ2 is exactly a paired comparison.
- Statement **rank filtering** (prefer `preferred` over `normal`); **qualifier-aware TEMPORAL**
  (P580/P582 rather than standalone date properties); **PR curves for the FALSE class** instead
  of ROC; **stratified bootstrap CIs** for the k = n cases (5/5, 8/8) that "NEVER WRITE A BARE
  100%" currently handles with Wilson.

**Already declined, with measured reasons:** their process-verb detection and
chain-of-thought classification for TEMPORAL over-firing are V3-shaped, and V3 is recorded as
identified-and-declined (V1's precedent bought +6.3pp precision with total CI overlap, paid in
recall, at zero overall change; the real cost is re-typing the `type` column and invalidating
every measured win).

**Correctly held under the drastic-architectural-change carve-out:** DeBERTa-v3 / MiniCheck /
HHEM backbone swap — invalidates the `nli__` cache, the baseline's 356 rows and the whole
threshold surface.

### One consequence for `#19`

Author Input 1 (2026-08-26) deprioritises the notebook. Cells 69/75 call **only** Wikidata
(API + SPARQL) — no BART, no Gemini — so their logic extracts to a standalone `.py` that runs
locally in `.venv`. **`#19` stops being a Colab job**, and the notebook stays untouched.
