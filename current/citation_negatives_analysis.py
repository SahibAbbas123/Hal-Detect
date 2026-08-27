#!/usr/bin/env python3
"""What the 24 CITATION synthetic negatives attack, and what Wikidata can reach.

Written 2026-08-25. Full analysis:
`reference/citation_negatives_headroom_2026-08-25.md`.

It was 25 until 2026-08-26, when `SYN_CITA_083` was dropped (task #23): a
`source_swap` moving FAO -> WHO off `Q22_C01`, but WHO CO-PUBLISHED SOFI 2023, so
the swap injected no falsity. It was an `org`-class row, so the composition moved
6 -> 5 org-only and 11 -> 10 source_swap; `year` (12), `title` (5) and `content`
(2) are untouched, and so is the "needs no NLI" count of 17. See CLAUDE.md §5.

This exists because the obvious next experiment -- "run routed CITATION Level 1
on its gold negatives, the way Step 33 did for QUANTITATIVE" -- turned out not
to be worth the network calls, and establishing WHY is the result:

    Not one of the 24 negatives perturbs source EXISTENCE, which is the only
    question Level 1 asks. So L1 detects 0/24 no matter what its FALSE policy is.

Modes
-----
  --composition   offline, zero network, ~1s. Classifies all 24 negatives by what
                  they perturb and prints the detectability breakdown.
  --reachability  ~15 Wikidata calls. Resolves the works behind the reachable
                  classes and reports whether the evidence (P577 / P123) exists.
  --selftest      offline. Enforces the composition invariants.

The reachability mode deliberately calls `quantitative_verifier.resolve_entity`
rather than re-implementing resolution: that function is the only resolver in the
project carrying all three 2026-08-23 fixes (`mul` labels, prefix-unioned-with-
full-text search, prominence tie-break). Re-implementing it here is exactly how a
"faithful" check stops being faithful -- the same discipline as
`original_classifier.py` parsing its prompts verbatim rather than retyping them.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NEGATIVES = os.path.join(HERE, "synthetic_negatives.csv")

# =============================================================================
# COMPOSITION (offline)
# =============================================================================

# Each CITATION negative falls into exactly one detectability class. The
# assignment is derived from `injection_type` plus one structural test -- whether
# the swap corrupts a WORK TITLE ("WHO Sixth Assessment Report") or only the
# ATTRIBUTING ORGANISATION ("The WHO reported in 2023 that..."). That distinction
# is what decides whether a structured lookup can see the perturbation at all, and
# it is not recoverable from injection_type alone.
#
# Title-corrupting rows, identified by reading every source_swap claim (11 at
# authoring, 10 after task #23 dropped `SYN_CITA_083`, which was org-only): the
# swapped organisation name is embedded INSIDE the name of a specific work.
TITLE_CORRUPTING = {
    "SYN_CITA_075",  # 'The WHO Sixth Assessment Report was published in 2023.'
    "SYN_CITA_076",  # 'The WHO Sixth Assessment Report states that human activities...'
    "SYN_CITA_077",  # 'The WHO Sixth Assessment Report states that the world will...'
    "SYN_CITA_081",  # 'The CDC World Mental Health Report 2022 emphasizes...'
    "SYN_CITA_085",  # 'The Food and Agriculture Organization (WHO) publishes...'
}

CLASSES = {
    "year":        ("wrong year on a correctly-named work",
                    "publication date (P577)", False),
    "title":       ("fabricated composite title",
                    "real title resolves, its publisher (P123) conflicts", False),
    "org":         ("org-only attribution swap",
                    "does that org actually assert this", True),
    "content":     ("content swap between two real reports",
                    "does that report actually assert this", True),
}


def classify(row: dict) -> str:
    inj = (row.get("injection_type") or "").strip()
    if inj == "year_shift":
        return "year"
    if inj == "source_swap":
        return "title" if row["claim_id"] in TITLE_CORRUPTING else "org"
    if inj == "cross_substitute_categorical":
        return "content"
    return "unknown"


def load_citation_negatives() -> list[dict]:
    with open(NEGATIVES, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if (r.get("type") or "").strip() == "CITATION"]


def composition(verbose: bool = True) -> dict[str, list[dict]]:
    rows = load_citation_negatives()
    groups: dict[str, list[dict]] = {k: [] for k in CLASSES}
    for r in rows:
        groups.setdefault(classify(r), []).append(r)

    if not verbose:
        return groups

    print(f"CITATION synthetic negatives: {len(rows)}")
    print(f"injection_type: {dict(Counter(r['injection_type'] for r in rows))}")
    print()
    print("Every one of these names a REAL source. Level 1 asks only 'does the")
    print("cited source exist' -- so it detects 0/%d, and not because it is broken." % len(rows))
    print()

    hdr = f"{'n':>3}  {'class':8s}  {'perturbs':42s}  {'detectable by':52s}  NLI?"
    print(hdr)
    print("-" * len(hdr))
    no_nli = 0
    for key, (what, how, needs_nli) in CLASSES.items():
        n = len(groups.get(key, []))
        if not needs_nli:
            no_nli += n
        print(f"{n:>3}  {key:8s}  {what:42s}  {how:52s}  {'YES' if needs_nli else 'no'}")
    print("-" * len(hdr))
    print(f"{no_nli:>3}  reachable with NO inference step "
          f"({no_nli}/{len(rows)} = {100*no_nli/len(rows):.0f}%)")
    print()
    print("That matters specifically because NLI is the component that SIGBUSes")
    print("locally AND whose contradiction precision caps at 0.20 across all 225")
    print("threshold-sweep grid points.")
    print()

    for key in CLASSES:
        g = groups.get(key, [])
        if not g:
            continue
        print(f"--- {key} ({len(g)}) " + "-" * (60 - len(key)))
        for r in g:
            print(f"  [{r['claim_id']}] base={r.get('base_claim_id','?'):12s} {r['claim']}")
        print()
    return groups


# =============================================================================
# REACHABILITY (live Wikidata)
# =============================================================================

# PIDs that would carry the evidence a citation verifier needs.
INTEREST = {
    "P577": "publication date",
    "P571": "inception",
    "P123": "publisher",
    "P50": "author",
    "P31": "instance of",
    "P1433": "published in",
}

# (probe string, context, why we are asking)
TARGETS = [
    ("IPCC Sixth Assessment Report", "IPCC climate report published 2023",
     "5 year_shift rows claim 2024/2025/2028/2033/2123; actual 2023"),
    ("Sixth Assessment Report", "IPCC climate assessment report",
     "same work, bare title -- the composite-title route for SYN_CITA_075/076/077"),
    ("Lancet Commission on dementia prevention",
     "2020 Lancet Commission 12 modifiable risk factors",
     "5 year_shift rows claim 2021/2022/2025/2030/2120; actual 2020"),
    ("Poverty and Shared Prosperity", "World Bank report global extreme poverty rate",
     "2 year_shift rows claim 2024/2025; actual 2023"),
    ("World Mental Health Report", "WHO 2022 report mental health",
     "SYN_CITA_081 fabricates 'CDC World Mental Health Report 2022'"),
    ("The State of World Fisheries and Aquaculture", "FAO biennial report fisheries",
     "SYN_CITA_085 fabricates 'Food and Agriculture Organization (WHO)'"),
]


def reachability() -> None:
    sys.path.insert(0, HERE)
    from quantitative_verifier import resolve_entity, RESOLUTION_THRESHOLD
    from property_resolver import fetch_entity_claims, load_cache, save_cache

    cache = load_cache()
    print(f"resolver: quantitative_verifier.resolve_entity  "
          f"(threshold {RESOLUTION_THRESHOLD})")
    print("cache writes are ADDITIVE ONLY -- new subject and QID keys, no prefix")
    print("reuse and no deletion, per the project's cache discipline.")
    print("=" * 78)

    for probe, ctx, why in TARGETS:
        print(f"\n>>> {probe!r}\n    why: {why}")
        try:
            res = resolve_entity(probe, cache, ctx)
        except Exception as exc:  # noqa: BLE001
            print(f"    !! resolve_entity raised {type(exc).__name__}: {exc}")
            continue

        qid = res.get("qid")
        cands = res.get("candidates") or []
        print(f"    -> qid={qid}  score={res.get('score') or 0.0:.3f}  "
              f"{'ACCEPTED' if qid else 'REJECTED (below threshold)'}")
        if res.get("detail"):
            print(f"       detail: {res['detail']}")
        for i, c in enumerate(cands[:3]):
            # (qid, score, label, description, tier, sim, n_sitelinks)
            print(f"       cand{i}: {c[0]} @{c[1]:.3f} tier={c[4]} sim={c[5]} "
                  f"sitelinks={c[6]}  {c[2]!r}")

        # Inspect the best candidate even when REJECTED: whether the evidence
        # EXISTS in Wikidata is a separate question from whether the current
        # threshold reaches it, and both matter for a build decision.
        probe_qid = qid or (cands[0][0] if cands else None)
        if not probe_qid:
            print("       (no candidate at all -- unreachable)")
            continue
        if not qid:
            print(f"       [inspecting rejected best candidate {probe_qid} anyway]")

        claims = fetch_entity_claims(probe_qid, cache)
        if claims is None:
            print("       !! claims fetch failed (not cached)")
            continue
        print(f"       entity has {len(claims)} properties")
        for pid, name in INTEREST.items():
            if pid in claims:
                print(f"       {pid:6s} {name:18s} = {claims[pid][:4]}")
        missing = [p for p in ("P577", "P123") if p not in claims]
        if missing:
            print(f"       MISSING: {', '.join(missing)}")

    save_cache(cache)
    print("\n" + "=" * 78)
    print("See reference/citation_negatives_headroom_2026-08-25.md for the reading.")
    print("Headline: 8 of 24 reachable today, and ALL 8 through one item")
    print("(Q103843442, the IPCC AR6) -- one work working, not CITATION working.")


# =============================================================================
def _selftest() -> None:
    fails = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))
        if not cond:
            fails.append(label)

    print("citation_negatives_analysis --selftest")
    rows = load_citation_negatives()
    check("24 CITATION negatives present", len(rows) == 24, f"got {len(rows)}")

    groups = composition(verbose=False)
    check("every row classified (no 'unknown')", "unknown" not in groups,
          f"unknown={len(groups.get('unknown', []))}")
    check("classes partition the set",
          sum(len(v) for v in groups.values()) == len(rows))
    check("12 year_shift", len(groups.get("year", [])) == 12,
          f"got {len(groups.get('year', []))}")
    check("5 title-corrupting", len(groups.get("title", [])) == 5,
          f"got {len(groups.get('title', []))}")
    check("5 org-only", len(groups.get("org", [])) == 5,
          f"got {len(groups.get('org', []))}")
    check("2 content swap", len(groups.get("content", [])) == 2,
          f"got {len(groups.get('content', []))}")
    # 17 is unchanged by task #23 -- the dropped row was org-only, and neither
    # `year` nor `title` lost a member. The denominator moved, the numerator did
    # not, which is the whole shape of that drop.
    check("17 of 24 need no NLI",
          len(groups.get("year", [])) + len(groups.get("title", [])) == 17)

    # The central claim of the whole analysis: every negative is gold FALSE, and
    # every one names a real source. The second half is not machine-checkable, but
    # the first half is, and if it broke the analysis would be void.
    check("all 24 are gold FALSE",
          all((r.get("gold_verdict") or "").strip().upper() == "FALSE" for r in rows))
    check("TITLE_CORRUPTING ids are all source_swap",
          all(r["injection_type"] == "source_swap"
              for r in rows if r["claim_id"] in TITLE_CORRUPTING))
    check("TITLE_CORRUPTING ids all exist in the CSV",
          TITLE_CORRUPTING <= {r["claim_id"] for r in rows},
          f"missing={TITLE_CORRUPTING - {r['claim_id'] for r in rows}}")

    # Every title-corrupting claim must literally contain the swapped-in org name
    # inside it; that is the structural property the class is defined by.
    swapped_in = [r for r in rows if r["claim_id"] in TITLE_CORRUPTING
                  and ("WHO" in r["claim"] or "CDC" in r["claim"])]
    check("title-corrupting claims name the swapped-in org",
          len(swapped_in) == len(TITLE_CORRUPTING), f"got {len(swapped_in)}")

    print()
    print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
    sys.exit(1 if fails else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--composition", action="store_true",
                    help="offline: classify all 25 by what they perturb")
    ap.add_argument("--reachability", action="store_true",
                    help="live: ~15 Wikidata calls, does the evidence exist")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        _selftest()
    elif args.reachability:
        reachability()
    elif args.composition:
        composition()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
