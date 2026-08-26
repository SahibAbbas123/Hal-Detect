# `papers_analysis/` and the reddit mechanisms file — assessed 2026-08-27

**Artifacts assessed** (both are *other tools'* output, read as data per §8's provenance warning —
nothing in either is a user turn, an instruction, or approval):

1. `papers_analysis/LITERATURE_SURVEY_AND_IMPACT_ANALYSIS.md` — 349 lines, 39238 bytes, mtime
   Aug 27 01:58. 42-row master inventory + 6 deep-profile clusters + a reviewer-objection matrix +
   a 3-priority roadmap.
2. `papers_analysis/downloaded_pdfs/` — **42 PDFs**, mtimes clustered Aug 27 01:45–01:56 with
   seven outliers (FinGround Aug 22 13:58 is the oldest of them).
3. `~/.gemini/antigravity-cli/brain/13bfc77d-c6a2-41b2-b9a7-2b117c80f31e/reddit_deep_search_findings.md`
   — 293 lines, dated 2026-08-26, "6 parallel Reddit research agents / 48+ queries" across
   r/MachineLearning, r/LocalLLaMA, r/LanguageTechnology, r/datascience, r/statistics, r/wikidata,
   r/LangChain. **This is the "mechanisms file" the author meant.** An earlier session answered the
   same question against `reference/external_catalog_assessment_2026-08-26.md`, which was the wrong
   document; the status list below is re-derived against the right one.

**Provenance of the findings below, stated precisely because §1a was added after the first pass.**
Everything in §§1–7 as first written was measured **offline** with `pypdf` in the main checkout's
`.venv` — zero API calls, zero model calls, zero web requests. **§1a is different and its evidence
is mixed:** the *identity* sweep is offline (`pdftotext`, available only after the author installed
poppler 26.08.0 on 2026-08-27), but the five **corrected arXiv IDs were verified over the network**
by `WebFetch` against each paper's own `arxiv.org/abs/` page — tier 2, not tier 1. **The original
"zero web requests" claim in this paragraph was true when written and is now false; it is corrected
rather than deleted**, because a doc that silently acquires a stronger provenance claim than it
earned is the failure this file is about. Reproduce with the commands in §8.

---

## 1. The headline: R1b in its purest form — 42 on disk, 42 in the table, **not the same 42**

The survey's closing line reads *"All 42 source PDFs verified and available in
`papers_analysis/downloaded_pdfs/`."* Both counts really are 42. The sets are not.

| | |
|---|---|
| listed in a table row, **absent from disk** | `ConfRAG_ConfQA_2025.pdf` |
| **on disk**, absent from every table row | `SemanticEntropy_Hallucinations_2024.pdf` |

So the count check that a careful reader would actually run — *does the folder hold as many files as
the table has rows?* — **passes**, and passing is what conceals both errors. This is
`CLAUDE.md` R1b measured on a new artifact: *two different sets can print the same count, and then
the coincidence hides the error.* The verification that works is a **set difference**, never a
cardinality comparison.

**The missing PDF matters specifically.** ConfRAG is one of the project's two grounded citations
(`CLAUDE.md` §7), and it is the one paper in the bibliography whose primary source is **not** on
disk — so it remains the citation that can only be checked over the network.

---

## 1a. Worse than a wrong ID: **5 of the 42 files are not the paper their filename claims**

Found 2026-08-27, *after* the author installed poppler, by a check the first pass never ran: extract
page 1 of every PDF and read the **title off the paper itself**, then compare it to the filename.
Five files are entirely unrelated papers.

| filename on disk | what the file **actually is** | survey's claimed ID | the **real** ID |
|---|---|---|---|
| `ClaimDecomp_DecomposingClaims_2022.pdf` | *El-WaveHoltz: A Time-Domain Iterative Solver for Time-Harmonic Elastic Waves* (Appelö, Garcia, Alvarez Loya, Runborg) — computational mathematics | `2205.12344` | **`2205.06938`** — *Generating Literal and Implied Subquestions to Fact-check Complex Claims*, Chen/Sriram/Choi/Durrett, EMNLP 2022 (survey says ACL 2022) |
| `Claimify_ExtractingVerifiableClaims_2024.pdf` | *FLARE: A New Federated Learning Framework with Adjustable Learning Rates* — federated learning | `2404.14811` | **`2502.10855`** — *Towards Effective Extraction and Evaluation of Factual Claims*, Metropolitansky & Larson, **ACL 2025** (survey says 2024) |
| `FactCheckGPT_ExplainableFactChecking_2023.pdf` | *GalliformeSpectra: A Hen Breed Dataset* (Himel & Islam) — a poultry image dataset, Word 2019 / Elsevier template, **not an arXiv paper at all** | `2310.19830` | **`2311.09000`** — *Factcheck-Bench: Fine-Grained Evaluation Benchmark for Automatic Fact-checkers*, Wang et al., 13 authors |
| `GENRE_GenerativeEntityRetrieval_2021.pdf` | *User Fairness, Item Fairness, and Diversity for Rankings in Two-Sided Markets* (Wang & Joachims, Cornell) — ACM SIGIR | `2010.01470` | **`2010.00904`** — *Autoregressive Entity Retrieval*, De Cao/Izacard/Riedel/Petroni, **ICLR 2021 spotlight** |
| `WICE_FineGrainedClaimVerification_2023.pdf` | an *Astronomy & Astrophysics* manuscript (`©ESO 2023`) | `2310.01601` | **`2303.01432`** — *WiCE: Real-World Entailment for Claims in Wikipedia*, Kamoi/Goyal/Rodriguez/Durrett, EMNLP 2023 |

All five **real** IDs were read from the paper's own `arxiv.org/abs/` page, so the right-hand column
is tier-2 evidence and citable; the middle column is measured from the file on disk and is tier 1.
Note the survey's *titles* are wrong too where the real paper differs: WiCE is *"Real-World
Entailment for Claims in Wikipedia"*, not *"Real-World Fine-Grained Claim Verification"*.

**Why the first pass missed all five, which is the part worth keeping.** §2's ID check diffed each
row's claimed ID against the `arXiv:` stamp printed inside the PDF. For **four of these five the
stamp MATCHES the claimed ID exactly** — `2205.12344`, `2404.14811`, `2010.01470`, `2310.01601` are
all stamped in their files. That is not a coincidence and not a second error: **the wrong ID is what
fetched the file.** A fabricated-but-well-formed arXiv ID resolves to a real paper, the download
succeeds, and the file is saved under the intended paper's name — so the ID inside it is *guaranteed*
to match the ID that was claimed. **A check that verifies a claim against a document the claim itself
selected cannot fail.** It measures the self-consistency of a fetch-by-ID pipeline, which is a
property of the pipeline, not of the bibliography.

This is the same defect shape as `CLAUDE.md` §6's resolver audit — *"the audit verified correctness
by checking the chosen entity's label against the subject string, the same signal used for
selection, so it could not fail"* — and it is now recorded twice in this project on unrelated
artifacts. The non-circular check is the one that reads an **independent field**: the title *the
paper prints about itself*. The fifth file, `FactCheckGPT_…`, evaded differently and just as
instructively — it carries **no arXiv stamp**, so it landed in §2's *"unverifiable this way"* bucket.
**Absence of evidence was filed as inconclusive when it was the loudest signal available**: every
other fact-checking paper in the folder is an arXiv preprint, so a file with no stamp was the one
most worth opening.

**One repair is free.** The correct paper for the `FactCheckGPT_…` row is **already on disk** as
`FactcheckBench_FineGrainedEvaluation_2023.pdf`, whose page 1 reads *"Factcheck-Bench: Fine-Grained
Evaluation Benchmark for Automatic Fact-Checkers — Yuxia Wang, Revanth Gangi Reddy, Zain Muhammad
Mujahid, Arnav …"*. The survey lists **one paper twice under two names** (it was renamed from
*Factcheck-GPT* to *Factcheck-Bench* between preprint versions), and the second row's download used
a fabricated ID and brought back the hen-breed dataset. This also explains §2's duplicate-ID
collision at `2311.08401`: two rows carrying one ID is what a renamed paper entered twice looks
like.

**Nothing the thesis quotes moves.** None of the five is cited anywhere in `CLAUDE.md` — the file's
citations are R-Tuning, ConfRAG, Farquhar/Nature, Kuhn/ICLR, FinGround and ReFinED, and **all six of
those PDFs pass the identity check** (ReFinED's page 1 reads *"ReFinED: An Efficient
Zero-shot-capable Approach to End-to-End Entity Linking — Tom Ayoola, Shubhi Tyagi, Joseph Fisher,
Christos Christodoulopoulos"*, so §7's task-#21 precedent stands). So **0 measured numbers change**
and no bibliography entry is wrong. What changes is the *evidence base*: **11.9% of the folder is
not what it says it is**, so a PDF's presence on disk is tier-1 evidence for **the paper it actually
is**, never for the paper its filename names.

**The other 37 pass.** The sweep printed the first three page-1 lines of all 42 files and every
remaining title matches its filename, including the four with no arXiv stamp (ClaimBuster,
Factcheck-Bench, SemanticEntropy_Nature — plus FactCheckGPT, the failure).

---

## 2. Where the survey's defects actually are — and it is **not** the arXiv IDs

This is the finding that overturned my own working assumption. `CLAUDE.md` §7 records a
failure-mode prediction that held for the agy-supplied bibliography: *"author lists and venues in
such summaries are usually right; page ranges and arXiv IDs are what they get subtly wrong."*
**On this survey that prediction INVERTS.** Measured by diffing each row's claimed ID against the
`arXiv:` stamp printed inside the PDF itself:

| | count |
|---|---|
| rows whose claimed arXiv ID **matches the stamp in the PDF** | **35** |
| rows whose claimed ID **contradicts** the PDF | **2** |
| rows unverifiable this way (no arXiv stamp — VLDB/ACL/Nature typeset) | 4 |
| rows naming a PDF that is not on disk | 1 |

**35 of 37 checkable IDs AGREE with the stamp in the PDF — and §1a shows agreement is not
correctness here.** Read the table as *"35 files came from the ID the survey claims"*, which is all a
fetch-by-ID pipeline can ever tell you: 4 of the 5 wrong-paper files are inside that 35, stamped with
the very ID that fetched them. **The one thing this check genuinely detects is a MISMATCH** — a
stamp that contradicts the claimed ID proves the file did *not* come from that ID, which is why the
two rows below are real findings and the 35 are not a clean bill of health. Corrected conclusion: the
ID *layer* is internally consistent, the defects concentrate in **venue, year and author
attribution** (§5) and in **file identity** (§1a), and **the §7 prediction should not be reused as a
general law** — it describes one channel (a chat summary), not all of them.

### The two genuine ID errors

- **OpenFactCheck** — survey says `arXiv:2311.08401`; the PDF is stamped **`2405.05583`**. This
  **resolves the duplicate-ID collision** flagged on first read: rows 8 and 9 both carried
  `2311.08401`, and at most one could be right. Row 8 (**Factcheck-Bench**) keeps it; **row 9 is
  the wrong one.**
- **RealFactBench** — survey says `arXiv:2401.02468` and *(2024)*; the PDF is stamped
  **`arXiv:2506.12538v1 [cs.CL] 14 Jun 2025`**. Both the ID and the year are wrong, and the
  **filename `..._2024.pdf` carries the wrong year too**.

### One suspicion of mine that was wrong — and then the RETRACTION was wrong too

Recorded in full because both directions are instructive. On first read I flagged **Claimify's
`arXiv:2404.14811`** as suspect on nothing but pattern-matching. I then retracted the flag: the ID
*is* stamped in the PDF, so I wrote *"Claimify's `2404.14811` is CORRECT"* and filed it against
myself as an R1 lesson about unfounded suspicion.

**§1a overturns the retraction.** `2404.14811` is stamped in that file because the file **is not
Claimify** — it is *FLARE: A New Federated Learning Framework*, and the stamp is FLARE's. Claimify's
real ID is **`2502.10855`** (ACL 2025). So the original suspicion was pointing at a real defect, and
I dismissed it using **the circular check §1a describes** — the strongest form of the error, because
the retraction *felt* like the disciplined move. **The lesson is not "trust hunches" but "a
retraction needs an independent signal exactly as much as the claim it retracts."** I had opened a
primary source; it was the wrong primary source, selected by the claim under test.

**R-Tuning's `2311.09677` survives** — that file's page 1 reads *"R-Tuning: Instructing Large
Language Models to Say 'I Don't Know' — Hanning Zhang, Shizhe Diao, Yong Lin, Yi R. Fung, …"*, so it
passes the identity check as well as the stamp check.

### Year-layer errors

Two real ones, after discarding two false positives my own regex produced (**ClaimBuster's
"2079-83" is a VLDB *page range*, not an arXiv ID**; **DeBERTaV3's Nov-2021 preprint → ICLR 2023
venue is a legitimate divergence, not an error**):

- **FinGround** — survey says *(2024)*; the PDF is stamped **`arXiv:2604.23588v1 [cs.AI] 26 Apr
  2026`**, and its abstract motivates itself by the **EU AI Act high-risk deadline (August 2026)**
  as *approaching*. It is a 2026 paper. The **filename carries the wrong year** as well.
- **RealFactBench** — above.

---

## 3. The two claims that could actually change a thesis argument — both resolved

### 3a. FinGround's granularity ablation — the QUOTE is verbatim, the INFERENCE is a non-sequitur

The survey calls this "GOLDEN EVIDENCE" and uses it as the justification for the 5-type taxonomy.
Verified against the PDF body, and the survey quotes it **accurately**:

> §3.1: *"Validation confirming appropriate granularity (6-type outperforms 3-type by 4.3 F1;
> 10-type shows no significant gain, p=0.23) is in Appendix A."*
>
> Appendix A: *"The 6-type achieves 91.4% F1; the 3-type achieves 87.1% (−4.3, p<0.01); the
> 10-type achieves 91.7% (+0.3, p=0.23), supporting the 6-type as the preferred
> accuracy-complexity trade-off."*

**But the survey's gloss — "proving HalDetect's 5-type taxonomy is optimal" — does not follow, and
must not be written into the thesis in that form.** Three reasons, in increasing severity:

1. **FinGround never tested 5.** It tested 3, 6 and 10. A curve measured at three points cannot
   locate an optimum at a fourth, unmeasured one.
2. **Its 6 types are not HalDetect's 5.** FinGround's are *numerical, temporal, entity-attribute,
   comparative, regulatory, computational* — `regulatory` is finance-specific and
   `numerical`/`comparative`/`computational` are three separate top-level types where HalDetect
   makes them **subtypes inside QUANTITATIVE**. HalDetect has RELATIONAL and CITATION, which
   FinGround has not. The two taxonomies overlap on 2 of 5/6 labels.
3. **It is a single-domain result** on FinHalu, a financial dataset.

**What it legitimately supports, and this is still worth citing:** *coarse taxonomies lose real
accuracy (−4.3 F1, p<0.01) while granularity beyond roughly half a dozen types buys nothing
(+0.3, p=0.23)* — an independent, published, directional corroboration that mid-single-digit
granularity is the right regime, and a citable rebuttal to a *"why not 3 types?"* or *"why not
20?"* objection. **Cite it as a regime argument, never as proof of the number 5.**

**Also verified verbatim** (both figures the survey quotes exist, and they are *different*
statistics — do not merge them): *"Computational claims show the highest hallucination rate
(28.4%)"* is the per-type rate **within FinHalu**; *"missing 43% of computational errors that
require arithmetic re-verification against structured tables"* is what uniform detectors miss.
The abstract carries the 43%, §5 carries the 28.4%.

### 3b. An unforced independent corroboration the survey never noticed: **±0.5%**

FinGround §3.2: *"(3) re-computing the derived quantity with **±0.5% tolerance** for rounding
conventions."*

`current/quantitative_verifier.py` uses a **0.5% tolerance**, chosen locally, and `CLAUDE.md` §3
records the sensitivity result: *all 8 covered Batch-3 claims flip TRUE→FALSE when the claimed
value moves ≤1%, and none flips inside the 0.5% tolerance.* An independent published system
arrived at the **same constant for the same reason** (rounding conventions in reported figures).

This is the most useful single thing in the whole `papers_analysis/` folder for the thesis: a
constant that was previously defensible only by local sensitivity analysis now has external
support. **It is corroboration, not derivation** — the 0.5% was set before this paper was read,
and the sensitivity result remains the primary evidence.

---

## 4. A citation correction that touches a number the thesis already quotes: **AURAC**

`CLAUDE.md` §2 quotes **AURAC 0.898** for CITATION L1. The survey's row 33 reads
*"Kuhn et al. (Oxford, 2024) | Nature 630 (2024)"* linking `arXiv:2302.09664`. **That row conflates
two different papers**, and the two PDFs on disk prove it:

| file | first line of the PDF | authors |
|---|---|---|
| `SemanticEntropy_Hallucinations_2024.pdf` | *"Published as a conference paper at **ICLR 2023** — SEMANTIC UNCERTAINTY: LINGUISTIC INVARIANCES FOR UNCERTAINTY ESTIMATION IN NATURAL LANGUAGE GENERATION"* | **Lorenz Kuhn, Yarin Gal, Sebastian Farquhar** (3) |
| `SemanticEntropy_Nature_2024.pdf` | *"**Nature \| Vol 630 \| 20 June 2024 \| 625** — Detecting hallucinations in large language models using semantic entropy"* | **Sebastian Farquhar**, Jannik Kossen, Lorenz Kuhn & Yarin Gal (4) |

The survey takes the **ICLR paper's lead author and arXiv ID** and pairs them with the **Nature
paper's venue**. `arXiv:2302.09664` is the ICLR 2023 paper (stamped in that PDF). The filename
`SemanticEntropy_Hallucinations_2024.pdf` also carries the wrong year — it is ICLR **2023**.

**Which one owns AURAC — measured, not assumed.** The string `AURAC` appears **16 times in the
Nature PDF** and its definition is there:

> *"We also show a new measure, the area under the 'rejection accuracy' curve (AURAC). This studies
> the case in which the confabulation detection score is used to refuse to answer the questions
> judged most likely to cause confabulations."*

**So AURAC must be cited as Farquhar, Kossen, Kuhn & Gal, *Nature* 630 (20 June 2024), p. 625 —
NOT "Kuhn et al."** Citing the ICLR paper for AURAC would attribute a metric to a paper that does
not define it, in support of a number (0.898) the thesis reports. That is the one defect in either
document with a direct line to a quoted result.

*(Incidental: `Wilson` appears **0** times in the Nature paper — the Wilson interval discipline in
R2 comes from Wilson 1927, not from there, and nothing in the project claims otherwise.)*

---

## 5. Other survey defects, none load-bearing

- **`FinGround`'s title is wrong.** Survey: *"FinGround: Financial Factuality & Computational
  Routing"*. Actual: ***"FinGround: Detecting and Grounding Financial Hallucinations via Atomic
  Claim Verification"***, **Dongxin Guo¹, Jikun Wu², Siu Ming Yiu¹** (¹The University of Hong Kong,
  ²Stellaris AI Limited). The survey lists **no authors at all** for it.
- **"Flaucon-NLI"** (profile #5, MiniCheck) is not a real model name — a garbled generation. The
  real pair is Bespoke-MiniCheck-7B and a Flan-T5 / *AlignScore*-family baseline; take model names
  for MiniCheck from `MiniCheck_EfficientFactChecking_2024.pdf` (on disk, `2404.10774`, 30 pp).
- **"Outstanding Paper"** for R-Tuning appears **twice** in the survey. This is the exact
  attribution removed from `CLAUDE.md` on 2026-08-27 as `NOT VERIFIED` — the ACL Anthology page
  does not record award status. **The survey is where that claim came from; it is not a second
  independent source for it.** The on-disk `RTuning_SayIDontKnow_2024.pdf` is the arXiv preprint
  (27 pp), so it cannot settle award status either. Restore only from an ACL award list.
- **R-Tuning author spelling.** The PDF gives **"Yi R. Fung"**; both `CLAUDE.md` and the survey say
  "Yi Fung". Nine authors and the title otherwise confirm exactly:
  *Hanning Zhang, Shizhe Diao, Yong Lin, **Yi R. Fung**, Qing Lian, Xingyao Wang, Yangyi Chen,
  Heng Ji, Tong Zhang* (HKUST + UIUC).
- **Stale project numbers**, same root cause as `external_catalog_assessment_2026-08-26.md`: §4
  objection #4 says **"13 gold negatives"** (now **14** post-`Q22_C01`-flip) and "343
  counterfactuals" (the project has **84** synthetic negatives + **27** B3N).
- **Roadmap items already done or already declined:** Priority 1 #2 (P31 type-check → task **#21**,
  built as the sibling `current/type_consistency.py`, *not* inside `property_resolver.py` as the
  doc proposes); Priority 1 #3 (AURAC / Wilson — long since standing rules R2 and §2);
  Priority 3 #7 (World Bank / WHO GHO — already a **measured** §6 finding, not a proposal);
  Priority 3 #6 (chain-of-thought in the router) is **V3-shaped and declined** in §4 for reasons
  that have not changed — it re-types the `type` column and invalidates every measured win.

---

## 6. The reddit mechanisms file — status list, re-derived against the RIGHT document

Its Top-10 ranked actions, scored against the project as it actually stands:

| # | its recommendation | status here |
|---|---|---|
| 1 | DeBERTa-v3-large-mnli-fever-anli-ling-wanli NLI swap | **held** under §7's drastic-architectural-change carve-out — invalidates the `nli__` cache, the baseline's 356 rows and the whole threshold surface; BART SIGBUSes locally so it needs Colab. Its rationale is the best argument for it on record: FEVER's **NOT-ENOUGH-INFO** class trains the contradiction-vs-irrelevance distinction *directly*, which is precisely §6's measured ROC-shape limit. |
| 2 | cross-encoder re-ranking of retrieved passages | **new, and aimed at the right target** — §3 records coverage 90.2% as *retrieval*-bound, not threshold-bound. Untried. |
| 3 | synthetic negatives for all 5 types | **partially done and the gap is documented**: 84 negatives across **4** types; **no RELATIONAL synthetic negatives exist**, and `negatives_needing_manual_authoring.csv` holds 14 rows, **12 of them EA** (§5). |
| 4 | apply the `mul` fix project-wide | **DONE, and its WARNING is stale** — see below. |
| 5 | hybrid BM25 + dense retrieval | new, untried, same target as #2. |
| 6 | `P31` type-checking | **DONE — task #21**, `current/type_consistency.py`, selftest 24/24 + vacuity 4/4. Both original resolution bugs now return CONFLICT. |
| 7 | chain-of-thought in the classifier prompt | **declined** — V3-shaped (§4). |
| 8 | McNemar's test | **DONE — task #22**, and it made a quoted claim *weaker* exactly as predicted, producing R20's three admissibility conditions and the `2/2ⁿ` power floor. |
| 9 | MiniCheck | held with #1 (backbone swap). |
| 10 | two-step NLI | held with #1. |

**Two blocks in that file are stale, and both would mislead if acted on:**

- Its **WARNING** says the `mul`/full-text fixes are *"NOT yet applied project-wide …
  `property_resolver.py` and notebook cells 69/75 still use `languages=en` and prefix search."*
  **Wrong on both counts now.** Cells 69/75 were fixed in task **#12** (`en|mul`, full-text
  `list=search`, sitelinks/TIE_BAND, prefixes bumped); `property_resolver.py`'s bad path was
  **removed entirely** in task **#20** — resolution there is now *injected*, so the module cannot
  re-acquire the bug by drifting. The live caveat is different and is already recorded: cells 69/75
  have **never been executed** since the fix (zero `meta2__` cache keys), which is why TEMPORAL 0/12
  and EA 0/22 are *last-measured* rather than current.
- Its **CAUTION** quotes **"13 gold negatives"** — now **14**.

**Genuinely new, cheap, and not yet on the open-work list** — all four are Wikidata-side or
statistics-side, no model calls, no cache invalidation:

1. **Qualifier-aware verification (`P580`/`P582`)** — start/end qualifiers on a statement. Directly
   relevant to TEMPORAL, where a value can be right *for a period*.
2. **Statement rank filtering** — prefer `preferred` over `normal` rank. A cheap precision guard on
   exactly the multi-statement properties (`P2044` elevations) that carry QUANTITATIVE's 6/6.
3. **Description matching** in resolution — an *independent* signal in the same spirit as #21's
   `P31`, and it would further reduce the 72/72 circularity.
4. **Stratified bootstrap CIs** and **PR curves for the FALSE class** — the bootstrap addresses R2's
   `5/5` and `8/8` problem directly; the PR curve is the honest picture of §6's
   "contradiction precision never leaves 0.08–0.12" finding.

Also in the file and worth keeping on record: DBpedia fall-through, infobox extraction,
`P1566`/`P213` identifier bridging, `wbsgetsuggestions`; a multi-source routing table that
**independently reproduces §6's own structured-source finding** (QUANTITATIVE → Wikidata tier 1 →
World Bank / WHO GHO / OECD tier 2; CITATION → Crossref / PubMed / DOI); and tools to benchmark
against (Vectara HHEM, Patronus Lynx, DeepEval, RAGAS, OpenFactCheck, SelfCheckGPT).

**Provenance limit, stated because the file's own framing invites forgetting it:** these are
*Reddit* findings — practitioner opinion aggregated by an LLM. They are **leads, not evidence**,
and R1 applies in full. The two stale blocks above are the demonstration.

---

## 7. The evidence-tier finding — and the lesson that cost the project a wrong number

**42 primary-source PDFs on disk are a better evidence tier than either `agy` or `WebFetch`.**
They are offline, keyless, immune to ranking drift, immune to the FAO-style 403, and reproducible
byte-for-byte a year from now. Ranked:

| tier | what it licenses |
|---|---|
| **1. a PDF in `papers_analysis/downloaded_pdfs/`** | a verbatim quote with a page number — **for the paper the file's own page 1 names, never for the paper its filename names** (§1a) |
| 2. `WebFetch` on the publisher's own host (aclanthology.org, arxiv.org) | a citable field (BibTeX `pages`, author list, the real arXiv ID) |
| 3. `agy` headless with `read_url(*)` | **discovery only** — never quotable |

**§1a adds an admission condition to tier 1, and it is cheap: read the title off page 1 before
quoting the file.** 5 of 42 files here are unrelated papers, so *"the PDF is on disk"* licenses
nothing by itself. The check is one `pdftotext -f 1 -l 1` and it is the only signal in the folder
independent of the ID that fetched the file.

**The concrete lesson: `RTuning_SayIDontKnow_2024.pdf` was on disk the entire time the project
carried the wrong page range `7831–7848`**, and that error was closed on 2026-08-27 by
agy-discovery + WebFetch-verification — tiers 3 and 2 — while tier 1 sat unopened in the repo.
The PDF would not have given the NAACL page range (it is the arXiv preprint), but it *would* have
given the title and all nine authors instantly and offline.

**Operational rule this produces: check `papers_analysis/downloaded_pdfs/` before reaching for the
web at all — then check that the file is the paper.** `.venv/bin/python` already ships **`pypdf`**,
so text extraction needs zero installs; poppler's `pdftotext` (installed 2026-08-27) is better for
this particular job because `-layout` preserves the title block.

**A weak signal, measured so it is not over-trusted: embedded PDF metadata is nearly useless here.**
`pdfinfo` over all 42 finds a non-empty `Title`/`Author` in only **5** — LaTeX+hyperref leaves them
blank unless configured, so this is an opportunistic check, not a mechanism. But those 5 paid for
themselves twice: `SemanticEntropy_Nature_2024.pdf` carries `Title: Detecting hallucinations in large
language models using semantic entropy`, `Author: Sebastian Farquhar`, `Creator: Springer` —
**publisher-embedded confirmation of §4's AURAC correction, from Springer's own toolchain** — and
`GENRE_GenerativeEntityRetrieval_2021.pdf` carries a *different paper's* title with
`Creator: LaTeX with acmart`, which is what first exposed §1a.

---

## 8. Reproduce

All offline, seconds, zero API calls. From the **main checkout** (`ThesisCode_copy/`). **The one
step NOT reproducible offline is §1a's right-hand column** — the five corrected arXiv IDs were read
by `WebFetch` from `https://arxiv.org/abs/2010.00904`, `2205.06938`, `2303.01432`, `2311.09000` and
`2502.10855`, one call each.

```
.venv/bin/python -c "
from pypdf import PdfReader
r = PdfReader('papers_analysis/downloaded_pdfs/FinGround_FinancialFactuality_2024.pdf')
t = ' '.join(' '.join((p.extract_text() or '').split()) for p in r.pages)
import re
print([t[m.start()-120:m.start()+200] for m in re.finditer('0.23', t)])"
```

The set-difference check that catches §1 (and that a count comparison cannot):

```
.venv/bin/python -c "
import os, re
surv = open('papers_analysis/LITERATURE_SURVEY_AND_IMPACT_ANALYSIS.md').read()
listed = set(re.findall(r'([A-Za-z0-9_]+\.pdf)', surv))
disk = set(f for f in os.listdir('papers_analysis/downloaded_pdfs') if f.endswith('.pdf'))
print('listed not on disk:', sorted(listed - disk))
print('on disk not listed:', sorted(disk - listed))"
```

The **identity** check that catches §1a, and that neither a count nor an ID diff can. Note it needs
poppler, which the author installed 2026-08-27:

```
python3 -c "
import subprocess, os
d = 'papers_analysis/downloaded_pdfs/'
for f in sorted(x for x in os.listdir(d) if x.endswith('.pdf')):
    o = subprocess.run(['pdftotext','-f','1','-l','1',d+f,'-'],capture_output=True,text=True).stdout
    ls = [l.strip() for l in o.splitlines() if l.strip()]
    print(f'{f[:46]:<46} >> ' + ' | '.join(ls[:3])[:150])"
```

The circularity demonstration — for the four wrong-paper files the stamp *matches* the claimed ID,
so this prints agreement on files that are the wrong papers:

```
python3 -c "
import subprocess, re
d = 'papers_analysis/downloaded_pdfs/'
for f in ['ClaimDecomp_DecomposingClaims_2022.pdf','Claimify_ExtractingVerifiableClaims_2024.pdf',
          'GENRE_GenerativeEntityRetrieval_2021.pdf','WICE_FineGrainedClaimVerification_2023.pdf']:
    o = subprocess.run(['pdftotext','-f','1','-l','2',d+f,'-'],capture_output=True,text=True).stdout
    print(f, re.search(r'arXiv:(\d{4}\.\d{4,5})', o).group(1))"
```

**`Read` can now open these PDFs** — poppler 26.08.0 was installed by the author on 2026-08-27, so
`pdftotext`, `pdftoppm`, `pdfinfo`, `pdfimages` and `pdftohtml` are all at `/opt/homebrew/bin/`
(`mutool` and `qpdf` remain absent; `gs` was already present). Native page rendering, figures and
table layout are available; `pypdf` in the venv remains the zero-install text path. **The §8 note in
the first version of this doc — that `brew install poppler` was the one outstanding
user-actionable install — is DISCHARGED**, and it paid for itself within minutes: the poppler-only
identity sweep is what found §1a.

**Related:** `CLAUDE.md` R1/R1b (the count coincidence), R2 (Wilson), §2 (AURAC 0.898), §4 (the
V3 refusal that Priority 3 #6 re-proposes), §5 (negatives inventory), §6 (structured-source
routing, the ROC-shape limit), §7 (the verified R-Tuning/ConfRAG strings, the `agy` path) ·
`reference/external_catalog_assessment_2026-08-26.md` (**the same stale-snapshot root cause, third
occurrence**) · `reference/type_consistency_2026-08-27.md` (task #21, which the survey's roadmap
proposes as new).
