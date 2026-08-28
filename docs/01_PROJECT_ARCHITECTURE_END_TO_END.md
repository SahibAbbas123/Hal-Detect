# 🏗️ HalDetect 2.0: End-to-End System Architecture & Technical Specification

## 1. Executive Overview

**HalDetect 2.0** is an asymmetric, neuro-symbolic hallucination detection and fact-verification engine designed to verify complex, multi-sentence generative LLM responses and structured factual claims with sub-millisecond latency, zero inference token costs, and mathematically deterministic precision.

Traditional fact-checking pipelines deploy massive foundation models (e.g., GPT-4o, Claude 3.5 Sonnet) or monolithic Dense Neural Retrieval-Augmented Generation (RAG) cross-encoders (e.g., DeBERTa-v3, MiniCheck). While effective for general semantic similarity, neural text models suffer from:
1. **Token Overlap Bias:** Blindness to negation words and subtle entity swaps when 90%+ of tokens overlap.
2. **Dimensional & Scale Blindness:** Inability to perform unit conversions (77 K vs -196 °C vs 77 °C) or scale arithmetic (Million vs Billion).
3. **Severe Computational Cost & Latency:** 2,500 ms – 4,000 ms latency and non-zero dollar costs per verified sentence.

HalDetect solves this through **Modality-Driven Asymmetric Routing**: routing deterministic queries (arithmetic, dates, bibliographic citations) to exact symbolic arithmetic ALUs and authoritative REST registries, while reserving neural semantic models strictly for open qualitative claims.

---

## 2. The 5-Stage Verification Pipeline

```
                                [Raw Input Text / LLM Generation]
                                                │
                                                ▼
                     ┌──────────────────────────────────────────────────────┐
                     │ STAGE 1: 5-Tuple Semantic Schema Atomizer            │
                     │ (Co-reference Resolution + Clause Disambiguation)    │
                     └──────────────────────────────────────────────────────┘
                                                │
                                                ▼
                     ┌──────────────────────────────────────────────────────┐
                     │ STAGE 2: Modality Taxonomy Classifier & Router       │
                     │ (Quantitative, Temporal, Entity, Citation, Relation) │
                     └──────────────────────────────────────────────────────┘
                                                │
                        ┌───────────────────────┼───────────────────────┐
                        ▼                       ▼                       ▼
            ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐
            │ STAGE 3A: Quantitative│ │ STAGE 3B: Temporal│ │ STAGE 3C: Citation│
            │ SI Engine & World Bank│ │ State Guard       │ │ DOI Registry      │
            └───────────────────────┘ └───────────────────┘ └───────────────────┘
                        │                       │                       │
                        └───────────────────────┼───────────────────────┘
                                                ▼
                     ┌──────────────────────────────────────────────────────┐
                     │ STAGE 4: Asymmetric Tri-Logic Truth Resolver         │
                     │ (TRUE, FALSE, UNVERIFIABLE under Open-World Model)   │
                     └──────────────────────────────────────────────────────┘
                                                │
                                                ▼
                     ┌──────────────────────────────────────────────────────┐
                     │ STAGE 5: Executive Factuality Dashboard (RFI & RHR)  │
                     └──────────────────────────────────────────────────────┘
```

---

## 3. Stage-by-Stage Engineering Detail

### 📐 Stage 1: 5-Tuple Schema Atomizer & Co-Reference Engine (`schema_atomizer.py`)
Raw paragraphs cannot be evaluated as monolithic text blocks because true statements will "drown out" subtle false assertions.
* **5-Tuple Proposition Structure:**
  $$\mathcal{T} = \langle 	ext{Subject } (S), 	ext{Predicate } (P), 	ext{Object/Value } (O), 	ext{Temporal Scope } (T), 	ext{Epistemic Mode } (M) angle$$
* **Anaphoric Pronoun Resolution:** Resolves ambiguous pronouns (`she, he, it, they, his, her`) to the active paragraph subject (e.g. *"She won 3 Nobel Prizes"* $	o$ *"Marie Curie won 3 Nobel Prizes"*).
* **Compound Subject Preservation:** Prevents erroneous clause splitting on compound entity conjunctions (e.g., *"John Cena and Roman Reigns are rivals"* remains a single atomic assertion).

---

### 🚦 Stage 2: Modality Taxonomy Router
Categorizes propositions into 5 mutually exclusive operational modalities:
1. **`QUANTITATIVE`:** Numerical magnitudes, scientific SI units, percentages, financial currencies, ratios.
2. **`TEMPORAL`:** Birth/death years, founding/dissolution dates, presidential tenures, active vs. expired roles.
3. **`ENTITY_ATTRIBUTE`:** Canonical ontological properties (country capitals, chemical formulas, parents, awards).
4. **`CITATION`:** Academic paper titles, authors, journal names, publication years, DOI strings.
5. **`RELATIONAL`:** Open-domain multi-entity semantic associations.

---

### ⚙️ Stage 3: Specialized Symbolic Verifier Engines

#### A. Dimensional Quantity & SI Unit Normalizer (`dimensional_quantity_engine.py`)
* Converts non-standard units to SI base units before arithmetic comparison:
  * **Temperature:** Kelvin ($K$), Celsius ($^\circ C$), Fahrenheit ($^\circ F$)
  * **Length & Elevation:** Meters ($m$), Kilometers ($km$), Feet ($ft$), Miles ($mi$)
  * **Digital Units:** Transistors, Bits, Bytes, Terabytes, Qubits
* Implements calibrated relative tolerance:
  $$	ext{Relative Error } \epsilon = rac{|V_{	ext{claimed}} - V_{	ext{grounded}}|}{V_{	ext{grounded}}} \le 	au \quad (	au = 0.05 	ext{ for general, } 0.01 	ext{ for physical constants})$$

#### B. Temporal State Transition Guard (`temporal_ea_verifier.py`)
* Enforces grammatical tense invariants:
  * Present tense assertions (*"is the captain", "is the president"*) require active ongoing status ($	ext{End Date} = 	ext{None}$).
  * If canonical evidence documents $	ext{End Date} < 	ext{Current Year}$, flags **`❌ FALSE (Expired Tenure Contradiction)`**.

#### C. Live Open Data REST Registries
* **Macroeconomics:** World Bank OData REST API for dynamic GDP, population, inflation time-series.
* **Bibliographic Citations:** CrossRef REST API for exact DOI resolution and author-title attribution.
* **Knowledge Graphs:** Wikidata SPARQL query endpoint with Sitename tie-breaking and bidirectional superlative resolution.

---

### ⚖️ Stage 4: 3-Valued Epistemic Logic (Open-World Assumption)
HalDetect enforces 3-valued truth semantics:
* **`✅ TRUE`:** Positively grounded by exact symbolic calculation or authoritative triple match (Confidence $\ge 85\%$).
* **`❌ FALSE`:** Explicit counter-factual or physical contradiction detected (Confidence $\ge 90\%$).
* **`⚠️ UNVERIFIABLE`:** Claim asserts an unmentioned, out-of-scope, or speculative relationship without canonical refutation (Confidence $\le 40\%$).

---

### 📊 Stage 5: Response Factuality Synthesis (Chapter 6 Matrix)
For multi-sentence paragraphs, computes:
* **Response Factuality Index (RFI):**
  $$	ext{RFI} = rac{N_{	ext{TRUE}}}{N_{	ext{Total}}} 	imes 100\%$$
* **Response Hallucination Rate (RHR):**
  $$	ext{RHR} = rac{N_{	ext{FALSE}}}{N_{	ext{Total}}} 	imes 100\%$$
