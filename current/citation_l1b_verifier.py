"""CITATION Level 1b -- the WORK-PROPERTY check. Task #18.

Level 1 asks *"does the cited source exist?"*.  Level 2 (unbuilt, needs NLI) asks
*"does it actually say this?"*.  The 2026-08-25 composition analysis exposed a
**third** question that neither asks and that 17 of 25 CITATION negatives turn on:

    are the cited work's OWN Wikidata properties consistent with how the claim
    describes it?

Two routes, neither of which needs NLI:

    DATE      P577 publication-date span, via series_resolver  (12 year_shift rows)
    PUBLISHER P123/P1433 provenance conflict, via source_consistency (composite
              fabricated titles -- "The WHO Sixth Assessment Report")

------------------------------------------------------------------------------
WHY THIS MODULE IS ALL GATE AND ALMOST NO DETECTOR
------------------------------------------------------------------------------
Measured, not assumed, on the 29 natural CITATION claims: **all 3 gold-FALSE ones
are CONTENT falsities** -- Q12_C11 (wrong largest-reduction factor), B3_05_C02 (the
ten criteria did not come from the 1972 Convention, though 1972 is the right year),
B3_12_C07 (wrong percentage).  Not one is a wrong date or a wrong publisher.

So on the natural set **Level 1b's maximum achievable true-positive count is zero.**
Its entire measurable value sits on the synthetic negatives, and its entire risk --
every single thing that can go wrong -- is a false alarm on one of the 25 gold-TRUE
natural claims.  That asymmetry is the whole design brief:

  * unlike `source_consistency.check_source`, which only ever REMOVES a verdict and
    is therefore safe in both error directions, this module EMITS FALSE.  It can
    manufacture exactly the confident-wrong verdict the 2026-08-21 QID fix drove to
    zero, so it is precision-gated **at the front**, per the standing warning after
    four recorded coverage-up/precision-down events;
  * there is **no TRUE verdict**.  Consistent provenance or a year inside the span
    returns UNVERIFIABLE.  Level 1 already emits TRUE for existence; 1b can only
    subtract or refute.

------------------------------------------------------------------------------
THE GATE: two licensed syntactic positions for a year, and nothing else
------------------------------------------------------------------------------
A year in a claim is not automatically a publication date, and treating it as one is
how this route would manufacture false alarms.  Three positions occur in the data and
only the first two license a date test:

    PUBLICATION  "The IPCC Sixth Assessment Report was published in 2024."
    EDITION      "The 2021 Lancet Commission identified 12 modifiable risk factors"
    ---- licensed above / abstain below ----
    REPORTING    "The World Bank reported in 2024 that the poverty rate ..."
    PREDICATE    "WHO reports that 149 million children ... suffered in 2022."

REPORTING is when the organisation *spoke*, not when an edition was published, and
PREDICATE is the year of the fact being reported -- SYN_CITA_082's 2022 is when the
stunting happened.  Testing either against a publication span is a category error
that would read FALSE on true claims.

The work title is the longest title-case run in the claim, and it must survive a
content gate of >= MIN_WORK_CONTENT words after removing years, generic work nouns
and any acronym.  That is what separates a real cited work from a bare organisation
reference:

    "WHO Sixth Assessment Report"  -> WHO + {Sixth, Assessment}   -> 2  ACTIVE
    "The WHO report"               -> WHO + {}                    -> 0  abstain
    "its 2024 Renewables report"   ->       {Renewables}          -> 1  abstain

------------------------------------------------------------------------------
WHY THE PUBLISHER ROUTE KEYS ON AN ACRONYM
------------------------------------------------------------------------------
Every source_swap negative substitutes a REAL organisation for another (WHO in 10 of
11), so there is no surface-form or plausibility signal -- the same control property
`cross_substitute` gives the QUANTITATIVE negatives.  What the fabricated ones share
is structural: an acronym welded onto a title-case work name that belongs to somebody
else.  An acronym (>= 2 consecutive capitals) is a structural signal, not a curated
list -- the `ORG_URL_MAP` mistake Level 1 already had to undo.  Two or more acronyms
in one claim is ambiguous, so it abstains.

The conflict itself is delegated to `source_consistency.check_source`, which keeps its
own asymmetry: only P1433/P123 can veto (an author is not a publisher), any match
wins, and NO_EVIDENCE never rejects.

Run:
    python current/citation_l1b_verifier.py --selftest      # offline gate + live routes
    python current/citation_l1b_verifier.py --diagnose      # END-TO-END, both populations
    python current/series_resolver.py      --selftest       # where the CEILING is measured

The last one is not a formality. The ceiling (8/12 year-shift negatives) is measured
there from HAND-CURATED subject strings taken from the headroom doc; `--diagnose` here
extracts the subject from the claim text and gets a lower number. Both are real; they
answer different questions, and the gap between them is a retrieval finding recorded
below. Quote them separately, never interchangeably.

------------------------------------------------------------------------------
EXTRACTION READS THE CLAIM TEXT ONLY, AND THE `subject` COLUMN IS CONTAMINATED
------------------------------------------------------------------------------
The corpus carries a `subject` column that looks like exactly the right input, and
using it would be a measurement error rather than a shortcut. Verified 2026-08-26:

    SYN_CITA_068  claim "The 2021 Lancet Commission ..."   subject '2020 Lancet Commission'
    SYN_CITA_071  claim "The 2030 Lancet Commission ..."   subject '2020 Lancet Commission'

The perturbation harness rewrote the claim and left `subject` holding the ORIGINAL,
un-perturbed year. Resolving from that column would hand the verifier the very value
the negative was built to hide, so every "detection" would be measuring the harness.
The negatives file also carries `original_value` / `corrupted_value` outright.

`--ceiling` therefore differs from `--diagnose` for a second reason beyond curation:
the ceiling's subject strings were hand-supplied from the headroom doc during design,
and end-to-end extraction cannot recover them. Both numbers are reported; neither
substitutes for the other, and the gap is a retrieval finding (below), not a bug.
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import series_resolver as SR              # noqa: E402
import source_consistency as SC           # noqa: E402

OUT = os.path.join(HERE, "citation_l1b_results.csv")

# A work title needs this many content words to count as a title rather than a bare
# organisation reference. 2 is the value that separates "Sixth Assessment" (active)
# from "Renewables" (abstain); see the gate table in the docstring.
MIN_WORK_CONTENT = 2

# Confidence for a 1b refutation. Below a Wikidata *quantity* match (0.80) because a
# publication span is a weaker instrument than an exact value comparison: it refutes
# by exclusion rather than by contradiction.
L1B_FALSE_DATE = 0.75
L1B_FALSE_PUBLISHER = 0.70

_YEAR_RE = re.compile(r"(?<!\d)(1[5-9]\d\d|20\d\d|21\d\d)(?!\d)")
_ACRONYM_RE = re.compile(r"\b([A-Z]{2,})\b")
_PUBLISHED_RE = re.compile(
    r"\b(?:was\s+|were\s+)?publish(?:ed|ing)\s+in\s+(?:the\s+year\s+)?"
    r"(1[5-9]\d\d|20\d\d|21\d\d)\b", re.I)

# Lowercase words allowed INSIDE a title-case run without breaking it. A run may not
# begin or end with one.
_CONNECTORS = {"of", "the", "and", "for", "in", "on", "to", "a", "an", "de", "du",
               "des", "van", "von"}

# A run may not START with a determiner even when capitalised. "The" at the head of a
# sentence is orthography, not part of the title -- and letting it start the run was a
# real bug: it swallowed the attributive year in "The 2021 Lancet Commission", putting
# the year INSIDE the run where the adjacency test could not see it.
_DETERMINERS = {"the", "a", "an", "this", "that", "these", "those", "its", "their",
                "our", "his", "her"}

# A year after one of these is when the organisation SPOKE, not when an edition was
# published. The veto is on the verb, so it holds regardless of what follows the year:
# "reported in 2024 World Bank data showed ..." must not read as an edition.
_REPORTING_RE = re.compile(
    r"\b(?:report|reports|reported|say|says|said|state|states|stated|announce|"
    r"announces|announced|find|finds|found|estimate|estimates|estimated|note|notes|"
    r"noted|conclude|concludes|concluded|warn|warns|warned|publish|publishes)\b"
    r"[^.;]{0,24}?\bin\s+(1[5-9]\d\d|20\d\d|21\d\d)\b", re.I)

# Nouns that make "<ORG> <noun>" a bare organisation reference rather than a title.
# Deliberately narrow: "Assessment", "Commission", "Convention", "Guidelines" and
# "Outlook" are all load-bearing parts of real work titles and must NOT be here.
_GENERIC_WORK = {"report", "reports", "study", "studies", "paper", "papers",
                 "publication", "statement", "data", "findings", "projection",
                 "projections", "analysis", "sheet", "release", "bulletin"}

# Acronyms that are not organisations, so they must not trigger the publisher route.
_NOT_ORG_ACRONYM = {"PM", "GDP", "CO", "AI", "US", "UK", "EU", "TB", "HIV", "AIDS",
                    "DNA", "RNA", "SARS", "COVID", "NLI", "OK", "II", "III", "IV"}


def _tok(claim: str) -> list[str]:
    """Word tokens, punctuation stripped but case preserved.

    A trailing period is stripped unless the token is an initialism ("U.S."), because
    otherwise sentence-final punctuation lands inside the work title and degrades
    resolution -- "World Heritage Convention." does not match any Wikidata label.
    """
    out = []
    for t in re.split(r"[^A-Za-z0-9'’.-]+", claim or ""):
        if not t:
            continue
        if t.endswith(".") and not re.fullmatch(r"(?:[A-Za-z]\.)+", t):
            t = t.rstrip(".")
        if t:
            out.append(t)
    return out


def _is_cap(t: str) -> bool:
    return bool(t) and t[0].isupper() and t[0].isalpha()


def title_runs(claim: str) -> list[list[str]]:
    """Maximal runs of capitalised tokens, connectors and years allowed inside.

    A run must START with a capitalised alphabetic token that is not a determiner --
    which is why the attributive year in "The 2021 Lancet Commission" falls OUTSIDE
    the run. That is the point: the year modifies the title, it is not part of it.
    """
    toks = _tok(claim)
    runs, cur = [], []
    for t in toks:
        year = bool(_YEAR_RE.fullmatch(t))
        startable = _is_cap(t) and t.lower() not in _DETERMINERS
        if startable or (cur and (year or t.lower() in _CONNECTORS or _is_cap(t))):
            if not cur and not startable:
                continue
            cur.append(t)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    # Trim trailing connectors/years -- "Lancet Commission in" is not a title.
    out = []
    for r in runs:
        while r and (r[-1].lower() in _CONNECTORS or _YEAR_RE.fullmatch(r[-1])):
            r = r[:-1]
        if r:
            out.append(r)
    return out


def acronyms(claim: str) -> list[str]:
    seen, out = set(), []
    for m in _ACRONYM_RE.finditer(claim or ""):
        a = m.group(1)
        if a in _NOT_ORG_ACRONYM or a in seen:
            continue
        seen.add(a)
        out.append(a)
    return out


def _find_run(toks: list[str], run: list[str]) -> int:
    """Index in `toks` where `run` starts, or -1."""
    for k in range(len(toks) - len(run) + 1):
        if toks[k:k + len(run)] == run:
            return k
    return -1


def content_words(run: list[str], drop: set[str]) -> list[str]:
    """Tokens that carry title identity: not years, connectors, generics, or `drop`."""
    out = []
    for t in run:
        low = t.lower().strip(".")
        if _YEAR_RE.fullmatch(t) or low in _CONNECTORS or low in _GENERIC_WORK:
            continue
        if t in drop or low in {d.lower() for d in drop}:
            continue
        out.append(t)
    return out


def year_role(claim: str) -> tuple[int | None, str, int]:
    """Classify the year in the claim by its syntactic position.

    Returns (year, role, token_index_of_the_word_the_year_modifies).  Only
    PUBLICATION and EDITION license a date test -- see the gate table in the module
    docstring.  The index is how the work is located for EDITION: an attributive year
    modifies the noun phrase immediately to its right, so the work is the run that
    STARTS there, not merely the longest run in the sentence.
    """
    toks = _tok(claim)
    m = _PUBLISHED_RE.search(claim or "")
    if m:
        return int(m.group(1)), "PUBLICATION", -1

    # Reporting act: the year records when the organisation spoke. Vetoed on the VERB,
    # so it holds whatever follows the year.
    reporting = {int(mm.group(1)) for mm in _REPORTING_RE.finditer(claim or "")}

    for i, t in enumerate(toks):
        if not _YEAR_RE.fullmatch(t):
            continue
        y = int(t)
        if y in reporting:
            continue
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        if _is_cap(nxt) and nxt.lower() not in _DETERMINERS:
            return y, "EDITION", i + 1
    if _YEAR_RE.search(claim or ""):
        return None, "UNLICENSED", -1
    return None, "", -1


def extract_frame(claim: str) -> dict:
    """Pull the citation frame out of claim text. No knowledge graph, no model.

    Returns work_title / claimed_year / year_role / org / gate / gate_reason.
    `gate` is one of DATE, PUBLISHER, BOTH, NONE.
    """
    frame = {"work_title": "", "claimed_year": None, "year_role": "",
             "org": "", "acronyms": "", "gate": "NONE", "gate_reason": ""}
    runs = title_runs(claim)
    acr = acronyms(claim)
    frame["acronyms"] = ",".join(acr)
    year, role, at = year_role(claim)
    frame["claimed_year"], frame["year_role"] = year, role
    if not runs:
        frame["gate_reason"] = "no title-case run in the claim"
        return frame

    drop = set(acr)
    run = None
    if role == "EDITION" and at >= 0:
        # The work is what the attributive year modifies, so locate the run that
        # starts at that token. Anything else would let a longer, unmodified title
        # elsewhere in the sentence be judged by a year that does not belong to it.
        toks = _tok(claim)
        for r in runs:
            k = _find_run(toks, r)
            if k == at:
                run = r
                break
    if run is None:
        # Work = the run with the most content words; ties go to the LAST such run,
        # because English puts the cited work after the citing organisation
        # ("The Food and Agriculture Organization (FAO) publishes the State of ...").
        best, best_n = None, -1
        for r in runs:
            n = len(content_words(r, drop))
            if n >= best_n:
                best, best_n = r, n
        run = best or []
    content = content_words(run, drop)
    title_toks = [t for t in run if not _YEAR_RE.fullmatch(t)]
    frame["work_title"] = " ".join(title_toks)

    # --- gate ---------------------------------------------------------------
    if len(content) < MIN_WORK_CONTENT:
        frame["gate_reason"] = (
            f"work title {frame['work_title']!r} has {len(content)} content word(s) "
            f"(<{MIN_WORK_CONTENT}) -- a bare organisation reference, not a cited work")
        return frame

    gates = []
    if frame["claimed_year"] is not None:
        gates.append("DATE")
    elif frame["year_role"] == "UNLICENSED":
        frame["gate_reason"] = ("a year is present but in an unlicensed position "
                               "(reporting act or predicate), so no date test; ")
    if len(acr) == 1:
        frame["org"] = acr[0]
        gates.append("PUBLISHER")
    elif len(acr) > 1:
        frame["gate_reason"] += (f"{len(acr)} acronyms ({','.join(acr)}) -- ambiguous "
                                f"which is the citing organisation; ")

    frame["gate"] = ("BOTH" if len(gates) == 2 else (gates[0] if gates else "NONE"))
    if gates:
        frame["gate_reason"] += (f"work {frame['work_title']!r} passes with "
                                 f"{len(content)} content word(s)")
    elif not frame["gate_reason"]:
        frame["gate_reason"] = "no licensed year and no single acronym"
    return frame


def strip_years(text: str) -> str:
    """Remove every 4-digit year from a string.

    Applied to the context handed to resolution. `resolve_entity` uses ctx for
    full-text candidate generation and SBERT similarity, so an unstripped claim would
    let the CLAIMED year influence which edition is selected -- the exact circularity
    series_resolver's signature was designed to exclude. Excluding it from the
    signature and then smuggling it in through ctx would be the same bug wearing a
    different hat. `--selftest` asserts the span is invariant to the claimed year.
    """
    return _YEAR_RE.sub(" ", text or "")


_ANCHOR_STOP = frozenset({
    "that", "which", "who", "whom", "whose", "this", "these", "those", "there",
    "with", "from", "into", "about", "over", "under", "between", "among",
    "was", "were", "has", "have", "had", "been", "being", "are", "its", "their",
    "than", "then", "also", "such", "each", "per", "all", "any", "some", "more",
    "most", "other", "both", "new", "found", "account", "accounts", "identified",
    "says", "said", "shows", "shown", "states", "stated",
})


def claim_anchors(claim: str, work_title: str) -> frozenset:
    """Topical terms the claim supplies BEYOND the extracted work title.

    Feeds guard 4 in series_resolver. Three exclusions, each load-bearing:

    - Years and bare numerals. A year is the value under test, and a numeral like
      "12" in "12 modifiable risk factors" would anchor on any label containing a
      number.
    - Function words and reporting verbs (`_ANCHOR_STOP`). "that" is not a topic,
      and a label containing it would be rescued on no topical evidence at all.
    - `series_resolver._STOP`, applied inside `_tokens`.

    Every exclusion makes guard 4 STRICTER -- fewer anchors means fewer members
    survive, which means more abstentions. That is the safe direction for a check
    that can emit FALSE: a missing anchor costs coverage, a spurious one buys a
    confident-wrong verdict.
    """
    terms = SR._tokens(strip_years(claim)) - SR._tokens(work_title)
    return frozenset(t for t in terms
                     if len(t) > 2 and t not in _ANCHOR_STOP
                     and not any(ch.isdigit() for ch in t))


def verify_l1b(row: dict, cache: dict) -> dict:
    """Run whichever routes the gate licenses. Never returns TRUE."""
    claim = row.get("claim", "") or ""
    f = extract_frame(claim)
    out = {
        "claim_id": row.get("claim_id", ""), "claim": claim,
        "gold_verdict": row.get("gold_verdict", ""),
        "synthetic": str(row.get("synthetic", "")),
        "injection_type": row.get("injection_type", ""),
        "work_title": f["work_title"], "claimed_year": f["claimed_year"] or "",
        "year_role": f["year_role"], "org": f["org"], "gate": f["gate"],
        "verdict": "UNVERIFIABLE", "confidence": 0.0, "route": "",
        "span": "", "span_mode": "", "qid": "", "resolution_score": "",
        "anchors": "", "reason": f["gate_reason"],
    }
    if f["gate"] == "NONE":
        out["route"] = "gated"
        return out

    # ---- DATE route ------------------------------------------------------
    if f["gate"] in ("DATE", "BOTH"):
        anchors = claim_anchors(claim, f["work_title"])
        out["anchors"] = " ".join(sorted(anchors))[:120]
        sp = SR.resolve_edition_span(f["work_title"], cache,
                                     ctx=strip_years(claim), anchors=anchors)
        out["span_mode"] = sp["mode"]
        out["span"] = "" if not sp["span"] else f"{sp['span'][0]}-{sp['span'][1]}"
        if sp.get("members"):
            out["qid"] = sp["members"][0]["qid"]
            out["resolution_score"] = sp["members"][0]["score"]
        t = SR.test_year_in_span(f["claimed_year"], sp)
        if t["verdict"] == "FALSE":
            out.update(verdict="FALSE", confidence=L1B_FALSE_DATE, route="date",
                       reason=f"{f['year_role']} year {f['claimed_year']}: {t['detail']}")
            return out
        out["route"] = "date"
        out["reason"] = f"date route abstained: {t['detail']}"

    # ---- PUBLISHER route -------------------------------------------------
    if f["gate"] in ("PUBLISHER", "BOTH"):
        from property_resolver import fetch_entity_claims
        from quantitative_verifier import resolve_entity
        # Resolve the work WITHOUT the acronym: "WHO Sixth Assessment Report" must
        # find the real AR6, or the fabrication has nothing to conflict with.
        bare = " ".join(t for t in f["work_title"].split()
                        if t not in {f["org"]} and t.lower() != f["org"].lower())
        r = resolve_entity(bare or f["work_title"], cache, ctx=strip_years(claim))
        qid = r.get("qid") or ""
        if qid:
            out["qid"] = out["qid"] or qid
            out["resolution_score"] = out["resolution_score"] or round(
                r.get("score", 0.0), 3)
            claims = fetch_entity_claims(qid, cache)
            chk = SC.check_source(qid, f["org"], cache, claims=claims)
            if chk["verdict"] == "CONFLICT":
                out.update(verdict="FALSE", confidence=L1B_FALSE_PUBLISHER,
                           route=(out["route"] + "+publisher").lstrip("+"),
                           reason=f"publisher conflict: {chk['detail']}")
                return out
            out["route"] = (out["route"] + "+publisher").lstrip("+")
            out["reason"] = (f"{out['reason']}; publisher {chk['verdict']}: "
                             f"{chk['detail']}").lstrip("; ")
        else:
            out["route"] = (out["route"] + "+publisher").lstrip("+")
            out["reason"] = (f"{out['reason']}; work {bare!r} not resolvable: "
                             f"{r.get('detail', '')}").lstrip("; ")
    return out


# =============================================================================
# GATE CASES -- every one is a real claim string from the corpus, and the expected
# gate is asserted. These run with no network at all.
GATE_CASES = [
    # (claim, want_gate, want_year, want_role, why)
    ("The IPCC Sixth Assessment Report was published in 2024.",
     "BOTH", 2024, "PUBLICATION", "SYN_CITA_063 -- the clean publication case"),
    ("The 2021 Lancet Commission identified 12 modifiable risk factors that "
     "account for 40% of dementia cases.",
     "DATE", 2021, "EDITION",
     "SYN_CITA_068 -- attributive year, OUTSIDE the title-case run"),
    ("The World Bank reported in 2024 that the global extreme poverty rate "
     "remained stagnant at 8.4% of the population.",
     "NONE", None, "UNLICENSED",
     "SYN_CITA_073 -- 'reported in' is the REPORTING act, and 'World Bank' is a "
     "bare organisation. Both halves of the gate reject it independently"),
    ("WHO reports that approximately 149 million children under five suffered "
     "from stunting in 2022.",
     "NONE", None, "UNLICENSED",
     "SYN_CITA_082 -- 2022 is when the STUNTING happened. The trap this gate exists "
     "for: reading it as a publication year manufactures a false alarm"),
    ("The WHO Sixth Assessment Report was published in 2023.",
     "BOTH", 2023, "PUBLICATION",
     "SYN_CITA_075 -- fabricated composite; the year is the TRUE one, so only the "
     "publisher route can catch it"),
    ("The WHO report attributed the rise in food insecurity to the combined "
     "effects of conflict, economic shocks, and climate extremes.",
     "NONE", None, "", "SYN_CITA_084 -- '<ORG> report' is a bare reference"),
    ("The Food and Agriculture Organization (WHO) publishes the State of World "
     "Fisheries and Aquaculture report every two years.",
     "PUBLISHER", None, "",
     "SYN_CITA_085 -- two title runs; the LONGER one is the cited work, and the "
     "acronym is the swapped-in organisation"),
    ("The Food and Agriculture Organization (FAO) publishes the State of World "
     "Fisheries and Aquaculture report every two years.",
     "PUBLISHER", None, "",
     "B3_12_C01 -- gold TRUE, same shape. Only the acronym differs, so the gate "
     "MUST treat them identically and let the graph decide"),
    ("The International Energy Agency reported in its 2024 Renewables report "
     "that global renewable capacity additions rose.",
     "NONE", 2024, "EDITION",
     "B3_02_C01 -- gold TRUE. 'Renewables' is one content word, so the title gate "
     "abstains even though the year IS attributive"),
    ("The World Health Organization's Global Air Quality Guidelines lower the "
     "recommended levels of fine particulate matter.",
     "NONE", None, "",
     "Q11_C03 -- gold TRUE, no acronym and no year, so nothing is licensed. "
     "'Guidelines' is deliberately NOT a generic work noun"),
    ("The CDC World Mental Health Report 2022 emphasizes that mental health gaps "
     "are driven by insufficient funding and systemic neglect.",
     "PUBLISHER", None, "UNLICENSED",
     "SYN_CITA_081 -- a TRAILING year is inside the run, not attributive to it, so "
     "it is unlicensed and only the publisher route runs"),
    ("These ten specific criteria were established by the 1972 World Heritage "
     "Convention.",
     "DATE", 1972, "EDITION",
     "B3_05_C02 -- gold FALSE but the YEAR IS RIGHT. The date route must abstain "
     "here; the falsity is in the content and belongs to Level 2"),
]

# Live route cases: (claim, want_verdict, why)
LIVE_CASES = [
    ("The IPCC Sixth Assessment Report was published in 2033.",
     "FALSE", "SYN_CITA_066 -- outside the 2021-2023 span"),
    ("The IPCC Sixth Assessment Report was published in 2023.",
     "UNVERIFIABLE", "Q5_C01 gold TRUE -- REGRESSION GUARD"),
    ("The IPCC Sixth Assessment Report was published in 2022.",
     "UNVERIFIABLE",
     "THE MEMBERSHIP TRAP -- 2022 is not among AR6's two P577 values but WG2/WG3 "
     "did appear then, so span-not-membership must abstain"),
    ("The 2030 Lancet Commission identified 12 modifiable risk factors that "
     "account for 40% of dementia cases.",
     "UNVERIFIABLE",
     "SYN_CITA_071 -- A DETECTION DELIBERATELY GIVEN UP. This returned FALSE before "
     "guard 4, but off the span 2014-2018 built from three unrelated Lancet "
     "Commissions (Editor's note 2015, Value of Death 2018, UK nursing 2014). That "
     "span is MISPLACED, not merely narrow, and it read its gold-TRUE twin Q12_C01 "
     "(2020) FALSE too. A detection off a wrong span is luck; the guard that saves "
     "the twin necessarily removes it, and that is the right trade"),
    ("The 2020 Lancet Commission identified 12 modifiable risk factors that "
     "account for 40% of dementia cases.",
     "UNVERIFIABLE", "Q12_C01 gold TRUE -- REGRESSION GUARD"),
    ("The WHO Sixth Assessment Report was published in 2023.",
     "FALSE", "SYN_CITA_075 -- P123 of AR6 is the IPCC, so a WHO expectation "
              "conflicts. The date is TRUE, so only the publisher route reaches it"),
    ("The IPCC Sixth Assessment Report was published in 2023.",
     "UNVERIFIABLE",
     "the must-not-veto control for the line above: same claim, correct acronym"),
]


def _selftest() -> None:
    fails = []

    def check(label, ok, extra=""):
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" -- {extra}" if extra else ""))
        if not ok:
            fails.append(label)

    print("-- offline: the gate, on real corpus strings --")
    for claim, want_gate, want_year, want_role, why in GATE_CASES:
        f = extract_frame(claim)
        check(f"gate {f['gate']:<9} want {want_gate:<9} [{why[:44]}]",
              f["gate"] == want_gate,
              f"got {f['gate']}: {f['gate_reason'][:70]}")
        check(f"  year {str(f['claimed_year']):<6} role {f['year_role'] or '-':<12}",
              f["claimed_year"] == want_year and f["year_role"] == want_role,
              f"want {want_year}/{want_role}, work={f['work_title']!r}")

    print("\n-- offline: the two gate halves reject independently --")
    f = extract_frame("The WHO report was published in 2024.")
    check("'<ORG> report' + published-in still gates OUT", f["gate"] == "NONE",
          f"got {f['gate']} -- a licensed year must not rescue a bare org reference")
    f = extract_frame("The WHO and CDC Sixth Assessment Report was published in 2024.")
    check("two acronyms -> no publisher route", "PUBLISHER" not in f["gate"],
          f"got {f['gate']}")
    check("  but the date route survives", f["gate"] == "DATE", f"got {f['gate']}")

    print("\n-- offline: no TRUE verdict exists in this module --")
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    # Scan PRODUCTION code only. The first attempt scanned the whole file and failed
    # on its own check label, which contains the literal it was searching for.
    prod = src.split("# GATE CASES --")[0]
    check("no TRUE assignment in production code",
          not re.search(r"verdict\s*=\s*[\"']TRUE[\"']", prod),
          "1b may only subtract or refute; Level 1 owns the TRUE verdict")
    check("the scan actually covers verify_l1b", "def verify_l1b" in prod,
          "a split that cut too early would make the check above vacuous")

    print("\n-- live: the routes end to end --")
    from property_resolver import load_cache, save_cache
    cache = load_cache()
    for claim, want, why in LIVE_CASES:
        r = verify_l1b({"claim": claim, "claim_id": "ST", "gold_verdict": ""}, cache)
        check(f"{want:<13} [{why[:52]}]", r["verdict"] == want,
              f"got {r['verdict']} via {r['route'] or 'gated'}: {r['reason'][:78]}")

    print("\n-- live: non-circularity, measured rather than asserted --")
    # The signature check in series_resolver proves no year can be PASSED in. This
    # proves none LEAKS in: ctx is stripped of years, and anchors are a term set with
    # numerals removed, so perturbing the claimed year must leave the span identical.
    # A signature guarantee plus an unstripped ctx would have been the same bug in a
    # different channel.
    #
    # This MUST run on a claim that resolves to a real span. The Lancet claim now
    # returns NO_TOPICAL_MATCH at every year, so running it here would compare empty
    # to empty and pass while testing nothing -- a vacuous invariance check is worse
    # than none, because it reads as evidence. Hence AR6, plus an explicit non-vacuity
    # assertion below.
    base = "The IPCC Sixth Assessment Report was published in {}."
    spans = {}
    for y in (2021, 2022, 2033, 2133):
        r = verify_l1b({"claim": base.format(y), "claim_id": f"ST{y}",
                        "gold_verdict": ""}, cache)
        spans[y] = (r["span"], r["span_mode"], r["anchors"])
    observed = {v for v in spans.values()}
    check(f"span invariant to the claimed year: {sorted({v[0] for v in spans.values()})}",
          len(observed) == 1, f"{spans}")
    check("  ... and the span is non-empty, so the check above is not vacuous",
          all(v[0] and v[1] in ("SERIAL", "SINGLE_WORK") for v in spans.values()),
          f"modes {sorted({v[1] for v in spans.values()})}")
    # The verdicts still differ across those years -- invariance is a property of the
    # EVIDENCE, not of the answer. If both were invariant the verifier would be inert.
    verdicts = {y: verify_l1b({"claim": base.format(y), "claim_id": f"SV{y}",
                               "gold_verdict": ""}, cache)["verdict"]
                for y in (2022, 2133)}
    check(f"  ... while the verdict still varies: {verdicts}",
          len(set(verdicts.values())) == 2, f"{verdicts}")
    save_cache(cache)

    print()
    print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
    sys.exit(1 if fails else 0)


def _load_populations():
    import consolidate_claims as CC
    rows, _ = CC.load_all()
    nat = [r for r in rows
           if (r.get("type") or "").upper() == "CITATION"
           and (r.get("gold_verdict") or "").strip()
           and str(r.get("synthetic", "")).lower() != "true"]
    neg_path = os.path.join(HERE, "synthetic_negatives.csv")
    with open(neg_path, newline="", encoding="utf-8") as fh:
        neg = [r for r in csv.DictReader(fh)
               if (r.get("gold_type") or "").upper() == "CITATION"]
    return nat, neg


def _diagnose() -> None:
    from property_resolver import load_cache, save_cache
    nat, neg = _load_populations()
    print(f"natural CITATION: {len(nat)}  "
          f"gold={dict(collections.Counter(r['gold_verdict'] for r in nat))}")
    print(f"synthetic negatives: {len(neg)}  "
          f"{dict(collections.Counter(r['injection_type'] for r in neg))}")
    print("\nNOTE, measured not assumed: all 3 gold-FALSE natural claims are CONTENT")
    print("falsities, so max achievable TP on the natural set is 0. Every natural-set")
    print("FALSE below is a FALSE ALARM by construction.\n")

    cache = load_cache()
    rows = []
    for tag, pop in (("natural", nat), ("negative", neg)):
        print(f"=== {tag} " + "=" * 62)
        for i, r in enumerate(pop, 1):
            res = verify_l1b(r, cache)
            res["population"] = tag
            rows.append(res)
            flag = ""
            if res["verdict"] == "FALSE":
                flag = ("  <<< FALSE ALARM" if tag == "natural"
                        else "  <<< DETECTION")
            print(f"  [{i:>2}] {res['claim_id']:<14}{res['gate']:<9}"
                  f"{res['verdict']:<13}{(res['route'] or 'gated'):<16}"
                  f"{res['reason'][:52]}{flag}")
    save_cache(cache)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")

    print("\n-- gate disposition --")
    for tag in ("natural", "negative"):
        c = collections.Counter(r["gate"] for r in rows if r["population"] == tag)
        print(f"  {tag:<10}{dict(c)}")

    print("\n-- what it does --")
    nat_r = [r for r in rows if r["population"] == "natural"]
    neg_r = [r for r in rows if r["population"] == "negative"]
    fa = [r for r in nat_r if r["verdict"] == "FALSE"
          and r["gold_verdict"] == "TRUE"]
    tp = [r for r in neg_r if r["verdict"] == "FALSE"]
    print(f"  detections on the 25 negatives : {len(tp)}/{len(neg_r)}")
    print(f"  FALSE ALARMS on gold-TRUE natural: {len(fa)}/"
          f"{sum(1 for r in nat_r if r['gold_verdict'] == 'TRUE')}")
    by_inj = collections.Counter(r["injection_type"] for r in tp)
    for k, v in sorted(by_inj.items()):
        tot = sum(1 for r in neg_r if r["injection_type"] == k)
        print(f"    {k:<30}{v}/{tot}")
    by_work = collections.Counter((r["qid"] or "-") for r in tp)
    print(f"  detections by Wikidata item: {dict(by_work)}")
    print("  CONCENTRATION: state this wherever the count is quoted -- detections")
    print("  come from a handful of works, not from 'CITATION working'. Same caveat")
    print("  QUANTITATIVE's 6/6-from-P2044 carries.")
    if fa:
        print("\n  !! EVERY LINE BELOW IS A CONFIDENT-WRONG VERDICT -- the class the")
        print("  !! 2026-08-21 QID fix drove to zero. Fix the gate, do not tune it.")
        for r in fa:
            print(f"     {r['claim_id']:<14}{r['route']:<16}{r['reason'][:88]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--diagnose", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selftest()
    elif args.diagnose:
        _diagnose()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
