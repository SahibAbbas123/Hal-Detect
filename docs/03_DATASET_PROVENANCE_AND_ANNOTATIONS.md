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

## 2. Deep "WHY" Behind Dataset Construction Choices

### • WHY did we mix human benchmarks (FActScore) with scientific registries (World Bank, IUPAC)?
> **Avoiding Benchmark Overfitting:**  
> If an evaluation uses only one dataset (e.g. only Wikipedia infoboxes), the system overfits to the linguistic style of Wikipedia editors.  
> By triangulating between:
> 1. Human-annotated conversational biographies (Stanford FActScore),
> 2. Structured macroeconomic tables (World Bank),
> 3. Hard physical/biochemical constants (IUPAC, USGS), and
> 4. Raw generative LLM paragraphs (Qwen, Mistral, DeepSeek),  
> we guarantee that HalDetect's accuracy reflects true open-world generalizability.

### • WHY did we create high-entropy counter-factual negatives?
> **Testing Specific Failure Modes:**  
> Randomly generated negative claims (e.g. *"Albert Einstein is an airplane"*) are trivial for any system to reject.  
> Real-world LLM hallucinations are **subtle, high-entropy errors**:
> * Corrupting $51$ amino acids to $150$ (Confusing insulin with proinsulin).
> * Corrupting $3	ext{nm}$ to $14	ext{nm}$ (Confusing modern TSMC node with legacy node).
> * Corrupting $8,611	ext{ m}$ to $9,100	ext{ m}$ (Asserting a non-existent elevation exceeding Mount Everest).  
> These hard negatives force the verifier to prove its arithmetic and categorical discrimination power.

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
