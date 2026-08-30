# Forensic Red-Team Audit: Primary & Secondary Weaknesses and Loopholes of HalDetect
**Thesis Project:** HalDetect (CSE 700, University of Chittagong)  
**Date:** August 30, 2026  
**Chapter Reference:** Chapter 7 (Discussion, Limitations & Threats to Validity)  

---

## 🧭 Panoramic Limitation Architecture

```
                          HALDETECT LIMITATION TAXONOMY
┌──────────────────────────────────────────┬──────────────────────────────────────────┐
│ 🔴 PRIMARY ARCHITECTURAL BOTTLENECKS     │ 🟡 SECONDARY ENGINEERING CONSTRAINTS     │
│ 1. Structured Registry Horizon (Cold Start)│ 1. Entity Polysemy & Acronym Clashes   │
│ 2. Upstream Coreference/Atomizer Loss    │ 2. Dynamic Temporal Knowledge Drift      │
│ 3. Compound Multi-Modal Claim Clashes    │ 3. Obscure Unit & Scale Polysemy         │
│                                          │ 4. Fallback DeBERTa NLI Precision Decay  │
├──────────────────────────────────────────┴──────────────────────────────────────────┤
│ 🚨 ADVERSARIAL RED-TEAM LOOPHOLES                                                   │
│ 1. False Presupposition Injection (Grounded in non-existent entities)               │
│ 2. Epistemic Hedge Stripping (Treating hypotheses as verified facts)                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. 🔴 Primary Weaknesses (Core Architectural Limitations)

### 1. The "Closed-World Registry Horizon" (Cold-Start Boundary)
* **The Weakness:** HalDetect's high precision comes from grounding against authoritative registries (Wikidata SPARQL, World Bank REST API, CrossRef DOIs, NIST physical constants).
* **The Failure Mode:** If a claim concerns an **unindexed, private, highly localized, or obscure long-tail fact** (*"A small startup in Chittagong was founded in 2024 with 3 employees"*), HalDetect has no structured graph nodes or REST endpoints for it.
* **Impact:** HalDetect is forced to either fall back to open Wikipedia neural NLI or safely emit `UNVERIFIABLE`. It cannot provide deterministic ALU guarantees on unregistered private data.

### 2. Upstream Coreference & Decontextualization Loss
* **The Weakness:** HalDetect's verifiers depend entirely on the quality of the upstream `SchemaAtomizer`.
* **The Failure Mode:** When an LLM writes complex, multi-clause narrative sentences with pronoun chains:
  * *Example:* *"After joining the Swiss Patent Office, where he reviewed inventions, Einstein derived his equation."*
  * If the parser fails to resolve *"he"* $\to$ *"Einstein"*, it emits orphaned tuples like $\langle \text{he}, \text{reviewed}, \text{inventions} \rangle$, which cannot be linked to Wikidata.

### 3. Compound Multi-Modal Claim Clashes (Single-Label Routing)
* **The Weakness:** Real-world sentences often blend multiple modalities into a single compound statement:
  * *Example:* *"In 2023, the US GDP reached $27.36T, according to the World Bank report (DOI: 10.1596/...)."*
* **The Failure Mode:** This sentence is simultaneously **Temporal** (`2023`), **Quantitative** (`$27.36T`), **Relational** (`US GDP reached`), and **Citation** (`DOI: 10.1596/...`). HalDetect currently uses single-label routing (assigning it to the dominant modality) rather than spawning a multi-aspect verification DAG.

---

## 2. 🟡 Secondary Weaknesses (Engineering Constraints)

### 1. Entity Disambiguation Polysemy (Homonyms)
* Mentions like *"Jordan"* (the country vs. Michael Jordan), *"Paris"* (Paris, France vs. Paris, Texas), or *"Apple"* (the company vs. the fruit).
* While the `alias_lexicon_resolver` and sitelinks tie-breakers resolve >90% of cases, without deep bidirectional dense entity linkers (like BLINK), lexical matching can occasionally latch onto the wrong Wikidata QID.

### 2. Dynamic Temporal Knowledge Drift
* Facts that change continuously (e.g. *"Current Prime Minister of the UK"*, *"CEO of Twitter"*, or *"Number of confirmed moons of Jupiter"* — which updated from 95 to 97).
* If the underlying knowledge graph or local cache has not been refreshed, HalDetect will judge a newly true fact as `FALSE` or `UNVERIFIABLE`.

### 3. Obscure Unit & Scale Polysemy
* While HalDetect has dedicated ALUs for SI units (Kelvin↔Celsius, m/s, transistor counts, megawatt-hours, currencies), it does not cover every possible obscure regional unit (e.g., British Thermal Units, nautical miles, barrels of oil equivalent, short tons vs. metric tonnes).

### 4. Relational Fallthrough NLI Decay
* On open-world relational claims where no SPARQL triple exists, HalDetect falls back to Wikipedia passage retrieval + DeBERTa-v3 cross-encoder NLI.
* In this specific fallback path, HalDetect inherits neural NLI's known weaknesses (e.g., lower precision on complex multi-hop negations).

---

## 3. 🚨 Adversarial Loopholes (Red-Team Vectors)

### 1. False Presupposition Injection
* *Adversarial Claim:* *"The 40-story wooden skyscraper in downtown Tokyo built in 1850 had 4 elevators."*
* *The Loophole:* HalDetect's Quantitative ALU might verify whether the number `4` matches an elevator count, while failing to detect the **false underlying presupposition** (that a 40-story wooden skyscraper existed in 1850 Tokyo).

### 2. Epistemic Hedge Stripping
* *Adversarial Claim:* *"Scientists hypothesize that dark matter might comprise 85% of cosmic matter."*
* *The Loophole:* If the atomizer strips the epistemic hedge (*"Scientists hypothesize that"*), it converts a speculative hypothesis into a rigid factual assertion (*"Dark matter comprises 85% of matter"*), falsely evaluating scientific conjecture as established historical fact.

---

## 4. 🎓 Defense Pitch for the Oral Examination

> **The Examiner Defense Pitch:**
> *"HalDetect makes an intentional, scientifically principled trade-off: **we trade universal open-domain coverage for uncompromising mathematical precision within structured verification horizons**.
> 
> Its primary boundary is the **Closed-World Registry Horizon**—HalDetect excels where authoritative registries (Wikidata, World Bank, CrossRef, NIST) exist, but safely abstains ($\mathcal{L}_3$ logic) when asked about private or unindexed long-tail facts. Furthermore, compound sentences blending multiple modalities highlight the need for our proposed future work: a **multi-aspect directed acyclic graph (DAG) verification pipeline**."*
