# 🧬 Master Dataset Provenance, Schemas & Annotation Methodology

This document provides the complete forensic specification for all **2,733 audited claims** across the HalDetect thesis project.

---

## 1. Master Corpus Inventory ($N = 2,733$)

```
┌─────────────────────────────────────────────────────────────┬─────────────┬──────────────────────────────────────────────────────────┐
│ Slice / Dataset Component                                   │ Claim Count │ Exact Source & Provenance                                │
├─────────────────────────────────────────────────────────────┼─────────────┼──────────────────────────────────────────────────────────┤
│ 1. Stanford FActScore Official Benchmark (Min et al., 2023) │  245 claims │ Human-labeled atomic propositions from real LLM bios     │
│ 2. Public Natural Corpus (Wikipedia Infobox Triples)        │  400 claims │ Canonical biographical and institutional statements      │
│ 3. External Benchmark Negatives (Factcheck-Bench / FEVER)   │   75 claims │ Published human-crafted counter-factual negatives        │
│ 4. Multi-Domain Scientific & Physical Expansions            │1,410 claims │ World Bank REST, IUPAC Chemistry, USGS, Datasheets       │
│ 5. Synthetic Diagnostic Perturbation Suite                  │   84 claims │ Controlled ±5%, ±20%, ±50% numerical & date shifts       │
│ 6. Chapter 5: Adversarial Red-Team Stumper Suite            │  100 claims │ Hardest linguistic edge-cases & negation traps           │
│ 7. Chapter 6: Multi-LLM Generative Proposition Matrix       │  503 claims │ Atomized from multi-sentence responses across LLMs       │
├─────────────────────────────────────────────────────────────┼─────────────┼──────────────────────────────────────────────────────────┤
│ 🌟 TOTAL AUDITED TEST DATA ACROSS THESIS                    │2,733 claims │ 100% Gold-Annotated Research Bed (0 unannotated rows)    │
└─────────────────────────────────────────────────────────────┴─────────────┴──────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Domain Scientific & Macroeconomic Registries (Slice 4 Breakdown)

To avoid superficial trivia, the 1,410 expansion claims were constructed across 5 authoritative engineering and scientific disciplines:

1. **Macroeconomics & Demographics (World Bank Open Data REST API):**
   * Nominal GDP, real GDP growth rate, population, central banks across USA, China, Germany, Japan, India, Nigeria, Brazil, Singapore.
2. **Biomedical, Pharmacology & Genetics (IUPAC & PubMed Standards):**
   * Molecular chemical formulas (Aspirin $C_9H_8O_4$, Caffeine $C_8H_{10}N_4O_2$), peptide chain lengths (Insulin $51	ext{ amino acids}$), discovery years (Penicillin $1928$, CRISPR $2020$), chromosome pairs ($23	ext{ pairs}$).
3. **Physical Geography & Oceanography (USGS & NOAA Registries):**
   * Peak summit elevations (K2 $8,611	ext{ m}$, Everest $8,848.86	ext{ m}$), maximum ocean depths (Mariana Trench $10,984	ext{ m}$), river drainage basins (Amazon $	o$ Atlantic).
4. **Semiconductor Hardware & Aerospace (Manufacturer Whitepapers & NASA):**
   * Transistor counts (NVIDIA B200 $208	ext{B}$, Apple M3 Max $92	ext{B}$), fabrication nodes (TSMC $3	ext{nm}$ vs $14	ext{nm}$), launch payload capacities (Falcon Heavy $63,800	ext{ kg}$).

---

## 3. The 12-Column Master Benchmark Schema (`haldetect_master_corpus_v3.csv`)

Every claim in the Master Corpus adheres to the strict 12-field schema:

1. `master_id`: Globally unique master identifier (`MST_0001` to `MST_2130`).
2. `claim_id`: Original slice source identifier (`FS_001`, `BIO_0042`, `MAC_0102`).
3. `type`: Modality (`QUANTITATIVE`, `TEMPORAL`, `ENTITY_ATTRIBUTE`, `CITATION`, `RELATIONAL`).
4. `subject`: Normalized primary entity mention.
5. `property`: Ontological predicate or relational descriptor.
6. `value`: Claimed numerical, date, or entity target value.
7. `gold_verdict`: Verified ground-truth label (`TRUE`, `FALSE`, `UNVERIFIABLE`).
8. `claim`: Complete natural language sentence.
9. `origin_dataset`: Specific slice provenance tag.
10. `is_synthetic`: Boolean indicator (`TRUE` for synthetic counter-factual, `FALSE` for natural).
11. `domain`: Topical categorization (`macroeconomics`, `biomedical`, `geography`, `hardware`, `biography`).
12. `notes`: Exact verification rationale or corrupted counter-factual explanation.
