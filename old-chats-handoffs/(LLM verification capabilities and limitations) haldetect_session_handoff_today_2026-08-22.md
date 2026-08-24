# HalDetect — Session Handoff (today, 2026-08-22)

> Chat name: LLM verification capabilities and limitations

_Read this first. Everything below assumes no prior context._

---

## What This Session Was

This was not a coding or experiment session. It was a literature review and theoretical framing session focused on one question: is building a structured verification pipeline necessary in a world where LLMs have large parametric knowledge bases and access to web search? The session examined this question through multiple published papers and established the theoretical foundation for HalDetect's related work chapter and discussion section.

---

## A. What Happened This Session, In Order

1. Started with the core dilemma: if GPT-4/Claude with web search can just answer a factual question, why build a pipeline at all?
2. Examined parametric-only LLM verification — established it is untrustworthy with no internal mechanism to verify facts or flag uncertainty reliably.
3. Examined RAG-augmented verification — found it does not reliably fix the problem. Traced the failure mechanism: parametric prior → biased retrieval query → biased evidence retrieved → verdict driven by prior regardless of evidence.
4. Examined web-search-enabled LLMs (Perplexity, GPT-5) — found citation fabrication rates of 39–55% (GPT-3.5), 18–28% (GPT-4), ~7–8% (GPT-5 with web search). Improvement trajectory confirmed but not zero.
5. Read and dissected "(Fact) Check Your Bias" (2025) in full — traced the HerO pipeline's three-stage operation (HyDE document generation → BM25 retrieval → Q&A-based verdict), identified the two core findings: biased retrieval and verdict decoupling from evidence.
6. Clarified the AVeriTeC knowledge store — confirmed it is a pre-collected offline corpus from fact-checking websites (Snopes, PolitiFact), not parametric memory and not simulated web search.
7. Mapped relationships between six papers: FEVER, AIC CTU Simple RAG, HerO, "(Fact) Check Your Bias," Knowledge Conflicts Survey (Xu et al.), Abstention Survey, "Perils and Promises," "Surprising Efficacy of Fine-Tuned Transformers."
8. Examined Xu et al. (EMNLP 2024) taxonomy figure — confirmed all branches (Causes, Analysis, Solution) support rather than negate HalDetect's design rationale.
9. Established that no published paper argues verification pipelines are obsolete. The field's direction is toward smarter pipelines, not their elimination.
10. Identified two genuine counterarguments that were underweighted: "RAG is Dead" ICLR 2025 (million-token contexts reduce retrieval necessity) and GPT-5's ~7–8% fabrication rate as a meaningful improvement trajectory.
11. Confirmed that LLM self-reported confidence is poorly calibrated — models are confidently wrong, making confidence scores unreliable as verification signals.
12. Confirmed FActScore as the paper that operationalized atomic claim-level verification specifically for LLM-generated long-form text, distinguishing it from paragraph-level RAG evaluation.
13. Fetched and read the Springer "Hallucination to Truth" review (January 2026) — confirmed it is a broad survey aligned with but shallower than "(Fact) Check Your Bias."
14. Fetched "Detecting and Correcting Reference Hallucinations in Commercial LLMs and Deep Research Agents" (2025) — confirmed it characterizes citation URL failures empirically but does not directly argue for structured pipelines over generative RAG.
15. Produced a neutral summary of the session for handoff purposes.

---

## B. Papers Examined

| Paper | Venue/Source | Year | Role in HalDetect framing |
|-------|-------------|------|--------------------------|
| FEVER (Thorne et al.) | NAACL-HLT | 2018 | Foundation — establishes retrieval+NLI paradigm |
| FActScore (Min et al.) | EMNLP | 2023 | Atomic claim-level verification standard; motivates pipeline necessity |
| Knowledge Conflicts Survey (Xu et al.) | EMNLP | 2024 | Theoretical taxonomy of context-memory conflict |
| AIC CTU Simple RAG | AVeriTeC workshop | 2024 | Counterpoint — simple RAG competitive with complex pipelines |
| HerO at AVeriTeC | AVeriTeC workshop | 2024 | Architectural foil — most similar pipeline to HalDetect |
| (Fact) Check Your Bias | arXiv | 2025 | Core supporting paper — empirically shows retrieval bias and verdict decoupling |
| Abstention/Selective Prediction Survey | — | 2024 | Grounds UNVERIFIABLE as first-class outcome |
| Perils and Promises of Fact-Checking with LLMs | — | 2024 | Bridges theory to empirical failure rates |
| Surprising Efficacy of Fine-Tuned Transformers | — | 2024 | Supports fine-tuned NLI (bart-large-mnli) over general LLMs |
| Detecting and Correcting Reference Hallucinations | arXiv | 2025 | Characterizes citation failures across LLMs and agents |
| Hallucination to Truth review | Springer AI Review | 2026 | Broad survey; confirms field direction toward stronger pipelines |
| INRA.AI citation accuracy blog | INRA.AI | 2025 | Empirical citation fabrication rates by model |

---

## C. Key Findings — Ranked by Evidence Strength

1. **Parametric prior dominates verdict regardless of retrieved evidence.** "(Fact) Check Your Bias" showed that even when retrieval differs substantially across bias conditions (~50% unique sentences per condition), final verdicts remain stable — meaning the LLM is not reading the evidence to form its verdict. This is empirically demonstrated, replicated across conditions, and directly citable.

2. **Biased retrieval query is the first failure point in RAG-based verification.** HyDE's hypothetical document carries parametric bias into BM25 retrieval before any reasoning occurs. The LLM never encounters contradicting evidence because its own prior shaped what got retrieved. This is the upstream failure that verdict decoupling compounds.

3. **Citation fabrication persists across all web-search-enabled LLMs tested.** GPT-3.5: 39–55%. GPT-4: 18–28%. GPT-5 with web search: ~7–8%. Perplexity: ~37%. No model tested achieves zero fabrication rate autonomously.

4. **LLM confidence signals are uncalibrated.** The Abstention Survey established that internal logit-based confidence scores reflect linguistic plausibility, not evidential reliability. Models are confidently wrong at meaningful rates.

5. **Single-source verification is a known limitation the field accepts for reproducibility.** Most existing pipelines use Wikipedia only. Multi-source verification is acknowledged as preferable but not yet standard. HalDetect's use of Wikidata SPARQL + Wikipedia is already multi-source for TEMPORAL claims.

6. **Two genuine counterarguments exist and must be acknowledged.** Million-token context windows (ICLR 2025) reduce but do not eliminate the case for retrieval pipelines. GPT-5's ~7–8% fabrication rate represents a meaningful improvement trajectory. Neither resolves the core problem for high-stakes verifiable claims.

---

## D. Open Theoretical Questions — NOT YET RESOLVED

- **At what fabrication rate does LLM-with-web-search become an acceptable substitute for structured verification?** The answer is domain-dependent (medical, legal, academic each have different tolerances) and no paper has drawn this line.
- **Does the "RAG is Dead" ICLR 2025 argument apply to verification pipelines specifically, or only to generation pipelines?** Not yet examined in depth.
- **How does agentic AI (multi-step tool use, self-correction) change the verification landscape?** "Detecting and Correcting Reference Hallucinations" touches this but does not resolve it.
- **Is atomic claim-level verification via NLI still the right granularity, or does sentence-level context need to be preserved?** FActScore assumes atomicity is safe; this has not been challenged directly in the papers examined.

---

## E. Standing Theoretical Commitments (for thesis writing)

- LLM verdicts are treated as probabilistically unreliable at all enhancement levels unless grounded in deterministic external verification.
- UNVERIFIABLE is a first-class outcome, not a system failure — grounded in the Abstention Survey's coverage-accuracy tradeoff framing.
- Counterarguments (GPT-5 trajectory, million-token context) are acknowledged in the thesis Discussion/Limitations section, not suppressed.
- The distinction between generation-with-citations and verification-with-auditable-evidence is maintained throughout — these are not equivalent systems.
- Single-source limitation is acknowledged; multi-source design of TEMPORAL verifier is documented as a partial response to this critique.

---

## F. What to Use This Session For

1. **Related Work chapter** — the paper relationships established here (FEVER → AIC CTU / HerO → "(Fact) Check Your Bias" → Knowledge Conflicts Survey → Abstention Survey → FActScore) form the backbone of the related work narrative.
2. **Motivation section** — citation fabrication rates and the parametric-prior-overrides-evidence finding are the two strongest empirical motivations for HalDetect's pipeline approach.
3. **Discussion/Limitations section** — GPT-5 trajectory and million-token context counterarguments belong here, stated plainly.
4. **Defense of UNVERIFIABLE label** — cite the Abstention Survey to justify abstention as a design choice rather than a failure mode.
5. **Defense of claim-type-specific routing** — cite "(Fact) Check Your Bias" and the Knowledge Conflicts Survey together: uniform retrieval fails because the prior contaminates retrieval; claim-type routing to deterministic verifiers bypasses this failure mode for structured claim types.

Priority for thesis writing: Related Work > Motivation > Discussion/Limitations.

---

## Key Papers to Have for Context

- "(Fact) Check Your Bias" (2025, arXiv:2506.21745) — the most directly relevant paper; read in full this session.
- Knowledge Conflicts for LLMs: A Survey (Xu et al., EMNLP 2024) — the theoretical frame; the taxonomy figure was examined in full.
- FActScore (Min et al., EMNLP 2023) — the methodological standard HalDetect builds on.
- "Detecting and Correcting Reference Hallucinations" (2025, arXiv:2604.03173) — citation failure empirics.
- "Hallucination to Truth" review (Springer AI Review, January 2026, DOI: 10.1007/s10462-025-11454-w) — broad 2020–2025 survey.

---

## Tone Note

This session resolved the author's dilemma about whether HalDetect is necessary. The answer from the literature is: pipelines are not obsolete, the field is moving toward smarter pipelines not their elimination, and the specific failure modes HalDetect is designed to avoid (parametric prior contaminating retrieval, probabilistic NLI for claim types that permit deterministic verification) are empirically documented in published work. Two counterarguments were identified honestly and are to be treated as thesis content, not threats.
