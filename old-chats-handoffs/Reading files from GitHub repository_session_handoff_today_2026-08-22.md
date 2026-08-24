# FActScore-priv — Session Handoff (Today, 2026-08-22)

> Chat name: Reading files from GitHub repository

_Read this first. Everything below assumes no prior context._

---

## What This Project Is

An exploration of the **FActScore-priv** GitHub repository (github.com/SahibAbbas123/FActScore-priv.git), a factuality-evaluation dataset for LLM-generated biographies, built on the FActScore benchmark (arXiv:2305.14251) and referencing FEVER (arXiv:1803.05355) for methodological comparison.

**Core content:** the repo contains labeled data (183 entries × 3 models, human-verified atomic facts), unlabeled data (500 entries × 11 models, no annotations), and prediction outputs (12 models, automated S/NS labels from two retrieval-verifier systems). The session's job was to explain the repo's structure and answer a detailed methodology Q&A grounded in both the repo's actual JSONL contents and the two source papers.

---

## A. What Happened This Session, In Order

1. User linked the repo and asked whether Claude could read it, especially the JSONL files.
2. Claude cloned the repo directly in its environment (couldn't fetch it as a normal URL) and ran commands to inventory the file structure.
3. Produced a full breakdown: `data/labeled/` (3 models × 183 entries with `annotations`), `data/unlabeled/` (11 models × 500 entries, no annotations), `factscore-unlabeled-predictions/` (12 models, `facts` + `ChatGPT_Labels` + `LLAMA+NP_Labels`), and `prompt_entities.txt`.
4. User uploaded `ChatGPT.jsonl` (from the predictions folder) and asked nine specific methodology questions, citing both papers directly.
5. Claude fetched both papers (FActScore, FEVER) and re-examined the uploaded file's actual contents before answering, rather than relying on general recall.
6. Answered all nine questions in order — see Section C below for the substantive findings, not just the file inventory.
7. Flagged one open methodological concern proactively: InstructGPT was used both to help generate some biographies and to auto-atomize facts, raising a possible circularity/bias question the user hadn't asked about yet.

---

## B. Current File State

| File | Source | Status | Notes |
|---|---|---|---|
| `data/labeled/ChatGPT.jsonl`, `InstructGPT.jsonl`, `PerplexityAI.jsonl` | Repo, cloned | Confirmed | 183 entries each; full annotation objects with human + model atomic facts. |
| `data/unlabeled/*.jsonl` (11 models) | Repo, cloned | Confirmed | 500 entries each; `input`/`output`/`topic`/`cat` only, no annotations. |
| `factscore-unlabeled-predictions/*.jsonl` (12 models) | Repo, cloned | Confirmed | 421–500 entries each; `facts`, `prompt`, `ChatGPT_Labels`, `LLAMA+NP_Labels`. |
| `prompt_entities.txt` | Repo, cloned | Confirmed | List of person names used as prompts. |
| Uploaded `ChatGPT.jsonl` (predictions folder) | User upload, this session | Analyzed | 421 entries; only 86 have `ChatGPT_Labels`, all 421 have `LLAMA+NP_Labels`. Explains the <500 count (model abstention, ~14.2% of runs). |
| FActScore paper (arXiv:2305.14251) | Fetched this session | Read | Used to answer atomization/verification, retrieval-verifier design, and error-rate questions. |
| FEVER paper (arXiv:1803.05355) | Fetched this session | Read | Used only for the training-comparison question (Q2); confirms FEVER trained a retrieval + RTE pipeline, FActScore did not train anything. |

**Golden rule:** the labeled dataset's `human-atomic-facts` field is the only ground-truth signal in the repo — `model-atomic-facts` and both prediction label columns are automated and should not be treated as verified.

---

## C. Key Findings — Ranked by Relevance to Follow-up Work

1. **Atomization/verification is a two-phase hybrid, not uniform across the repo.** Labeled data = AI-assisted atomization (InstructGPT draft, human-corrected) + fully human verification. Unlabeled/predictions data = fully automated atomization and verification via retrieval + zero-shot LM judgment, with <2% reported error rate.

2. **FActScore trained nothing; FEVER did.** FEVER's whole purpose was building a dataset to train retrieval + textual-entailment models (they used an MLP over TF-IDF, plus a SOTA RTE model). FActScore only does zero-shot prompting of existing LMs (LM_EVAL, comparing P("True") vs P("False")) — no fine-tuning anywhere in the pipeline.

3. **The hallucination-in-the-verifier concern is mitigated, not eliminated, by retrieval grounding.** The best-performing verifier setup retrieves Wikipedia passages first, then asks the LM to judge the atomic fact against that fixed context — closer to reading comprehension than free recall. The no-context baseline (no retrieval) performs measurably worse, confirming retrieval grounding is doing real work. Residual error (<2%) remains and is not fully eliminated.

4. **The 421-vs-500 entry count in the uploaded predictions file is explained by model abstention, not arbitrary filtering.** ChatGPT abstained ~14.2% of the time on the original 500 prompts; the gap between the ~429 expected and 421 actual likely comes from additional malformed-output filtering. This is not a bug — it reflects real generation refusals.

5. **The `cat` field is two-dimensional (rarity + region), and it matters for score interpretation.** Rarity (very freq → very rare) is estimated from Wikipedia page-view/mention frequency and is strongly correlated with factuality — ChatGPT's FActScore reportedly drops from ~80% on frequent entities to ~16% on very rare ones. Any downstream analysis of this repo's data should stratify by rarity before comparing models.

6. **`is-relevant` is a sentence-level filter, distinct from fact-level `S`/`NS`/`IR` labels.** Irrelevant sentences (off-topic, or downstream of an earlier hallucinated claim) are excluded from FActScore entirely rather than penalized — important if reproducing the scoring formula from raw JSONL.

---

## D. Open Decisions — NOT YET MADE

- **Circularity question raised but not investigated:** InstructGPT was used both as a generation source and as the automated fact-atomizer. Whether this introduces bias into the labeled dataset's `model-atomic-facts` field vs. `human-atomic-facts` field has not been checked.
- **No downstream analysis has been run yet** — Claude offered (in the first turn) to compare factuality scores across models or examine which topics have the most hallucinations; this was not taken up.
- **The `LLAMA+NP` "NP" abbreviation was inferred, not confirmed against the paper text** — Claude labeled it as likely "non-parametric" retrieval but flagged this as an inference, not a confirmed reading. Worth verifying directly against the paper if it matters for later work.

---

## E. Standing Methodological Commitments

- Distinguish clearly between human-verified fields (`human-atomic-facts` labels) and automated/predicted fields (`model-atomic-facts`, `ChatGPT_Labels`, `LLAMA+NP_Labels`) in any future analysis — they are not interchangeable ground truth.
- When answering questions about this repo, ground claims in the actual fetched papers and actual JSONL contents rather than general recall of FActScore/FEVER methodology.
- Flag entity rarity (`cat` field) as a required stratification variable before making any cross-model factuality comparisons.

---

## F. What to Actually Do Next

1. **Investigate the InstructGPT circularity concern** — check whether atomization bias differs when InstructGPT is atomizing its own generations vs. other models' generations.
2. **Confirm the "NP" abbreviation** in LLAMA+NP directly against the FActScore paper text rather than relying on the inferred reading.
3. **Run a downstream analysis** if desired — e.g., factuality by rarity tier, or S/NS agreement rate between the ChatGPT and LLAMA+NP verifier systems on the 86 entries that have both.
4. **If further work touches other repo files** (unlabeled sets, other prediction files), re-verify entry counts and field structure per-file rather than assuming uniformity — the predictions folder already showed count and field variation between models.

Priority: 1 > 3 > 2 > 4.

---

## Key Files to Have for Context

- The exported chat itself: `Claude-Reading files from GitHub repository-20260822-1917.md`.
- Uploaded `ChatGPT.jsonl` (predictions folder, 421 entries) — the file the 9-question methodology Q&A was answered against.
- FActScore paper (arXiv:2305.14251) and FEVER paper (arXiv:1803.05355) — both fetched and cited during this session; re-fetch if precise section numbers are needed later.

---

## Tone Note

This was a **reference/comprehension session**, not a build session — no code was fixed, no pipeline was run, no bugs were found in the repo itself. The value produced is a verified, paper-grounded methodology explanation the user can build on. Nothing here is broken or blocked; the "next steps" are optional deepening, not fixes to prerequisites.
