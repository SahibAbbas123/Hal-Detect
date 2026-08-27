# HalDetect: Taxonomy-Routed Neuro-Symbolic Hallucination Detection for LLMs

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Kaggle GPU Ready](https://img.shields.io/badge/Kaggle-Dual%20T4%20GPU-blue)](https://www.kaggle.com/)
[![Benchmark Claims](https://img.shields.io/badge/Corpus-1%2C005%20Claims-green.svg)](current/haldetect_master_corpus_v2.csv)

**HalDetect** is an open-source, ultra-low latency (<25ms) **Neuro-Symbolic Fact-Verification Engine** designed to detect factual hallucinations in Large Language Model (LLM) outputs. 

Instead of relying on monolithic, expensive, and hallucination-prone "LLM self-checking" or uncalibrated uniform NLI, HalDetect decomposes natural language assertions into a **5-modality taxonomy** and routes them to specialized symbolic registries (Wikidata SPARQL, World Bank Open Data REST API, CrossRef DOI registry) with hybrid text NLI fallthrough.

---

## 🌟 Key Architecture & Findings

```
                               ┌─────────────────────────────┐
                               │  LLM-Generated Assertion    │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
                        ┌───────────────────────────────────────────┐
                        │      5-Modality Taxonomy Router           │
                        └─────┬───────┬───────┬───────┬───────┬─────┘
                              │       │       │       │       │
       ┌──────────────────────┘       │       │       │       └──────────────────────┐
       ▼                              ▼       ▼       ▼                              ▼
┌──────────────┐              ┌──────────────┐ ┌──────────────┐              ┌──────────────┐
│ QUANTITATIVE │              │   TEMPORAL   │ │ ENTITY_ATTR  │              │  RELATIONAL  │
│ Extract &    │              │ Wikidata P569│ │ Instance-of  │              │ Wikipedia    │
│ Compare (WB) │              │ Date Clusters│ │ Guard (P31)  │              │ Hybrid NLI   │
└──────┬───────┘              └──────┬───────┘ └──────┬───────┘              └──────┬───────┘
       │                             │                │                             │
       ▼                             ▼                ▼                             ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│     Deterministic Decision Engine: TRUE / FALSE / Calibrated UNVERIFIABLE Abstention      │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### 📊 Master 4-Way Paradigm Benchmark ($N = 1,005$ Claims)

| Verification System | Coverage | Selective Accuracy [95% CI] | Precision (TRUE) | Precision (FALSE) | Latency / Claim |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 🏆 **HalDetect (Ours)** | **39.3%** | **77.7% [73.4%, 81.5%]** | **90.9%** | **56.9%** | **22.4 ms** |
| 🤖 **Web-Search RAG (BART)** | **3.2%** | **59.4% [42.3%, 74.5%]** | **66.7%** | **58.6%** | **221.1 ms** |
| ⚡ **Uniform DeBERTa-v3** | **79.0%** | **51.6% [48.1%, 55.1%]** | **50.7%** | **64.8%** | **42.1 ms** |
| 🧠 **Uniform MiniCheck (SOTA '24)** | **99.1%** | **51.2% [48.1%, 54.3%]** | **53.7%** | **42.7%** | **67.8 ms** |

---

## 🚀 Quickstart Guide

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-username/HalDetect.git
cd HalDetect

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Live Interactive Fact-Checking
Verify any custom assertion in **<25 milliseconds**:
```bash
# Single query mode:
python current/verify_live.py "The nominal GDP of the United States reached 27.8 trillion dollars in 2023."

# Interactive REPL mode:
python current/verify_live.py
```

### 3. Run Full Benchmark Evaluation ($N = 1,005$)
```bash
# Run full evaluation across the 1,005-claim Master Corpus
python current/evaluate_master_corpus.py

# Run Master Ablation Suite (Routing, Tiers, Tolerances)
python current/ablation_suite.py

# Generate Publication Plots (300 DPI)
python current/generate_publication_plots.py
```

---

## ☁️ Running MiniCheck-7B on Kaggle (Free GPU)

We provide a self-contained one-click notebook ready for Kaggle / Colab:
1. Upload [`current/haldetect_minicheck7b_kaggle.ipynb`](current/haldetect_minicheck7b_kaggle.ipynb) to [kaggle.com/code](https://www.kaggle.com/code).
2. Attach GPU (`GPU T4 x2` or `P100`) and toggle `Internet: ON`.
3. Add [`current/kaggle_minicheck_input_claims.csv`](current/kaggle_minicheck_input_claims.csv) to input.
4. Click **"Run All"** to batch-score all 1,005 claims in **<90 seconds**!

---

## 📁 Repository Structure

```
.
├── current/
│   ├── verify_live.py                     # Live interactive CLI verifier
│   ├── quantitative_verifier.py           # Quantitative Tier 1 Extract-and-Compare
│   ├── quantitative_tier2_verifier.py     # Quantitative Tier 2 World Bank REST API
│   ├── temporal_ea_verifier.py            # Temporal & Entity Attribute Verifier
│   ├── citation_l1b_verifier.py           # Citation L1/L1b Registry Verifier
│   ├── hybrid_fallthrough.py              # Tier 2 Wikipedia + NLI Fallthrough
│   ├── evaluate_master_corpus.py          # Master 1,005 evaluation runner
│   ├── ablation_suite.py                  # Full ablation decomposition suite
│   ├── haldetect_master_corpus_v2.csv     # 1,005 Master Benchmark Dataset
│   └── haldetect_minicheck7b_kaggle.ipynb # Ready-to-run Kaggle GPU Notebook
├── README.md                              # Main documentation
└── requirements.txt                       # Minimal pinned dependencies
```

---

## 📜 Citation & Academic Context

If you use this codebase or benchmark in your research, please cite:
```bibtex
@mastersthesis{chowdhury2026haldetect,
  author  = {Sahib Ab Chowdhury},
  title   = {HalDetect: Taxonomy-Routed Neuro-Symbolic Verification for Post-Hoc LLM Hallucination Detection},
  school  = {University of Chittagong, Department of Computer Science & Engineering},
  year    = {2026}
}
```
