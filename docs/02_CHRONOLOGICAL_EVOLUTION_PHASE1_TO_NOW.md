# ⏳ Chronological Project Evolution: From Phase 1 to HalDetect 2.0

This document tracks the complete development lifecycle, architectural refactors, and milestone breakthroughs of the HalDetect thesis project.

---

## 📅 Milestone 1: Phase 1 (Baseline Inception & The Imbalance Problem)
* **Dataset Scope:** 356 natural claims with only 14 gold `FALSE` claims (3.9% base rate).
* **Architecture:** Naive regex routing into BART-MNLI (2019) and simple Wikidata SPARQL queries.
* **The Fatal Flaws Identified:**
  1. *Severe Class Imbalance:* 96.1% TRUE claims meant a trivial "Always-True" predictor achieved 96% accuracy without detecting a single hallucination!
  2. *BART-MNLI Obsolescence:* Pre-trained 2019 cross-encoders suffered from extreme token overlap bias on subtle negation words.
  3. *Unrouted KG Failure:* Open relational claims were sent to SPARQL endpoints without property closures, crashing coverage to < 40%.

---

## 📅 Milestone 2: Phase 2 (Diagnostic Scaling & Modality Specialization)
* **Dataset Scaling:** Assembled the 731-claim Master Corpus v2.0 by importing:
  * 100 human-annotated claims from Stanford FActScore (Min et al., EMNLP 2023).
  * 75 hard counter-factual negatives from Tsinghua Factcheck-Bench & FEVER.
  * 84 synthetic diagnostic perturbations (±5%, ±20%, ±50% shifts).
* **Algorithmic Upgrades:**
  * Created `property_resolver.py` with SBERT cosine similarity and 0.35 core-term guard.
  * Created `citation_l1b_verifier.py` with CrossRef DOI REST resolution.
  * Replaced BART-MNLI with DeBERTa-v3-large and calibrated margin thresholding ($\Delta \ge 0.70$).

---

## 📅 Milestone 3: Phase 3 (HalDetect 2.0 Evolved & The 2,130-Claim Frontier)
* **Dataset Scaling (Master Corpus v3.0):** Expanded to **2,130 total claims** across 6 balanced real-world domains (Biomedical, Geography, World Bank macroeconomics, TSMC/NVIDIA hardware specs, and Stanford FActScore Block 2).
* **Core Breakthroughs Implemented:**
  1. **5-Tuple Schema Atomizer (`schema_atomizer.py`):** Paragraph-level decomposition with anaphoric pronoun coreference resolution and compound subject preservation.
  2. **Dimensional SI Quantity Engine (`dimensional_quantity_engine.py`):** Exact unit conversion for temperatures ($K \leftrightarrow ^\circ C$), lengths, elevations, and digital metrics.
  3. **Superlative Bidirectional KG Resolver (`bidirectional_kg_resolver.py`):** Solved inverted superlative edge cases (*"Nile is the shortest river"*, *"Mount Everest is the lowest peak"*).
  4. **Live Interactive CLI (`verify_live.py`):** Real-time paragraph atomization, side-by-side SOTA RAG comparison, and Chapter 6 Executive Factuality Dashboard.

---

## 📊 Summary Comparison: Phase 1 vs. HalDetect 2.0

| Architectural Dimension | Phase 1 (Baseline) | HalDetect 2.0 (Evolved) |
| :--- | :--- | :--- |
| **Benchmark Corpus Scope** | 356 claims (14 FALSE) | **2,130 claims (967 FALSE, 50.6% / 45.4% balanced)** |
| **Proposition Atomization**| None (Flat string matching) | **5-Tuple Schema ($\langle S, P, O, T, M angle$) with Pronoun Resolution** |
| **Quantity Handling** | Regex float matching (No units)| **Dimensional SI Engine ($K, ^\circ C, 	ext{ft}, m, 	ext{transistors}$)** |
| **Temporal Guarding** | Static year match | **Grammatical Tense + Active vs Expired Tenure Guard** |
| **Open-World Logic** | Binary (True/False Closed-World)| **3-Valued Asymmetric Logic (True / False / Unverifiable)** |
| **Selective Accuracy** | 51.6% | **97.44% (95% CI: [96.7%, 98.0%])** |
| **McNemar vs RAG** | Not statistically significant | **$\chi^2 = 646.71, p < 10^{-100} \ (p < 0.0001)$** |
