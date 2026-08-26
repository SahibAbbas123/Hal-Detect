"""P31/P279 type consistency -- an INDEPENDENT signal on entity resolution.

Task #21. Built as a SIBLING of source_consistency.py, never an edit to a
validated verifier.

WHY THIS EXISTS
---------------
The resolver's recorded "72/72 correct" was verified by checking the chosen
entity's LABEL against the subject string -- the same signal used for selection.
That is circular, so CLAUDE.md downgrades it to "0% refusal, correctness
unverified by an independent signal". A label check cannot catch
wrong-sense-same-name, which is the original bug (failure mode #1):

    "Panama Canal"  -> Q498979 Panama Canal Zone   (an ADMINISTRATIVE TERRITORY)
    "Rosetta Stone" -> Q1703969 Rosetta Stone      (a BRITISH PUNK BAND)

Both wrong entities pass a label check perfectly. Their TYPES do not.
P31/P279 typing is independent of the label, and fine-grained P31/P279 typing is
how ReFinED (Ayoola et al. 2022) scores its own candidates -- so this is the
mechanism a SOTA entity linker relies on, not a local heuristic.

SAFETY MODEL -- three states, and CONFLICT requires POSITIVE evidence
--------------------------------------------------------------------
    CONSISTENT      the entity's bounded type closure meets an expected family
    CONFLICT        EVERY family the entity is in is EXPLICITLY disjoint from
                    EVERY expected family
    NO_EVIDENCE     anything else: no P31, unmapped types, an unlisted pair
    NO_EXPECTATION  the caller supplied no expectation

The point of the "every ... every" rule is that a gap in these tables, an
unusual Wikidata class, or a truncated closure yields NO_EVIDENCE -- the status
quo, no veto -- rather than a false veto. Never-reached is not disjoint.

Like source_consistency, this check only ever REMOVES a verdict, so both error
directions are safe: a missed conflict leaves today's behaviour unchanged, and a
spurious CONSISTENT cannot manufacture a confident-wrong verdict. It can only
fail to prevent one.

TWO MEASURED CONSTRAINTS ON THE DESIGN
--------------------------------------
1. DEPTH IS CAPPED AT 2, and that is not arbitrary. citation_l1_verifier.py:76
   already declined an unbounded P279* walk -- "a broad subclass walk lets almost
   anything qualify, which would rebuild the tautology in a new shape". Probed
   2026-08-27, depth 2 ALREADY collides across domains: a ship canal (Q949819)
   and a stele (Q178743) both reach `architectural structure` (Q811979). Depth 2
   is the point where the fine-to-coarse lift is done (ship canal -> canal,
   waterway; stele -> monument, archaeological artefact) but before the upper
   ontology flattens everything together.

2. WIKIDATA'S UPPER ONTOLOGY HAS UNION CLASSES THAT MERGE FAMILIES. Measured:
   `organization` (Q43229) reaches `person or organization` (Q106559804), and
   `human` (Q5) reaches `legal person` (Q3778211). A naive closure comparison
   therefore concludes a person IS an organization. Every such class is listed
   in HUB_CLASSES and deliberately excluded from every family.

   State the mechanism precisely, because the obvious phrasing is wrong. The
   runtime filter in families_of_closure() is INERT BY CONSTRUCTION while the
   selftest's first check passes: that check asserts no hub QID is a family
   anchor, and if no hub is an anchor then dropping hubs from a closure cannot
   change which anchors it intersects. Measured 2026-08-27 -- emptying
   HUB_CLASSES changes the families of 0 of the 13 INVARIANT_QIDS. That is
   defence in depth, not redundancy: check #1 DETECTS a hub wrongly added as an
   anchor, and the filter NEUTRALISES the same mistake, so the two selftest
   checks exercise one each. An earlier pair of checks claimed to prove "hub
   exclusion works" and could not fail; they were found by proving the selftest
   non-vacuous rather than by reading its PASS, and replaced.

THE CURATED PART, STATED PLAINLY
--------------------------------
FAMILIES and DISJOINT are hand-curated, and this project has already been bitten
by a curated class list once: citation_l1_verifier's first version required P31
to be in SOURCE_CLASSES and downgraded FOUR correctly-resolved entities (IPCC
AR6, CDC, World Bank, IEA) purely because Wikidata used a class the list did not
anticipate. The lesson taken there was to prefer a structural signal (P856) over
enumeration.

The same hazard is live here, with one difference that matters: an unanticipated
class makes this check return NO_EVIDENCE, which changes nothing, whereas L1's
list produced a wrong weak verdict. So the failure is lost COVERAGE, not a wrong
answer. Expect the CONFLICT rate in the wild to be low, and measure it rather
than assume it -- that is what --audit is for.

Reproduce:  python type_consistency.py --selftest      (offline logic + 7 live)
            python type_consistency.py --demo
            python type_consistency.py --audit CSV     (live; needs go-ahead)
Model calls: zero. Wikidata API only, through property_resolver's cache.
"""
from __future__ import annotations

import argparse
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import property_resolver as PR           # noqa: E402

# -----------------------------------------------------------------------------
# DEPTH
# -----------------------------------------------------------------------------
# See docstring note 1. Raising this is not a free "more coverage" move: it
# imports the upper ontology, where everything is an object, and the DISJOINT
# table stops meaning anything. Lowering it to 1 loses the fine-to-coarse lift
# that makes the anchors reachable at all.
MAX_DEPTH = 2

# -----------------------------------------------------------------------------
# HUB / UNION CLASSES -- never a family anchor
# -----------------------------------------------------------------------------
# Each of these is either an explicit union of two families, or so general that
# unrelated entities meet in it. Measured from live closures 2026-08-27; the
# comment records WHICH closure exposed it, because that is the evidence.
HUB_CLASSES = {
    "Q106559804": "person or organization -- an explicit UNION; in Q43229's closure",
    "Q3778211": "legal person -- in Q5's closure, and organizations are legal persons",
    "Q155076": "juridical person -- in Q3624078's closure, same collision",
    "Q223557": "physical object -- meets canal, stele, inscription",
    "Q488383": "object",
    "Q386724": "work -- meets the Rosetta Stone and every publication",
    "Q17537576": "creative work",
    "Q15621286": "intellectual work",
    "Q88392887": "part of a work",
    "Q811979": "architectural structure -- REACHED BY BOTH a ship canal and a stele",
    "Q795052": "individual",
    "Q24229398": "being",
    "Q1639378": "social system",
    "Q854457": "complex system",
    "Q58778": "system",
    "Q830077": "subject",
    "Q53617489": "independent continuant",
    "Q340169": "communications media -- too broad; meets inscriptions and articles",
    "Q3523102": "source of information",
    "Q3750478": "historical source",
    "Q16686448": "artificial object -- meets a canal and a stele",
    "Q729": "animal -- biological, would admit non-persons to PERSON",
    "Q164509": "omnivore",
    "Q72638": "consumer",
}

# -----------------------------------------------------------------------------
# FAMILIES -- every QID below was read off live Wikidata (R1), never recalled
# -----------------------------------------------------------------------------
FAMILIES: dict[str, dict[str, str]] = {
    "PERSON": {
        "Q5": "human",
        "Q215627": "person",
        "Q154954": "natural person",
        "Q2250224": "individual person",
        "Q5891007": "anatomically modern human",
        "Q15978631": "Homo sapiens",
    },
    "ORGANIZATION": {
        "Q43229": "organization",
        "Q16334295": "group of humans",
        "Q106668099": "corporate body",
        "Q134601727": "group of persons",
        "Q99527517": "collective entity",
        "Q131085629": "collective agent",
        "Q215380": "musical group",
        "Q2088357": "musical ensemble",
        "Q32178211": "music organization",
        "Q105815710": "performing arts group",
        "Q327333": "government agency",
        "Q2659904": "government organization",
        "Q17505024": "space agency",
        "Q11753232": "launch service provider",
        "Q136410232": "research organization",
    },
    "ADMIN_TERRITORY": {
        "Q56061": "administrative territorial entity",
        "Q3268571": "administrative territorial entity of a single country",
        "Q852446": "administrative territorial entity of the United States",
        "Q783733": "unincorporated territory of the United States",
        "Q161243": "dependent territory",
        "Q1048835": "political territorial entity",
        "Q4835091": "territory",
        "Q82794": "region",
        "Q6256": "country",
        "Q3624078": "sovereign state",
        "Q7275": "state",
    },
    "NATURAL_PLACE": {
        "Q2221906": "geographic location",
        "Q618123": "geographical feature",
        "Q271669": "landform",
        "Q35145263": "natural geographic object",
        "Q27096220": "natural geographic entity",
        "Q16686022": "natural physical object",
        "Q8502": "mountain",
        "Q106589819": "elevation",
    },
    "WATERWAY": {
        "Q1267889": "waterway",
        "Q12284": "canal",
        "Q949819": "ship canal",
        "Q15324": "body of water",
        "Q355304": "watercourse",
        "Q12376661": "artificial body of water",
    },
    "STRUCTURE": {
        "Q121359": "infrastructure",
        "Q2466889": "hydraulic structure",
        "Q11794693": "linear construction",
        "Q924286": "transport network",
        "Q83620": "thoroughfare",
        "Q136749248": "way",
    },
    "PHYSICAL_ARTIFACT": {
        "Q8205328": "artificial physical object",
        "Q220659": "archaeological artefact",
        "Q4989906": "monument",
        "Q5003624": "memorial",
        "Q178743": "stele",
        "Q1791627": "cultural artifact",
        "Q838948": "work of art",
        "Q97570030": "carving",
    },
    "WRITTEN_WORK": {
        "Q47461344": "written work",
        "Q732577": "publication",
        "Q49848": "document",
        "Q234460": "text",
        "Q1640824": "inscription",
        "Q191067": "article",
        "Q13442814": "scholarly article",
        "Q591041": "scientific publication",
        "Q10383930": "academic work",
        "Q55915575": "scholarly work",
        "Q11826511": "scientific work",
        "Q10870555": "report",
        "Q3099732": "technical report",
        "Q113992938": "IPCC report",
        "Q871232": "editorial",
        "Q59908": "opinion piece",
        "Q267628": "column",
        "Q5707594": "news article",
        "Q30070590": "magazine article",
        "Q12042160": "scientific non-fiction literature",
        "Q68200780": "scholarly literature",
        "Q27801": "non-fiction literature",
        "Q1391420": "specialized literature",
        "Q213051": "non-fiction",
    },
}

# -----------------------------------------------------------------------------
# DISJOINT -- the ONLY pairs that may produce a CONFLICT
# -----------------------------------------------------------------------------
# A pair belongs here only if NO single entity can be in both. The selftest
# enforces that empirically: if any probed entity occupies two families listed
# here, the pair is WRONG and the test fails -- one entity in both disproves it.
_DISJOINT_SPEC = {
    "PERSON": ["ORGANIZATION", "ADMIN_TERRITORY", "NATURAL_PLACE", "WATERWAY",
               "STRUCTURE", "PHYSICAL_ARTIFACT", "WRITTEN_WORK"],
    "ORGANIZATION": ["NATURAL_PLACE", "WATERWAY", "STRUCTURE",
                     "PHYSICAL_ARTIFACT", "WRITTEN_WORK"],
    "ADMIN_TERRITORY": ["WATERWAY", "STRUCTURE", "PHYSICAL_ARTIFACT",
                        "WRITTEN_WORK"],
    "NATURAL_PLACE": ["STRUCTURE", "PHYSICAL_ARTIFACT", "WRITTEN_WORK"],
    "WATERWAY": ["WRITTEN_WORK"],
    "STRUCTURE": ["WRITTEN_WORK"],
}
DISJOINT = {frozenset((a, b)) for a, bs in _DISJOINT_SPEC.items() for b in bs}

# Pairs DELIBERATELY LEFT OUT, with the reason. These are the conservative
# choices -- each one costs CONFLICT coverage and buys safety. Measured cases
# are marked; the rest are conceptual and could be revisited WITH evidence.
NOT_DISJOINT = {
    ("PHYSICAL_ARTIFACT", "WRITTEN_WORK"):
        "MEASURED: the Rosetta Stone (Q48584) is a stele AND an inscription",
    ("STRUCTURE", "PHYSICAL_ARTIFACT"):
        "MEASURED: a stele reaches architectural structure",
    ("WATERWAY", "STRUCTURE"):
        "MEASURED: a ship canal is a waterway AND a hydraulic structure",
    ("WATERWAY", "PHYSICAL_ARTIFACT"):
        "a canal is an artificial object; the boundary is not clean",
    ("NATURAL_PLACE", "WATERWAY"):
        "a lake or river is both a body of water and a natural feature",
    ("ORGANIZATION", "ADMIN_TERRITORY"):
        "a state is arguably an organization; both closures reach juridical person",
    ("ADMIN_TERRITORY", "NATURAL_PLACE"):
        "a country is a geographic entity under much modelling",
}

# -----------------------------------------------------------------------------
# The expectation side: which family may bear which property.
# -----------------------------------------------------------------------------
# CURATED, and that is the weakest part of this module -- see the docstring's
# note on citation_l1_verifier's SOURCE_CLASSES. `--probe-constraints` prints
# what Wikidata's OWN type constraint says for each PID so this map can be
# audited against the source rather than trusted.
PROPERTY_EXPECTATION: dict[str, set[str]] = {
    "P2044": {"NATURAL_PLACE", "ADMIN_TERRITORY", "STRUCTURE"},   # elevation
    "P2046": {"NATURAL_PLACE", "ADMIN_TERRITORY", "WATERWAY"},    # area
    "P1082": {"ADMIN_TERRITORY", "NATURAL_PLACE"},                # population
    "P2047": {"STRUCTURE", "WATERWAY", "NATURAL_PLACE"},          # duration
    "P569": {"PERSON"},                                           # date of birth
    "P570": {"PERSON"},                                           # date of death
    "P571": {"ORGANIZATION", "STRUCTURE", "WATERWAY",
             "ADMIN_TERRITORY"},                                  # inception
    "P1619": {"STRUCTURE", "WATERWAY", "ORGANIZATION"},           # official opening
    "P577": {"WRITTEN_WORK"},                                     # publication date
    "P123": {"WRITTEN_WORK"},                                     # publisher
    "P1433": {"WRITTEN_WORK"},                                    # published in
    "P186": {"PHYSICAL_ARTIFACT", "STRUCTURE"},                   # made from material
    "P610": {"ADMIN_TERRITORY", "NATURAL_PLACE"},                 # highest point
}

VERDICTS = ("CONSISTENT", "CONFLICT", "NO_EVIDENCE", "NO_EXPECTATION")


# -----------------------------------------------------------------------------
# PURE LOGIC -- no network, so the selftest can cover it offline
# -----------------------------------------------------------------------------
def families_of_closure(closure: dict[str, int] | set[str]) -> set[str]:
    """Map a type closure to family names. Hub classes never contribute."""
    qids = {q for q in closure if q not in HUB_CLASSES}
    out = set()
    for fam, anchors in FAMILIES.items():
        if qids & set(anchors):
            out.add(fam)
    return out


def decide(entity_families: set[str], expected: set[str] | None) -> tuple[str, str]:
    """The whole verdict rule, isolated and offline-testable.

    Returns (verdict, detail). CONFLICT demands that EVERY entity family be
    explicitly disjoint from EVERY expected family, so one unlisted or
    non-disjoint pair is enough to fall back to NO_EVIDENCE.
    """
    if not expected:
        return "NO_EXPECTATION", "no expected family supplied"
    if not entity_families:
        return "NO_EVIDENCE", "entity has no recognised type family"
    hit = entity_families & expected
    if hit:
        return "CONSISTENT", f"entity is {'/'.join(sorted(hit))}, as expected"
    pairs = [(e, x) for e in sorted(entity_families) for x in sorted(expected)]
    unlisted = [p for p in pairs if frozenset(p) not in DISJOINT]
    if unlisted:
        return ("NO_EVIDENCE",
                f"no overlap, but {len(unlisted)}/{len(pairs)} pair(s) not "
                f"declared disjoint, e.g. {unlisted[0][0]} vs {unlisted[0][1]}")
    return ("CONFLICT",
            f"entity is {'/'.join(sorted(entity_families))}, expected "
            f"{'/'.join(sorted(expected))}; every pair explicitly disjoint")


def expectation_for(pid: str | None,
                    expected_families: set[str] | None) -> set[str] | None:
    """Explicit families win; otherwise fall back to the property map."""
    if expected_families:
        return set(expected_families)
    if pid:
        return set(PROPERTY_EXPECTATION.get(pid, set())) or None
    return None


# -----------------------------------------------------------------------------
# LIVE PATH
# -----------------------------------------------------------------------------
def type_closure(qid: str, cache: dict, max_depth: int = MAX_DEPTH) -> dict[str, int]:
    """Bounded P279 closure over the entity's P31 values. {qid: min_depth}.

    Depth 0 is the direct P31 set. Returns {} when the entity has no P31 at all
    (Q68487022 'human liver' is a real such case), which decide() turns into
    NO_EVIDENCE rather than a veto.
    """
    claims = PR.fetch_entity_claims(qid, cache) or {}
    seeds = [v for v in claims.get("P31", [])
             if isinstance(v, str) and v.startswith("Q") and v[1:].isdigit()]
    out = {s: 0 for s in seeds}
    frontier = list(seeds)
    for d in range(1, max_depth + 1):
        nxt = []
        for q in frontier:
            cl = PR.fetch_entity_claims(q, cache) or {}
            for s in cl.get("P279", []):
                if (isinstance(s, str) and s.startswith("Q")
                        and s[1:].isdigit() and s not in out):
                    out[s] = d
                    nxt.append(s)
        frontier = nxt
        if not frontier:
            break
    return out


def check_type(qid: str, cache: dict, pid: str | None = None,
               expected_families: set[str] | None = None,
               subject: str = "") -> dict:
    """Independent type check on a resolved entity.

    Mirrors source_consistency.check_source's contract: returns
    {verdict, detail, evidence} and never raises on a missing entity.
    """
    out = {"qid": qid, "subject": subject, "pid": pid or "",
           "verdict": "NO_EVIDENCE", "detail": "", "families": "",
           "expected": "", "evidence": ""}
    expected = expectation_for(pid, expected_families)
    out["expected"] = "/".join(sorted(expected)) if expected else ""
    if not qid:
        out["detail"] = "no qid to check"
        return out
    closure = type_closure(qid, cache)
    fams = families_of_closure(closure)
    out["families"] = "/".join(sorted(fams))
    out["verdict"], out["detail"] = decide(fams, expected)
    direct = [q for q, d in closure.items() if d == 0]
    labs = PR.fetch_item_labels(direct[:6], cache) if direct else {}
    out["evidence"] = ("P31=" + ", ".join(f"{labs.get(q, q)}" for q in direct[:6])
                       if direct else "no P31 statements")
    return out


# -----------------------------------------------------------------------------
# LIVE CASES -- the two motivating bugs, both directions, plus the empty case
# -----------------------------------------------------------------------------
LIVE = [
    # (qid, subject, expected families, want verdict, why)
    ("Q7350", "Panama Canal", {"WATERWAY"}, "CONSISTENT",
     "the correct entity for the motivating claim"),
    ("Q498979", "Panama Canal Zone", {"WATERWAY"}, "CONFLICT",
     "THE BUG: failure mode #1's wrong-sense pick, an admin territory"),
    ("Q48584", "Rosetta Stone", {"PHYSICAL_ARTIFACT"}, "CONSISTENT",
     "the correct entity, a stele"),
    ("Q1703969", "Rosetta Stone", {"PHYSICAL_ARTIFACT"}, "CONFLICT",
     "THE BUG: the British punk band"),
    ("Q1189", "Usain Bolt", {"PERSON"}, "CONSISTENT",
     "a plain person case"),
    ("Q30", "United States", {"PERSON"}, "CONFLICT",
     "a country is not a person"),
    ("Q68487022", "human liver", {"PERSON"}, "NO_EVIDENCE",
     "SAFETY: this entity has NO P31 at all, so it must not be vetoed"),
    # SPECIFICITY. The two CONFLICT rows above are only evidence if the verdict
    # tracks BOTH sides. Re-ask the same two entities under the expectation that
    # actually fits them: if these came back CONFLICT too, the check would be
    # detecting "this entity is unusual" rather than "entity vs expectation".
    ("Q498979", "Panama Canal Zone", {"ADMIN_TERRITORY"}, "CONSISTENT",
     "SPECIFICITY: CONFLICT above was about the EXPECTATION, not the entity"),
    ("Q1703969", "Rosetta Stone", {"ORGANIZATION"}, "CONSISTENT",
     "SPECIFICITY: the punk band really is an organization"),
]

# Entities used to test the DISJOINT table empirically: any entity occupying two
# families declared disjoint DISPROVES that pair.
INVARIANT_QIDS = ["Q7350", "Q498979", "Q48584", "Q1703969", "Q1189", "Q30",
                  "Q130018", "Q103843442", "Q92676744", "Q229058", "Q949819",
                  "Q178743", "Q13442814"]


def _selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    # ---- ARM A: offline logic -------------------------------------------
    # Hub classes must not leak into any family.
    leaked = {q: f for f, a in FAMILIES.items() for q in a if q in HUB_CLASSES}
    checks.append(("no HUB_CLASS is a family anchor", not leaked, str(leaked)))

    # A QID must not anchor two families -- that would make the two families
    # trivially non-disjoint and silently weaken every CONFLICT.
    owner: dict[str, list[str]] = collections.defaultdict(list)
    for f, a in FAMILIES.items():
        for q in a:
            owner[q].append(f)
    dupes = {q: fs for q, fs in owner.items() if len(fs) > 1}
    checks.append(("no QID anchors two families", not dupes, str(dupes)))

    # DISJOINT and NOT_DISJOINT must not contradict each other.
    clash = [p for p in NOT_DISJOINT if frozenset(p) in DISJOINT]
    checks.append(("DISJOINT and NOT_DISJOINT do not overlap", not clash, str(clash)))

    # Every family named in either table must exist.
    named = {f for p in DISJOINT for f in p} | {f for p in NOT_DISJOINT for f in p}
    named |= {f for fs in PROPERTY_EXPECTATION.values() for f in fs}
    unknown = named - set(FAMILIES)
    checks.append(("every family named anywhere is defined", not unknown, str(unknown)))

    # decide()'s four states, driven by synthetic closures -- no network.
    v, _ = decide({"ORGANIZATION"}, {"PHYSICAL_ARTIFACT"})
    checks.append(("disjoint pair -> CONFLICT", v == "CONFLICT", v))
    v, _ = decide({"WATERWAY", "STRUCTURE"}, {"WATERWAY"})
    checks.append(("overlap -> CONSISTENT", v == "CONSISTENT", v))
    v, d = decide({"PHYSICAL_ARTIFACT"}, {"WRITTEN_WORK"})
    checks.append(("a NOT_DISJOINT pair -> NO_EVIDENCE, not CONFLICT",
                   v == "NO_EVIDENCE", f"{v}: {d}"))
    v, _ = decide(set(), {"PERSON"})
    checks.append(("no families (no P31) -> NO_EVIDENCE", v == "NO_EVIDENCE", v))
    v, _ = decide({"PERSON"}, None)
    checks.append(("no expectation -> NO_EXPECTATION", v == "NO_EXPECTATION", v))
    # The conservatism rule itself: ONE unlisted pair must defeat a CONFLICT.
    v, d = decide({"PERSON", "WRITTEN_WORK"}, {"PHYSICAL_ARTIFACT"})
    checks.append(("one non-disjoint pair defeats CONFLICT (PERSON+WRITTEN_WORK "
                   "vs PHYSICAL_ARTIFACT)", v == "NO_EVIDENCE", f"{v}: {d}"))

    # The two hub checks below replace an earlier pair that PASSED FOR THE WRONG
    # REASON, found 2026-08-27 by proving the selftest non-vacuous rather than
    # trusting its own PASS. The old pair asserted "organization + `person or
    # organization` is not PERSON" and "Q106559804 is in HUB_CLASSES". The first
    # cannot fail while check #1 holds -- Q106559804 is not a PERSON anchor, so
    # nothing would put it in PERSON with or without the filter -- and the second
    # is a tautology over two constants. Measured consequence: emptying
    # HUB_CLASSES changes the families of 0 of the 13 INVARIANT_QIDS.
    #
    # So the runtime filter at families_of_closure() is INERT *by construction*
    # while check #1 passes, and that is a defence-in-depth relationship worth
    # stating rather than a redundancy worth deleting: check #1 DETECTS a hub
    # wrongly added as an anchor, and the filter NEUTRALISES the same mistake.
    # These two checks test exactly that, one each.
    saved_person = dict(FAMILIES["PERSON"])
    FAMILIES["PERSON"]["Q106559804"] = "INJECTED for the check below"
    fams_hub = families_of_closure({"Q43229", "Q106559804"})
    FAMILIES["PERSON"].clear()
    FAMILIES["PERSON"].update(saved_person)
    checks.append(("the hub filter NEUTRALISES a hub wrongly added as a PERSON "
                   "anchor (the only case where the filter can matter)",
                   "PERSON" not in fams_hub, str(sorted(fams_hub))))
    checks.append(("...and it is inert while check #1 holds: emptying "
                   "HUB_CLASSES changes no family on a real closure",
                   families_of_closure({"Q43229", "Q106559804"})
                   == {f for f, a in FAMILIES.items()
                       if {"Q43229", "Q106559804"} & set(a)},
                   "filter changed a result"))

    # expectation_for(): explicit wins, property map is the fallback.
    checks.append(("explicit expectation overrides the PID map",
                   expectation_for("P569", {"WATERWAY"}) == {"WATERWAY"}, ""))
    checks.append(("unmapped PID -> None, so NO_EXPECTATION not a guess",
                   expectation_for("P9999999", None) is None, ""))

    print("ARM A -- offline logic")
    for name, ok, info in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   [{info}]" if info and not ok else ""))
    a_pass = sum(1 for _, ok, _ in checks if ok)
    print(f"  {a_pass}/{len(checks)} passed")

    # ---- ARM B: live Wikidata ------------------------------------------
    print("\nARM B -- live Wikidata")
    cache = PR.load_cache()
    b_checks = []
    for qid, subj, exp, want, why in LIVE:
        r = check_type(qid, cache, expected_families=exp, subject=subj)
        ok = r["verdict"] == want
        b_checks.append(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {qid:12s} {subj:22s} "
              f"exp={'/'.join(sorted(exp)):18s} -> {r['verdict']}"
              f"{'' if ok else f' (want {want})'}")
        print(f"        {r['detail']}")
        print(f"        families={r['families'] or '(none)'}  {r['evidence']}")
        print(f"        why: {why}")

    # ---- ARM C: the DISJOINT table, tested against real entities --------
    print("\nARM C -- DISJOINT table vs real entities")
    violations = []
    for qid in INVARIANT_QIDS:
        fams = families_of_closure(type_closure(qid, cache))
        for a in sorted(fams):
            for b in sorted(fams):
                if a < b and frozenset((a, b)) in DISJOINT:
                    violations.append((qid, a, b))
    ok_c = not violations
    print(f"  {'PASS' if ok_c else 'FAIL'}  no entity occupies two families "
          f"declared disjoint  [{len(INVARIANT_QIDS)} entities]")
    for qid, a, b in violations:
        print(f"        VIOLATION {qid} is both {a} and {b} -- that pair is WRONG")
    PR.save_cache(cache)

    total = len(checks) + len(b_checks) + 1
    passed = a_pass + sum(b_checks) + (1 if ok_c else 0)
    print(f"\nTOTAL {passed}/{total} passed")
    return 0 if passed == total else 1


def _demo() -> None:
    cache = PR.load_cache()
    print("The two resolution bugs a LABEL check cannot see, and a type check can:\n")
    for qid, subj, exp, want, why in LIVE:
        r = check_type(qid, cache, expected_families=exp, subject=subj)
        print(f"  {subj:22s} -> {qid:12s} {r['verdict']:14s} {r['evidence']}")
    PR.save_cache(cache)
    print("\nBoth wrong entities have a PERFECT label match to the subject string.")
    print("That is exactly why the recorded 72/72 label audit could not fail.")


def _probe_constraints() -> None:
    """Print Wikidata's OWN subject type constraint for each mapped PID.

    PROPERTY_EXPECTATION is curated, and a curated class list has already
    misfired once in this project. This does not replace the map -- it makes it
    auditable against the source.

    MEASURED 2026-08-27, and this is why the map is NOT read from here:
      * the constraint lists the very HUB_CLASSES this module must exclude --
        P2044 -> `object` (Q488383), P577 and P1433 -> `work` (Q386724).
        Intersecting against those makes almost everything CONSISTENT, which is
        citation_l1_verifier.py:76's "rebuilds the tautology in a new shape"
        arriving from the other direction.
      * it is ABSENT for P571 (inception) and P2046 (area) -- n=0.
      * a property carries several constraint KINDS. P186's first class-bearing
        constraint is Q21510865 VALUE-type, describing the value, not the
        subject. Filtering on Q21503250 is mandatory; the first draft of this
        function did not, and reported P186's value classes as though they
        constrained the subject.
    Where the constraint IS clean it corroborates the map (P569 -> human,
    P610 -> geographic location/feature, P1082 -> region/territory/settlement).
    """
    SUBJECT_TYPE = "Q21503250"          # subject type constraint
    cache = PR.load_cache()
    for pid in sorted(PROPERTY_EXPECTATION):
        d = PR._get_with_retry({"action": "wbgetentities", "ids": pid,
                                "props": "claims", "format": "json"}) or {}
        ent = (d.get("entities", {}) or {}).get(pid, {})
        classes, kinds = [], []
        for st in (ent.get("claims", {}) or {}).get("P2302", []):
            val = (((st.get("mainsnak", {}) or {}).get("datavalue", {}) or {})
                   .get("value", {}) or {})
            kind = val.get("id") if isinstance(val, dict) else None
            if kind:
                kinds.append(kind)
            if kind != SUBJECT_TYPE:          # skip value-type etc. -- see above
                continue
            for q in (st.get("qualifiers", {}) or {}).get("P2308", []):
                v = ((q.get("datavalue", {}) or {}).get("value", {}) or {})
                if isinstance(v, dict) and v.get("id"):
                    classes.append(v["id"])
        labs = PR.fetch_item_labels(classes[:15], cache)
        hubs = [c for c in classes if c in HUB_CLASSES]
        mine = "/".join(sorted(PROPERTY_EXPECTATION[pid]))
        print(f"\n{pid}  my map: {mine}")
        if not classes:
            print(f"      NO subject type constraint (kinds present: {len(kinds)})"
                  f" -- nothing to audit against")
            continue
        print(f"      subject-type classes (n={len(classes)}): "
              f"{[labs.get(c, c) for c in classes[:15]]}")
        if hubs:
            print(f"      >>> includes {len(hubs)} HUB class(es) this module must "
                  f"exclude: {[HUB_CLASSES[h].split(' --')[0] for h in hubs]}")
    PR.save_cache(cache)


def _vacuity() -> int:
    """Prove the selftest's load-bearing checks are CAPABLE OF FAILING.

    This exists because #20 shipped a selftest that printed 11/11 while
    destroying a quoted result, and because this module's own first draft had
    TWO checks that passed for the wrong reason (see the note in _selftest).
    A test's own PASS is not evidence.

    Each proof injects the defect the check is supposed to catch and asserts the
    check reacts. Every mutation is restored before the next proof runs.
    """
    cache = PR.load_cache()
    out = []

    # V1 -- Arm C reacts to a WRONG disjoint pair.
    fams = {q: families_of_closure(type_closure(q, cache)) for q in INVARIANT_QIDS}
    both = [q for q, f in fams.items() if {"PHYSICAL_ARTIFACT", "WRITTEN_WORK"} <= f]
    saved = set(DISJOINT)
    DISJOINT.add(frozenset(("PHYSICAL_ARTIFACT", "WRITTEN_WORK")))
    viol = [(q, a, b) for q, f in fams.items()
            for a in sorted(f) for b in sorted(f)
            if a < b and frozenset((a, b)) in DISJOINT]
    DISJOINT.clear()
    DISJOINT.update(saved)
    out.append(("V1  Arm C reacts to a wrong DISJOINT pair",
                bool(viol) and bool(both),
                f"injecting PHYSICAL_ARTIFACT x WRITTEN_WORK -> {len(viol)} "
                f"violation(s), e.g. {viol[0][0] if viol else '-'}; "
                f"restored to {len(DISJOINT)} pairs"))

    # V2 -- the verdict is a function of BOTH sides, not just the entity.
    spec = [("Q498979", {"WATERWAY"}, "CONFLICT"),
            ("Q498979", {"ADMIN_TERRITORY"}, "CONSISTENT"),
            ("Q1703969", {"PHYSICAL_ARTIFACT"}, "CONFLICT"),
            ("Q1703969", {"ORGANIZATION"}, "CONSISTENT"),
            ("Q1703969", {"NATURAL_PLACE"}, "CONFLICT")]
    got = [check_type(q, cache, expected_families=e)["verdict"] == w
           for q, e, w in spec]
    out.append(("V2  CONFLICT tracks the EXPECTATION, not the entity",
                all(got), f"{sum(got)}/{len(got)} flips as expected"))

    # V3 -- the hub-leak check reacts to a hub added as an anchor.
    HUB = "Q106559804"
    FAMILIES["PERSON"][HUB] = "INJECTED"
    leaked = {q: f for f, a in FAMILIES.items() for q in a if q in HUB_CLASSES}
    del FAMILIES["PERSON"][HUB]
    clean = {q: f for f, a in FAMILIES.items() for q in a if q in HUB_CLASSES}
    out.append(("V3  the hub-leak check reacts to a hub used as an anchor",
                bool(leaked) and not clean,
                f"injected {HUB} -> detected {list(leaked)}; clean after removal"))

    # V4 -- MEASUREMENT, not a pass/fail: is the runtime hub filter inert?
    # It is, by construction, while V3's check passes -- no hub is an anchor, so
    # dropping hubs cannot change which anchors a closure intersects.
    saved_hubs = dict(HUB_CLASSES)
    diffs = []
    for q in INVARIANT_QIDS:
        clo = type_closure(q, cache)
        a = families_of_closure(clo)
        HUB_CLASSES.clear()
        b = families_of_closure(clo)
        HUB_CLASSES.update(saved_hubs)
        if a != b:
            diffs.append(q)
    out.append(("V4  hub filter inertness MEASURED (defence in depth, not a "
                "mechanism)", True,
                f"emptying HUB_CLASSES changes {len(diffs)}/{len(INVARIANT_QIDS)} "
                f"entities' families -> "
                f"{'INERT' if not diffs else 'LOAD-BEARING: ' + str(diffs)}"))

    print("VACUITY PROOFS -- can each load-bearing check actually fail?")
    for name, ok, info in out:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"        {info}")
    n = sum(1 for _, ok, _ in out if ok)
    print(f"\n  {n}/{len(out)} passed")
    PR.save_cache(cache)
    return 0 if n == len(out) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--vacuity", action="store_true",
                    help="prove the selftest's checks are capable of failing")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--probe-constraints", action="store_true",
                    help="print Wikidata's own type constraints for the mapped PIDs")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    if args.vacuity:
        return _vacuity()
    if args.demo:
        _demo()
        return 0
    if args.probe_constraints:
        _probe_constraints()
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
