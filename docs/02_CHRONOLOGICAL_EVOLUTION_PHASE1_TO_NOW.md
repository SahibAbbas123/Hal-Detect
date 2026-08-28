# ⏳ Chronological Project Evolution: The Naive Mistakes, Breakthroughs & Paradigm Shifts

---

## 1. The 3 Epochs of HalDetect

```
┌───────────────────────────────────┬───────────────────────────────────┬───────────────────────────────────┐
│ EPOCH 1: Phase 1 (The Naive Start)│ EPOCH 2: Phase 2 (The Realization)│ EPOCH 3: HalDetect 2.0 (Evolved)  │
├───────────────────────────────────┼───────────────────────────────────┼───────────────────────────────────┤
│ • 356 claims (14 FALSE = 3.9%)    │ • 731 claims (287 FALSE = 39.3%)  │ • 2,130 claims (967 FALSE = 45.4%)│
│ • BART-MNLI (2019 cross-encoder)  │ • DeBERTa-v3 + Margin Filtering   │ • Dimensional SI + 5-Tuple Schema │
│ • Flat string matching            │ • Stanford FActScore Integration  │ • World Bank + CrossRef REST APIs │
│ • Binary True/False Closed-World  │ • SBERT Property Closures         │ • 3-Valued Open-World Logic       │
│ • 🚨 Fatal: 96% Class Imbalance   │ • 🚨 Fatal: Number Blindness      │ • 🏆 97.44% Accuracy, p < 0.0001  │
└───────────────────────────────────┴───────────────────────────────────┴───────────────────────────────────┘
```

---

## 2. Forensic Phase-by-Phase Breakdown: Why Each Move Happened

### 🚨 EPOCH 1: Phase 1 — The Naive Baseline & The 96% Imbalance Trap

#### • What was the initial setup?
* 356 natural claims scraped from Wikipedia infoboxes.
* Only **14 claims were labeled FALSE (a 3.9% negative base rate)**.
* Classification relied on BART-MNLI (a 2019 neural text entailment model) and basic unguided SPARQL queries.

#### • Where did we go wrong? (The Naive Mistake)
1. **The Degenerate Baseline Trap:** Because 96.1% of the dataset was TRUE, a stupid "Always-True" script that evaluated nothing achieved **96.1% accuracy**! High accuracy was an illusion caused by dataset poverty.
2. **BART-MNLI Entailment Bias:** When tested on a false claim like *"Marie Curie was not born in Poland"*, BART-MNLI saw `"Marie Curie"` and `"Poland"`, ignored the word `"not"`, and predicted `ENTAILMENT` (TRUE) with 94% confidence.
3. **SPARQL Crashes:** Unconstrained SPARQL lookups failed whenever a property name didn't match Wikidata's exact P-number label (e.g. searching for `"birth date"` instead of `"date of birth / P569"` returned 0 results).

---

### 🛠️ EPOCH 2: Phase 2 — Diagnostic Scaling & Modality Specialization

#### • Why did we make this pivot?
* We realized we could not defend a thesis where 96% of claims were TRUE.
* We scaled the corpus to **731 claims** by importing:
  * 100 human-annotated biographical facts from Stanford FActScore (Min et al., EMNLP 2023).
  * 75 hard adversarial counter-factuals from Tsinghua Factcheck-Bench and FEVER.
  * 84 synthetic diagnostic perturbations (altering numbers by ±5%, ±20%, ±50%).

#### • What breakthroughs occurred?
1. **Property Resolver (`property_resolver.py`):** Created SBERT vector similarity matching over Wikidata property alias sets with a 0.35 core-term guard.
2. **DeBERTa-v3 Upgrade:** Replaced 2019 BART with modern DeBERTa-v3 and calibrated margin thresholding ($	ext{Score}_{	ext{Entail}} - 	ext{Score}_{	ext{Contradict}} \ge 0.70$).
3. **Citation Verifier (`citation_l1b_verifier.py`):** Integrated live CrossRef REST API for exact DOI resolution.

#### • Where was the remaining loophole?
* The system was still **unit-blind** (e.g., treating $77	ext{ K}$ and $77	ext{ }^\circ	ext{C}$ as equal) and **compound-sentence blind** (evaluating multi-sentence paragraphs as a single flat string).

---

### 🏆 EPOCH 3: HalDetect 2.0 (Evolved) — The 2,130-Claim Frontier

#### • Why did we expand to 2,130 claims across 6 domains?
* To eliminate all remaining synthetic bias and test every physical, temporal, and mathematical point of failure.
* Added authoritative datasets from **World Bank (Macroeconomics)**, **IUPAC/PubMed (Biomedical)**, **USGS (Geography)**, and **Semiconductor Whitepapers (TSMC 3nm, NVIDIA B200)**.

#### • The Permanent Solutions Delivered:
1. **5-Tuple Schema Atomizer:** Paragraph decomposition with pronoun coreference resolution and compound subject preservation.
2. **Dimensional SI Quantity Engine:** Full algebraic unit conversion across temperature, length, speed, and transistor counts.
3. **Bidirectional Superlative Resolver:** Solved inverted extremes (*"Nile is the shortest river"* $	o$ caught as FALSE).
4. **Live Multi-LLM Factuality Dashboard:** Tested on actual generative outputs from Qwen 2.5, Mistral, and DeepSeek, computing live Response Factuality Index (RFI).
