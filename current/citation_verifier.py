"""
HalDetect — CITATION Verifier
CSE 700 · University of Chittagong · 2026

Two-level verification:
    Level 1 — Source existence: does this named source/report exist?
               APIs: CrossRef, Semantic Scholar, known org URL fetch
               Confidence: 0.85 if found

    Level 2 — Claim attribution: did this source actually assert this claim?
               Method: fetch abstract/summary, run BART NLI entailment
               Confidence: 0.90 if entailed, 0.80 if contradicted

Final verdict logic:
    Source not found              → UNVERIFIABLE (0.3)
    Source found, claim entailed  → TRUE (0.90)
    Source found, claim neutral   → UNVERIFIABLE (0.5)
    Source found, claim contradicted → FALSE (0.80)
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup          # FIX 2: proper HTML stripping
from transformers import pipeline

# =============================================================================
# CONFIGURATION
# =============================================================================

CACHE_FILE        = "verifier_cache.json"
CROSSREF_URL      = "https://api.crossref.org/v1/works"
SEMSCHOLAR_URL    = "https://api.semanticscholar.org/graph/v1/paper/search"
MAILTO            = "your-email@example.com"

ENTAIL_THRESHOLD      = 0.50
CONTRADICT_THRESHOLD  = 0.40

HEADERS = {
    "User-Agent": "HalDetectVerifier/1.0 (haldetect-thesis)",
}

# =============================================================================
# KNOWN ORGANIZATION URL MAP
# =============================================================================

ORG_URL_MAP = {
    "who":          "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health",
    "world health organization": "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health",
    "ipcc":         "https://www.ipcc.ch/report/ar6/syr/",
    "ipcc sixth assessment report": "https://www.ipcc.ch/report/ar6/syr/",
    "ar6":          "https://www.ipcc.ch/report/ar6/syr/",
    "lancet commission": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30367-6/fulltext",
    "2020 lancet commission": "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30367-6/fulltext",
    "lancet":       "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(20)30367-6/fulltext",
    "cdc":          "https://www.cdc.gov/vaccines/schedules/index.html",
    "world bank":   "https://www.worldbank.org/en/topic/poverty/overview",
    "nasa":         "https://climate.nasa.gov/vital-signs/sea-level/",
    "un human development report": "https://hdr.undp.org/content/human-development-report-2023-24",
    "nature":       "https://www.nature.com/",
    "world health organization global air quality guidelines": "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health",
    "global air quality guidelines": "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health",
}

TRIVIALLY_KNOWN_ORGS = {
    "who", "world health organization", "ipcc", "cdc",
    "world bank", "nasa", "lancet", "un", "united nations",
    "nature", "science", "ieee", "nih", "fda",
    "2020 lancet commission", "lancet commission",
    "ipcc sixth assessment report",
    "world health organization global air quality guidelines",
    "global air quality guidelines",
}

# =============================================================================
# CACHE
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
# NLI MODEL
# =============================================================================

print("Loading BART NLI model...")
nli_classifier = pipeline(
    "zero-shot-classification",
    model="cross-encoder/nli-deberta-v3-large",
    device=-1
)
print("BART loaded.")

# =============================================================================
# FIX 2: PROPER HTML STRIPPING
# =============================================================================

def strip_html(raw: str) -> str:
    """
    Use BeautifulSoup to extract readable text from HTML.
    Removes scripts, styles, nav elements before extracting text.
    Old approach (regex tag removal) left JS/CSS content intact.
    """
    soup = BeautifulSoup(raw, "html.parser")
    # Remove script, style, nav, header, footer — not content
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:3000]

# =============================================================================
# FIX 1: SOURCE EXTRACTION
# Prioritizes claim text parsing over raw subject field,
# since subject often contains the claim topic not the citing org.
# =============================================================================

# Org name patterns to match in claim text
ORG_PATTERNS = [
    r"(?:The\s+)?((?:IPCC|WHO|CDC|World\s+Health\s+Organization|World\s+Bank|"
    r"NASA|Lancet(?:\s+Commission)?|(?:\d{4}\s+)?Lancet\s+Commission|"
    r"Global\s+Air\s+Quality\s+Guidelines|"
    r"IPCC\s+(?:Sixth\s+)?Assessment\s+Report(?:\s+AR\d)?)"
    r"(?:\s+[\w\s]+?)??)(?=\s+(?:report|state|found|identif|publish|warn|show|recommend|update|lower))",
    r"(?:According to|Per)\s+(?:the\s+)?([\w\s\d]+?)(?:,|\s+which|\s+report|\s+state)",
]

def extract_source_name(claim_row: dict) -> str:
    """
    FIX 1: Parse org name from claim text first.
    Fall back to subject field only if parsing fails.
    Subject field is often the claim topic (e.g. 'air pollution'),
    not the citing organization.
    """
    claim   = (claim_row.get("claim") or "").strip()
    subject = (claim_row.get("subject") or "").strip()

    # First: try to match known org names directly in claim text
    claim_lower = claim.lower()
    # Check against known org keys longest-first to avoid partial matches
    for key in sorted(ORG_URL_MAP.keys(), key=len, reverse=True):
        if key in claim_lower:
            # Return the canonical casing from the map key
            return key.title()

    # Second: regex patterns for org attribution phrases
    for pattern in ORG_PATTERNS:
        match = re.search(pattern, claim, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Third: subject field — but only if it looks like an org, not a topic
    # Heuristic: org names tend to be proper nouns / acronyms / include known keywords
    org_keywords = {"organization", "institute", "commission", "bank", "who",
                    "cdc", "ipcc", "nasa", "lancet", "report", "guidelines"}
    if subject and any(kw in subject.lower() for kw in org_keywords):
        return subject

    # Last resort: subject field as-is
    return subject

def extract_embedded_claim(claim_row: dict) -> str:
    """
    Extracts the factual assertion, stripping the source attribution prefix.
    """
    claim = (claim_row.get("claim") or "").strip()
    value = (claim_row.get("value") or "").strip()

    if value and len(value) > 10:
        return value

    stripped = re.sub(
        r"^(?:The\s+)?[\w\s,]+ (?:report|state|found|identif|warn|show|recommend)[s]?\s+that\s+",
        "", claim, flags=re.IGNORECASE
    )
    return stripped if stripped != claim else claim

# =============================================================================
# LEVEL 1 — SOURCE EXISTENCE
# =============================================================================

def check_source_crossref(source_name: str, cache: dict) -> tuple[bool, str]:
    cache_key = f"crossref__{source_name.lower().replace(' ', '_')}"
    if cache_key in cache:
        cached = cache[cache_key]
        return cached["found"], cached["evidence"]

    try:
        response = requests.get(
            CROSSREF_URL,
            params={"query": source_name, "rows": 3, "mailto": MAILTO},
            timeout=10
        )
        response.raise_for_status()
        items = response.json()["message"]["items"]
        if items:
            top = items[0]
            title    = top.get("title", [""])[0]
            year     = top.get("published", {}).get("date-parts", [[""]])[0][0]
            doi      = top.get("DOI", "")
            evidence = f"CrossRef found: '{title}' ({year}) DOI:{doi}"
            cache[cache_key] = {"found": True, "evidence": evidence}
            save_cache(cache)
            return True, evidence
    except Exception:
        pass

    cache[cache_key] = {"found": False, "evidence": "Not found in CrossRef"}
    save_cache(cache)
    return False, "Not found in CrossRef"

def check_source_semantic_scholar(source_name: str, cache: dict) -> tuple[bool, str]:
    cache_key = f"semscholar__{source_name.lower().replace(' ', '_')}"
    if cache_key in cache:
        cached = cache[cache_key]
        return cached["found"], cached["evidence"]

    try:
        response = requests.get(
            SEMSCHOLAR_URL,
            params={"query": source_name, "limit": 3, "fields": "title,year,authors,abstract"},
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        data = response.json().get("data", [])
        if data:
            top      = data[0]
            title    = top.get("title", "")
            year     = top.get("year", "")
            abstract = top.get("abstract", "")
            evidence = f"Semantic Scholar found: '{title}' ({year})"
            cache[cache_key] = {"found": True, "evidence": evidence, "abstract": abstract[:500]}
            save_cache(cache)
            return True, evidence
    except Exception:
        pass

    cache[cache_key] = {"found": False, "evidence": "Not found in Semantic Scholar"}
    save_cache(cache)
    return False, "Not found in Semantic Scholar"

def check_source_org_url(source_name: str, cache: dict) -> tuple[bool, str, str]:
    """
    FIX 2 applied here: strip_html() used instead of regex tag removal.
    """
    source_lower = source_name.lower().strip()
    url = None

    for key, mapped_url in ORG_URL_MAP.items():
        if key in source_lower or source_lower in key:
            url = mapped_url
            break

    if not url:
        return False, "No URL mapping for this source", ""

    cache_key = f"orgurl__{source_lower.replace(' ', '_')}"
    if cache_key in cache:
        cached = cache[cache_key]
        return cached["found"], cached["evidence"], cached.get("text", "")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            text     = strip_html(response.text)          # FIX 2: BeautifulSoup
            evidence = f"Source URL fetched: {url}"
            cache[cache_key] = {"found": True, "evidence": evidence, "text": text}
            save_cache(cache)
            return True, evidence, text
    except Exception:
        pass

    cache[cache_key] = {"found": False, "evidence": f"URL fetch failed: {url}", "text": ""}
    save_cache(cache)
    return False, f"URL fetch failed: {url}", ""

def level1_source_exists(source_name: str, cache: dict) -> tuple[bool, float, str, str]:
    source_lower = source_name.lower().strip()

    for known in TRIVIALLY_KNOWN_ORGS:
        if known in source_lower or source_lower in known:
            _, _, page_text = check_source_org_url(source_name, cache)
            return True, 0.85, f"Source '{source_name}' is a well-known organization", page_text

    found_cr, evidence_cr = check_source_crossref(source_name, cache)
    if found_cr:
        time.sleep(0.3)
        # FIX 3: also try to get page text even for CrossRef hits
        _, _, page_text = check_source_org_url(source_name, cache)
        return True, 0.85, evidence_cr, page_text

    time.sleep(0.3)
    found_ss, evidence_ss = check_source_semantic_scholar(source_name, cache)
    if found_ss:
        _, _, page_text = check_source_org_url(source_name, cache)
        return True, 0.80, evidence_ss, page_text

    found_url, evidence_url, page_text = check_source_org_url(source_name, cache)
    if found_url:
        return True, 0.80, evidence_url, page_text

    return False, 0.30, "Source not found in CrossRef, Semantic Scholar, or known URLs", ""

# =============================================================================
# LEVEL 2 — CLAIM ATTRIBUTION (NLI)
# =============================================================================

def level2_claim_attribution(embedded_claim: str, page_text: str, source_name: str, cache: dict) -> tuple[str, float, str]:
    if not page_text or len(page_text) < 50:
        return "UNVERIFIABLE", 0.50, "No page text available for attribution check"

    cache_key = f"nli__{embedded_claim[:60].replace(' ', '_')}"
    if cache_key in cache:
        cached = cache[cache_key]
        return cached["verdict"], cached["confidence"], cached["evidence"]

    try:
        chunks = [page_text[i:i+400] for i in range(0, min(len(page_text), 2000), 300)]

        best_entail     = 0.0
        best_contradict = 0.0
        best_chunk      = ""

        for chunk in chunks:
            if len(chunk.strip()) < 20:
                continue
            result = nli_classifier(
                chunk,
                candidate_labels=["entailment", "contradiction", "neutral"],
                hypothesis_template="This text supports the claim: {}"
            )
            # Pass embedded_claim separately to avoid f-string in hypothesis_template
            result = nli_classifier(
                chunk,
                candidate_labels=[embedded_claim],
                hypothesis_template="This text is evidence that: {}"
            )
            scores     = dict(zip(result["labels"], result["scores"]))
            entail     = result["scores"][0]   # score for the single candidate label
            contradict = 1 - entail            # approximate

            if entail > best_entail:
                best_entail = entail
                best_chunk  = chunk[:100]
            if contradict > best_contradict:
                best_contradict = contradict

        if best_entail >= ENTAIL_THRESHOLD:
            verdict    = "TRUE"
            confidence = round(0.5 + best_entail * 0.4, 3)
            evidence   = f"NLI entailment {best_entail:.2f} in: '{best_chunk}...'"
        elif best_contradict >= CONTRADICT_THRESHOLD:
            verdict    = "FALSE"
            confidence = round(0.5 + best_contradict * 0.3, 3)
            evidence   = f"NLI contradiction {best_contradict:.2f}"
        else:
            verdict    = "UNVERIFIABLE"
            confidence = 0.50
            evidence   = f"NLI inconclusive (entail={best_entail:.2f}, contradict={best_contradict:.2f})"

        cache[cache_key] = {"verdict": verdict, "confidence": confidence, "evidence": evidence}
        save_cache(cache)
        return verdict, confidence, evidence

    except Exception as e:
        return "UNVERIFIABLE", 0.30, f"NLI error: {e}"

# =============================================================================
# MAIN VERIFIER
# =============================================================================

def verify_citation(claim_row: dict) -> dict:
    claim          = claim_row.get("claim", "")
    source_name    = extract_source_name(claim_row)
    embedded_claim = extract_embedded_claim(claim_row)

    print(f"\n  Verifying: {claim[:80]}")
    print(f"    Source='{source_name}' | Embedded='{embedded_claim[:60]}'")

    result = {
        "verdict":       "UNVERIFIABLE",
        "confidence":    0.30,
        "evidence":      "",
        "level1_result": {},
        "level2_result": {}
    }

    if not source_name:
        result["evidence"] = "Could not extract source name from claim"
        return result

    cache = load_cache()

    exists, l1_conf, l1_evidence, page_text = level1_source_exists(source_name, cache)

    result["level1_result"] = {
        "exists":     exists,
        "confidence": l1_conf,
        "evidence":   l1_evidence
    }

    if not exists:
        result["verdict"]    = "UNVERIFIABLE"
        result["confidence"] = 0.30
        result["evidence"]   = f"L1 FAIL: {l1_evidence}"
        print(f"    → UNVERIFIABLE (source not found)")
        return result

    print(f"    L1 ✓ Source exists ({l1_conf:.2f}): {l1_evidence[:60]}")

    l2_verdict, l2_conf, l2_evidence = level2_claim_attribution(
        embedded_claim, page_text, source_name, cache
    )

    result["level2_result"] = {
        "verdict":    l2_verdict,
        "confidence": l2_conf,
        "evidence":   l2_evidence
    }

    print(f"    L2 verdict={l2_verdict} ({l2_conf:.2f}): {l2_evidence[:60]}")

    if l2_verdict == "TRUE":
        result["verdict"]    = "TRUE"
        result["confidence"] = round((l1_conf + l2_conf) / 2, 3)
        result["evidence"]   = f"L1: {l1_evidence[:80]} | L2: {l2_evidence[:80]}"
    elif l2_verdict == "FALSE":
        result["verdict"]    = "FALSE"
        result["confidence"] = l2_conf
        result["evidence"]   = f"L1 source found | L2: {l2_evidence}"
    else:
        result["verdict"]    = "UNVERIFIABLE"
        result["confidence"] = 0.50
        result["evidence"]   = f"L1 source found ({l1_evidence[:60]}) | L2 inconclusive: {l2_evidence[:60]}"

    print(f"    → {result['verdict']} (conf={result['confidence']})")
    return result

# =============================================================================
# BATCH RUNNER
# =============================================================================

def run_citation_verifier(claim_rows: list[dict]) -> list[dict]:
    citation_count = sum(1 for r in claim_rows if r.get("type") == "CITATION")
    print(f"\nRunning CITATION verifier on {citation_count} claims...")

    for row in claim_rows:
        if row.get("type") != "CITATION":
            continue
        result = verify_citation(row)
        row["verified_verdict"]  = result["verdict"]
        row["verified_evidence"] = result["evidence"]
        row["verified_conf"]     = result["confidence"]
        row["l1_exists"]         = result["level1_result"].get("exists", False)
        row["l2_verdict"]        = result["level2_result"].get("verdict", "")

    return claim_rows

# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_citation(verified_rows: list[dict]) -> dict:
    citation_rows = [
        r for r in verified_rows
        if r.get("type") == "CITATION" and r.get("gold_verdict", "").strip()
    ]

    if not citation_rows:
        print("No CITATION rows with gold labels found.")
        return {}

    total        = len(citation_rows)
    correct      = 0
    unverifiable = 0
    breakdown    = {"TRUE": 0, "FALSE": 0, "UNVERIFIABLE": 0}
    gold_map     = {"T": "TRUE", "F": "FALSE", "U": "UNVERIFIABLE"}

    for row in citation_rows:
        gold    = gold_map.get(row.get("gold_verdict", "").strip().upper(),
                               row.get("gold_verdict", "").strip().upper())
        verdict = row.get("verified_verdict", "").strip().upper()
        breakdown[verdict] = breakdown.get(verdict, 0) + 1

        if verdict == "UNVERIFIABLE":
            unverifiable += 1
        elif verdict == gold:
            correct += 1

    verifiable = total - unverifiable
    accuracy   = correct / verifiable if verifiable else 0.0
    coverage   = verifiable / total if total else 0.0

    print("\n" + "=" * 50)
    print("CITATION VERIFIER EVALUATION")
    print("=" * 50)
    print(f"  Total CITATION claims   : {total}")
    print(f"  Verifiable (non-UV)     : {verifiable}")
    print(f"  Correct verdicts        : {correct}")
    print(f"  Verdict breakdown       : {breakdown}")
    print(f"  Accuracy (excl. UV)     : {accuracy:.2%}")
    print(f"  Coverage                : {coverage:.2%}")

    return {
        "total": total, "verifiable": verifiable, "correct": correct,
        "accuracy": accuracy, "coverage": coverage, "breakdown": breakdown
    }

# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CITATION VERIFIER — QUICK TEST")
    print("=" * 60)

    test_claims = [
        {
            "claim_id": "C_TEST_01",
            "claim": "The WHO reports that air pollution causes approximately 7 million premature deaths globally each year.",
            "type": "CITATION", "subject": "World Health Organization",
            "property": "reported_statistic",
            "value": "air pollution causes approximately 7 million premature deaths annually",
            "secondary": "{}", "gold_verdict": "T"
        },
        {
            "claim_id": "C_TEST_02",
            "claim": "The IPCC Sixth Assessment Report states that human activities have caused 1.1°C of global warming.",
            "type": "CITATION", "subject": "IPCC Sixth Assessment Report",
            "property": "stated_finding",
            "value": "human activities caused 1.1 degrees Celsius of warming",
            "secondary": "{}", "gold_verdict": "T"
        },
        {
            "claim_id": "C_TEST_03",
            "claim": "The 2020 Lancet Commission identified 12 modifiable risk factors that account for 40% of dementia cases.",
            "type": "CITATION", "subject": "Lancet Commission",
            "property": "identified_risk_factors",
            "value": "12 modifiable risk factors account for 40% of dementia cases",
            "secondary": "{}", "gold_verdict": "T"
        },
        {
            "claim_id": "C_TEST_04",
            "claim": "The World Bank reported in 2023 that the global extreme poverty rate remained stagnant at 8.4%.",
            "type": "CITATION", "subject": "World Bank",
            "property": "reported_statistic",
            "value": "global extreme poverty rate stagnant at 8.4% in 2023",
            "secondary": "{}", "gold_verdict": "T"
        },
        {
            "claim_id": "C_TEST_05",
            "claim": "The CDC updated its immunization guidelines in 2021.",
            "type": "CITATION", "subject": "CDC",
            "property": "updated_guidelines_year",
            "value": "2021", "secondary": "{}", "gold_verdict": "T"
        },
    ]

    verified = run_citation_verifier(test_claims)
    evaluate_citation(verified)

    print("\nDetailed results:")
    for row in verified:
        if row.get("type") == "CITATION":
            print(f"\n  [{row['claim_id']}]")
            print(f"    Gold={row['gold_verdict']} | Verdict={row.get('verified_verdict')}")
            print(f"    L1 exists={row.get('l1_exists')} | L2={row.get('l2_verdict')}")
            print(f"    Evidence: {row.get('verified_evidence', '')[:100]}")