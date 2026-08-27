"""
HalDetect — Property Resolver (Wikidata statement-set matching)
===============================================================

Replaces the static ``PROPERTY_TO_WIKIDATA`` lookup with retrieval over the
entity's ACTUAL Wikidata statements.

Root cause this addresses (5-Why)
---------------------------------
TEMPORAL/EA coverage is 0%
  -> 25/34 Batch 3 claims die on an unmapped property
  -> ``PROPERTY_TO_WIKIDATA`` is a static hand-written dict (7 entries in EA)
  -> the design assumed claim predicates form a small closed set
  -> but free-text claims produce open-vocabulary predicates
  -> ROOT: predicate mapping is treated as a LOOKUP problem when it is a
     MATCHING/RETRIEVAL problem.

Per CLAUDE.md this is explicitly a structural fix, *not* per-claim map patches.

Both known Batch 3 bugs are covered by this approach — in each case the correct
property was already sitting in the entity's statement set:
  * Panama Canal   Q7350  -> P1619 = 1914-08-15   (map said P571, which Q7350 lacks)
  * Rosetta Stone  Q48584 -> P186  = granodiorite (map said P527, which it lacks)

Design notes
------------
* The static map is kept as a fast path / prior, never as a hard gate.
* Candidate PIDs are filtered by *datatype* against the claim type before
  scoring — a cheap, strong prior that sharply narrows the candidate set.
* Scoring reuses the lexical-tier + SBERT scheme already proven in
  ``resolve_entity`` (RESOLUTION_THRESHOLD = 0.60 calibration), so the two
  stages behave consistently and are calibrated the same way.
* Every decision emits a route + score so the next bottleneck stays
  diagnosable rather than silent.

This module is standalone and importable; it does not modify or depend on the
notebook. Run it directly for the Batch 3 coverage diagnostic:

    .venv/bin/python current/property_resolver.py --diagnose
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter

import requests

# =============================================================================
# CONFIGURATION  (mirrors cell 69 / cell 75 so behaviour stays consistent)
# =============================================================================
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "verifier_cache_wikidata.json")
SBERT_MODEL = "all-MiniLM-L6-v2"

MAX_RETRIES = 4
BASE_BACKOFF_SECONDS = 2.0
POLITE_DELAY = 1.1

# Calibrated in the same spirit as RESOLUTION_THRESHOLD (0.60). Property
# matching is a strictly easier problem than entity resolution (the candidate
# set is small and datatype-filtered), so we start at the same floor and
# recalibrate against Batch 3 in the diagnostic below.
PROPERTY_THRESHOLD = 0.60

HEADERS = {
    "User-Agent": "HalDetectVerifier/4.0 (haldetect-thesis; contact: your-email@example.com)",
    "Accept": "application/json",
}

# Datatype prior: which Wikidata value types can possibly satisfy each claim
# type. Filtering on this before scoring is what makes matching precise.
#
# `external-id` is deliberately EXCLUDED. Measured on Batch 3 it is pure noise:
# 'tallest_peak_in' matched P3109 (Peakbagger mountain ID) = "10640" against a
# claimed value of "Asia", purely because "peak" appears in the ID's label.
# External IDs are opaque database keys, never claim values. Same reasoning
# drops bare `string`, which is dominated by identifiers and formatter URLs.
TYPE_TO_DATATYPES = {
    "TEMPORAL": {"time"},
    "ENTITY_ATTRIBUTE": {"wikibase-item", "monolingualtext"},
    "QUANTITATIVE": {"quantity"},
}

# -----------------------------------------------------------------------------
# DIRECTIONAL GUARD
# -----------------------------------------------------------------------------
# SBERT scores topical relatedness, not directional semantics: 'part of' and
# 'consists of' are near-identical in embedding space and OPPOSITE in meaning.
# Measured on Batch 3 this produced 7 confident-wrong matches --
#   human liver 'consists_of' -> P361 (part of) = "human"
#   Lobules     'consists_of' -> P361 (part of) = "liver"
#   Denali      'tallest_mountain_in' -> P610 (highest point) = Denali itself
# -- every one of which would have flipped a gold-TRUE claim to FALSE.
#
# This is a STRUCTURAL property of how Wikidata models relations, so it is
# encoded as a direction rule rather than patched per claim.

# Predicate says: subject CONTAINS / COMPRISES the value.
_MERONYM_PREDICATES = re.compile(
    r"\b(consists?[\s_]*of|comprises?|contains?|composed[\s_]*of|"
    r"made[\s_]*(up[\s_]*)?of|has[\s_]*(part|component|member|program|"
    r"ingredient)s?|includes?)\b")

# Properties that say the reverse: subject IS CONTAINED IN / IS A KIND OF.
# Accepting one of these for a meronym predicate inverts the claim.
_HOLONYM_PROPERTIES = {
    "P361",   # part of
    "P279",   # subclass of
    "P31",    # instance of
    "P1269",  # facet of
    "P138",   # named after
}

# Superlative-containment predicates ('tallest peak in X') are not a property
# of the subject at all -- Wikidata models them on the CONTAINER (X's P610
# 'highest point' == subject). Matching them forward always picks something
# wrong, so they are forced to an honest gap pending an inverse-lookup path.
_SUPERLATIVE_PREDICATES = re.compile(
    r"\b(tallest|highest|largest|longest|biggest|deepest|smallest)[\s_]*"
    r"(peak|mountain|point|lake|river|building|city)[\s_]*(in|of)\b")


# -----------------------------------------------------------------------------
# CORE-TERM GUARD (TEMPORAL)
# -----------------------------------------------------------------------------
# Every TEMPORAL predicate and every time-valued property label shares the same
# scaffolding ('year', 'date', 'time', 'of'), which dominates the embedding and
# makes unrelated dates look alike. Measured on Batch 3:
#   'decipherment_year' matched P569 'date of birth' @0.746 -- 1790 vs a claimed
#   1822, i.e. a gold-TRUE claim flipped to FALSE by comparing a decipherment
#   year against a birth date.
# Stripping the scaffolding leaves the word that actually carries the claim
# ('decipherment' vs 'birth'), which separates cleanly.
_TIME_SCAFFOLD = {"year", "date", "time", "day", "month", "of", "in", "on",
                  "at", "the", "when", "period", "era"}
CORE_SIM_THRESHOLD = 0.35

# Date-kind synonym clusters: groups of words that all refer to the same
# lifecycle concept. If a predicate's core terms and a property's surfaces
# share a cluster, the core-term guard lets it through even when SBERT
# cosine is below CORE_SIM_THRESHOLD.
# WHY: 'inception' vs 'official opening' = 0.194 in MiniLM, which trips the
# 0.35 guard -- but they're semantically identical for civil infrastructure.
_DATE_KIND_CLUSTERS: dict[str, frozenset[str]] = {
    "inception": frozenset({
        "inception", "opening", "official opening", "opened", "open",
        "establishment", "established",
        "founding", "founded", "creation", "created",
        "formation", "formed", "launch", "launched",
        "inauguration", "inaugurated", "commission", "commissioned",
    }),
    "termination": frozenset({
        "dissolution", "dissolved", "abolition", "abolished",
        "ended", "ending", "closure", "closed", "demise",
        "decommission", "decommissioned", "shutdown",
    }),
    "construction": frozenset({
        "construction", "built", "building", "erected",
    }),
    "discovery": frozenset({
        "discovery", "discovered", "invention", "invented",
        "first described", "first observed",
    }),
    "publication": frozenset({
        "publication", "published", "release", "released",
        "issued", "broadcast", "aired",
    }),
    "birth": frozenset({"birth", "born"}),
    "death": frozenset({"death", "died", "passing"}),
}

# Invert: word -> cluster name, for O(1) lookup.
_WORD_TO_DATE_KIND: dict[str, str] = {}
for _kind, _words in _DATE_KIND_CLUSTERS.items():
    for _w in _words:
        _WORD_TO_DATE_KIND[_w] = _kind


def _core_terms(text: str) -> str:
    toks = [t for t in _norm(text).split() if t not in _TIME_SCAFFOLD]
    return " ".join(toks) if toks else _norm(text)


def _date_kinds_compatible(pred_core: str, prop_surfaces: list[str]) -> bool:
    """Check if any word/phrase in the predicate's core terms and any of the
    property's surfaces (label + aliases) map to the same date-kind cluster.

    This is a lexical escape hatch for the SBERT guard: synonyms that are
    semantically identical but have low cosine similarity (e.g. 'inception'
    vs 'official opening' = 0.194) can still pass if they share a cluster.
    """
    # Collect cluster memberships for the predicate
    pred_kinds: set[str] = set()
    pred_lower = pred_core.lower()
    # Check multi-word phrases first, then single words
    for phrase, kind in _WORD_TO_DATE_KIND.items():
        if " " in phrase and phrase in pred_lower:
            pred_kinds.add(kind)
    for tok in pred_lower.split():
        if tok in _WORD_TO_DATE_KIND:
            pred_kinds.add(_WORD_TO_DATE_KIND[tok])

    if not pred_kinds:
        return False

    # Check surfaces of the property
    for surface in prop_surfaces:
        surface_core = _core_terms(surface).lower()
        for phrase, kind in _WORD_TO_DATE_KIND.items():
            if " " in phrase and phrase in surface_core:
                if kind in pred_kinds:
                    return True
        for tok in surface_core.split():
            if tok in _WORD_TO_DATE_KIND and _WORD_TO_DATE_KIND[tok] in pred_kinds:
                return True

    return False


def directional_veto(pred: str, pid: str) -> str | None:
    """Return a reason string if `pid` is directionally wrong for `pred`."""
    if _SUPERLATIVE_PREDICATES.search(pred):
        return (f"superlative-containment predicate '{pred}' is modelled on the "
                f"container, not the subject — needs inverse lookup, not {pid}")
    if _MERONYM_PREDICATES.search(pred) and pid in _HOLONYM_PROPERTIES:
        return (f"'{pred}' asserts subject contains value, but {pid} asserts the "
                f"inverse (subject is contained in / is a kind of value)")
    return None

# Retained as a prior/shortcut only — NOT a gate. If the mapped PID is present
# in the entity's statements we take it; otherwise we fall through to matching.
PROPERTY_TO_WIKIDATA = {
    "member_of": "P463",
    "membership_status": "P463",
    "is_specialized_agency_of": "P1268",
    "birth_name": "P1477",
    "place_of_birth": "P19",
    "cause_of_death": "P509",
    "consists_of": "P527",
    "inception_date": "P571",
    "date_of_birth": "P569",
    "date_of_death": "P570",
    "publication_date": "P577",
}

_sbert_model = None


def get_sbert():
    global _sbert_model
    if _sbert_model is None:
        from sentence_transformers import SentenceTransformer
        _sbert_model = SentenceTransformer(SBERT_MODEL)
    return _sbert_model


# =============================================================================
# CACHE  (shared with the notebook verifiers — same file, same conventions)
# =============================================================================
def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_cache(cache: dict) -> None:
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)
    os.replace(tmp, CACHE_FILE)


def _get_with_retry(params: dict) -> dict | None:
    """GET with backoff. Failed calls are NEVER cached (cache-poisoning bug)."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(WIKIDATA_API, params=params,
                                headers=HEADERS, timeout=25)
            if resp.status_code == 429:
                time.sleep(BASE_BACKOFF_SECONDS * (2 ** attempt))
                continue
            resp.raise_for_status()
            time.sleep(POLITE_DELAY)
            return resp.json()
        except Exception as exc:  # noqa: BLE001 - surface, don't swallow
            if attempt == MAX_RETRIES - 1:
                print(f"    [API error] {exc}", file=sys.stderr)
                return None
            time.sleep(BASE_BACKOFF_SECONDS * (2 ** attempt))
    return None


# =============================================================================
# STATEMENT FETCH — the core of the fix
# =============================================================================
def _snak_value(snak: dict) -> tuple[str | None, str | None]:
    """Return (rendered_value, referenced_qid) for one mainsnak."""
    if snak.get("snaktype") != "value":
        return None, None
    dv = snak.get("datavalue", {})
    kind, val = dv.get("type"), dv.get("value")
    if kind == "wikibase-entityid":
        qid = val.get("id")
        return qid, qid
    if kind == "time":
        return (val.get("time") or "").lstrip("+"), None
    if kind == "quantity":
        amount = (val.get("amount") or "").lstrip("+")
        unit = (val.get("unit") or "").rsplit("/", 1)[-1]
        return (f"{amount} {unit}" if unit and unit != "1" else amount), None
    if kind == "monolingualtext":
        return val.get("text"), None
    if kind == "string":
        return val, None
    if kind == "globecoordinate":
        return f"{val.get('latitude')},{val.get('longitude')}", None
    return (json.dumps(val) if val is not None else None), None


def fetch_entity_claims(qid: str, cache: dict) -> dict[str, list[str]] | None:
    """All statements for an entity: {pid: [rendered values]}.

    ONE call returns every property the entity actually has — which is the
    whole point. No PID needs to be guessed in advance.
    """
    key = f"claims__{qid}"
    if key in cache:
        return cache[key]

    data = _get_with_retry({
        "action": "wbgetentities", "ids": qid,
        "props": "claims", "format": "json",
    })
    if data is None:
        return None  # never cache a failure

    ent = data.get("entities", {}).get(qid, {})
    raw = ent.get("claims", {}) or {}
    out: dict[str, list[str]] = {}
    refs: set[str] = set()
    for pid, statements in raw.items():
        vals = []
        for st in statements:
            rendered, ref_qid = _snak_value(st.get("mainsnak", {}))
            if rendered is None:
                continue
            vals.append(rendered)
            if ref_qid:
                refs.add(ref_qid)
        if vals:
            out[pid] = vals

    cache[key] = out
    if refs:
        cache.setdefault("_pending_labels", [])
        cache["_pending_labels"] = sorted(set(cache["_pending_labels"]) | refs)
    save_cache(cache)
    return out


def _pick_label(labels: dict, fallback: str = "") -> str:
    """Prefer the `en` label, fall back to `mul`, then to `fallback`.

    Wikidata stores language-agnostic labels under the pseudo-language `mul`, and a
    large and growing class of items has NO `en` label at all:

        Q130018 (Denali)       en=None             mul='Denali'
        Q554469 (6194 Denali)  en=None             mul='6194 Denali'
        Q513  (Mount Everest)  en='Mount Everest'  mul=None

    Requesting only `en` therefore returns an EMPTY string for those items. That is
    silently destructive in two places in this file:

      * `fetch_item_labels` renders **statement values**. If Wikidata says the
        Rosetta Stone's P186 is Q<granodiorite> and that item's label is in `mul`,
        the retrieved value comes back blank and the comparison against the claim's
        "granodiorite stele" fails — a verifier that had the right entity AND the
        right property still reports no match.
      * `fetch_property_meta` renders **property names** used for matching, so a
        `mul`-labelled property becomes unmatchable.

    Proper nouns are the class most likely to live in `mul`, because a proper noun
    is the same string in every language — and proper nouns are exactly what these
    verifiers compare. Found 2026-08-23 while fixing the same bug in
    quantitative_verifier.py.
    """
    return (labels.get("en", {}).get("value", "")
            or labels.get("mul", {}).get("value", "")
            or fallback)


def fetch_property_meta(pids: list[str], cache: dict) -> dict[str, dict]:
    """Label, aliases and datatype for each PID, batched 50 at a time.

    Cache key is `pmeta2__`: `pmeta__` entries were written with `languages=en` and
    may hold empty labels. Reusing them would preserve the bug while making the fix
    appear to work.
    """
    missing = [p for p in pids if f"pmeta2__{p}" not in cache]
    for i in range(0, len(missing), 50):
        chunk = missing[i:i + 50]
        data = _get_with_retry({
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "labels|aliases|datatype", "languages": "en|mul",
            "format": "json",
        })
        if data is None:
            break  # never cache a failure
        ents = data.get("entities", {})
        for p in chunk:
            e = ents.get(p, {})
            als = e.get("aliases", {}) or {}
            aliases = [a.get("value", "") for a in als.get("en", [])]
            aliases += [a.get("value", "") for a in als.get("mul", [])
                        if a.get("value", "") not in aliases]
            cache[f"pmeta2__{p}"] = {
                "label": _pick_label(e.get("labels", {}) or {}),
                "aliases": aliases,
                "datatype": e.get("datatype", ""),
            }
        save_cache(cache)
    return {p: cache.get(f"pmeta2__{p}", {"label": "", "aliases": [],
                                          "datatype": ""}) for p in pids}


def fetch_item_labels(qids: list[str], cache: dict) -> dict[str, str]:
    """Labels for entity-valued statement values, batched. `en` then `mul`.

    Cache key is `ilabel2__` for the same reason as `pmeta2__` above — old entries
    silently hold the QID string where the label should be.
    """
    missing = [q for q in qids if f"ilabel2__{q}" not in cache]
    for i in range(0, len(missing), 50):
        chunk = missing[i:i + 50]
        data = _get_with_retry({
            "action": "wbgetentities", "ids": "|".join(chunk),
            "props": "labels", "languages": "en|mul", "format": "json",
        })
        if data is None:
            break
        ents = data.get("entities", {})
        for q in chunk:
            cache[f"ilabel2__{q}"] = _pick_label(
                ents.get(q, {}).get("labels", {}) or {}, fallback=q)
        save_cache(cache)
    return {q: cache.get(f"ilabel2__{q}", q) for q in qids}


# =============================================================================
# PROPERTY MATCHING — same lexical-tier + SBERT scheme as resolve_entity
# =============================================================================
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _predicate_text(prop: str) -> str:
    """'inception_date' -> 'inception date'."""
    return _norm(re.sub(r"[_\-]+", " ", prop or ""))


def _tier_one(s: str, l: str) -> int:
    if not l:
        return 0
    if s == l:
        return 3
    if l.startswith(s) or s.startswith(l):
        return 2
    if set(s.split()) & set(l.split()):
        return 1
    return 0


def _label_tier(pred: str, meta: dict) -> int:
    surfaces = [meta.get("label", "")] + list(meta.get("aliases", []))
    return max((_tier_one(pred, _norm(x)) for x in surfaces), default=0)


TIER_NORM = {3: 1.0, 2: 0.66, 1: 0.33, 0: 0.0}


TIER_BONUS = 0.40


def _score(tier: int, sim: float) -> float:
    """Semantic similarity, boosted (never capped) by lexical agreement.

    NOT the 0.5*tier + 0.5*sim blend used by resolve_entity. That blend is
    correct for entity resolution, where the subject string and the entity
    label are drawn from the same vocabulary and an exact lexical hit is the
    norm. It is WRONG here: claim predicates and Wikidata property labels come
    from different vocabularies, so tier is legitimately 0 for most correct
    matches ('consists_of' shares no token with 'made from material'). Under
    the old blend tier=0 caps the score at 0.50, putting a 0.60 threshold out
    of mathematical reach for every semantic-only match — which is exactly
    what the self-test caught: P1619 and P186 both ranked #1 and were still
    rejected.

    Here similarity carries the signal and tier only pulls it toward 1.0, so
    ranking is unchanged but the score range is honest.
    """
    return sim + (1.0 - sim) * TIER_BONUS * TIER_NORM[tier]


def match_property(prop: str, claim_type: str, entity_claims: dict,
                   cache: dict, claim_text: str = "") -> dict:
    """Pick the PID from the entity's OWN statements that best matches `prop`.

    Returns a dict with pid / score / route / detail / candidates. `pid` is
    None when nothing clears PROPERTY_THRESHOLD — an honest gap, named.
    """
    pred = _predicate_text(prop)
    allowed = TYPE_TO_DATATYPES.get(claim_type, set())
    present = list(entity_claims.keys())
    if not present:
        return {"pid": None, "score": 0.0, "route": "gap",
                "detail": "entity has no statements", "candidates": []}

    meta = fetch_property_meta(present, cache)

    # Datatype prior: keep only properties whose value type could satisfy this
    # claim type at all. This is what makes matching precise rather than noisy.
    cands = [p for p in present
             if not allowed or meta[p].get("datatype") in allowed]
    if not cands:
        return {"pid": None, "score": 0.0, "route": "gap",
                "detail": (f"entity has {len(present)} properties but none of "
                           f"datatype {sorted(allowed)}"),
                "candidates": []}

    # Directional guard, applied BEFORE scoring so a wrong-direction property
    # can never win on similarity alone.
    superlative = _SUPERLATIVE_PREDICATES.search(pred)
    if superlative:
        return {"pid": None, "score": 0.0, "route": "gap",
                "detail": directional_veto(pred, "-"), "candidates": []}

    vetoed = {p: directional_veto(pred, p) for p in cands}
    kept = [p for p in cands if not vetoed[p]]
    if not kept:
        blocked = ", ".join(sorted(p for p in cands if vetoed[p]))
        return {"pid": None, "score": 0.0, "route": "gap",
                "detail": f"all candidates directionally vetoed ({blocked})",
                "candidates": []}
    cands = kept

    # Fast path: the static map's guess, but only if the entity really has it
    # AND it survived the datatype filter. Prior, not gate.
    mapped = PROPERTY_TO_WIKIDATA.get((prop or "").lower())
    if mapped and mapped in cands:
        return {"pid": mapped, "score": 1.0, "route": "mapped",
                "detail": f"static map hit, present on entity ({mapped})",
                "candidates": [(mapped, 1.0, meta[mapped].get("label", ""), 3, 1.0)]}

    # Retrieval: score every surviving candidate on its own label + aliases.
    model = get_sbert()
    from sentence_transformers import util as sbert_util

    surfaces, owners = [], []
    for p in cands:
        m = meta[p]
        for surface in [m.get("label", "")] + list(m.get("aliases", []))[:6]:
            if surface:
                surfaces.append(surface)
                owners.append(p)
    if not surfaces:
        return {"pid": None, "score": 0.0, "route": "gap",
                "detail": "no English labels for candidate properties",
                "candidates": []}

    # Predicate ONLY. `claim_text` is deliberately NOT appended: the predicate
    # is a property *name* and Wikidata labels are property *names*, so this is
    # a name-to-name match. Appending the full claim sentence mixes granularity
    # and swamps the signal — measured on Q48584/'consists_of', P186 falls from
    # 0.686 (matched) to 0.397 (rejected) and nearly loses rank to P1343
    # 'described by source'. The parameter is kept for callers/logging only.
    embs = model.encode([pred] + surfaces, convert_to_tensor=True,
                        show_progress_bar=False)
    sims = sbert_util.cos_sim(embs[0], embs[1:])[0]

    best_sim: dict[str, float] = {}
    for owner, sim in zip(owners, sims):
        best_sim[owner] = max(best_sim.get(owner, 0.0), float(sim))

    scored = []
    for p in cands:
        tier = _label_tier(pred, meta[p])
        sim = best_sim.get(p, 0.0)
        scored.append((p, _score(tier, sim), meta[p].get("label", ""),
                       tier, round(sim, 3)))
    scored.sort(key=lambda t: -t[1])

    # Core-term guard: for TEMPORAL, re-check the winner on content words alone
    # so shared time-scaffolding cannot carry an unrelated date over the line.
    # Escape hatch: date-kind synonym clusters let semantically identical but
    # lexically distant terms through (e.g. 'inception' ↔ 'official opening').
    if claim_type == "TEMPORAL" and scored:
        pred_core = _core_terms(pred)
        cores = [_core_terms(c[2]) for c in scored]
        ce = model.encode([pred_core] + cores, convert_to_tensor=True,
                          show_progress_bar=False)
        core_sims = [float(x) for x in sbert_util.cos_sim(ce[0], ce[1:])[0]]
        surviving = []
        for c, cs in zip(scored, core_sims):
            if cs >= CORE_SIM_THRESHOLD:
                surviving.append(c)
            else:
                # Synonym escape: check if predicate core and property
                # surfaces (label + aliases) share a date-kind cluster.
                p_meta = meta.get(c[0], {})
                prop_surfaces = ([p_meta.get("label", "")]
                                 + list(p_meta.get("aliases", []))[:6])
                if _date_kinds_compatible(pred_core, prop_surfaces):
                    # Re-score with a tier bump: the synonym match provides
                    # semantic confirmation equivalent to a partial lexical
                    # hit (tier 2), ensuring it can clear PROPERTY_THRESHOLD.
                    boosted_tier = min(c[3] + 1, 2)
                    boosted_score = _score(boosted_tier, c[4])
                    surviving.append((c[0], boosted_score, c[2], boosted_tier, c[4]))
        if not surviving:
            p, lab, cs = scored[0][0], scored[0][2], core_sims[0]
            return {"pid": None, "score": scored[0][1], "route": "gap",
                    "detail": (f"core-term guard: '{pred_core}' vs "
                               f"'{_core_terms(lab)}' ={cs:.3f} < "
                               f"{CORE_SIM_THRESHOLD} — {p} ({lab}) is a different "
                               f"kind of date, not this claim's"),
                    "candidates": scored[:5]}
        scored = surviving

    top_pid, top_score, top_label = scored[0][0], scored[0][1], scored[0][2]
    if top_score < PROPERTY_THRESHOLD:
        return {"pid": None, "score": top_score, "route": "gap",
                "detail": (f"best candidate {top_pid} ({top_label}) scored "
                           f"{top_score:.3f} < {PROPERTY_THRESHOLD}"),
                "candidates": scored[:5]}

    return {"pid": top_pid, "score": top_score, "route": "matched",
            "detail": f"matched '{pred}' -> {top_pid} ({top_label}) @{top_score:.3f}",
            "candidates": scored[:5]}


def resolve_property_values(qid: str, prop: str, claim_type: str, cache: dict,
                            claim_text: str = "") -> dict:
    """End-to-end: entity QID + predicate -> matched PID and its values."""
    claims = fetch_entity_claims(qid, cache)
    if claims is None:
        return {"pid": None, "values": [], "route": "error", "score": 0.0,
                "detail": "statement fetch failed"}

    m = match_property(prop, claim_type, claims, cache, claim_text)
    if not m["pid"]:
        return {**m, "values": [], "n_statements": len(claims)}

    raw = claims.get(m["pid"], [])
    qids = [v for v in raw if re.fullmatch(r"Q\d+", v or "")]
    labels = fetch_item_labels(qids, cache) if qids else {}
    values = [labels.get(v, v) for v in raw]
    return {**m, "values": values, "n_statements": len(claims)}


# =============================================================================
# DIAGNOSTIC — measures the actual thing: how many B3 claims find a property
# =============================================================================
def diagnose(csv_path: str, limit: int | None = None) -> None:
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh)
                if r.get("type") in ("TEMPORAL", "ENTITY_ATTRIBUTE")]
    if limit:
        rows = rows[:limit]

    print(f"Loaded {len(rows)} TEMPORAL+EA claims from {os.path.basename(csv_path)}\n")
    print(f"{'#':>3} {'type':<17} {'subject':<28} {'property':<24} "
          f"{'route':<8} {'pid':<7} value")
    print("-" * 130)

    cache = load_cache()
    routes: Counter = Counter()
    results = []

    for i, r in enumerate(rows, 1):
        subj = (r.get("subject") or "").strip()
        prop = (r.get("property") or "").strip()
        ctype = r.get("type", "")
        qid = (r.get("resolved_qid") or "").strip()

        if not qid:
            # Resolution is the notebook's job; here we only measure the
            # property layer. Resolve by exact search hit for the diagnostic.
            data = _get_with_retry({
                "action": "wbsearchentities", "search": subj, "language": "en",
                "format": "json", "limit": 1, "type": "item",
            })
            hits = (data or {}).get("search", [])
            qid = hits[0]["id"] if hits else ""

        if not qid:
            routes["unresolved"] += 1
            print(f"{i:>3} {ctype:<17} {subj[:27]:<28} {prop[:23]:<24} "
                  f"{'unresolv':<8} {'-':<7} -")
            results.append({**r, "property_route": "unresolved"})
            continue

        out = resolve_property_values(qid, prop, ctype, cache, r.get("claim", ""))
        routes[out["route"]] += 1
        val = ", ".join(str(v) for v in out.get("values", [])[:3])[:44]
        print(f"{i:>3} {ctype:<17} {subj[:27]:<28} {prop[:23]:<24} "
              f"{out['route']:<8} {str(out['pid'] or '-'):<7} {val}")
        results.append({**r, "resolved_qid": qid,
                        "property_pid": out["pid"] or "",
                        "property_route": out["route"],
                        "property_score": round(out["score"], 3),
                        "property_detail": out["detail"],
                        "property_values": " | ".join(map(str, out.get("values", [])))})

    total = len(rows)
    found = routes["mapped"] + routes["matched"]
    print("\n" + "=" * 60)
    print(f"PROPERTY COVERAGE: {found}/{total} = {100*found/total:.1f}%")
    for k, v in routes.most_common():
        print(f"   {k:<12} {v:>3}  ({100*v/total:.1f}%)")
    print("=" * 60)
    print("\nBaseline for comparison: 25/34 B3 claims previously died on")
    print("'unmapped property' before the entity was even resolved.")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "property_match_diagnostic.csv")
    if results:
        keys = sorted({k for r in results for k in r})
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(results)
        print(f"\nWrote {out_path}")


def _selftest() -> None:
    """The two known B3 bugs, checked directly against live Wikidata."""
    cache = load_cache()
    cases = [
        ("Q7350", "inception_date", "TEMPORAL", "P1619",
         "Panama Canal — map said P571, which Q7350 lacks"),
        ("Q48584", "consists_of", "ENTITY_ATTRIBUTE", "P186",
         "Rosetta Stone — map said P527, which Q48584 lacks"),
    ]
    print("SELF-TEST: the two confirmed Batch 3 resolution bugs\n")
    ok = 0
    for qid, prop, ctype, expect, note in cases:
        out = resolve_property_values(qid, prop, ctype, cache)
        hit = out["pid"] == expect
        ok += hit
        print(f"  {'PASS' if hit else 'FAIL'}  {qid} '{prop}' -> "
              f"{out['pid']} (want {expect}) @{out['score']:.3f}")
        print(f"        {note}")
        print(f"        values: {out.get('values', [])[:4]}")
        print(f"        {out['detail']}")
        if out.get("candidates"):
            top = ", ".join(f"{c[0]}({c[2]})@{c[1]:.2f}[t{c[3]} s{c[4]}]"
                            for c in out["candidates"][:4])
            print(f"        top: {top}")
        print()
    print(f"{ok}/{len(cases)} passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diagnose", action="store_true",
                    help="run the property-coverage diagnostic over a gold CSV")
    ap.add_argument("--selftest", action="store_true",
                    help="check the two known Batch 3 bugs")
    ap.add_argument("--csv", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "haldetect_claims_b3_gold.csv"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if args.selftest:
        _selftest()
    elif args.diagnose:
        diagnose(args.csv, args.limit)
    else:
        ap.print_help()
