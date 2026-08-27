#!/usr/bin/env python3
"""An INDEPENDENT check on a resolved entity: does its provenance match the claim?

Written 2026-08-26. Motivation and first evidence:
`reference/citation_negatives_headroom_2026-08-25.md` §5.

WHY THIS IS NOT REDUNDANT WITH THE RESOLVER
-------------------------------------------
`reference/negatives_cache_audit_2026-08-25.md` downgraded the resolver's recorded
"72/72 correct" to **"0% refusal, correctness unverified by an independent
signal"**, because the audit checked the chosen entity's LABEL against the subject
string -- the same signal the selection used. A check that reuses the selection's
own signal cannot fail, so it proved only that the resolver does not return
something with an unrelated name. It named the fix as future work:

    An independent test would check the resolved entity's other properties for
    consistency with the claim's context -- information the resolver never
    consulted.

That is this module. `resolve_entity` scores labels, aliases and descriptions; it
never looks at P1433/P123. So those properties are genuinely independent evidence,
and they are already in the claims payload every Wikidata verifier fetches anyway.

FIRST EVIDENCE, BEFORE A LINE OF THIS WAS WRITTEN
-------------------------------------------------
Probing `Lancet Commission on dementia prevention` (2026-08-25) the resolver
ACCEPTED Q92676744 @0.605 over the correct Q98186330 @0.595. The accepted item's
label really does read "The Lancet Commission on Dementia Prevention..." so the
label-based check passes it -- but its `P1433` (published in) is **Q15751849 =
Irish Journal of Psychological Medicine**, not The Lancet. Its `P577 = 2019-06-01`
would then have falsified a gold-TRUE claim about the *2020* Commission: a
confident-wrong FALSE, the exact class the 2026-08-21 QID fix drove to zero.

BOTH ERROR DIRECTIONS OF THIS CHECK ARE SAFE
--------------------------------------------
This matters more than the accuracy of the name matcher, so it is stated up front:

  * a wrong CONSISTENT (matcher too lenient)  -> no veto -> status quo behaviour;
  * a wrong CONFLICT   (matcher too strict)   -> veto    -> honest UNVERIFIABLE.

Neither direction can manufacture a confident-wrong verdict, because the check
only ever REMOVES a verdict. That is why it is safe to deploy ahead of the harder
half of the fix (series-level resolution, task #17b).

ABSENCE IS NOT CONFLICT
-----------------------
`NO_EVIDENCE` is returned when the entity carries none of the provenance
properties, and it MUST NOT be treated as a rejection. This is the same asymmetry
the CITATION Level 1 verifier already encodes -- "a source that fails to resolve
is UNVERIFIABLE, not fabricated". Most Wikidata items have no P123 at all; making
absence reject would delete coverage without detecting anything.

Modes
-----
  --selftest   9 offline matcher checks + 3 live entity checks (~4 Wikidata calls)
  --demo       narrated walk-through of the three live cases
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Only these two decide a CONFLICT. They answer "who put this work out", which is
# what a citation names. P50/P179/P361 are reported for context but never veto:
# an author is not a publisher, so a mismatch there is not a provenance conflict.
SOURCE_PIDS = {
    "P1433": "published in",
    "P123": "publisher",
}
CONTEXT_PIDS = {
    "P50": "author",
    "P179": "part of the series",
    "P361": "part of",
    "P31": "instance of",
}

_QID_RE = re.compile(r"^Q\d+$")

# Dropped when building initials, so "World Health Organization" -> WHO and
# "Intergovernmental Panel on Climate Change" -> IPCC.
_STOP = {"of", "the", "and", "on", "for", "in", "to", "a", "an", "at", "de"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def _initials(name: str) -> str:
    words = [w for w in _norm(name).split() if w and w not in _STOP]
    return "".join(w[0] for w in words).upper()


def names_match(expected: str, candidate: str) -> bool:
    """Is `candidate` plausibly the organisation `expected` names?

    Deliberately lenient -- see the module docstring on error directions. A
    false match costs nothing (no veto); a false mismatch costs coverage only.
    """
    e, c = _norm(expected), _norm(candidate)
    if not e or not c:
        return False
    if e == c or e in c or c in e:
        return True
    # Acronym match, in both directions. Prefix rather than equality so that
    # "FAO" matches "Food and Agriculture Organization of the United Nations"
    # (initials FAOUN) and "WHO" matches "World Health Organization Regional
    # Office". "CDC" vs "World Health Organization" (WHO) still fails.
    eu, cu = expected.strip().upper(), candidate.strip().upper()
    if 2 <= len(eu) <= 6 and eu.isalpha():
        if _initials(candidate).startswith(eu):
            return True
    if 2 <= len(cu) <= 6 and cu.isalpha():
        if _initials(expected).startswith(cu):
            return True
    return False


def _label_and_aliases(qid: str, cache: dict) -> list[str]:
    from quantitative_verifier import fetch_candidate_meta
    meta = fetch_candidate_meta([qid], cache).get(qid, {})
    out = [meta.get("label", "")] + list(meta.get("aliases", []) or [])
    return [x for x in out if x]


def check_source(qid: str, expected_source: str, cache: dict,
                 claims: dict | None = None) -> dict:
    """Does `qid`'s provenance match the source named in the claim?

    Returns {verdict, detail, evidence} with verdict in
    CONSISTENT / CONFLICT / NO_EVIDENCE / NO_EXPECTATION.

    `claims` may be passed in when the caller has already fetched it, so this
    costs zero extra API calls in the common path.
    """
    if not expected_source or not expected_source.strip():
        return {"verdict": "NO_EXPECTATION", "detail": "no source named in claim",
                "evidence": {}}
    if not qid:
        return {"verdict": "NO_EVIDENCE", "detail": "no entity to check",
                "evidence": {}}

    if claims is None:
        from property_resolver import fetch_entity_claims
        claims = fetch_entity_claims(qid, cache)
    if claims is None:
        return {"verdict": "NO_EVIDENCE", "detail": f"claims fetch failed for {qid}",
                "evidence": {}}

    evidence: dict[str, list[str]] = {}
    matched: list[str] = []
    conflicting: list[str] = []

    for pid, pname in SOURCE_PIDS.items():
        for raw in claims.get(pid, []) or []:
            raw = str(raw).strip()
            names = _label_and_aliases(raw, cache) if _QID_RE.match(raw) else [raw]
            if not names:
                continue
            evidence.setdefault(pid, []).extend(names[:1])
            if any(names_match(expected_source, n) for n in names):
                matched.append(f"{pid} ({pname}) = {names[0]!r}")
            else:
                conflicting.append(f"{pid} ({pname}) = {names[0]!r}")

    for pid in CONTEXT_PIDS:
        vals = claims.get(pid, []) or []
        if vals:
            evidence.setdefault(pid, []).extend(str(v) for v in vals[:2])

    if matched:
        # Any match wins: a work can legitimately carry several provenance
        # values (a co-published report), and one genuine hit is confirmation.
        return {"verdict": "CONSISTENT",
                "detail": f"{expected_source!r} matches " + "; ".join(matched),
                "evidence": evidence}
    if conflicting:
        return {"verdict": "CONFLICT",
                "detail": (f"{expected_source!r} matches none of the entity's "
                           f"provenance: " + "; ".join(conflicting)),
                "evidence": evidence}
    return {"verdict": "NO_EVIDENCE",
            "detail": (f"{qid} carries none of {'/'.join(SOURCE_PIDS)} -- absence "
                       f"is NOT conflict, so this must not reject"),
            "evidence": evidence}


# =============================================================================
# Live cases. The third is the one that converts an analysis into a detection:
# SYN_CITA_075/076/077 fabricate "The WHO Sixth Assessment Report", and AR6's
# P123 is the IPCC, so a WHO expectation conflicts.
LIVE = [
    ("Q92676744", "The Lancet", "CONFLICT",
     "the wrongly-accepted 2019 article; P1433 is the Irish Journal of "
     "Psychological Medicine (found 2026-08-25)"),
    ("Q103843442", "IPCC", "CONSISTENT",
     "IPCC AR6 correctly attributed -- the check must not veto a right answer"),
    ("Q103843442", "WHO", "CONFLICT",
     "the SYN_CITA_075/076/077 fabrication: AR6 attributed to WHO"),
]


def _selftest() -> None:
    fails = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))
        if not cond:
            fails.append(label)

    print("source_consistency --selftest")
    print("\n-- offline: the name matcher --")
    for exp, cand, want in [
        ("WHO", "World Health Organization", True),
        ("FAO", "Food and Agriculture Organization of the United Nations", True),
        ("IPCC", "Intergovernmental Panel on Climate Change", True),
        ("The Lancet", "The Lancet", True),
        ("World Bank", "World Bank Group", True),
        ("The Lancet", "Irish Journal of Psychological Medicine", False),
        ("WHO", "Intergovernmental Panel on Climate Change", False),
        ("CDC", "World Health Organization", False),
        ("WHO", "Food and Agriculture Organization of the United Nations", False),
    ]:
        got = names_match(exp, cand)
        check(f"{exp!r} vs {cand[:44]!r} -> {want}", got == want, f"got {got}")

    print("\n-- live: provenance of three real entities --")
    from property_resolver import load_cache, save_cache
    cache = load_cache()
    for qid, expected, want, why in LIVE:
        res = check_source(qid, expected, cache)
        check(f"{qid} vs {expected!r} -> {want}", res["verdict"] == want,
              f"got {res['verdict']}: {res['detail'][:100]}")
    save_cache(cache)

    print()
    print("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}")
    sys.exit(1 if fails else 0)


def _demo() -> None:
    from property_resolver import load_cache, save_cache
    cache = load_cache()
    print("An independent check on a resolved entity, using properties the")
    print("resolver never consulted. CONFLICT vetoes; NO_EVIDENCE must not.")
    print("=" * 78)
    for qid, expected, want, why in LIVE:
        print(f"\n>>> {qid}  expecting source {expected!r}")
        print(f"    why: {why}")
        res = check_source(qid, expected, cache)
        print(f"    -> {res['verdict']}  (expected {want})")
        print(f"       {res['detail']}")
        for pid, vals in sorted(res["evidence"].items()):
            name = SOURCE_PIDS.get(pid) or CONTEXT_PIDS.get(pid, "")
            flag = "  <-- decides" if pid in SOURCE_PIDS else ""
            print(f"       {pid:6s} {name:20s} {vals}{flag}")
    save_cache(cache)
    print("\n" + "=" * 78)
    print("Deploy note: this is the SAFETY half of task #17. It removes the")
    print("confident-wrong verdict but does not yet resolve the right edition --")
    print("that is series-level resolution, still to build.")


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
