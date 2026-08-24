"""
HalDetect — RELATIONAL Verifier (Phase 1: Retrieval Only)
CSE 700 · University of Chittagong · 2026

Phase 1 scope: retrieval only. No verdict, no NLI yet.
Goal: confirm that for a given RELATIONAL claim, the right evidence
passages are actually retrievable from Wikipedia before any
verification logic is built on top.

Pipeline for this phase:
    1. Build a search query from the claim's `subject` field (LLM
       extraction already done upstream — reused here, not re-derived)
    2. Resolve subject -> Wikipedia page via opensearch
    3. Fetch page plain-text extract
    4. Chunk into passages (paragraph-level)
    5. Rank passages by Sentence-BERT cosine similarity to the claim
    6. Print claim + top-k passages side by side for manual inspection

Input: a claim row from the annotated CSV (dict)
Output: list of (passage_text, similarity_score) — no verdict
"""

import json
import time
import requests
from sentence_transformers import SentenceTransformer, util

# =============================================================================
# CONFIGURATION
# =============================================================================

WIKIPEDIA_API   = "https://en.wikipedia.org/w/api.php"
CACHE_FILE      = "relational_cache.json"
SBERT_MODEL     = "all-MiniLM-L6-v2"   # same model already used for dedup

HEADERS = {
    "User-Agent": "HalDetectVerifier/1.0 (haldetect-thesis; contact: your-email@example.com)"
}

TOP_K_DEFAULT = 3

# =============================================================================
# CACHE SYSTEM (same pattern as temporal verifier)
# =============================================================================

def load_cache() -> dict:
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

# =============================================================================
# STEP 1 — resolve subject string -> Wikipedia page title
# =============================================================================

def resolve_wikipedia_title(subject: str, cache: dict) -> str | None:
    """
    Resolves a subject string to a Wikipedia page title via opensearch.
    Returns the canonical page title, or None if not found.
    """
    cache_key = f"title__{subject.lower().replace(' ', '_')}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "opensearch",
                "search": subject,
                "limit": 1,
                "namespace": 0,
                "format": "json"
            },
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        titles = result[1] if len(result) > 1 else []

        if titles:
            title = titles[0]
            cache[cache_key] = title
            save_cache(cache)
            return title

    except Exception as e:
        print(f"    [title resolution error] {subject}: {e}")

    time.sleep(0.3)
    return None

# =============================================================================
# STEP 2 — fetch plain-text extract for a page title
# =============================================================================

def fetch_page_text(title: str, cache: dict) -> str:
    """
    Fetches the plain-text extract of a Wikipedia page.
    Returns full extract text (empty string on failure).
    """
    cache_key = f"text__{title.lower().replace(' ', '_')}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "titles": title,
                "format": "json"
            },
            headers=HEADERS,
            timeout=15
        )
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        text = ""
        for page in pages.values():
            text = page.get("extract", "")
            break

        cache[cache_key] = text
        save_cache(cache)
        time.sleep(0.3)
        return text

    except Exception as e:
        print(f"    [page fetch error] {title}: {e}")
        time.sleep(0.5)
        return ""

# =============================================================================
# STEP 3 — chunk page text into paragraph-level passages
# =============================================================================

def chunk_passages(text: str, min_len: int = 50) -> list[str]:
    """
    Splits raw Wikipedia extract text into paragraph-level passages.
    Drops section headers (lines like '== History ==') and short fragments.
    """
    if not text:
        return []

    raw_paragraphs = text.split("\n")
    passages = []
    for p in raw_paragraphs:
        p = p.strip()
        if not p or p.startswith("=="):
            continue
        if len(p) < min_len:
            continue
        passages.append(p)

    return passages

# =============================================================================
# STEP 4 — rank passages by similarity to the claim
# =============================================================================

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(SBERT_MODEL)
    return _model

def rank_passages(claim: str, passages: list[str], top_k: int) -> list[tuple[str, float]]:
    """
    Ranks passages by cosine similarity to the claim text.
    Returns top_k (passage, score) pairs, sorted descending.
    """
    if not passages:
        return []

    model = get_model()
    claim_emb = model.encode(claim, convert_to_tensor=True)
    passage_embs = model.encode(passages, convert_to_tensor=True)

    scores = util.cos_sim(claim_emb, passage_embs)[0]
    ranked = sorted(zip(passages, scores.tolist()), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]

# =============================================================================
# MAIN — retrieval only, no verdict
# =============================================================================

def retrieve_for_claim(claim_row: dict, top_k: int = TOP_K_DEFAULT) -> list[tuple[str, float]]:
    """
    Runs Phase 1 retrieval for a single RELATIONAL claim row.
    Returns list of (passage, similarity_score). No verdict assigned.
    """
    claim   = claim_row.get("claim", "")
    subject = claim_row.get("subject", "")

    print(f"\n  Claim: {claim}")
    print(f"    Subject (query seed): {subject}")

    if not subject:
        print("    -> SKIPPED (no subject extracted)")
        return []

    cache = load_cache()

    title = resolve_wikipedia_title(subject, cache)
    if not title:
        print(f"    -> No Wikipedia page found for '{subject}'")
        return []
    print(f"    Wikipedia page: {title}")

    text = fetch_page_text(title, cache)
    if not text:
        print(f"    -> No text retrieved for page '{title}'")
        return []

    passages = chunk_passages(text)
    print(f"    Passages extracted: {len(passages)}")

    ranked = rank_passages(claim, passages, top_k)

    print(f"    Top-{top_k} passages:")
    for i, (passage, score) in enumerate(ranked, 1):
        snippet = passage[:160].replace("\n", " ")
        print(f"      [{i}] score={score:.3f} | {snippet}...")

    return ranked

# =============================================================================
# BATCH TEST — run retrieval over a handful of claims, no verdict
# =============================================================================

def run_phase1_test(claim_rows: list[dict], top_k: int = TOP_K_DEFAULT):
    print("=" * 70)
    print(f"RELATIONAL VERIFIER — PHASE 1 RETRIEVAL TEST (top_k={top_k})")
    print("=" * 70)

    for row in claim_rows:
        retrieve_for_claim(row, top_k=top_k)

if __name__ == "__main__":
    test_claims = [
        {
            "claim_id": "Q2_C01",
            "claim": "The 2008 financial crisis began with a collapse in the United States housing market.",
            "subject": "2008 financial crisis",
        },
        {
            "claim_id": "Q1_C03",
            "claim": "Albert Einstein derived the equation E=mc².",
            "subject": "Albert Einstein",
        },
        {
            "claim_id": "Q1_C05",
            "claim": "Albert Einstein proposed that light consists of discrete packets called quanta.",
            "subject": "Albert Einstein",
        },
    ]

    run_phase1_test(test_claims, top_k=3)