"""
HalDetect — RELATIONAL Verifier (Phase 3d: LLM-Guided Query + Full-Text Search)
CSE 700 · University of Chittagong · 2026

Builds on Phase 3b (NLI verdict + CSV batch runner). Adds:
    - Gemini-based disambiguated query generation per claim
    - Wikipedia full-text search (action=query&list=search) replacing
      opensearch — resolves descriptive queries to correct page titles
      where opensearch fails on non-title strings

Pipeline:
    1. claim + structured fields → Gemini → disambiguated search query
    2. query → Wikipedia full-text search → canonical page title
    3. title → plain-text extract
    4. text → paragraph-level chunks
    5. chunks → top-k by SBERT cosine similarity to claim
    6. filter by MIN_PASSAGE_SCORE threshold
    7. each surviving passage → BART-MNLI (premise=passage, hypothesis=claim)
    8. aggregate: max entailment / max contradiction across passages
    9. verdict: TRUE / FALSE / UNVERIFIABLE

NLI uses proper 3-way classification (entailment / contradiction / neutral)
replacing the broken 1-entail approximation used in earlier phases.
"""

import json
import time
import requests
from sentence_transformers import SentenceTransformer, util
from google.colab import userdata

# Gemini API — for disambiguated search query generation
GEMINI_API_KEY  = userdata.get('GEMINI_API_KEY')
GEMINI_MODEL    = "gemini-3.1-flash-lite-preview"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# =============================================================================
# CONFIGURATION
# =============================================================================

WIKIPEDIA_API        = "https://en.wikipedia.org/w/api.php"
CACHE_FILE           = "relational_cache.json"
SBERT_MODEL          = "all-MiniLM-L6-v2"

TOP_K                = 3
MIN_PASSAGE_SCORE    = 0.50

ENTAIL_THRESHOLD     = 0.50
CONTRADICT_THRESHOLD = 0.40

HEADERS = {
    "User-Agent": "HalDetectVerifier/1.0 (haldetect-thesis; contact: your-email@example.com)"
}

# =============================================================================
# LAZY MODEL LOADERS
# =============================================================================

_sbert_model    = None
_nli_classifier = None

def get_sbert() -> SentenceTransformer:
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer(SBERT_MODEL)
    return _sbert_model

def get_nli():
    global _nli_classifier
    if _nli_classifier is None:
        from transformers import pipeline
        print("Loading BART NLI model...")
        _nli_classifier = pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-deberta-v3-large",
            device=-1
        )
        print("BART loaded.")
    return _nli_classifier

# =============================================================================
# CACHE SYSTEM
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
# RETRIEVAL
# =============================================================================

def resolve_wikipedia_title(subject: str, cache: dict) -> str | None:
    cache_key = f"title__{subject.lower().replace(' ', '_')}"
    if cache_key in cache:
        return cache[cache_key]
    try:
        r = requests.get(
            WIKIPEDIA_API,
            params={"action": "query", "list": "search", "srsearch": subject,
                    "srlimit": 1, "format": "json"},
            headers=HEADERS, timeout=10
        )
        r.raise_for_status()
        results = r.json().get("query", {}).get("search", [])
        if results:
            title = results[0]["title"]
            cache[cache_key] = title
            save_cache(cache)
            return title
    except Exception as e:
        print(f"    [title resolution error] {subject}: {e}")
    time.sleep(2.0)
    return None

def fetch_page_text(title: str, cache: dict) -> str:
    cache_key = f"text__{title.lower().replace(' ', '_')}"
    if cache_key in cache:
        return cache[cache_key]
    try:
        r = requests.get(
            WIKIPEDIA_API,
            params={"action": "query", "prop": "extracts", "explaintext": 1,
                    "titles": title, "format": "json"},
            headers=HEADERS, timeout=15
        )
        r.raise_for_status()
        pages = r.json().get("query", {}).get("pages", {})
        text = ""
        for page in pages.values():
            text = page.get("extract", "")
            break
        cache[cache_key] = text
        save_cache(cache)
        time.sleep(2.0)
        return text
    except Exception as e:
        print(f"    [page fetch error] {title}: {e}")
        time.sleep(2.0)
        return ""

def chunk_passages(text: str, min_len: int = 50) -> list[str]:
    if not text:
        return []
    return [
        p.strip() for p in text.split("\n")
        if p.strip() and not p.strip().startswith("==") and len(p.strip()) >= min_len
    ]

def rank_passages(claim: str, passages: list[str], top_k: int) -> list[tuple[str, float]]:
    if not passages:
        return []
    model        = get_sbert()
    claim_emb    = model.encode(claim, convert_to_tensor=True)
    passage_embs = model.encode(passages, convert_to_tensor=True)
    scores       = util.cos_sim(claim_emb, passage_embs)[0]
    ranked       = sorted(zip(passages, scores.tolist()), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]

# =============================================================================
# NLI VERDICT — proper 3-way classification
# =============================================================================

def run_nli_on_passages(claim: str, passages: list[tuple[str, float]], cache: dict) -> tuple[str, float, str]:
    """
    Runs BART-MNLI over each passage as premise, claim as hypothesis.
    Uses proper 3-way NLI (entailment / contradiction / neutral) so that
    'not supported' and 'contradicted' are distinguishable — fixing the
    broken 1-entail approximation used in earlier phases.
    Aggregates by max entailment and max contradiction across passages.
    Returns (verdict, confidence, evidence).
    """
    if not passages:
        return "UNVERIFIABLE", 0.30, "No passages survived similarity threshold"

    nli = get_nli()

    best_entail           = 0.0
    best_contradict       = 0.0
    best_entail_passage   = ""
    best_contradict_passage = ""

    for passage, sim_score in passages:
        cache_key = f"nli__{claim[:60].replace(' ', '_')}__{passage[:40].replace(' ', '_')}"
        if cache_key in cache:
            cached     = cache[cache_key]
            entail     = cached["entail"]
            contradict = cached["contradict"]
        else:
            try:
                result = nli(
                    passage,
                    candidate_labels=["entailment", "contradiction", "neutral"],
                    hypothesis_template="This passage {}s that " + claim
                )
                scores     = dict(zip(result["labels"], result["scores"]))
                entail     = scores["entailment"]
                contradict = scores["contradiction"]
                cache[cache_key] = {"entail": entail, "contradict": contradict}
                save_cache(cache)
            except Exception as e:
                print(f"    [NLI error] {e}")
                continue

        print(f"      NLI: entail={entail:.3f}, contradict={contradict:.3f} | sim={sim_score:.3f} | {passage[:80]}...")

        if entail > best_entail:
            best_entail         = entail
            best_entail_passage = passage[:120]
        if contradict > best_contradict:
            best_contradict         = contradict
            best_contradict_passage = passage[:120]

    if best_entail >= ENTAIL_THRESHOLD:
        verdict    = "TRUE"
        confidence = round(0.5 + best_entail * 0.4, 3)
        evidence   = f"NLI entailment {best_entail:.2f} | '{best_entail_passage}...'"
    elif best_contradict >= CONTRADICT_THRESHOLD:
        verdict    = "FALSE"
        confidence = round(0.5 + best_contradict * 0.3, 3)
        evidence   = f"NLI contradiction {best_contradict:.2f} | '{best_contradict_passage}...'"
    else:
        verdict    = "UNVERIFIABLE"
        confidence = 0.50
        evidence   = f"NLI inconclusive (entail={best_entail:.2f}, contradict={best_contradict:.2f})"

    return verdict, confidence, evidence

# =============================================================================
# GEMINI QUERY GENERATION
# =============================================================================

def generate_search_query(claim_row: dict, cache: dict) -> str:
    """
    Uses Gemini to produce a disambiguated Wikipedia search query
    from the claim's structured fields, avoiding generic or ambiguous
    subject strings. Falls back to bare subject on API failure.
    """
    claim   = claim_row.get("claim", "")
    subject = claim_row.get("subject", "")
    prop    = claim_row.get("property", "")
    value   = claim_row.get("value", "")
    q_id    = claim_row.get("q_id", "")

    cache_key = f"llmquery__{claim[:80].replace(' ', '_')}"
    if cache_key in cache:
        return cache[cache_key]

    prompt = (
        "You are helping a fact-checking system find the right Wikipedia page "
        "for a factual claim. Given the claim and its structured fields below, "
        "produce the single best Wikipedia search query — specific enough to "
        "avoid disambiguation errors (e.g. prefer 'Emperor Wu Han dynasty' over "
        "'Emperor Wu', 'Cas9 CRISPR protein' over 'Cas9 protein'). "
        "Return ONLY the search query string, nothing else.\n\n"
        f"Claim: {claim}\n"
        f"Subject: {subject}\n"
        f"Property: {prop}\n"
        f"Value: {value}\n"
        f"Topic ID: {q_id}\n"
        "Search query:"
    )

    try:
        response = requests.post(
            GEMINI_ENDPOINT,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        response.raise_for_status()
        query = (
            response.json()
            ["candidates"][0]["content"]["parts"][0]["text"]
            .strip()
            .strip('"')
        )
        print(f"    LLM query: '{query}' (was: '{subject}')")
        cache[cache_key] = query
        save_cache(cache)
        time.sleep(0.3)
        return query

    except Exception as e:
        print(f"    [Gemini error] {e} — falling back to subject")
        return subject

# =============================================================================
# MAIN VERIFIER
# =============================================================================

def verify_relational(claim_row: dict, top_k: int = TOP_K) -> dict:
    """
    Main entry point for RELATIONAL verification.

    Input:  claim_row dict with keys: claim, subject, property, value
    Output: {
        verdict:    "TRUE" | "FALSE" | "UNVERIFIABLE"
        confidence: float 0.0–1.0
        evidence:   str
        method:     str
    }
    """
    claim   = claim_row.get("claim", "")
    subject = claim_row.get("subject", "")

    print(f"\n  Verifying: {claim[:90]}")
    print(f"    Subject (query seed): {subject}")

    result = {
        "verdict":    "UNVERIFIABLE",
        "confidence": 0.0,
        "evidence":   "",
        "method":     "wikipedia_sbert_nli"
    }

    if not claim or not subject:
        result["evidence"] = "Missing claim or subject"
        print(f"    -> UNVERIFIABLE (missing fields)")
        return result

    cache = load_cache()

    search_query = generate_search_query(claim_row, cache)
    title        = resolve_wikipedia_title(search_query, cache)
    if not title:
        result["evidence"] = f"No Wikipedia page found for '{subject}'"
        print(f"    -> UNVERIFIABLE (page not found)")
        return result
    print(f"    Wikipedia page: {title}")

    text = fetch_page_text(title, cache)
    if not text:
        result["evidence"] = f"No text retrieved for '{title}'"
        print(f"    -> UNVERIFIABLE (no page text)")
        return result

    passages = chunk_passages(text)
    print(f"    Passages extracted: {len(passages)}")

    ranked    = rank_passages(claim, passages, top_k)
    surviving = [(p, s) for p, s in ranked if s >= MIN_PASSAGE_SCORE]
    print(f"    After threshold ({MIN_PASSAGE_SCORE}): {len(surviving)}/{len(ranked)} passages survive")

    if not surviving:
        result["evidence"] = f"No passages above similarity threshold {MIN_PASSAGE_SCORE}"
        print(f"    -> UNVERIFIABLE (all passages below threshold)")
        return result

    verdict, confidence, evidence = run_nli_on_passages(claim, surviving, cache)

    result["verdict"]    = verdict
    result["confidence"] = confidence
    result["evidence"]   = evidence

    print(f"    -> {verdict} (conf={confidence}) | {evidence[:80]}")
    return result

# =============================================================================
# BATCH VERIFICATION
# =============================================================================

def run_relational_verifier(claim_rows: list[dict]) -> list[dict]:
    results          = []
    relational_count = sum(1 for r in claim_rows if r.get("gold_type") == "RELATIONAL")
    print(f"\nRunning RELATIONAL verifier on {relational_count} claims...")

    for row in claim_rows:
        if row.get("gold_type") != "RELATIONAL":
            results.append(row)
            continue
        verification             = verify_relational(row)
        row["verified_verdict"]  = verification["verdict"]
        row["verified_evidence"] = verification["evidence"]
        row["verified_conf"]     = verification["confidence"]
        results.append(row)

    return results

# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_relational(verified_rows: list[dict]) -> dict:
    """
    Compares verified verdicts against gold_verdict labels.
    Only evaluates RELATIONAL claims with non-empty gold labels.
    Note: accuracy is only meaningful after gold labels have been
    manually verified — use coverage and verdict breakdown as
    primary indicators until then.
    """
    rows = [
        r for r in verified_rows
        if r.get("gold_type") == "RELATIONAL" and r.get("gold_verdict", "").strip()
    ]
    if not rows:
        print("No RELATIONAL rows with gold labels found.")
        return {}

    total        = len(rows)
    correct      = 0
    unverifiable = 0
    breakdown    = {"TRUE": 0, "FALSE": 0, "UNVERIFIABLE": 0}

    for row in rows:
        gold    = row.get("gold_verdict", "").strip().upper()
        verdict = row.get("verified_verdict", "").strip().upper()
        breakdown[verdict] = breakdown.get(verdict, 0) + 1
        if verdict == "UNVERIFIABLE":
            unverifiable += 1
        elif verdict == gold:
            correct += 1

    verifiable = total - unverifiable
    accuracy   = correct / verifiable if verifiable else 0.0
    coverage   = verifiable / total   if total      else 0.0

    print("\n" + "=" * 50)
    print("RELATIONAL VERIFIER EVALUATION")
    print("=" * 50)
    print(f"  Total RELATIONAL claims : {total}")
    print(f"  Verifiable (non-UV)     : {verifiable}")
    print(f"  Correct verdicts        : {correct}")
    print(f"  Verdict breakdown       : {breakdown}")
    print(f"  Accuracy (excl. UV)     : {accuracy:.2%}  ← unreliable until gold labels verified")
    print(f"  Coverage                : {coverage:.2%}")

    return {
        "total": total, "verifiable": verifiable, "correct": correct,
        "accuracy": accuracy, "coverage": coverage, "breakdown": breakdown
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import csv
    import sys
    import os

    INPUT_CSV  = "haldetect_phase2_goldlabeled.csv"
    OUTPUT_CSV = "relational_phase2_verified_results.csv"

    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: input file not found: {INPUT_CSV}")
        sys.exit(1)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader     = csv.DictReader(f)
        all_rows   = list(reader)
        fieldnames = reader.fieldnames or []

    relational_count = sum(1 for r in all_rows if r.get("gold_type") == "RELATIONAL")
    print("=" * 70)
    print("RELATIONAL VERIFIER — PHASE 3D")
    print("=" * 70)
    print(f"  Total rows in CSV      : {len(all_rows)}")
    print(f"  RELATIONAL claims      : {relational_count}")
    print(f"  Output will be written : {OUTPUT_CSV}")

    verified_rows = run_relational_verifier(all_rows)

    new_cols      = ["verified_verdict", "verified_evidence", "verified_conf"]
    out_fieldnames = list(fieldnames)
    for col in new_cols:
        if col not in out_fieldnames:
            out_fieldnames.append(col)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(verified_rows)

    print(f"\nResults written to: {OUTPUT_CSV}")
    evaluate_relational(verified_rows)
