# HalDetect — Start-Here Doc for a New Conversation - 20/08/2026

> Chat Name: Verifying factual claims across multiple domains

_Written 2026-08-09/10 (date only, no live clock access). This doc assumes ZERO prior context — read this first, before any other log file._

---

## 0. What this project is (for a genuinely fresh reader)

**HalDetect** is a thesis project (CSE 700, University of Chittagong) building a **post-hoc hallucination detection system** for LLM-generated text — i.e., given a paragraph an LLM wrote, break it into individual factual claims and check each one against real evidence, rather than trusting the LLM's own confidence.

The core design idea: **taxonomy-routing**. Claims get classified into 5 types, and each type is checked by a different, purpose-built verifier rather than one generic "ask an LLM if this is true" step:

- **RELATIONAL** (what something does/causes/how it works) → Wikipedia passage retrieval + NLI entailment (BART-MNLI)
- **TEMPORAL** (dates/years) → Wikidata SPARQL lookup
- **ENTITY_ATTRIBUTE** (what something is/has) → Wikidata SPARQL lookup
- **CITATION** (claims attributing a fact to a named source) → two-level check: does the source exist, does it actually say this
- **QUANTITATIVE** (specific numbers/percentages) → **no verifier built yet**, architecture undecided

The thesis's actual research bet: structured, evidence-grounded verification (retrieval + narrow judgment) should outperform open-ended "ask an LLM to check this" — trading some coverage for much higher reliability where it applies. This is explicitly _not_ the same claim as "routing = better than a single LLM at everything" — it's scoped to where routing can reach.

**Files referenced below are things the user has locally / has uploaded across sessions — Claude's own sandbox is ephemeral and does NOT persist verifier scripts between conversations.** Always ask the user to re-upload the actual current script/CSV before assuming its contents; don't reconstruct from memory of a prior chat.

---

## A. Chronological history — condensed pointers to prior logs

Two full prior logs exist and contain the detailed blow-by-blow. This doc summarizes their conclusions; read them if you need the full reasoning trail:

- `haldetect_transfer_2026-08-02.md` — covers: initial verifier builds/fixes (RELATIONAL, EA, TEMPORAL), Batch 3 claim generation + pipeline fixes, Batch 3 gold-labeling process.
- `haldetect_log_2026-08-09_consolidated.md` — covers: an audit session that independently re-verified claims from the first doc against raw files, resolved several stale/contradictory records, found new evidence (RELATIONAL's Batch 3 numbers, the B3_10_C17 hallucination miss).

**Everything below is the current, up-to-date state as of this doc.** If a new chat is given only this file, it has everything needed to proceed — the two files above are for deep-dive provenance only.

---

## B. Verifier status — current, confirmed state

| Verifier         | File                              | Status                                                 | Numbers                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------- | --------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RELATIONAL       | `relational_verifier_v2.py`       | Stable, validated, actively producing good results     | Phase 2 (64 claims): ~61-67% acc / 70-84% cov. **Batch 3 held-out (47 claims): 80.77% acc / 55.32% cov — confirmed via independent computation + matching execution log.** Page-relevance gate tried twice, reverted both times (documented in-file).                                                                                                                                     |
| ENTITY_ATTRIBUTE | `entity_attribute_verifier_v2.py` | Stable code, but generalizes poorly                    | Phase 2 (13 claims): 87.5% acc / 61.5% cov (execution-unconfirmed — code-consistent but no matching printed run found in any file audited). 8-claim cross-domain held-out: 0% coverage. **Batch 3 (22 claims): 0% acc / 4.5% cov — the one verifiable claim was wrong** (Rosetta Stone resolved to a garbage Wikidata entity).                                                            |
| TEMPORAL         | `temporal_verifier_v2.py`         | Stable code, generalizes poorly, one known unfixed bug | Phase 2 (26 claims): 75% acc / 15.4% cov. **Batch 3 (12 claims): 0% acc / 8.3% cov** — the one verifiable claim was wrong (Panama Canal resolved to the wrong Wikidata entity, got 1903 instead of 1914). Known unfixed bug: P800 "notable work" two-hop date lookup only special-cased for publications (P577), not inventions/openings.                                                 |
| CITATION         | `citation_verifier.py`            | **Not fixed**                                          | Reintroduces the `1-entail` NLI approximation already fixed elsewhere in this project (should use proper 3-way entailment/contradiction/neutral). Static `ORG_URL_MAP`/`TRIVIALLY_KNOWN_ORGS` (~15 hardcoded orgs) — confirmed via triage that 0/12 Batch 3 CITATION claims matched. Rebuild scoped (dynamic search-based source confirmation, same pattern as RELATIONAL) but not built. |
| QUANTITATIVE     | —                                 | **Does not exist**                                     | Architecture undecided: text+NLI fallback (like RELATIONAL) vs. stay UNVERIFIABLE per the project's stated rule. Blocks ~24% of Batch 3 from any analysis.                                                                                                                                                                                                                                |

---

## C. The single most important finding so far

**RELATIONAL (retrieval + NLI) generalizes to new domains; EA/TEMPORAL (static Wikidata property maps) do not.** This is now a clean, numbers-backed comparison, not a hunch:

- RELATIONAL: 80.77% acc / 55.32% cov on a genuinely held-out batch (topics never seen during development: Panama Canal, coral bleaching, OECD, FAO, etc.)
- EA and TEMPORAL: both collapsed to a single verifiable claim each on the same batch, and both of those single claims were wrong.

**The specific mechanism behind EA/TEMPORAL's failures is itself a finding, not just "low coverage":** both verifiers use a "try candidate entities in order, accept the first one with ANY non-empty result for the mapped property" heuristic. This assumes a wrong entity is unlikely to have data under the right property — but when the _property mapping itself_ is subtly wrong (which it was in both cases), the correctly-resolved entity legitimately has nothing, and the heuristic then accepts noise from an unrelated entity instead. **This converts an honest gap into a confidently wrong answer — worse than low coverage, a hallucination-shaped failure inside the verifier itself.** Not yet fixed. This is the single highest-priority open code fix (see Section F).

**Second key finding, now backed by a controlled mini-experiment:** RELATIONAL specifically struggles to catch claims where the core assertion is topically true but a **qualifier is wrong** — direction, timing/condition, or magnitude. Original evidence: `B3_10_C17` (a real hallucination — inverted glycogenesis/glycogenolysis) was verified TRUE, not caught. This was deliberately replicated with 14 hand-authored "minimal pair" negative claims (`relational_negatives_batch3.csv`, one qualifier changed per claim, gold=FALSE by construction) run against RELATIONAL:

| Injection type                    | Result pattern                                                                                                                                                                                                                                                       |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| negation, entity_swap             | Verifier does reasonably well — a real, explicit contradicting sentence usually exists in retrieved text                                                                                                                                                             |
| directional                       | 0% caught, but always fails to honest UNVERIFIABLE (not dangerous)                                                                                                                                                                                                   |
| **temporal_condition, magnitude** | **The dangerous cases** — verifier sometimes confidently validates the wrong claim as TRUE, because NLI rewards topical overlap with the claim's core verb/subject while never checking the specific qualifier (a time, a condition, a number) that's actually wrong |

Sample sizes for the two dangerous categories were thin (n=2 each) after the first round — an 8-claim expansion was designed to bring both to n=6 (`relational_negatives_batch3_round2.csv`), but **a parallel, independently-written 6-claim expansion also exists** (uploaded by the user, same claim_id range B3N_15–20, different actual content). These two expansions have NOT yet been merged — see Section F, item 1, this is the most immediate unresolved task.

---

## D. Batch 3 — data status

- `haldetect_claims_b3_gold.csv` — **122/122 gold-labeled, complete and trustworthy.** 115 TRUE / 4 FALSE / 3 UNVERIFIABLE. Built via a 6-source LLM ensemble (Claude/Grok/ChatGPT ×2 rounds) with 21 disputed claims resolved through independent search-grounded fact-check reports and direct primary-source checks (one claim, Q18_C09-equivalent reasoning pattern, was independently verified against the actual UNFCCC treaty text). Two confirmed, citable hallucination examples came out of this process: the glycogen inversion (`B3_10_C17`) and a UNESCO-criteria-timeline misattribution (`B3_05_C02`).
- `relational_negatives_batch3.csv` — 14 (or 20, if the user's independent expansion is already appended — check the actual current row count before assuming) hand-authored minimal-pair FALSE claims, designed to stress-test the qualifier-blindness finding above. **Explicitly marked `synthetic=True` in its own schema** — not blended into the main gold set as if LLM-generated.
- Phase 2's gold set (`haldetect_phase2_goldlabeled.csv` or a later-numbered copy, e.g. `__3_.csv` — **check which is current, this has been a recurring versioning problem**) has a severe class-imbalance problem: **zero FALSE examples across RELATIONAL (64), EA (13), and CITATION (6)** — only TEMPORAL has any FALSE labels at all (1, from the Paris-Agreement-2050 misattribution). This makes any hallucination-_catching_-rate claim on current Phase 2 data nearly meaningless until injected negatives exist for those three types too (RELATIONAL now has a start via the Batch 3 negatives above; EA and CITATION still have none).

---

## E. Standing methodological commitments — do not re-litigate these

- Gold-label corrections happen only where a human judges an existing label wrong — never nudged toward matching whatever a verifier outputs.
- Don't trust a doc's self-description of a file's contents — audit the actual uploaded file directly before relying on a claimed row count, label breakdown, or specific value. This has been the single largest source of wasted effort across multiple sessions (stale scripts re-uploaded, CSVs missing fills the doc claimed were present, a sandbox reset losing working files).
- Don't re-add RELATIONAL's page-relevance gate without prototyping on 2-3 cached claims first (tested twice, reverted twice).
- Don't expand static property/org maps claim-by-claim as new failures surface — this whack-a-mole pattern has been identified and explicitly rejected multiple times.
- LLM-ensemble agreement on a gold label is necessary but not sufficient — specific numeric/statistical claims need independent source verification regardless of how many models agree (this was the concrete lesson of the Batch 3 gold-labeling process, not just a general principle).
- Distinguish LLM-assisted **gold-labeling** from the actual **RQ2 non-routed ablation baseline** — they are not the same thing. A proper baseline needs a single plain LLM call per claim, run consistently, ideally a different model family than whatever helped build the gold labels (to avoid circularity).

---

## F. Immediate next steps, in priority order

1. **Resolve the duplicate B3N_15-20 negatives.** Two different 6-8 claim expansions exist for the same claim_id range with different content (one true duplicate found: an Aral-Sea-area magnitude claim expressed two ways). Needs a merge + dedup + clean renumbering before the negatives set is usable as a coherent whole.
2. **Fix the entity-resolution "prefer first non-empty candidate" heuristic** (Section C) — highest-priority code fix, actively producing wrong answers in both EA and TEMPORAL, not just gaps. Proposed approach: use the Wikidata search API's already-returned (currently discarded) description/snippet as a cheap relevance check before accepting a non-empty result over an honest empty one.
3. **Fix the retry-exhaustion cache-poisoning bug** in the RELATIONAL verifier's `resolve_wikipedia_titles`/`fetch_page_text` — currently, a transient rate-limit exhaustion (retries maxed out, `None` returned) gets cached identically to a genuine "no results found," and never self-corrects on rerun. Patch already written (see prior session) — only needs to be applied to whatever the user's current script copy is.
4. **Build injected negatives for EA and CITATION** — same rationale as RELATIONAL's (Section D), still entirely missing for these two types.
5. **Decide the QUANTITATIVE verifier architecture** — still blocking ~24% of Batch 3 from any analysis.
6. **CITATION rebuild** (dynamic search-based source confirmation) — lower priority than 1-5, unchanged from prior sessions.
7. **Get a real, execution-confirmed run of EA against the Phase 2 13-claim set** to lock down the 87.5%/61.54% figure before it goes in the thesis — currently only code-consistent, not printed-output-confirmed.

---

## G. What to ask the user, if picking this up cold

- "Which files do you have available right now?" — don't assume any script or CSV persists between sessions; always get a fresh upload.
- "Is `haldetect_phase2_goldlabeled.csv` or a later-numbered version (e.g. `__3_`) the current one?" — this has been wrong more than once.
- "Has the B3N_15-20 duplicate negatives issue (Section F, item 1) been resolved since this doc was written?"
