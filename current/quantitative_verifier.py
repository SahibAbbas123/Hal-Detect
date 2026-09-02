"""
HalDetect — QUANTITATIVE verifier (structured extract-and-compare)
==================================================================

Design authority: FinGround / FinHalu (`2604.23588v1`), read and verified
2026-08-22. See `reference/paper_findings_2026-08-22.md` §4.

Why this is NOT text+NLI
-----------------------
FinGround, verbatim:

    "Generic NLI fails on ratio and margin verification even when the correct
    evidence passage is retrieved, because the failure is in reasoning rather
    than retrieval."

So the open architecture question in CLAUDE.md ("text+NLI fallback vs. stay
UNVERIFIABLE") is settled against NLI. A number claim is checked by *extracting
a number and comparing it*, not by asking an entailment model how it feels.

Three subtypes (FinGround's split, adapted from financial tables to open domain)
-------------------------------------------------------------------------------
  NUMERICAL      a directly-stated magnitude          -> verifiable now
  COMPARATIVE    a rank or cross-entity comparison    -> honest gap (needs
                                                         multi-entity retrieval)
  COMPUTATIONAL  a derived value (share, difference)  -> honest gap (needs
                                                         formula + operands)

FinGround's granularity ablation supports exactly this: 6-type beats 3-type by
4.3 F1, while 10-type shows no significant gain (p = 0.23). Splitting our single
QUANTITATIVE bucket into three takes the taxonomy from 5 types to 7 — inside the
supported band. Going finer is not supported.

Hedging is handled BEFORE comparison
------------------------------------
FinGround: *"Hedged financial language ('approximately,' 'roughly') drives 52%
of false positives."* Measured on our own Batch 3, 8 of 29 QUANTITATIVE claims
are hedged ("over 20,000", "up to 90 percent", "less than 10 percent",
"around 200"). A hedged claim asserts a BOUND, not a value: "over 20,000 deaths"
is TRUE at 25,000 and FALSE at 15,000. Comparing it for equality is a category
error, so the hedge is parsed into a comparison OPERATOR first.

Evidence backend
----------------
FinGround compares against table cells from financial reports. We are
open-domain with no tables, so:
  tier 1  Wikidata `quantity`-datatype statements (this module)
  tier 2  Wikipedia text / infobox extraction     (not yet built)
Unit handling resolves the unit QID's own label rather than hardcoding QIDs.

The evaluation problem this module cannot solve on its own
---------------------------------------------------------
Batch 3 has 29 QUANTITATIVE claims: **28 gold-TRUE, 1 gold-FALSE.** An
unconditional "TRUE" scores 96.6%. The single FALSE claim (B3_02_C09, renewable
capacity "3,372 GW" — the end-2022 figure misattributed to end-2023) is an IRENA
statistic with no Wikidata home, so this verifier will honestly return
UNVERIFIABLE on the one claim that could demonstrate detection.

Any accuracy figure from this module on Batch 3 is therefore measuring the base
rate, not detection ability. That is why `--sensitivity` exists: it perturbs each
*successfully verified* claim by a known amount and records where the verdict
flips, which measures discrimination without needing gold negatives. Run it
alongside `--diagnose`; the coverage number is meaningful, the raw accuracy
number is not.

Usage
-----
    .venv/bin/python current/quantitative_verifier.py --selftest
    .venv/bin/python current/quantitative_verifier.py --diagnose
    .venv/bin/python current/quantitative_verifier.py --sensitivity
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter

# Reuse the proven, cached HTTP + matching machinery rather than duplicating it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from property_resolver import (  # noqa: E402
    TIER_NORM,
    _get_with_retry,
    _norm,
    _tier_one,
    _predicate_text,
    fetch_entity_claims,
    fetch_item_labels,
    fetch_property_meta,
    get_sbert,
    load_cache,
    match_property,
    save_cache,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# FinGround recomputes derived quantities "with +/-0.5% tolerance for rounding
# conventions". We adopt the same figure for exact-equality claims.
EXACT_TOLERANCE = 0.005

# Hedged "approximately/around/about" claims assert a neighbourhood, not a
# value. 5% is a starting point to be CALIBRATED by --sensitivity, not a
# constant to defend. Recorded in output so it is always auditable.
APPROX_TOLERANCE = 0.05

# Mirrors the notebook's calibrated entity-resolution floor (CLAUDE.md: at 0.60,
# 15/15 accepted resolutions on Batch 3 were correct).
RESOLUTION_THRESHOLD = 0.60

# Candidates whose identity score is within this band of the leader are treated as
# tied, and the tie is broken by sitelink count (prominence). Must stay below
# 0.17 = 0.5*(TIER_NORM[3]-TIER_NORM[2]), so a tier difference can never be tied
# away and an exact-label match always outranks an alias match, however famous.
RESOLUTION_TIE_BAND = 0.10

MAX_SEARCH_CANDIDATES = 7

# Extra candidates pulled from full-text search per query. Prefix search alone
# misses canonical entities (see wikidata_fulltext_search).
FULLTEXT_CANDIDATES = 8


# =============================================================================
# QUANTITY PARSING
# =============================================================================

# Word-form fractions and quantifiers seen in real claims ("three-quarters of
# the 2023 additions"). Bare digits are handled by the numeric path.
_WORD_FRACTIONS = {
    "half": 0.5, "one half": 0.5, "a half": 0.5,
    "third": 1 / 3, "one third": 1 / 3, "two thirds": 2 / 3,
    "quarter": 0.25, "one quarter": 0.25, "three quarters": 0.75,
    "fifth": 0.2, "two fifths": 0.4, "three fifths": 0.6, "four fifths": 0.8,
    "tenth": 0.1, "nine tenths": 0.9,
}

_WORD_INTEGERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "twenty": 20, "thirty": 30, "fifty": 50,
    "hundred": 100, "thousand": 1_000, "million": 1_000_000,
    "billion": 1_000_000_000,
}

_ORDINALS = {
    "first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4, "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "last": -1,
}

_MAGNITUDE_SUFFIX = {
    "k": 1_000, "thousand": 1_000,
    "M": 1_000_000, "million": 1_000_000, "mn": 1_000_000,
    "bn": 1_000_000_000, "billion": 1_000_000_000,
    "tn": 1_000_000_000_000, "trillion": 1_000_000_000_000,
}

# Canonical unit -> (canonical_name, factor_to_canonical). Deliberately small:
# only what our claim set actually contains. Unknown units are carried through
# verbatim and comparison is refused rather than guessed.
_UNIT_ALIASES = {
    # length
    "metre": ("metre", 1.0), "meter": ("metre", 1.0), "m": ("metre", 1.0),
    "metres": ("metre", 1.0), "meters": ("metre", 1.0),
    "kilometre": ("metre", 1000.0), "kilometer": ("metre", 1000.0),
    "kilometres": ("metre", 1000.0), "kilometers": ("metre", 1000.0),
    "km": ("metre", 1000.0),
    "foot": ("metre", 0.3048), "feet": ("metre", 0.3048), "ft": ("metre", 0.3048),
    "mile": ("metre", 1609.344), "miles": ("metre", 1609.344),
    "nautical mile": ("metre", 1852.0),
    # mass
    "kilogram": ("kilogram", 1.0), "kilograms": ("kilogram", 1.0),
    "kg": ("kilogram", 1.0),
    "gram": ("kilogram", 0.001), "grams": ("kilogram", 0.001),
    "g": ("kilogram", 0.001),
    "tonne": ("kilogram", 1000.0), "tonnes": ("kilogram", 1000.0),
    "metric ton": ("kilogram", 1000.0),
    "pound": ("kilogram", 0.45359237), "pounds": ("kilogram", 0.45359237),
    "lb": ("kilogram", 0.45359237),
    # time
    "second": ("second", 1.0), "seconds": ("second", 1.0), "s": ("second", 1.0),
    "minute": ("second", 60.0), "minutes": ("second", 60.0),
    "hour": ("second", 3600.0), "hours": ("second", 3600.0),
    "year": ("year", 1.0), "years": ("year", 1.0),
    # power
    "watt": ("watt", 1.0), "watts": ("watt", 1.0), "w": ("watt", 1.0),
    "megawatt": ("watt", 1e6), "megawatts": ("watt", 1e6), "mw": ("watt", 1e6),
    "gigawatt": ("watt", 1e9), "gigawatts": ("watt", 1e9), "gw": ("watt", 1e9),
    "terawatt": ("watt", 1e12), "tw": ("watt", 1e12),
    # dimensionless
    "percent": ("percent", 1.0), "percentage": ("percent", 1.0),
    "per cent": ("percent", 1.0), "%": ("percent", 1.0),
    "square kilometre": ("square metre", 1e6),
    "square kilometer": ("square metre", 1e6),
    "square metre": ("square metre", 1.0), "square meter": ("square metre", 1.0),
    "hectare": ("square metre", 10_000.0),
}

# Units that carry no dimension and must not be silently compared across scales.
_DIMENSIONLESS = {"percent", "1", "", None}


def canonical_unit(raw: str | None) -> tuple[str | None, float | None]:
    """'feet' -> ('metre', 0.3048). Unknown -> (normalised_raw, None)."""
    if not raw:
        return None, None
    key = _norm(str(raw))
    if key in _UNIT_ALIASES:
        return _UNIT_ALIASES[key]
    # singularise a trailing 's' before giving up
    if key.endswith("s") and key[:-1] in _UNIT_ALIASES:
        return _UNIT_ALIASES[key[:-1]]
    return key or None, None


# -----------------------------------------------------------------------------
# HEDGE DETECTION — runs before any comparison (FinGround: 52% of FPs)
# -----------------------------------------------------------------------------
# Operator semantics, which are easy to get backwards:
#   GE  claim asserts a LOWER bound  ("over 20,000")   -> TRUE iff actual >= c
#   LE  claim asserts an UPPER bound ("up to 90%")     -> TRUE iff actual <= c
#   APPROX                                             -> TRUE iff |a-c|/a small
#   EQ  no hedge                                       -> TRUE iff within 0.5%
_NUMBER_RE = re.compile(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[-+]?\d*\.?\d+")

_HEDGE_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\b(more than|over|above|greater than|at least|exceed(s|ing)?|"
                r"upwards? of|in excess of|north of)\b"), "GE", "lower bound"),
    (re.compile(r"\b(less than|fewer than|under|below|up to|at most|"
                r"no more than|as (many|much) as|within)\b"), "LE", "upper bound"),
    (re.compile(r"\b(approximately|approx|around|about|roughly|circa|nearly|"
                r"almost|some|an estimated|estimated|order of)\b|~"),
     "APPROX", "approximation"),
]

# 'above sea level' is a measurement DATUM, not a bound. Batch 3 B3_01_C09 is
# "locks lift ships 85 feet above sea level" — an exact figure that a whole-
# sentence hedge scan reads as "at least 85", inverting the check. Stripped
# before hedge detection.
_DATUM_PHRASES = re.compile(
    r"\b(above|below)\s+(sea\s+level|ground(\s+level)?|average|the\s+equator)\b")

# Hedges attach to the number they qualify. Scanning the whole sentence produces
# exactly the false positives FinGround warns about, only from the opposite
# direction, so the search is limited to the text immediately preceding the
# quantity.
_HEDGE_WINDOW = 40

# Explicit metadata fields our extractor uses to carry a hedge with no adjacency
# to exploit (B3_11_C02 carries {"precision": "approximately"}).
_PRECISION_FIELDS = ("precision", "qualifier", "modifier", "approximation",
                     "bound", "hedge")


def detect_hedge(value: str = "", secondary: dict | None = None,
                 claim_text: str = "") -> tuple[str, str | None]:
    """Return (operator, hedge_term), reading position, not just presence.

    Order: an explicit precision field, then the window immediately before the
    quantity in the value string, then the same window in the claim sentence.
    Bound hedges (GE/LE) outrank approximation within a window.
    """
    secondary = secondary or {}

    for key in _PRECISION_FIELDS:
        raw = secondary.get(key)
        if isinstance(raw, str) and raw.strip():
            for pattern, op, label in _HEDGE_PATTERNS:
                if pattern.search(_norm(raw)):
                    return op, f"secondary.{key}='{raw}' ({label})"

    # Locate the quantity, then look only at what precedes it.
    numeral = None
    vm = _NUMBER_RE.search((value or "").replace("−", "-"))
    if vm:
        numeral = vm.group(0)

    for text in (value, claim_text):
        if not text:
            continue
        clean = _DATUM_PHRASES.sub(" ", text.replace("−", "-"))
        # Prefer the position of THIS claim's numeral over the first number in
        # the sentence — "The 2014 to 2017 event affected over 70 percent" must
        # window on 70, not on 2014. Boundary-guarded so a numeral like "10"
        # cannot match inside "2010" or "10.5".
        idx = -1
        if numeral:
            nm = re.search(rf"(?<![\d.,]){re.escape(numeral)}(?![\d])", clean)
            idx = nm.start() if nm else -1
        if idx < 0:
            m = _NUMBER_RE.search(clean)
            idx = m.start() if m else -1
        window = _norm(clean[:idx])[-_HEDGE_WINDOW:] if idx > 0 else (
            "" if idx == 0 else _norm(clean))

        for pattern, op, label in _HEDGE_PATTERNS:
            m = pattern.search(window)
            if m and op in ("GE", "LE"):
                return op, f"{m.group(0)} ({label})"
        for pattern, op, label in _HEDGE_PATTERNS:
            m = pattern.search(window)
            if m:
                return op, f"{m.group(0)} ({label})"

    return "EQ", None


def parse_quantity(value: str, secondary: dict | None = None,
                   claim_text: str = "") -> dict:
    """Extract a comparable quantity from a claim's value field.

    Returns {value, unit, canonical_unit, factor, op, hedge, is_rank, raw,
             parse_route}. `value` is None when nothing numeric was found.
    """
    secondary = secondary or {}
    raw = (value or "").strip()
    low = _norm(raw)
    op, hedge = detect_hedge(raw, secondary, claim_text)

    unit_hint = secondary.get("unit") or secondary.get("units")

    # 1. Rank / ordinal ("second", "first") — not a magnitude.
    if low in _ORDINALS:
        return {"value": float(_ORDINALS[low]), "unit": "rank",
                "canonical_unit": "rank", "factor": 1.0, "op": "EQ",
                "hedge": hedge, "is_rank": True, "raw": raw,
                "parse_route": "ordinal"}

    # 2. Word-form fraction ("three-quarters") -> percent, so it lines up with
    #    the percentage claims it competes with.
    frac_key = low.replace("-", " ")
    for phrase, frac in sorted(_WORD_FRACTIONS.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"\b{re.escape(phrase)}\b", frac_key):
            return {"value": frac * 100.0, "unit": "percent",
                    "canonical_unit": "percent", "factor": 1.0, "op": op,
                    "hedge": hedge, "is_rank": False, "raw": raw,
                    "parse_route": f"word-fraction '{phrase}'"}

    # 3. Numeric.
    m = _NUMBER_RE.search(raw.replace("−", "-"))
    if m:
        num = float(m.group(0).replace(",", ""))
        tail = raw[m.end():]
        tail_norm = _norm(tail)

        # magnitude words attached to the number ("5,000" vs "5 million")
        for word, mult in _MAGNITUDE_SUFFIX.items():
            if re.match(rf"^\s*{re.escape(word)}\b", tail_norm):
                num *= mult
                tail_norm = tail_norm[len(word):].strip()
                break

        unit_txt = unit_hint or tail_norm or None
        if not unit_txt and "%" in raw:
            unit_txt = "percent"
        if not unit_txt:
            # last resort: a unit word sitting in the claim sentence
            for alias in ("percent", "percentage", "meters", "metres", "feet",
                          "kilograms", "seconds", "gigawatts", "miles"):
                if re.search(rf"\b{alias}\b", _norm(claim_text)):
                    unit_txt = alias
                    break

        canon, factor = canonical_unit(unit_txt)
        return {"value": num, "unit": unit_txt, "canonical_unit": canon,
                "factor": factor, "op": op, "hedge": hedge, "is_rank": False,
                "raw": raw, "parse_route": "numeric"}

    # 4. Word integer ("ten specific criteria")
    for word, val in sorted(_WORD_INTEGERS.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"\b{re.escape(word)}\b", low):
            return {"value": float(val), "unit": unit_hint,
                    "canonical_unit": canonical_unit(unit_hint)[0],
                    "factor": canonical_unit(unit_hint)[1], "op": op,
                    "hedge": hedge, "is_rank": False, "raw": raw,
                    "parse_route": f"word-integer '{word}'"}

    return {"value": None, "unit": None, "canonical_unit": None, "factor": None,
            "op": op, "hedge": hedge, "is_rank": False, "raw": raw,
            "parse_route": "no-number-found"}


# =============================================================================
# SUBTYPE CLASSIFICATION
# =============================================================================
_EXPLICIT_RANK = re.compile(
    r"\b(rank|ranks|ranked|ranking|position|place|placement|standing)\b")

# Superlatives alone must NOT force COMPARATIVE. A property named
# `highest_elevation` still states a magnitude, and misrouting it would throw
# away the biggest winnable cluster in Batch 3 (7 mountain elevations, all
# Wikidata P2044). A superlative only signals a comparison when the claim states
# no measurable magnitude — i.e. it names a winner instead of a number.
_SUPERLATIVE_MARKERS = re.compile(
    r"\b(tallest|highest|largest|longest|biggest|deepest|smallest|shortest|"
    r"leads|leading|top|most|least|first|second|third|fourth|fifth)\b")

_DERIVED_MARKERS = re.compile(
    r"\b(share|share_of|percentage_of|proportion|fraction|ratio|rate|"
    r"reduction|increase|decrease|growth|difference|delta|margin|"
    r"per_capita|per_person|average|mean|median|density|"
    r"contribution|percentage)\b")


def classify_subtype(prop: str, parsed: dict, claim_text: str = "") -> tuple[str, str]:
    """Return (subtype, reason). Order matters: rank beats derived beats plain."""
    pred = _norm(re.sub(r"[_\-]+", " ", prop or ""))
    has_magnitude = parsed.get("value") is not None and not parsed.get("is_rank")
    has_unit = bool(parsed.get("canonical_unit")) and parsed.get("canonical_unit") != "rank"

    if parsed.get("is_rank"):
        return "COMPARATIVE", "value is an ordinal/rank, not a magnitude"
    if _EXPLICIT_RANK.search(pred):
        return "COMPARATIVE", f"predicate '{pred}' names a rank or position"
    # Superlative WITHOUT a measurable magnitude = naming a winner, not a number.
    if _SUPERLATIVE_MARKERS.search(pred) and not (has_magnitude and has_unit):
        return "COMPARATIVE", (f"predicate '{pred}' is superlative and the claim "
                               f"states no measurable magnitude — needs the field "
                               f"ranked, not one value looked up")
    if re.search(r"\b(more|less|fewer|greater|higher|lower)\s+than\b",
                 _norm(claim_text)) and not has_magnitude:
        return "COMPARATIVE", "claim compares two entities without stating a magnitude"
    if _DERIVED_MARKERS.search(pred):
        return "COMPUTATIONAL", (f"predicate '{pred}' names a derived quantity "
                                 f"(needs operands + formula, not a lookup)")
    if parsed.get("canonical_unit") == "percent":
        return "COMPUTATIONAL", ("value is a percentage of an implicit whole — "
                                 "needs numerator and denominator")
    return "NUMERICAL", "directly-stated magnitude"


# =============================================================================
# ENTITY RESOLUTION
# =============================================================================
# Mirrors the notebook's post-2026-08-21 design: score candidates on their OWN
# label/alias/description, commit, THEN query the property. The old "accept the
# first candidate that has a value for this PID" heuristic used the property as a
# proxy for identity, which inverts (CLAUDE.md: Panama Canal -> Panama Canal
# Zone; Rosetta Stone -> a British punk band).
#
# Duplicated here rather than imported because property_resolver.py exposes no
# resolve_entity (its diagnostic takes the first search hit, which is only safe
# for measuring the property layer in isolation). A later refactor should hoist
# this into a shared module; noted rather than silently forked.
def fetch_candidate_meta(qids: list[str], cache: dict) -> dict[str, dict]:
    """Label / description / aliases / sitelink count for each candidate.

    `n_sitelinks` is the prominence signal used to break resolution ties. It is a
    fame proxy: the real Mount Everest (Q513) has hundreds of language editions,
    a scholarly article that happens to be titled "Mount Everest" has ~zero.

    LABELS MUST BE REQUESTED AS `en|mul`, NOT `en` (found 2026-08-23)
    -----------------------------------------------------------------
    Wikidata stores language-agnostic labels under the pseudo-language `mul`, and
    a large and growing class of items has NO `en` label at all:

        Q130018 (Denali)       en=None            mul='Denali'
        Q554469 (6194 Denali)  en=None            mul='6194 Denali'
        Q513  (Mount Everest)  en='Mount Everest' mul=None

    Requesting only `en` therefore returned an EMPTY label for Denali, so the
    lexical tier could only match its aliases -- and its aliases are
    ['Mount Denali', 'Mt. Denali', 'Bolshaya Gora'], none of which equals
    "Denali". The correct entity was scored as though it were not even named
    "Denali", and lost to an asteroid.

    This is the worst possible case for the bug, not an edge case: **proper nouns
    are the class most likely to live in `mul`**, because a proper noun is the
    same string in every language -- and proper nouns are exactly what entity
    resolution resolves. Every Wikidata-backed verifier in this project shares
    this defect.

    Cache key is `cmeta3__`: `cmeta__` predates sitelinks and `cmeta2__` holds the
    empty-label rows written before this fix. Reusing either would preserve the
    bug while appearing to work. Old entries are left in place, unused.
    """
    missing = [q for q in qids if f"cmeta3__{q}" not in cache]
    for i in range(0, len(missing), 50):
        chunk = missing[i:i + 50]
        data = _get_with_retry({
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "labels|descriptions|aliases|sitelinks",
            "languages": "en|mul", "format": "json",
        })
        if data is None:
            break  # never cache a failure
        ents = data.get("entities", {})
        for q in chunk:
            e = ents.get(q, {})
            labs = e.get("labels", {}) or {}
            descs = e.get("descriptions", {}) or {}
            als = e.get("aliases", {}) or {}
            # Prefer en, fall back to mul. Never leave the label empty when the
            # item does in fact have a name.
            label = (labs.get("en", {}).get("value", "")
                     or labs.get("mul", {}).get("value", ""))
            aliases = [a.get("value", "") for a in als.get("en", [])]
            aliases += [a.get("value", "") for a in als.get("mul", [])
                        if a.get("value", "") not in aliases]
            cache[f"cmeta3__{q}"] = {
                "label": label,
                "description": (descs.get("en", {}).get("value", "")
                                or descs.get("mul", {}).get("value", "")),
                "aliases": aliases,
                "n_sitelinks": len(e.get("sitelinks", {}) or {}),
            }
        save_cache(cache)
    return {q: cache.get(f"cmeta3__{q}",
                         {"label": "", "description": "", "aliases": [],
                          "n_sitelinks": 0})
            for q in qids}


def wikidata_fulltext_search(query: str, limit: int = 8) -> list[str]:
    """Full-text item search (`list=search`), as opposed to prefix search.

    `wbsearchentities` is a PREFIX matcher over labels and aliases. That has two
    failure modes this project has now hit twice:

      * it can miss the canonical entity even on an exact label match. Searching
        "Denali" returns 8 items and does NOT include Q130018, whose English label
        is literally "Denali" -- while "Mount McKinley", its former name, returns
        it as hit #1.
      * it returns NOTHING for a descriptive multi-word query, because such a
        string is not a label prefix. "Denali mountain" -> zero hits.

    This is the same bug class the RELATIONAL verifier already fixed on the
    Wikipedia side, where switching `action=opensearch` -> `action=query&list=search`
    took coverage from 31.51% to 89.06%. The recorded reason there applies verbatim
    here: *"opensearch requires a title-like string; full-text search resolves
    descriptive queries to correct pages."*

    Full-text search finds Q130018 as hit #1 for "Denali mountain" and Q513 for
    "Mount Everest". It also surfaces a lot of scholarly articles, which is fine --
    they carry no label match and no sitelinks, so the identity scorer and the
    prominence tie-break reject them.
    """
    data = _get_with_retry({
        "action": "query", "list": "search", "format": "json",
        "srsearch": query, "srnamespace": 0, "srlimit": limit,
    })
    if data is None:
        return []
    out = []
    for h in data.get("query", {}).get("search", []):
        t = h.get("title", "")
        if t.startswith("Q") and t[1:].isdigit():
            out.append(t)
    return out


def gather_candidates(subject: str, subj_norm: str, ctx: str,
                      cache: dict) -> tuple[list[str], str]:
    """Union prefix search with full-text search. Returns (qids, provenance).

    Cache key is `cand2__`, not `search__`: entries written before full-text
    search existed hold only the prefix hits, and silently reusing them would
    make this fix a no-op on every already-seen subject while looking like it
    worked. Same discipline as `cmeta2__`.
    """
    ckey = f"cand2__{subj_norm}"
    if ckey in cache:
        return list(cache[ckey]), "cached"

    prefix = _get_with_retry({
        "action": "wbsearchentities", "search": subject, "language": "en",
        "format": "json", "limit": MAX_SEARCH_CANDIDATES, "type": "item",
    })
    if prefix is None:
        return [], "prefix search failed (not cached)"
    qids = [h["id"] for h in prefix.get("search", []) if h.get("id")]
    n_prefix = len(qids)

    # Full-text on the bare subject, then on subject+context. The second is what
    # rescues "Denali" -> "Denali mountain" -> Q130018.
    seen = set(qids)
    n_ft = 0
    queries = [subject]
    if ctx:
        queries.append(f"{subject} {ctx}".strip())
    for q in queries:
        for qid in wikidata_fulltext_search(q, limit=FULLTEXT_CANDIDATES):
            if qid not in seen:
                seen.add(qid)
                qids.append(qid)
                n_ft += 1

    prov = f"{n_prefix} prefix + {n_ft} full-text"
    if qids:
        cache[ckey] = qids     # only cached on success
        save_cache(cache)
    return qids, prov


def resolve_entity(subject: str, cache: dict, ctx: str = "") -> dict:
    """Score search candidates on their own identity; commit above threshold.

    Candidates come from prefix search UNIONED with full-text search (see
    `gather_candidates`), then are ranked by identity score with a prominence
    tie-break. The threshold is applied to the unmodified identity score, so the
    2026-08-21 calibration is preserved.
    """
    subj_norm = _norm(subject)
    if not subj_norm:
        return {"qid": None, "score": 0.0, "detail": "empty subject"}

    # The candidate set is cached: --sensitivity re-verifies the same subject up
    # to 8 times per claim, and without this that is 8 identical uncached HTTP
    # round trips each paying POLITE_DELAY, plus needless Wikidata API load.
    qids, prov = gather_candidates(subject, subj_norm, ctx, cache)

    if not qids:
        return {"qid": None, "score": 0.0,
                "detail": f"no Wikidata search hits for '{subject}' ({prov})"}

    meta = fetch_candidate_meta(qids, cache)

    model = get_sbert()
    from sentence_transformers import util as sbert_util

    surfaces = []
    for q in qids:
        m = meta[q]
        bits = [m.get("label", "")] + list(m.get("aliases", []))[:4]
        desc = m.get("description", "")
        surfaces.append(" ; ".join([b for b in bits if b] + ([desc] if desc else [])))

    query = f"{subject}. {ctx}".strip() if ctx else subject
    embs = model.encode([query] + surfaces, convert_to_tensor=True,
                        show_progress_bar=False)
    sims = [float(x) for x in sbert_util.cos_sim(embs[0], embs[1:])[0]]

    scored = []
    for q, sim in zip(qids, sims):
        m = meta[q]
        tier = max([_tier_one(subj_norm, _norm(m.get("label", "")))]
                   + [_tier_one(subj_norm, _norm(a))
                      for a in m.get("aliases", [])] or [0])
        # 0.5*tier + 0.5*sim IS correct here: subject strings and entity labels
        # come from the same vocabulary, so an exact lexical hit is the norm.
        # (Contrast property matching, where tier must be a bonus — see
        # property_resolver._score.)
        score = 0.5 * TIER_NORM[tier] + 0.5 * sim
        scored.append((q, score, m.get("label", ""), m.get("description", ""),
                       tier, round(sim, 3), int(m.get("n_sitelinks", 0) or 0)))
    scored.sort(key=lambda t: -t[1])

    # --- prominence tie-break -------------------------------------------------
    # Fixed 2026-08-23. The identity score cannot separate the real Mount Everest
    # (Q513, hundreds of sitelinks) from a stub whose label is also literally
    # "Mount Everest" (Q19977041, 6 statements): both take tier 3, so both land
    # near 0.5 + 0.5*sim, and the sort picked the wrong one. Observed live:
    #   ST_everest -> Q19977041 @0.797 ;  ST_denali -> Q554469 @0.74, whose best
    #   property candidate was P2045 *orbital inclination* (an asteroid).
    #
    # Prominence is applied as a TIE-BREAK ONLY, never as a term added to the
    # score, and that distinction is the safety property. RESOLUTION_THRESHOLD is
    # still tested against the unmodified identity score, so the 2026-08-21
    # calibration holds exactly: 15/15 accepted resolutions on Batch 3 stay
    # accepted, and the near-misses that must keep failing still fail --
    # "China" 0.510, SpaceX Starlink 0.547, Denali-the-album 0.590. A famous
    # wrong entity cannot be promoted past 0.60 by being famous, because fame
    # never enters the number being compared to 0.60.
    #
    # TIE_BAND < 0.17 also means a tier difference can never be tied away: one
    # tier step is worth 0.5*(1.00-0.66) = 0.17 of score, so an exact-label match
    # always outranks an alias match regardless of sitelinks.
    tie_note = ""
    if len(scored) > 1:
        band = [t for t in scored if scored[0][1] - t[1] <= RESOLUTION_TIE_BAND]
        if len(band) > 1:
            winner = max(band, key=lambda t: t[6])
            if winner[0] != scored[0][0] and winner[6] > scored[0][6]:
                tie_note = (f"; prominence tie-break over {len(band)} candidates "
                            f"within {RESOLUTION_TIE_BAND}: chose {winner[0]} "
                            f"({winner[6]} sitelinks) over {scored[0][0]} "
                            f"({scored[0][6]})")
                scored = [winner] + [t for t in scored if t[0] != winner[0]]

    top = scored[0]
    if top[1] < RESOLUTION_THRESHOLD:
        return {"qid": None, "score": top[1],
                "detail": (f"best candidate {top[0]} ({top[2]}: {top[3]}) scored "
                           f"{top[1]:.3f} < {RESOLUTION_THRESHOLD}{tie_note}"),
                "candidates": scored[:4]}
    return {"qid": top[0], "score": top[1],
            "detail": (f"resolved '{subject}' -> {top[0]} ({top[2]}) "
                       f"@{top[1]:.3f} [{top[6]} sitelinks]{tie_note}"),
            "candidates": scored[:4]}


# =============================================================================
# VALUE EXTRACTION FROM WIKIDATA + COMPARISON
# =============================================================================
_WD_QUANTITY_RE = re.compile(r"^([-+]?[\d.]+)(?:\s+(Q\d+|1))?$")


def parse_wikidata_quantity(rendered: str, cache: dict) -> dict:
    """'8848.86 Q11573' -> {value: 8848.86, unit: 'metre', ...}.

    Unit QIDs are resolved to their own label rather than hardcoded, so the map
    does not need to anticipate every unit Wikidata uses.
    """
    m = _WD_QUANTITY_RE.match((rendered or "").strip())
    if not m:
        return {"value": None, "unit": None, "canonical_unit": None,
                "factor": None, "raw": rendered}
    num = float(m.group(1))
    unit_qid = m.group(2)
    unit_label = None
    if unit_qid and unit_qid != "1":
        unit_label = fetch_item_labels([unit_qid], cache).get(unit_qid, unit_qid)
    canon, factor = canonical_unit(unit_label)
    return {"value": num, "unit": unit_label, "canonical_unit": canon,
            "factor": factor, "raw": rendered}


def compare(claimed: dict, actual: dict,
            exact_tol: float = EXACT_TOLERANCE,
            approx_tol: float = APPROX_TOLERANCE) -> dict:
    """Compare a parsed claim value against a parsed Wikidata value.

    Returns {verdict, confidence, detail, rel_error}. Refuses (UNVERIFIABLE)
    rather than guessing whenever units cannot be reconciled — a wrong unit is
    exactly how a confident-wrong verdict gets manufactured.
    """
    cv, av = claimed.get("value"), actual.get("value")
    if cv is None:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": f"could not parse a number from '{claimed.get('raw')}'"}
    if av is None:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": f"could not parse Wikidata value '{actual.get('raw')}'"}

    cu, au = claimed.get("canonical_unit"), actual.get("canonical_unit")
    cf, af = claimed.get("factor"), actual.get("factor")

    # Unit reconciliation.
    if cu and au and cu != au:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": (f"unit mismatch: claim in '{claimed.get('unit')}' "
                           f"({cu}), Wikidata in '{actual.get('unit')}' ({au}) — "
                           f"refusing to compare across dimensions")}
    if cu and au and cu == au:
        if cf is None or af is None:
            return {"verdict": "UNVERIFIABLE", "confidence": 0.0,
                    "rel_error": None,
                    "detail": (f"no conversion factor for '{cu}' — refusing to "
                               f"compare unconverted magnitudes")}
        c_si, a_si = cv * cf, av * af
    elif cu and not au and cu not in _DIMENSIONLESS:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": (f"claim has unit '{claimed.get('unit')}' but Wikidata "
                           f"value is dimensionless — cannot align")}
    elif not cu and au and au not in _DIMENSIONLESS:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": (f"claim is dimensionless but Wikidata "
                           f"value has unit '{actual.get('unit')}' ({au}) — cannot align")}
    else:
        c_si, a_si = cv, av

    if a_si == 0:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": "reference value is zero; relative error undefined"}

    rel = abs(a_si - c_si) / abs(a_si)
    op = claimed.get("op", "EQ")
    hedge = claimed.get("hedge")
    hedge_note = f" [hedge: {hedge}]" if hedge else ""

    if op == "GE":
        ok = a_si >= c_si
        return {"verdict": "TRUE" if ok else "FALSE",
                "confidence": 0.85 if ok else 0.8, "rel_error": round(rel, 5),
                "detail": (f"lower-bound claim: actual {a_si:g} "
                           f"{'>=' if ok else '<'} claimed {c_si:g}{hedge_note}")}
    if op == "LE":
        ok = a_si <= c_si
        return {"verdict": "TRUE" if ok else "FALSE",
                "confidence": 0.85 if ok else 0.8, "rel_error": round(rel, 5),
                "detail": (f"upper-bound claim: actual {a_si:g} "
                           f"{'<=' if ok else '>'} claimed {c_si:g}{hedge_note}")}

    tol = approx_tol if op == "APPROX" else exact_tol
    ok = rel <= tol
    return {"verdict": "TRUE" if ok else "FALSE",
            "confidence": 0.9 if ok else 0.85, "rel_error": round(rel, 5),
            "detail": (f"{'within' if ok else 'outside'} {tol*100:g}% tolerance: "
                       f"claimed {c_si:g} vs actual {a_si:g} "
                       f"(rel err {rel*100:.3f}%){hedge_note}")}


# =============================================================================
# TOP-LEVEL VERIFIER
# =============================================================================
# Counting scaffolding dominates the embedding for quantity predicates exactly
# the way time words do for TEMPORAL: "number_of_active_satellites" and
# "population" both read as "a count of things". property_resolver applies its
# core-term guard only when claim_type == "TEMPORAL" (and strips a *time*
# vocabulary), so QUANTITATIVE needs its own. Kept here, not there, so
# TEMPORAL/EA behaviour is untouched.
#
# This blocks the worst failure mode available to this module. Q30 (United
# States) carries many quantity statements, so "number_of_active_satellites" can
# reach P1082 (population, ~3.4e8). Both are dimensionless counts, so compare()
# cannot refuse on units, and the GE-hedged claim "over 5,000" would come back
# TRUE *against population* — a right verdict from wrong evidence. That is
# invisible in aggregate accuracy and strictly worse than an honest gap.
_QTY_SCAFFOLD = {
    "number", "numbers", "count", "counts", "total", "amount", "quantity",
    "quantities", "value", "values", "measure", "measurement", "figure",
    "size", "of", "in", "the", "a", "an", "per", "at", "for", "and",
}
QTY_CORE_THRESHOLD = 0.35


def _qty_core_terms(text: str) -> str:
    toks = [t for t in _norm(text).split() if t not in _QTY_SCAFFOLD]
    return " ".join(toks) if toks else _norm(text)


def qty_core_guard(prop: str, pid: str, cache: dict) -> str | None:
    """Return a veto reason if `pid`'s content words don't match `prop`'s.

    Applied only to route == "matched". A static-map hit (route == "mapped") is
    a human decision and is not second-guessed.
    """
    meta = fetch_property_meta([pid], cache)
    label = (meta.get(pid) or {}).get("label", "")
    if not label:
        return None
    pred_core = _qty_core_terms(_predicate_text(prop))
    label_core = _qty_core_terms(label)
    model = get_sbert()
    from sentence_transformers import util as sbert_util
    enc = model.encode([pred_core, label_core], convert_to_tensor=True,
                       show_progress_bar=False)
    sim = float(sbert_util.cos_sim(enc[0], enc[1])[0][0])
    if sim < QTY_CORE_THRESHOLD:
        return (f"core-term guard: '{pred_core}' vs '{label_core}' "
                f"={sim:.3f} < {QTY_CORE_THRESHOLD} — {pid} ({label}) measures "
                f"a different kind of thing")
    return None


def verify_quantitative(claim_row: dict, cache: dict | None = None) -> dict:
    """Verify one QUANTITATIVE claim. Never raises; always explains itself."""
    own_cache = cache is None
    cache = cache if cache is not None else load_cache()

    subject = (claim_row.get("subject") or "").strip()
    prop = (claim_row.get("property") or "").strip()
    value = (claim_row.get("value") or "").strip()
    claim_text = (claim_row.get("claim") or "").strip()

    try:
        secondary = json.loads(claim_row.get("secondary") or "{}")
        if not isinstance(secondary, dict):
            secondary = {}
    except (json.JSONDecodeError, TypeError):
        secondary = {}

    out = {
        "claim_id": claim_row.get("claim_id", ""),
        "subject": subject, "property": prop, "claimed_raw": value,
        "verdict": "UNVERIFIABLE", "confidence": 0.0,
        "subtype": "", "subtype_reason": "",
        "op": "", "hedge": "", "parse_route": "",
        "resolved_qid": "", "resolution_score": 0.0, "resolution_detail": "",
        "property_pid": "", "property_route": "", "property_score": 0.0,
        "property_detail": "",
        "claimed_value": None, "claimed_unit": "",
        "actual_value": None, "actual_unit": "", "actual_raw": "",
        "rel_error": None, "tolerance_used": None, "detail": "",
    }

    # ---- 1. Parse the claimed quantity, hedge first.
    parsed = parse_quantity(value, secondary, claim_text)
    out.update({"op": parsed["op"], "hedge": parsed["hedge"] or "",
                "parse_route": parsed["parse_route"],
                "claimed_value": parsed["value"],
                "claimed_unit": parsed["unit"] or ""})

    # ---- 2. Subtype route.
    subtype, reason = classify_subtype(prop, parsed, claim_text)
    out.update({"subtype": subtype, "subtype_reason": reason})

    if subtype == "COMPARATIVE":
        out["detail"] = (f"COMPARATIVE claims need multi-entity retrieval "
                         f"(rank the field, then check position) — not built. "
                         f"{reason}")
        return out
    if subtype == "COMPUTATIONAL":
        out["detail"] = (f"COMPUTATIONAL claims need operand retrieval + formula "
                         f"reconstruction (FinGround §3.2) — not built. {reason}")
        return out

    if parsed["value"] is None:
        out["detail"] = f"no parseable number in value '{value}'"
        return out

    # ---- 3. Resolve the entity on its own identity.
    # The claim sentence IS the disambiguating context and belongs here: bare
    # "Denali" scores 0.590 against *"album by Denali"* (CLAUDE.md), and nothing
    # in `secondary` separates them. This does NOT contradict the documented
    # "predicate only" lesson from property_resolver — that lesson is about
    # matching a predicate NAME to a property LABEL, where a full sentence mixes
    # granularity. Entity resolution is the opposite case: it scores candidates
    # on their descriptions, which sentence-level context genuinely informs.
    #
    # Caveat worth keeping honest: RESOLUTION_THRESHOLD = 0.60 was calibrated in
    # the notebook with a different ctx construction, so it is inherited as a
    # starting point here, not as an established calibration for this module.
    ctx_bits = [claim_text] + [str(v) for v in secondary.values()
                               if isinstance(v, str)]
    res = resolve_entity(subject, cache, " ".join(b for b in ctx_bits if b))
    out.update({"resolved_qid": res.get("qid") or "",
                "resolution_score": round(res.get("score", 0.0), 3),
                "resolution_detail": res.get("detail", "")})
    if not res.get("qid"):
        out["detail"] = f"entity unresolved: {res.get('detail')}"
        return out

    # ---- 4. Match the predicate against the entity's own quantity statements.
    claims = fetch_entity_claims(res["qid"], cache)
    if claims is None:
        out["detail"] = "Wikidata statement fetch failed (not cached)"
        return out

    m = match_property(prop, "QUANTITATIVE", claims, cache, claim_text)
    out.update({"property_pid": m.get("pid") or "",
                "property_route": m.get("route", ""),
                "property_score": round(m.get("score", 0.0), 3),
                "property_detail": m.get("detail", "")})
    if not m.get("pid"):
        out["detail"] = f"no matching quantity property: {m.get('detail')}"
        return out

    if m.get("route") == "matched":
        veto = qty_core_guard(prop, m["pid"], cache)
        if veto:
            out.update({"property_route": "gap", "property_detail": veto})
            out["detail"] = f"no matching quantity property: {veto}"
            return out

    # ---- 5. Compare.
    rendered_values = claims.get(m["pid"], [])
    if not rendered_values:
        out["detail"] = f"{m['pid']} matched but holds no value"
        return out

    best = None
    for rendered in rendered_values:
        actual = parse_wikidata_quantity(rendered, cache)
        cmp = compare(parsed, actual)
        # Prefer a decisive verdict; among decisive ones prefer the closest.
        rank = (cmp["verdict"] == "UNVERIFIABLE",
                cmp["rel_error"] if cmp["rel_error"] is not None else 9e9)
        if best is None or rank < best[0]:
            best = (rank, cmp, actual, rendered)

    _, cmp, actual, rendered = best
    out.update({
        "verdict": cmp["verdict"], "confidence": cmp["confidence"],
        "actual_value": actual["value"], "actual_unit": actual["unit"] or "",
        "actual_raw": rendered, "rel_error": cmp["rel_error"],
        "tolerance_used": (APPROX_TOLERANCE if parsed["op"] == "APPROX"
                           else EXACT_TOLERANCE if parsed["op"] == "EQ" else None),
        "detail": cmp["detail"],
    })

    if own_cache:
        save_cache(cache)
    return out


# =============================================================================
# DIAGNOSTIC
# =============================================================================
def _load_quant_rows(csv_path: str, limit: int | None = None) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh)
                if (r.get("gold_type") or r.get("type")) == "QUANTITATIVE"]
    return rows[:limit] if limit else rows


def diagnose(csv_path: str, limit: int | None = None) -> None:
    rows = _load_quant_rows(csv_path, limit)
    print(f"Loaded {len(rows)} QUANTITATIVE claims from "
          f"{os.path.basename(csv_path)}\n")

    gold = Counter(r.get("gold_verdict", "") for r in rows)
    n = len(rows)
    always_true = 100 * gold.get("TRUE", 0) / n if n else 0.0
    print(f"GOLD DISTRIBUTION: {dict(gold)}")
    print(f"  -> an unconditional 'TRUE' scores {always_true:.1f}% here.")
    print(f"  -> with {gold.get('FALSE', 0)} gold-FALSE claim(s), accuracy on "
          f"this set measures the base rate, not detection.")
    print(f"  -> run --sensitivity for a discrimination measurement.\n")

    print(f"{'#':>3} {'claim':<12} {'subject':<24} {'property':<30} "
          f"{'subtype':<14} {'verdict':<13} detail")
    print("-" * 165)

    cache = load_cache()
    verdicts: Counter = Counter()
    subtypes: Counter = Counter()
    results = []

    for i, r in enumerate(rows, 1):
        out = verify_quantitative(r, cache)
        verdicts[out["verdict"]] += 1
        subtypes[out["subtype"]] += 1
        print(f"{i:>3} {out['claim_id'][:11]:<12} {out['subject'][:23]:<24} "
              f"{out['property'][:29]:<30} {out['subtype'][:13]:<14} "
              f"{out['verdict']:<13} {out['detail'][:60]}")
        results.append({**r, **{f"q_{k}": v for k, v in out.items()}})
    save_cache(cache)

    covered = verdicts["TRUE"] + verdicts["FALSE"]
    print("\n" + "=" * 70)
    print(f"COVERAGE: {covered}/{n} = {100*covered/n:.1f}% "
          f"(a verdict other than UNVERIFIABLE)")
    for k, v in verdicts.most_common():
        print(f"   verdict {k:<14} {v:>3}  ({100*v/n:.1f}%)")
    print()
    for k, v in subtypes.most_common():
        print(f"   subtype {k or '(none)':<14} {v:>3}  ({100*v/n:.1f}%)")

    # Accuracy on covered claims, reported WITH the caveat that makes it honest.
    scored = [r for r in results
              if r[f"q_verdict"] in ("TRUE", "FALSE")
              and r.get("gold_verdict") in ("TRUE", "FALSE")]
    if scored:
        correct = sum(1 for r in scored if r["q_verdict"] == r["gold_verdict"])
        neg = sum(1 for r in scored if r["gold_verdict"] == "FALSE")
        print(f"\nACCURACY on covered: {correct}/{len(scored)} = "
              f"{100*correct/len(scored):.1f}%")
        print(f"   gold-FALSE among covered: {neg}")
        if neg == 0:
            print("   *** UNINFORMATIVE: zero negatives in the covered set. ***")
            print("   *** This number cannot distinguish the verifier from  ***")
            print("   *** an unconditional 'TRUE'. Use --sensitivity.       ***")
    print("=" * 70)

    # Derive the output name from the INPUT, never a fixed string. Until
    # 2026-08-25 this was hardcoded to "quantitative_b3_results.csv", so
    # `--diagnose --csv <anything>` silently overwrote the Batch 3 result with
    # a different claim set's verdicts -- a file whose name still said "b3".
    # That is precisely the trap the project's standing rule exists for: a
    # filename is not evidence of its contents.
    stem = os.path.splitext(os.path.basename(csv_path))[0]
    if stem == "haldetect_claims_b3_gold":
        stem = "b3"          # preserve the established Batch 3 result filename
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"quantitative_{stem}_results.csv")
    if results:
        keys = sorted({k for r in results for k in r})
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(results)
        print(f"\nWrote {out_path}")


# =============================================================================
# SENSITIVITY — the answer to "the gold set has no negatives"
# =============================================================================
PERTURBATIONS = [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50]


def sensitivity(csv_path: str, limit: int | None = None) -> None:
    """Perturb each verified claim by a known amount; find where it flips.

    Batch 3 supplies 1 gold-FALSE QUANTITATIVE claim, so real-negative recall is
    unmeasurable. Corrupting a known-TRUE value by a known percentage creates a
    negative whose label is certain by construction, and the flip point IS the
    verifier's discrimination threshold. Costs no extra API calls: the true value
    is already in cache from --diagnose.

    Caveat to carry into the write-up: these are synthetic negatives, not real
    hallucinations. They measure numeric sensitivity, not hallucination realism.
    """
    rows = _load_quant_rows(csv_path, limit)
    cache = load_cache()

    verified = []
    for r in rows:
        out = verify_quantitative(r, cache)
        if out["verdict"] in ("TRUE", "FALSE") and out["actual_value"] is not None:
            verified.append((r, out))
    save_cache(cache)

    if not verified:
        print("No claims reached a comparison — nothing to perturb.")
        print("Run --diagnose first and fix coverage before calibrating tolerance.")
        return

    print(f"SENSITIVITY: {len(verified)} verified claim(s), perturbing the "
          f"CLAIMED value by known amounts.\n")
    print(f"EXACT_TOLERANCE = {EXACT_TOLERANCE*100:g}%  "
          f"APPROX_TOLERANCE = {APPROX_TOLERANCE*100:g}%\n")
    hdr = f"{'claim':<13} {'op':<7} " + " ".join(
        f"{p*100:>6g}%" for p in PERTURBATIONS)
    print(hdr)
    print("-" * len(hdr))

    flip_points = []
    for r, out in verified:
        row = f"{out['claim_id'][:12]:<13} {out['op']:<7} "
        flip = None
        # Direction matters, and getting it wrong makes a working verifier look
        # insensitive: raising a lower-bound claim ("over N") breaks it, but
        # raising an upper-bound claim ("up to N") only makes it easier to
        # satisfy. Perturb whichever way actually contradicts the assertion.
        sign = -1.0 if out["op"] == "LE" else 1.0
        # Re-inject the operator explicitly. The original hedge may have lived in
        # the value string, the claim sentence, or `secondary`; rewriting `value`
        # would silently drop it and turn a bound claim into an equality claim.
        prefix = {"GE": "over ", "LE": "up to ",
                  "APPROX": "approximately "}.get(out["op"], "")
        for p in PERTURBATIONS:
            probe = dict(r)
            new_val = out["claimed_value"] * (1.0 + sign * p)
            probe["value"] = f"{prefix}{new_val:g} {out['claimed_unit']}".strip()
            res = verify_quantitative(probe, cache)
            mark = {"TRUE": "  ok  ", "FALSE": " FLIP ",
                    "UNVERIFIABLE": "  --  "}.get(res["verdict"], "  ?   ")
            row += mark + " "
            if res["verdict"] == "FALSE" and flip is None:
                flip = p
        flip_points.append((out["claim_id"], out["op"], flip))
        print(row + (f"  flips at {'-' if sign < 0 else '+'}{flip*100:g}%" if flip
                     else "  never flips <=50%"))
    save_cache(cache)

    print("\n" + "=" * 70)
    detected = [f for _, _, f in flip_points if f is not None]
    print(f"Flipped within 50%: {len(detected)}/{len(flip_points)}")
    if detected:
        print(f"Median flip point: {sorted(detected)[len(detected)//2]*100:g}%")
    never = [c for c, _, f in flip_points if f is None]
    if never:
        print(f"NEVER FLIPPED (insensitive — investigate): {', '.join(never)}")
        print("  A claim that survives a 50% corruption is not being checked.")
    print("=" * 70)


# =============================================================================
# SELF-TEST
# =============================================================================
def _selftest() -> None:
    """Offline parser/hedge/compare tests, then live Wikidata elevation checks.

    The offline block runs with no network so a parsing regression is caught
    even when Wikidata is unreachable.
    """
    print("SELF-TEST part 1 — parsing & hedging (offline)\n")
    cases = [
        # (value, secondary, claim_text, expect_value, expect_op)
        ("8,848.86", {"unit": "meters"}, "Mount Everest reaches 8,848.86 meters.",
         8848.86, "EQ"),
        ("over 20,000", {}, "caused over 20,000 deaths", 20000.0, "GE"),
        ("up to 90 percent", {}, "provide up to 90 percent of energy",
         90.0, "LE"),
        ("less than 10 percent", {}, "shrank to less than 10 percent",
         10.0, "LE"),
        ("over 5,000", {}, "has over 5,000 active satellites", 5000.0, "GE"),
        ("600", {"precision": "approximately"},
         "China operates approximately 600 active satellites.", 600.0, "APPROX"),
        ("200", {}, "Russia maintains around 200 active satellites", 200.0,
         "APPROX"),
        ("three-quarters", {}, "accounted for three-quarters of additions",
         75.0, "EQ"),
        ("1.5", {"unit": "kilograms"},
         "weighs approximately 1.5 kilograms", 1.5, "APPROX"),
        ("9.58 seconds", {}, "a time of 9.58 seconds", 9.58, "EQ"),
        ("10", {}, "based on ten specific criteria", 10.0, "EQ"),
        ("second", {}, "China ranks second in annual launch frequency", 2.0, "EQ"),
        # REGRESSION (B3_01_C09): "above sea level" is a measurement datum, not
        # a lower bound. A whole-sentence hedge scan read this as GE and turned
        # an exact figure into "at least 85", inverting the check.
        ("85", {"unit": "feet"},
         "Three sets of locks lift ships 85 feet above sea level to cross the "
         "Continental Divide.", 85.0, "EQ"),
        # REGRESSION (B3_05_C03): the hedge is real but lives only in the claim
        # sentence, and the sentence contains no digits at all — so the window
        # must fall back to the whole text rather than finding nothing.
        ("1", {}, "A site must meet at least one of the ten criteria.",
         1.0, "GE"),
        # Hedge must attach to THIS claim's number, not the first number in the
        # sentence (here the year 2014, which carries no hedge).
        ("70", {}, "The 2014 to 2017 global bleaching event affected over 70 "
         "percent of reefs.", 70.0, "GE"),
    ]
    passed = 0
    for value, sec, text, want_v, want_op in cases:
        p = parse_quantity(value, sec, text)
        ok = (p["value"] == want_v and p["op"] == want_op)
        passed += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {value!r:<24} -> "
              f"value={p['value']} op={p['op']} unit={p['unit']!r} "
              f"({p['parse_route']})")
        if not ok:
            print(f"        wanted value={want_v} op={want_op}")

    print(f"\n  {passed}/{len(cases)} parse cases passed\n")

    print("SELF-TEST part 2 — unit conversion & comparison (offline)\n")
    cmp_cases = [
        # 85 feet vs 25.9 metres -> same thing
        ({"value": 85.0, "unit": "feet", "canonical_unit": "metre",
          "factor": 0.3048, "op": "EQ", "hedge": None, "raw": "85"},
         {"value": 25.908, "unit": "metre", "canonical_unit": "metre",
          "factor": 1.0, "raw": "25.908 Q11573"}, "TRUE"),
        # lower bound satisfied
        ({"value": 20000.0, "unit": None, "canonical_unit": None,
          "factor": None, "op": "GE", "hedge": "over", "raw": "over 20,000"},
         {"value": 25000.0, "unit": None, "canonical_unit": None,
          "factor": None, "raw": "25000"}, "TRUE"),
        # lower bound violated
        ({"value": 20000.0, "unit": None, "canonical_unit": None,
          "factor": None, "op": "GE", "hedge": "over", "raw": "over 20,000"},
         {"value": 15000.0, "unit": None, "canonical_unit": None,
          "factor": None, "raw": "15000"}, "FALSE"),
        # upper bound violated
        ({"value": 90.0, "unit": "percent", "canonical_unit": "percent",
          "factor": 1.0, "op": "LE", "hedge": "up to", "raw": "up to 90 percent"},
         {"value": 95.0, "unit": "percent", "canonical_unit": "percent",
          "factor": 1.0, "raw": "95"}, "FALSE"),
        # exact outside 0.5%
        ({"value": 8000.0, "unit": "meters", "canonical_unit": "metre",
          "factor": 1.0, "op": "EQ", "hedge": None, "raw": "8000"},
         {"value": 8848.86, "unit": "metre", "canonical_unit": "metre",
          "factor": 1.0, "raw": "8848.86 Q11573"}, "FALSE"),
        # cross-dimension refusal
        ({"value": 100.0, "unit": "kilograms", "canonical_unit": "kilogram",
          "factor": 1.0, "op": "EQ", "hedge": None, "raw": "100"},
         {"value": 100.0, "unit": "metre", "canonical_unit": "metre",
          "factor": 1.0, "raw": "100 Q11573"}, "UNVERIFIABLE"),
    ]
    cpassed = 0
    for claimed, actual, want in cmp_cases:
        got = compare(claimed, actual)
        ok = got["verdict"] == want
        cpassed += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {claimed['raw']!r} vs "
              f"{actual['raw']!r} -> {got['verdict']} (want {want})")
        print(f"        {got['detail']}")
    print(f"\n  {cpassed}/{len(cmp_cases)} comparison cases passed\n")

    print("SELF-TEST part 3 — live Wikidata (network)\n")
    cache = load_cache()
    live = [
        ({"claim_id": "ST_everest", "subject": "Mount Everest",
          "property": "elevation", "value": "8,848.86",
          "secondary": '{"unit": "meters"}',
          "claim": "Mount Everest reaches 8,848.86 meters."}, "TRUE"),
        ({"claim_id": "ST_denali", "subject": "Denali",
          "property": "elevation", "value": "6,190",
          "secondary": '{"unit": "meters"}',
          "claim": "Denali has an elevation of 6,190 meters."}, "TRUE"),
        # The negative Batch 3 does not contain: a corrupted elevation.
        ({"claim_id": "ST_everest_bad", "subject": "Mount Everest",
          "property": "elevation", "value": "8,000",
          "secondary": '{"unit": "meters"}',
          "claim": "Mount Everest reaches 8,000 meters."}, "FALSE"),
    ]
    lpassed = 0
    for row, want in live:
        out = verify_quantitative(row, cache)
        ok = out["verdict"] == want
        lpassed += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {row['claim_id']} -> "
              f"{out['verdict']} (want {want})")
        print(f"        qid={out['resolved_qid']} @{out['resolution_score']} "
              f"pid={out['property_pid']} ({out['property_route']} "
              f"@{out['property_score']})")
        print(f"        {out['detail']}")
    save_cache(cache)
    print(f"\n  {lpassed}/{len(live)} live cases passed")
    print(f"\nTOTAL: {passed + cpassed + lpassed}/"
          f"{len(cases) + len(cmp_cases) + len(live)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="offline parse/compare tests + live elevation checks")
    ap.add_argument("--diagnose", action="store_true",
                    help="run over the QUANTITATIVE claims of a gold CSV")
    ap.add_argument("--sensitivity", action="store_true",
                    help="perturb verified claims to measure discrimination")
    ap.add_argument("--csv", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "haldetect_claims_b3_gold.csv"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if args.selftest:
        _selftest()
    elif args.diagnose:
        diagnose(args.csv, args.limit)
    elif args.sensitivity:
        sensitivity(args.csv, args.limit)
    else:
        ap.print_help()
