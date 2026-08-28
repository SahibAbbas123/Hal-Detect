# 🗺️ Strategic Execution Roadmap: Track 1, Track 2 & Engineering Tasks

This document outlines the complete operational roadmap, technical task inventory, and defense presentation deliverables for HalDetect 2.0.

---

## 🛣️ 1. The Dual-Track Route to Defense

```
                        ┌──────────────────────────────────────────────┐
                        │          HALDETECT 2.0 THESIS SUITE          │
                        └──────────────────────────────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
        ┌─────────────────────────┐                           ┌─────────────────────────┐
        │ TRACK 1 (CHAPTER 4)     │                           │ TRACK 2 (CHAPTER 6)     │
        │ Master Benchmark N=2,130│                           │ Multi-LLM Live Matrix   │
        └─────────────────────────┘                           └─────────────────────────┘
                     │                                                     │
                     ▼                                                     ▼
        • 6 Domain Suites (FActScore,                         • 50 Multi-Domain Prompts
          Biomed, Geo, Macro, HW)                             • Live Generation across Qwen,
        • 4-Way Paradigm Comparison                             Mistral, DeepSeek, GLM-4
        • Ablation Hierarchy (Full vs                         • 5-Tuple Schema Atomization
          Semi vs Non-Routed vs RAG)                          • Response Factuality Index (RFI)
        • McNemar Chi-Squared & Wilson CIs                    • Latency & Cost Economy
                     │                                                     │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │ CHAPTER 5: ADVERSARIAL STUMPERS │
                               │ (100 Extreme Edge-Case Audits)  │
                               └─────────────────────────────────┘
                                                │
                                                ▼
                               ┌─────────────────────────────────┐
                               │ THESIS MANUSCRIPT & SLIDE DECK  │
                               │ (Chapters 4, 5, 6 + TikZ Deck)  │
                               └─────────────────────────────────┘
```

---

## 📋 2. Comprehensive Actionable Task Inventory

### Category A: Core Dataset & Benchmark Code Base (COMPLETED ✅)
* [x] **A.1 Master Benchmark Corpus v3.0 Assembly:** Scaled to $N = 2,130$ claims with 100% gold labels across 6 real-world domains.
* [x] **A.2 4-Way Comparative Paradigm Evaluation:** Ran HalDetect 2.0 ($97.44\%$), Semi-Routed ($78.15\%$), Non-Routed ($43.56\%$), and SOTA RAG ($64.11\%$).
* [x] **A.3 Formal Statistical Significance:** McNemar Paired Chi-Squared ($\chi^2 = 646.71, p < 10^{-100}$) and Wilson 95% Confidence Intervals.
* [x] **A.4 Publication Plot Generation:** High-resolution 300 DPI figures (`fig1` through `fig4`).
* [x] **A.5 Git Remote Sync:** Synced and pushed to GitHub branch `haldetect-v2-evolved`.

---

### Category B: Live Multi-LLM Benchmarking & Profiling (UPCOMING 🧪)
* [ ] **B.1 Live Ollama Foundation Model Matrix Run:**  
  * *Task:* Execute the 50 standardized prompts across local/cloud models (`gemma4:31b-cloud`, `minimax-m3:cloud`, `gpt-oss:120b-cloud`).
  * *Output:* Live 2026 Frontier Foundation Model Factuality Leaderboard computing $	ext{RFI}$ and caught hallucinations.
* [ ] **B.2 End-to-End Latency & Telemetry Profiler:**  
  * *Task:* Profile sub-millisecond CPU execution time, RAM footprint, and energy consumption ($	ext{Wh}$) of HalDetect 2.0 vs. local `Bespoke-MiniCheck-7B` vs. cloud APIs.

---

### Category C: Verifier Engine Fortification & Edge-Case Enhancements (UPCOMING ⚙️)
* [ ] **C.1 Multi-Hop Transitive Reasoning Prototype (2-Hop SPARQL):**  
  * *Task:* Implement a 2-hop graph traversal module for compound relational queries (e.g., *"The birthplace of the director of Inception"* $	o$ Christopher Nolan $	o$ London).
* [ ] **C.2 Nickname & Alias Lexicon Expansion:**  
  * *Task:* Integrate standard English nickname mappings (`Joe` $\leftrightarrow$ `Joseph`, `Bill` $\leftrightarrow$ `William`, `Bob` $\leftrightarrow$ `Robert`) into entity resolution.
* [ ] **C.3 Currency & PPP Macroeconomic Normalizer:**  
  * *Task:* Add historical exchange rates and Nominal vs. Purchasing Power Parity (PPP) GDP conversion logic to the World Bank verifier.

---

### Category D: Interactive Visualizations & Live Demo Tooling (UPCOMING 🎨)
* [ ] **D.1 Lightweight Local Web GUI (Streamlit / FastHTML):**  
  * *Task:* Build an interactive browser UI where an examiner can type any prompt, see live sentence atomization into colored 5-tuples, and view the real-time truth certificate.
* [ ] **D.2 High-Resolution Vector Architecture Layouts (TikZ & SVG):**  
  * *Task:* Generate standalone vector diagrams for the Grand Vision Architecture, Modality Routing Tree, and 5-Tuple Schema decomposition.

---

### Category E: Thesis Manuscript Writing (UPCOMING ✍️)
* [ ] **E.1 Chapter 4: Benchmark Methodology & Experimental Results:**  
  * *Sections:* Triangulated data provenance, 5-modality taxonomy, comparative benchmark tables, and McNemar statistical significance.
* [ ] **E.2 Chapter 5: Ablation Studies & Adversarial Red-Teaming:**  
  * *Sections:* Full vs Semi vs Non-Routed ablations, error taxonomy breakdown, and the 100 Stumper evaluation.
* [ ] **E.3 Chapter 6: End-to-End Generative Evaluation on Multi-LLM Outputs:**  
  * *Sections:* 50 prompt suite, paragraph atomization mechanics, Response Factuality Index (RFI) and Hallucination Rate (RHR) across foundation models.

---

### Category F: Defense Presentation Deliverables (FINAL 🎓)
* [ ] **F.1 Master Defense Slide Deck (15–20 Slides):** Markdown/Marp and LaTeX Beamer formats with high-impact visuals.
* [ ] **F.2 Presenter Speaking Notes & Timing Guide:** Slide-by-slide presenter script calibrated for a 20-minute oral defense.
* [ ] **F.3 Adversarial Defense Q&A Preparation Script:** Pre-formulated academic answers for the 15 toughest examiner questions.
