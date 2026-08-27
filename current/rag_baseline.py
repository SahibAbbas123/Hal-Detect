#!/usr/bin/env python3
"""
HalDetect -- Web-Search RAG Baseline (Track B)
==============================================
Standard Search-Augmented Generation / Fact Verification Baseline (RQ3).

Pipeline Architecture:
  1. Claim / Structured Fields -> Disambiguated Search Query
  2. Query -> Wikipedia Full-Text MediaWiki API (action=query&list=search)
  3. Titles -> Plain-Text Extract (action=query&prop=extracts&explaintext=1)
  4. Text -> Paragraph & Sentence-level Passage Chunks
  5. Chunks -> SBERT Dense Retrieval Ranking (all-MiniLM-L6-v2)
  6. Top-k Passages -> BART-MNLI (facebook/bart-large-mnli) on Apple Silicon MPS / GPU
  7. Margin-Calibrated Thresholding -> TRUE / FALSE / UNVERIFIABLE
  8. Statistical Scoring & Cross-Modality Comparison vs HalDetect Router

Caching:
  Deterministic cache saved to `current/rag_search_cache.json` seeded from
  historical retrieval and NLI caches.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import torch

# ---------------------------------------------------------------------------
# CONFIGURATION & HYPERPARAMETERS
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
CORPUS_PATH = HERE / "haldetect_master_corpus_v2.csv"
CACHE_PATH = HERE / "rag_search_cache.json"
RESULTS_PATH = HERE / "rag_baseline_evaluation_results.csv"

CACHE_SEEDS = [
    HERE / "nonrouted_cache.json",
    HERE / "relational_retrieval_cache.json",
    HERE / "relational_nli_cache.json",
]

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "HalDetectResearchBot/1.0 (academic-thesis; fact-verification-benchmark)"
HEADERS = {"User-Agent": USER_AGENT}

SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
NLI_MODEL_NAME = "facebook/bart-large-mnli"

TOP_K = 2
MIN_PASSAGE_SCORE = 0.38
MAX_PASSAGE_CHARS = 1200

ENTAIL_THRESHOLD = 0.50
CONTRADICT_THRESHOLD = 0.40
MIN_MARGIN = 0.15

# Lazy globals
_sbert_model = None
_nli_model = None
_nli_tokenizer = None
_device = None
_http_session = None


def get_http_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.headers.update(HEADERS)
    return _http_session


def get_device() -> torch.device:
    global _device
    if _device is None:
        if torch.backends.mps.is_available():
            _device = torch.device("mps")
        elif torch.cuda.is_available():
            _device = torch.device("cuda")
        else:
            _device = torch.device("cpu")
    return _device


# ---------------------------------------------------------------------------
# CACHE SYSTEM
# ---------------------------------------------------------------------------
def load_cache() -> dict:
    cache = {}
    for seed_path in CACHE_SEEDS:
        if seed_path.exists():
            try:
                with open(seed_path, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)
                    for k, v in seed_data.items():
                        if k not in cache:
                            cache[k] = v
            except Exception:
                pass

    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cache.update(saved)
        except Exception:
            pass
    return cache


def save_cache(cache: dict) -> None:
    clean_cache = {k: v for k, v in cache.items() if isinstance(v, (str, int, float, list, dict, bool))}
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_cache, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# MODEL LOADERS
# ---------------------------------------------------------------------------
def get_sbert():
    global _sbert_model
    if _sbert_model is None:
        from sentence_transformers import SentenceTransformer
        _sbert_model = SentenceTransformer(SBERT_MODEL_NAME, device=str(get_device()))
    return _sbert_model


def get_nli():
    global _nli_model, _nli_tokenizer
    if _nli_model is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        dev = get_device()
        print(f"Loading {NLI_MODEL_NAME} onto {dev}...", flush=True)
        _nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
        _nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME).to(dev)
        _nli_model.eval()
        print("BART NLI model ready.")
    return _nli_model, _nli_tokenizer


# ---------------------------------------------------------------------------
# QUERY FORMULATION & NORMALIZATION
# ---------------------------------------------------------------------------
def formulate_query(claim_row: dict) -> str:
    subject = (claim_row.get("subject") or "").strip()
    prop = (claim_row.get("property") or "").strip()
    claim = (claim_row.get("claim") or "").strip()

    if subject and len(subject) >= 3:
        if subject.lower() not in {"he", "she", "it", "they", "this", "that"}:
            if prop and len(prop) >= 3 and not prop.startswith("P"):
                return f"{subject} {prop}"
            return subject

    cleaned = re.sub(r"^(as recognized by the [a-z]+,?|in \d{4},?|according to [^,]+,?)", "", claim, flags=re.IGNORECASE).strip()
    words = [w for w in cleaned.split() if w.lower() not in {"the", "a", "an", "is", "was", "are", "were", "of", "in", "by", "for", "to"}]
    return " ".join(words[:6]) if words else claim[:50]


# ---------------------------------------------------------------------------
# RETRIEVAL & PASSAGE EXTRACTION
# ---------------------------------------------------------------------------
def search_wikipedia_titles(query: str, cache: dict, max_titles: int = 2) -> list[str]:
    cache_key = f"titles__{query.lower().replace(' ', '_')}__{max_titles}"
    if cache_key in cache:
        return cache[cache_key]

    session = get_http_session()
    try:
        r = session.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_titles,
                "format": "json"
            },
            timeout=6
        )
        r.raise_for_status()
        items = r.json().get("query", {}).get("search", [])
        titles = [item["title"] for item in items if "title" in item]
        cache[cache_key] = titles
        return titles
    except Exception:
        return []


def fetch_wikipedia_text(title: str, cache: dict) -> str:
    cache_key = f"text__{title.lower().replace(' ', '_')}"
    if cache_key in cache:
        return cache[cache_key]

    session = get_http_session()
    try:
        r = session.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "titles": title,
                "format": "json"
            },
            timeout=8
        )
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        for p in pages.values():
            text = p.get("extract", "")
            if text:
                cache[cache_key] = text
                return text
    except Exception:
        pass
    return ""


def extract_passages(text: str, max_chars: int = MAX_PASSAGE_CHARS) -> list[str]:
    if not text:
        return []
    passages = []
    sections = text.split("\n\n")
    for sec in sections:
        lines = [line.strip() for line in sec.split("\n") if line.strip()]
        for line in lines:
            if line.startswith("==") and line.endswith("=="):
                continue
            if len(line) < 40:
                continue
            if len(line) > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", line)
                curr = ""
                for s in sentences:
                    if len(curr) + len(s) < max_chars:
                        curr = f"{curr} {s}".strip()
                    else:
                        if len(curr) >= 40:
                            passages.append(curr)
                        curr = s
                if len(curr) >= 40:
                    passages.append(curr)
            else:
                passages.append(line)
    return passages


def rank_passages(claim: str, passages: list[str], top_k: int = TOP_K) -> list[tuple[str, float]]:
    if not passages:
        return []
    from sentence_transformers import util
    model = get_sbert()
    
    candidate_passages = passages[:40]
    claim_emb = model.encode(claim, convert_to_tensor=True)
    passage_embs = model.encode(candidate_passages, convert_to_tensor=True)
    cos_scores = util.cos_sim(claim_emb, passage_embs)[0]

    ranked = sorted(zip(candidate_passages, cos_scores.tolist()), key=lambda x: x[1], reverse=True)
    return [(p, score) for p, score in ranked[:top_k] if score >= MIN_PASSAGE_SCORE]


# ---------------------------------------------------------------------------
# NLI INFERENCE & DECISION RULE (BART-MNLI on MPS)
# ---------------------------------------------------------------------------
def run_nli_verification(claim: str, ranked_passages: list[tuple[str, float]], cache: dict) -> dict:
    if not ranked_passages:
        return {
            "verdict": "UNVERIFIABLE",
            "confidence": 0.30,
            "entail_prob": 0.0,
            "contradict_prob": 0.0,
            "neutral_prob": 1.0,
            "best_evidence": "No relevant passage retrieved from Wikipedia search.",
            "top_passage_score": 0.0,
        }

    model, tok = get_nli()
    dev = get_device()

    best_entail = 0.0
    best_contradict = 0.0
    best_evidence = ""
    top_sim = ranked_passages[0][1]

    for passage, sim_score in ranked_passages:
        passage_snippet = passage[:MAX_PASSAGE_CHARS]
        cache_key = f"nli__{claim[:60].replace(' ', '_')}__{passage_snippet[:40].replace(' ', '_')}"
        if cache_key in cache:
            scores = cache[cache_key]
            entail = float(scores.get("entail", 0.0))
            contradict = float(scores.get("contradict", 0.0))
        else:
            try:
                inputs = tok(passage_snippet, claim, return_tensors="pt", truncation=True, max_length=512).to(dev)
                with torch.no_grad():
                    logits = model(**inputs).logits
                    probs = torch.softmax(logits, dim=-1)[0]
                contradict = float(probs[0].item())
                entail = float(probs[2].item())
                cache[cache_key] = {"entail": entail, "contradict": contradict}
            except Exception as e:
                continue

        if entail > best_entail:
            best_entail = entail
            best_evidence = f"[Entailment {entail:.2f}] {passage_snippet[:150]}..."
        if contradict > best_contradict:
            best_contradict = contradict
            if best_contradict > best_entail:
                best_evidence = f"[Contradiction {contradict:.2f}] {passage_snippet[:150]}..."

    if best_entail >= ENTAIL_THRESHOLD and (best_entail - best_contradict) >= MIN_MARGIN:
        verdict = "TRUE"
        conf = round(0.50 + best_entail * 0.45, 3)
    elif best_contradict >= CONTRADICT_THRESHOLD:
        verdict = "FALSE"
        conf = round(0.50 + best_contradict * 0.40, 3)
    else:
        verdict = "UNVERIFIABLE"
        conf = 0.40

    return {
        "verdict": verdict,
        "confidence": conf,
        "entail_prob": round(best_entail, 4),
        "contradict_prob": round(best_contradict, 4),
        "neutral_prob": round(max(0.0, 1.0 - best_entail - best_contradict), 4),
        "best_evidence": best_evidence,
        "top_passage_score": round(top_sim, 4),
    }


# ---------------------------------------------------------------------------
# MAIN EVALUATION HARNESS
# ---------------------------------------------------------------------------
def evaluate_corpus(max_claims: Optional[int] = None) -> list[dict]:
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if max_claims:
        rows = rows[:max_claims]

    cache = load_cache()
    print(f"Loaded cache with {len(cache)} pre-existing entries.")
    print(f"Evaluating {len(rows)} claims through Web-Search RAG Baseline on {get_device()}...")

    results = []
    start_time = time.time()

    for idx, row in enumerate(rows, 1):
        c_start = time.time()
        claim_id = row.get("claim_id") or row.get("master_id") or f"CLM_{idx:04d}"
        claim_text = row.get("claim", "").strip()
        gold_verdict = row.get("gold_verdict", "UNVERIFIABLE").strip().upper()
        modality = row.get("type", "UNKNOWN").strip().upper()

        query = formulate_query(row)
        titles = search_wikipedia_titles(query, cache, max_titles=1)

        passages = []
        for t in titles:
            text = fetch_wikipedia_text(t, cache)
            passages.extend(extract_passages(text))

        ranked = rank_passages(claim_text, passages, top_k=TOP_K)
        nli_res = run_nli_verification(claim_text, ranked, cache)
        c_elapsed = (time.time() - c_start) * 1000

        pred_verdict = nli_res["verdict"]
        is_correct = (pred_verdict == gold_verdict) if pred_verdict != "UNVERIFIABLE" else False
        is_answered = (pred_verdict != "UNVERIFIABLE")

        res_entry = {
            "master_id": row.get("master_id", f"MST_{idx:04d}"),
            "claim_id": claim_id,
            "type": modality,
            "origin_dataset": row.get("origin_dataset", ""),
            "claim": claim_text,
            "gold_verdict": gold_verdict,
            "rag_predicted_verdict": pred_verdict,
            "rag_confidence": nli_res["confidence"],
            "rag_entail_prob": nli_res["entail_prob"],
            "rag_contradict_prob": nli_res["contradict_prob"],
            "rag_passage_sim": nli_res["top_passage_score"],
            "is_answered": is_answered,
            "is_correct": is_correct,
            "latency_ms": round(c_elapsed, 1),
            "evidence": nli_res["best_evidence"]
        }
        results.append(res_entry)

        if idx % 25 == 0 or idx == len(rows):
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (len(rows) - idx) / rate if rate > 0 else 0
            print(f"  [{idx:4d}/{len(rows):4d}] ({elapsed:5.1f}s | {rate:4.1f} claims/s | ETA: {eta:4.1f}s) Last: {claim_id} -> {pred_verdict} (Gold: {gold_verdict})")
            save_cache(cache)

    save_cache(cache)
    return results


def compute_metrics(results: list[dict]) -> dict:
    total = len(results)
    answered = [r for r in results if r["is_answered"]]
    n_ans = len(answered)
    coverage = n_ans / total if total > 0 else 0.0

    corr_ans = sum(1 for r in answered if r["is_correct"])
    sel_acc = corr_ans / n_ans if n_ans > 0 else 0.0

    if n_ans > 0:
        z = 1.96
        p = sel_acc
        denom = 1 + z**2 / n_ans
        center = (p + z**2 / (2 * n_ans)) / denom
        delta = z * math.sqrt((p * (1 - p) / n_ans) + (z**2 / (4 * n_ans**2))) / denom
        ci_lower = max(0.0, center - delta)
        ci_upper = min(1.0, center + delta)
    else:
        ci_lower = ci_upper = 0.0

    pred_true = [r for r in results if r["rag_predicted_verdict"] == "TRUE"]
    tp_true = sum(1 for r in pred_true if r["gold_verdict"] == "TRUE")
    prec_true = tp_true / len(pred_true) if pred_true else 0.0

    pred_false = [r for r in results if r["rag_predicted_verdict"] == "FALSE"]
    tp_false = sum(1 for r in pred_false if r["gold_verdict"] == "FALSE")
    prec_false = tp_false / len(pred_false) if pred_false else 0.0

    gold_false = [r for r in results if r["gold_verdict"] == "FALSE"]
    rec_false = tp_false / len(gold_false) if gold_false else 0.0
    f1_false = (2 * prec_false * rec_false / (prec_false + rec_false)) if (prec_false + rec_false) > 0 else 0.0

    mean_latency = sum(r["latency_ms"] for r in results) / total if total > 0 else 0.0

    return {
        "total": total,
        "answered": n_ans,
        "coverage": coverage,
        "correct_answered": corr_ans,
        "selective_accuracy": sel_acc,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "pred_true_count": len(pred_true),
        "precision_true": prec_true,
        "pred_false_count": len(pred_false),
        "precision_false": prec_false,
        "recall_false": rec_false,
        "f1_false": f1_false,
        "mean_latency_ms": mean_latency,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Web-Search RAG Baseline on HalDetect Master Corpus")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of claims to process")
    args = parser.parse_args()

    results = evaluate_corpus(max_claims=args.limit)

    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nDetailed evaluation results saved to: {RESULTS_PATH}")

    overall_met = compute_metrics(results)

    by_type = collections.defaultdict(list)
    for r in results:
        by_type[r["type"]].append(r)

    print("\n" + "="*80)
    print(f" WEB-SEARCH RAG BASELINE EVALUATION REPORT (N={overall_met['total']})")
    print("="*80)
    print(f"  • Coverage:              {overall_met['coverage']*100:.1f}% ({overall_met['answered']}/{overall_met['total']})")
    print(f"  • Selective Accuracy:    {overall_met['selective_accuracy']*100:.1f}% [{overall_met['ci_lower']*100:.1f}%, {overall_met['ci_upper']*100:.1f}%] ({overall_met['correct_answered']}/{overall_met['answered']})")
    print(f"  • Precision (TRUE):      {overall_met['precision_true']*100:.1f}% ({overall_met['pred_true_count']} predicted)")
    print(f"  • Precision (FALSE):     {overall_met['precision_false']*100:.1f}% ({overall_met['pred_false_count']} predicted)")
    print(f"  • Hallucination F1:      {overall_met['f1_false']:.3f} (Recall: {overall_met['recall_false']*100:.1f}%)")
    print(f"  • Mean Latency:          {overall_met['mean_latency_ms']:.1f} ms/claim")
    print("-"*80)

    print(f"\n{'Modality':<20} | {'Total':<6} | {'Cov %':<6} | {'Sel Acc [95% CI]':<22} | {'P(TRUE)':<8} | {'P(FALSE)':<8} | {'F1(FALSE)'}")
    print(f"{'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*22}-+-{'-'*8}-+-{'-'*8}-+-{'-'*10}")
    for mod, mod_results in sorted(by_type.items()):
        m = compute_metrics(mod_results)
        ci_str = f"{m['selective_accuracy']*100:.1f}% [{m['ci_lower']*100:.1f}%, {m['ci_upper']*100:.1f}%]"
        print(f"{mod:<20} | {m['total']:<6} | {m['coverage']*100:>5.1f}% | {ci_str:<22} | {m['precision_true']*100:>6.1f}% | {m['precision_false']*100:>6.1f}% | {m['f1_false']:>8.3f}")
    print("="*80)


if __name__ == "__main__":
    main()
