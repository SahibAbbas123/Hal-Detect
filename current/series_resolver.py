#!/usr/bin/env python3
"""Series-level resolution for serial publications: the year tests, never selects.

Written 2026-08-26. Task #17b -- the hard half of the serial-edition fix. The safety
half is `current/source_consistency.py`. Motivation:
`reference/citation_negatives_headroom_2026-08-25.md` §4.

THE CIRCULARITY THIS EXISTS TO BREAK
------------------------------------
Asked for `Lancet Commission on dementia prevention`, the resolver ACCEPTED a 2019
article @0.605 over the correct 2020 report @0.595 -- three works (2019 / 2024 /
2020) inside a 0.010 score band, the right one rejected by one hundredth of a point.
The accepted item's `P577 = 2019` would then falsify a gold-TRUE claim about the
*2020* Commission: a confident-wrong FALSE, the class the 2026-08-21 QID fix drove
to zero.

Neither existing fix reaches it:

  * the prominence tie-break is inert BY CONSTRUCTION -- every candidate has 0
    sitelinks, because no edition of a serial is famous *as an edition*;
  * editions share nearly all of their label, and the one token that discriminates
    them is THE YEAR, WHICH IS THE VALUE UNDER TEST.

So resolving the edition uses the claimed value to pick the entity that will then
judge the claimed value. That is not a tuning problem; it is a circular one.

THE FIX, AND WHY IT IS ENFORCED BY THE SIGNATURES
-------------------------------------------------
`resolve_edition_span()` takes NO claimed year. It cannot, because the parameter
does not exist. It returns a publication-date span built from the evidence alone.
`test_year_in_span()` is the only function that ever sees a claimed year, and it
receives a span it cannot influence.

The non-circularity is therefore a property of the interface rather than of the
author's discipline -- the same reason the prominence tie-break is applied as a
tie-break rather than as a term added to the score.

WIDEN, DO NOT RE-PICK
---------------------
The obvious design is "identify the series, then pick the right edition". This
module deliberately does NOT do that, and the reason is the circularity itself, not
any weakness in the clustering. Label clustering works fine -- all three Lancet
works group together at J >= 0.75 once edition markers are stripped. But a cluster
can only tell you that these items are editions of the same work; the single token
that says WHICH edition is the year, and the year is the value under test. So
"identify the series, then pick" still routes the claimed value into the selection.
Clustering is used here to decide who is in the comparison set, never to rank it.

Instead, when several plausible editions compete, the span is taken across ALL of
them. A claimed year outside the span of *every* candidate edition is wrong under
*any* resolution of the ambiguity -- so the verdict survives the very ambiguity that
caused the bug. Widening can only ever produce fewer FALSE verdicts than picking,
which is the direction that matters.

AN UNDATED MEMBER IS A HOLE IN THE SPAN, NOT A ZERO (found while building this)
------------------------------------------------------------------------------
The span rule below guards against P577 being incomplete *within* an item. The first
live run exposed the level-up version of the same trap: a MEMBER whose P577 is
absent entirely contributes nothing, so the span silently closes short of it.

  Q139937996  label 'Dementia prevention, intervention, and care: 2024 report of
              the Lancet standing Commission'      P577 = ABSENT

Span came back 2019-2020, and `year 2024 -> FALSE` -- a confident-wrong verdict on a
report that genuinely exists, manufactured by missing data. Exactly the class this
task was opened to remove, reproduced by the fix for it.

Two guards, in this order:

  1. HARVEST YEARS FROM LABELS as well as from P577. The item's own label says
     '2024' while its statements do not. That is evidence about the edition's date,
     it is read off the entity and never off the claim, and it can only ever widen
     the span -- so it is safe in the same sense the consistency check is safe.
     Restores the span to 2019-2024 and turns `2024 -> FALSE` into an abstention.
  2. If a member's date is STILL unknown after that -- no P577 and no label year --
     the span has a hole of unknown position, so no FALSE verdict outside it is
     sound. Return mode INCOMPLETE_SPAN with span=None and abstain. This is the
     documented preference: "detects 3 of 5 with no confident-wrong risk, versus 5
     of 5 with it -- take the 3."

A DEGENERATE SPAN IS THE MOST AGGRESSIVE RULE, NOT THE MOST CONSERVATIVE (guard 3)
---------------------------------------------------------------------------------
Also found while building this, and the sharper trap of the two, because guard 1
CAUSED it. Asked for `Poverty and Shared Prosperity`, resolution returns two
BYTE-IDENTICAL duplicate items, both the 2020 edition:

  Q139955780  @0.731  'Poverty and Shared Prosperity 2020 : Reversals...'  P577 = ABSENT
  Q139954726  @0.731  'Poverty and Shared Prosperity 2020 : Reversals...'  P577 = ABSENT

Guard 1 reads 2020 off both labels, so guard 2 does not fire -- and the span
collapses to (2020, 2020). Every year but one is then outside it, including 2023,
which is the ORIGINAL GOLD-TRUE value of SYN_CITA_073/074. Two "detections" bought
with a confident-wrong verdict on the base claim: the project's coverage-up /
precision-down pattern, occurring for a fourth time.

  3. A SERIAL whose members cover fewer than TWO DISTINCT YEARS yields
     INCOMPLETE_SPAN. For a serial the span must be bounded by evidence about the
     SERIES, and one edition says nothing about how far the series extends. Note it
     counts distinct YEARS, not members: duplicates inflate member count without
     adding edition coverage, which is exactly how this got through.

The general lesson, worth keeping: a span rule is conservative only while the span
is WIDE. Narrow it enough and the same rule becomes the most aggressive detector in
the system. Conservatism was a property of the data, not of the rule.

TWO MODES, ONE SPAN
-------------------
  SINGLE_WORK -- one item, several P577 values. IPCC AR6 resolves decisively
                 @0.946 and is multi-part across 2021-2023. Not a serial at all;
                 the span comes from its own statements.
  SERIAL      -- several near-identical competing editions. Span across members.

Both yield `[min_year, max_year]`, so the caller has one code path.

SPAN, NOT SET-MEMBERSHIP
------------------------
AR6 is published across 2021-2023 but Wikidata lists only two P577 values. A
membership test ("is the claimed year one of the P577 values") marks "published in
2022" FALSE, although WG2 and WG3 genuinely appeared in 2022 -- a manufactured
confident-wrong verdict from incomplete data. FALSE only OUTSIDE [min, max]; abstain
inside. On the current negatives this costs nothing (every claimed year is after
2023), which is exactly why the trap is easy to miss.

Modes
-----
  --selftest   offline logic checks + live spans for AR6 and the Lancet Commission
  --demo       narrated walk-through of both modes
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Publication date. The only property this module reads for the span.
PUB_DATE_PID = "P577"
# Series membership, when the data happens to carry it. A strong positive signal,
# but absent on most of the items that actually exhibit the bug, so it can only
# ever confirm a serial -- never rule one out.
SERIES_PID = "P179"

# Candidates this far below the leader still count as plausible editions. Reuses
# the resolver's own tie band so "close competitor" means one thing project-wide.
from property_resolver import _norm  # noqa: E402
from quantitative_verifier import RESOLUTION_TIE_BAND  # noqa: E402

# Year-stripped token overlap with the SUBJECT below which a candidate is not an
# edition of the requested work at all. Deliberately low: this filter exists to
# drop unrelated items, not to rank editions.
SUBJECT_OVERLAP_MIN = 0.25

_YEAR_RE = re.compile(r"(?<!\d)(1[5-9]\d\d|20\d\d|21\d\d)(?!\d)")
# Ordinal edition markers ("Sixth Assessment Report", "6th edition") discriminate
# editions exactly as years do, so they are stripped for the same reason.
_ORDINALS = {
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
    "ninth", "tenth", "eleventh", "twelfth", "1st", "2nd", "3rd", "4th", "5th",
    "6th", "7th", "8th", "9th", "10th", "11th", "12th",
}
_STOP = {"of", "the", "and", "on", "for", "in", "to", "a", "an", "at", "de",
         "report", "edition", "volume", "part"}


def strip_edition_markers(label: str) -> str:
    """Remove years and ordinals -- the tokens that distinguish editions.

    This is what makes two editions of one serial comparable, and it is also why
    the result must never be used to CHOOSE between them: the discriminating
    information has deliberately been destroyed.
    """
    s = _YEAR_RE.sub(" ", label or "")
    toks = [t for t in _norm(s).split() if t and t not in _ORDINALS]
    return " ".join(toks)


def _tokens(label: str) -> set[str]:
    return {t for t in strip_edition_markers(label).split() if t not in _STOP}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def extract_year(rendered: str) -> int | None:
    """First plausible 4-digit year in a rendered Wikidata time value.

    Tolerant by design: `_snak_value` has rendered times as '+2021-08-09T00:00:00Z',
    '2021-08-09' and '2021' across different call sites, and a span built from a
    subset of the dates is still a valid (merely wider) span.
    """
    m = _YEAR_RE.search(str(rendered or "").lstrip("+"))
    return int(m.group(1)) if m else None


def label_years(label: str) -> list[int]:
    """Every year appearing in an entity's own label.

    Guard 1 from the docstring. Read off the ENTITY, never off the claim, so it
    cannot reintroduce circularity; and it can only widen a span, so a spurious
    match costs coverage rather than correctness.
    """
    return sorted({int(m) for m in _YEAR_RE.findall(str(label or ""))})


# =============================================================================
# YEAR-FREE HALF. Note the absence of a `claimed_year` parameter -- that absence
# is the load-bearing part of this module.

def resolve_edition_span(subject: str, cache: dict, ctx: str = "") -> dict:
    """Publication-date span for `subject`, built without any claimed value.

    Returns {mode, span, members, detail, evidence} where mode is
    SINGLE_WORK / SERIAL / NO_RESOLUTION / NO_DATES and span is
    (min_year, max_year) or None.
    """
    from property_resolver import fetch_entity_claims
    from quantitative_verifier import resolve_entity

    res = resolve_entity(subject, cache, ctx=ctx)
    cands = res.get("candidates") or []
    if not cands:
        return {"mode": "NO_RESOLUTION", "span": None, "members": [],
                "detail": f"no candidates for {subject!r}", "evidence": {}}

    top_score = cands[0][1]
    # Plausible editions: close competitors that are still recognisably the
    # requested work. Both filters are computed from labels and scores only.
    members = []
    for c in cands:
        qid, score, label = c[0], c[1], c[2]
        if top_score - score > RESOLUTION_TIE_BAND:
            continue
        ov = jaccard(subject, label)
        if ov < SUBJECT_OVERLAP_MIN:
            continue
        members.append({"qid": qid, "score": round(score, 3), "label": label,
                        "subject_overlap": round(ov, 2)})

    if not members:
        # Resolution committed to something, but nothing looks like an edition of
        # the requested work. Fall back to the resolved item alone if there is one.
        if res.get("qid"):
            members = [{"qid": res["qid"], "score": round(res["score"], 3),
                        "label": cands[0][2], "subject_overlap": 0.0}]
        else:
            return {"mode": "NO_RESOLUTION", "span": None, "members": [],
                    "detail": res.get("detail", ""), "evidence": {}}

    # Sibling detection is purely descriptive -- it labels the mode for the report
    # and never changes which members contribute to the span.
    sibling_pairs = [
        (a["qid"], b["qid"])
        for i, a in enumerate(members) for b in members[i + 1:]
        if jaccard(a["label"], b["label"]) >= 0.60
        and strip_edition_markers(a["label"]) != a["label"].lower()
    ]

    years: list[int] = []
    evidence: dict[str, list[str]] = {}
    series_vals: set[str] = set()
    undated: list[str] = []
    for m in members:
        claims = fetch_entity_claims(m["qid"], cache) or {}
        raw = claims.get(PUB_DATE_PID, []) or []
        ys = sorted({y for y in (extract_year(v) for v in raw) if y})
        lys = label_years(m["label"])
        m["years"], m["label_years"] = ys, lys
        if raw:
            evidence[m["qid"]] = [str(v) for v in raw]
        if not ys and not lys:
            undated.append(m["qid"])
        years.extend(ys)
        years.extend(lys)
        for sv in claims.get(SERIES_PID, []) or []:
            series_vals.add(str(sv))

    if not years:
        return {"mode": "NO_DATES", "span": None, "members": members,
                "detail": (f"{len(members)} candidate edition(s), none carrying "
                           f"{PUB_DATE_PID} or a year in its label -- absence is "
                           f"not evidence, so this must abstain"),
                "evidence": evidence}

    span = (min(years), max(years))
    mode = "SERIAL" if len(members) > 1 else "SINGLE_WORK"
    distinct = sorted(set(years))

    if undated:
        # Guard 2. A member of unknown date puts a hole of unknown position in the
        # span, so no FALSE verdict outside it is sound. Report the partial span for
        # auditing, but hand the caller span=None so the abstain path is taken.
        return {"mode": "INCOMPLETE_SPAN", "span": None, "members": members,
                "partial_span": span, "evidence": evidence,
                "detail": (f"{len(undated)} of {len(members)} candidate edition(s) "
                           f"carry no {PUB_DATE_PID} and no year in the label "
                           f"({', '.join(undated)}); observed years only span "
                           f"{span[0]}-{span[1]}, so a FALSE outside that range "
                           f"could be an artifact of the missing edition")}

    if mode == "SERIAL" and len(distinct) < 2:
        # Guard 3. Found while building this, and the most dangerous of the three.
        # `Poverty and Shared Prosperity` returns two BYTE-IDENTICAL duplicates of
        # the 2020 edition, so member count is 2 but edition coverage is 1 and the
        # span collapses to (2020, 2020). Everything outside a single year then
        # reads FALSE -- including 2023, the gold-TRUE original value. The span
        # rule is supposed to be the conservative option; a one-year span inverts
        # it into the most aggressive one.
        #
        # For a serial, the span must be bounded by evidence about the SERIES, and
        # one edition says nothing about how far the series extends. This is also
        # why the test counts DISTINCT YEARS rather than members: duplicate items
        # inflate the member count without adding edition coverage.
        return {"mode": "INCOMPLETE_SPAN", "span": None, "members": members,
                "partial_span": span, "evidence": evidence,
                "detail": (f"{len(members)} candidate editions of a serial resolve "
                           f"to only {len(distinct)} distinct year ({distinct}) -- "
                           f"one edition does not bound a series, so the span is "
                           f"unusable. Duplicate items inflate member count "
                           f"without adding edition coverage")}

    if mode == "SERIAL":
        why = (f"{len(members)} competing editions within {RESOLUTION_TIE_BAND} of "
               f"the leader spanning {len(distinct)} distinct years; span taken "
               f"across ALL of them so the verdict does not depend on which one "
               f"resolution picked")
        if sibling_pairs:
            why += f"; {len(sibling_pairs)} label-sibling pair(s)"
        if series_vals:
            why += f"; shared {SERIES_PID} = {sorted(series_vals)}"
    else:
        why = (f"one work with {len(members[0].get('years', []))} "
               f"{PUB_DATE_PID} value(s); multi-part works span years the "
               f"statements do not individually list")
    return {"mode": mode, "span": span, "members": members,
            "detail": f"span {span[0]}-{span[1]} from {len(years)} date(s): {why}",
            "evidence": evidence}


# =============================================================================
# THE ONLY FUNCTION THAT SEES A CLAIMED YEAR.

def test_year_in_span(claimed_year: int | None, span_result: dict) -> dict:
    """Span rule: FALSE only strictly outside [min, max]; abstain inside.

    Returns {verdict, detail} with verdict in FALSE / UNVERIFIABLE.

    There is deliberately no TRUE. Being inside the span of a serial is not
    evidence that this particular edition carries this particular year -- it is
    evidence that the claim is not refutable from publication dates alone. The
    caller decides what to do with an abstention; it must not be read as support.
    """
    span = span_result.get("span")
    if claimed_year is None:
        return {"verdict": "UNVERIFIABLE", "detail": "no year in the claim"}
    if not span:
        return {"verdict": "UNVERIFIABLE",
                "detail": f"no span available ({span_result.get('mode')})"}
    lo, hi = span
    if claimed_year < lo or claimed_year > hi:
        return {"verdict": "FALSE",
                "detail": (f"claimed {claimed_year} is outside the published span "
                           f"{lo}-{hi} of every candidate edition")}
    return {"verdict": "UNVERIFIABLE",
            "detail": (f"claimed {claimed_year} falls inside {lo}-{hi}; the span "
                       f"rule abstains here rather than assert a match on "
                       f"possibly-incomplete {PUB_DATE_PID} data")}


# =============================================================================
LIVE = [
    ("IPCC Sixth Assessment Report", "", "SINGLE_WORK", (2021, 2023),
     "resolves decisively @0.874; multi-part across 2021-2023, and Wikidata lists "
     "only two P577 values -- the span rule's whole point"),
    ("Lancet Commission on dementia prevention", "dementia", "SERIAL", (2019, 2024),
     "the live bug: 2019/2024/2020 works inside a 0.010 band, correct one rejected "
     "by one hundredth. Span across all of them, so the verdict survives it. The "
     "upper bound 2024 comes from Q139937996's LABEL -- its P577 is absent, and "
     "without guard 1 the span closes at 2020 and calls the real 2024 report FALSE"),
    ("Poverty and Shared Prosperity", "extreme poverty", "INCOMPLETE_SPAN", None,
     "SYN_CITA_073/074. Two byte-identical duplicates of the 2020 edition, both "
     "with P577 absent, so guard 1 supplies 2020 twice and the span degenerates to "
     "(2020, 2020). Guard 3 must catch it: without it 2023 -- the gold-TRUE "
     "original value -- reads FALSE"),
]

# The actual perturbed years from current/synthetic_negatives.csv, so the selftest
# measures the real ceiling instead of a hand-picked one. `why` records what each
# probe protects.
YEAR_PROBES = [
    # -- IPCC AR6: the 5 SYN_CITA_063..067 year_shift rows, all gold FALSE.
    ("IPCC Sixth Assessment Report", 2024, "FALSE", "SYN_CITA_063"),
    ("IPCC Sixth Assessment Report", 2025, "FALSE", "SYN_CITA_064"),
    ("IPCC Sixth Assessment Report", 2028, "FALSE", "SYN_CITA_065"),
    ("IPCC Sixth Assessment Report", 2033, "FALSE", "SYN_CITA_066"),
    ("IPCC Sixth Assessment Report", 2123, "FALSE", "SYN_CITA_067"),
    ("IPCC Sixth Assessment Report", 2023, "UNVERIFIABLE",
     "the gold-TRUE base claim -- must NOT be called FALSE"),
    ("IPCC Sixth Assessment Report", 2022, "UNVERIFIABLE",
     "THE MEMBERSHIP TRAP: 2022 is not one of AR6's two P577 values, but WG2 and "
     "WG3 genuinely appeared in 2022. Set-membership would say FALSE here."),
    # -- Lancet Commission: the 5 SYN_CITA_068..072 rows. Ceiling is 3 of 5, and
    #    the 2 misses are the documented price of not manufacturing a wrong verdict.
    ("Lancet Commission on dementia prevention", 2021, "UNVERIFIABLE",
     "SYN_CITA_068 -- inside the span, MISSED by design"),
    ("Lancet Commission on dementia prevention", 2022, "UNVERIFIABLE",
     "SYN_CITA_069 -- inside the span, MISSED by design"),
    ("Lancet Commission on dementia prevention", 2025, "FALSE", "SYN_CITA_070"),
    ("Lancet Commission on dementia prevention", 2030, "FALSE", "SYN_CITA_071"),
    ("Lancet Commission on dementia prevention", 2120, "FALSE", "SYN_CITA_072"),
    ("Lancet Commission on dementia prevention", 2020, "UNVERIFIABLE",
     "the gold-TRUE base claim -- must NOT be called FALSE"),
    ("Lancet Commission on dementia prevention", 2024, "UNVERIFIABLE",
     "REGRESSION GUARD for the undated-member hole: the 2024 standing Commission "
     "report is real, and P577 is absent from it. Before guard 1 this was FALSE."),
    # -- World Bank: the 2 SYN_CITA_073/074 rows. Guard 3 abstains on both, and the
    #    2023 probe is why that is the right answer rather than a lost detection.
    ("Poverty and Shared Prosperity", 2024, "UNVERIFIABLE",
     "SYN_CITA_073 -- MISSED by design, guard 3"),
    ("Poverty and Shared Prosperity", 2025, "UNVERIFIABLE",
     "SYN_CITA_074 -- MISSED by design, guard 3"),
    ("Poverty and Shared Prosperity", 2023, "UNVERIFIABLE",
     "REGRESSION GUARD for the degenerate span: 2023 is the gold-TRUE original "
     "value. Without guard 3 the span is (2020,2020) and this reads FALSE, buying "
     "2 detections with a confident-wrong verdict on the base claim."),
]


def _selftest() -> None:
    fails = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}"
              + (f" -- {detail}" if detail else ""))
        if not cond:
            fails.append(label)

    print("series_resolver --selftest")

    print("\n-- offline: edition-marker stripping --")
    for raw, want_gone in [
        ("Dementia prevention, intervention, and care: 2020 report of the "
         "Lancet Commission", "2020"),
        ("IPCC Sixth Assessment Report", "sixth"),
        ("Poverty and Shared Prosperity 2020", "2020"),
    ]:
        got = strip_edition_markers(raw)
        check(f"{want_gone!r} stripped from {raw[:38]!r}", want_gone not in got,
              f"-> {got[:46]!r}")

    print("\n-- offline: all three Lancet works cluster as editions --")
    a = ("Dementia prevention, intervention, and care: 2020 report of the "
         "Lancet Commission")
    b = ("Dementia prevention, intervention, and care: 2024 report of the "
         "Lancet standing Commission")
    c = ("The Lancet Commission on Dementia Prevention, Intervention, and Care: "
         "a call for action")
    # Corrected 2026-08-26: an earlier version of this test asserted that (c) was
    # NOT a sibling, from a hand-computed Jaccard that forgot _STOP strips 'report'
    # and 'of'/'the'. It does cluster, at 0.75. Clustering was never the reason for
    # widening -- circularity is; see the docstring.
    for x, y, nm in [(a, b, "2020 vs 2024 report"), (a, c, "2020 vs 2019 article"),
                     (b, c, "2024 vs 2019 article")]:
        check(f"{nm} cluster as editions (>=0.60)", jaccard(x, y) >= 0.60,
              f"J={jaccard(x, y):.2f}")
    for lbl in (a, b, c):
        ov = jaccard("Lancet Commission on dementia prevention", lbl)
        check(f"subject overlap >= {SUBJECT_OVERLAP_MIN} for {lbl[:30]!r}",
              ov >= SUBJECT_OVERLAP_MIN, f"J={ov:.2f}")

    print("\n-- offline: year extraction from rendered time values --")
    for raw, want in [("+2021-08-09T00:00:00Z", 2021), ("2023-03-20", 2023),
                      ("2020", 2020), ("", None), ("no date here", None)]:
        check(f"extract_year({raw!r}) == {want}", extract_year(raw) == want,
              f"got {extract_year(raw)}")

    print("\n-- offline: guard 1, years harvested from the entity's own label --")
    check("Q139937996's label yields [2024]", label_years(b) == [2024],
          f"got {label_years(b)} -- its P577 is ABSENT, so this is the only "
          f"evidence that the span reaches 2024")
    check("a year-free label yields []", label_years(c) == [],
          f"got {label_years(c)}")
    check("multi-year labels yield all of them",
          label_years("The 1918 pandemic: a 2020 retrospective") == [1918, 2020],
          "widening is the safe direction, so a spurious hit costs coverage only")

    print("\n-- offline: the span rule, incl. the membership trap --")
    fake = {"mode": "SINGLE_WORK", "span": (2021, 2023)}
    for yr, want in [(2022, "UNVERIFIABLE"), (2021, "UNVERIFIABLE"),
                     (2023, "UNVERIFIABLE"), (2024, "FALSE"), (2123, "FALSE"),
                     (2019, "FALSE"), (None, "UNVERIFIABLE")]:
        got = test_year_in_span(yr, fake)["verdict"]
        check(f"year {yr} vs span 2021-2023 -> {want}", got == want, f"got {got}")
    check("no span never yields FALSE",
          test_year_in_span(2050, {"mode": "NO_DATES", "span": None})["verdict"]
          == "UNVERIFIABLE")
    print("\n-- offline: guard 2, an undated member forbids FALSE entirely --")
    inc = {"mode": "INCOMPLETE_SPAN", "span": None, "partial_span": (2019, 2020)}
    for yr in (2018, 2024, 2120):
        check(f"year {yr} vs INCOMPLETE_SPAN -> UNVERIFIABLE",
              test_year_in_span(yr, inc)["verdict"] == "UNVERIFIABLE",
              "a hole of unknown position makes FALSE outside the observed range "
              "unsound in BOTH directions")

    print("\n-- offline: the interface forbids circularity --")
    import inspect
    sig = inspect.signature(resolve_edition_span)
    check("resolve_edition_span takes no year parameter",
          not any("year" in p for p in sig.parameters),
          f"params={list(sig.parameters)}")

    print("\n-- live: spans built from evidence alone --")
    from property_resolver import load_cache, save_cache
    cache = load_cache()
    spans = {}
    for subject, ctx, want_mode, want_span, why in LIVE:
        r = resolve_edition_span(subject, cache, ctx=ctx)
        spans[subject] = r
        check(f"{subject[:38]!r} mode -> {want_mode}", r["mode"] == want_mode,
              f"got {r['mode']}: {r['detail'][:84]}")
        check(f"{subject[:38]!r} span -> {want_span}", r["span"] == want_span,
              f"got {r['span']}")

    print("\n-- live: the real perturbed years from synthetic_negatives.csv --")
    det, tot = collections.Counter(), collections.Counter()
    for subject, yr, want, why in YEAR_PROBES:
        r = test_year_in_span(yr, spans[subject])
        ok = r["verdict"] == want
        check(f"{subject[:24]:24s} year {yr} -> {want:12s} [{why[:30]}]", ok,
              "" if ok else f"got {r['verdict']}")
        if why.startswith("SYN_CITA"):
            tot[subject] += 1
            det[subject] += int(r["verdict"] == "FALSE")
    save_cache(cache)

    print("\n-- ceiling on the 12 CITATION year_shift negatives (MEASURED) --")
    total = 0
    for subject, _c, _m, _s, _w in LIVE:
        d, t = det[subject], tot[subject]
        total += d
        print(f"    {subject[:34]:34s} {d}/{t}   mode={spans[subject]['mode']}")
    print(f"    {'TOTAL':34s} {total}/12")
    print("    CONCENTRATION: state this wherever the number is quoted. The")
    print("    detections come from a small number of works, not from CITATION")
    print("    working -- the same caveat QUANTITATIVE's 6/6-from-P2044 carries.")
    check("IPCC detects 5/5", det["IPCC Sixth Assessment Report"] == 5,
          f"got {det['IPCC Sixth Assessment Report']}")
    check("Lancet detects exactly 3/5 (the documented ceiling)",
          det["Lancet Commission on dementia prevention"] == 3,
          f"got {det['Lancet Commission on dementia prevention']} -- 5/5 here "
          f"would mean the 2024 hole is back")
    check("World Bank detects 0/2 (guard 3 abstains rather than risk 2023)",
          det["Poverty and Shared Prosperity"] == 0,
          f"got {det['Poverty and Shared Prosperity']}")

    print()
    print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
    sys.exit(1 if fails else 0)


def _demo() -> None:
    from property_resolver import load_cache, save_cache
    cache = load_cache()
    print("Series-level resolution: the year tests, it never selects.")
    print("=" * 78)
    for subject, ctx, want_mode, want_span, why in LIVE:
        r = resolve_edition_span(subject, cache, ctx=ctx)
        print(f"\n>>> {subject!r}")
        print(f"    why: {why}")
        print(f"    mode  = {r['mode']}")
        print(f"    span  = {r['span']}"
              + (f"   (partial {r['partial_span']})" if r.get("partial_span") else ""))
        print(f"    {r['detail']}")
        for m in r["members"]:
            print(f"      {m['qid']:12s} @{m['score']:.3f} "
                  f"ov={m['subject_overlap']:.2f} P577={m.get('years')} "
                  f"label_years={m.get('label_years')} {m['label'][:44]!r}")
        for yr in (2019, 2020, 2021, 2023, 2024, 2025, 2030, 2120):
            t = test_year_in_span(yr, r)
            print(f"      year {yr} -> "
                  + ("FALSE  " if t["verdict"] == "FALSE" else "abstain"))
    save_cache(cache)
    print("\n" + "=" * 78)
    print("Note the asymmetry: there is no TRUE verdict. Inside the span means")
    print("'not refutable from publication dates', never 'confirmed'.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        _selftest()
    elif args.demo:
        _demo()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
