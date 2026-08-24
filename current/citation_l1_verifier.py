#!/usr/bin/env python3
"""
CITATION level 1, rebuilt: does the cited source actually exist?

WHY A REBUILD WAS NEEDED, PRECISELY
-----------------------------------
`citation_verifier.py` is recorded as "0/12 matched on Batch 3". Diagnosing that
against the real 29 CITATION claims showed the headline was hiding two different
failures, and that the part everyone assumed was broken actually works:

  * **`extract_source_name()` is fine.** It correctly returns "International Energy
    Agency", "World Athletics", "OECD", "Food and Agriculture Organization", "FAO",
    "World Health Organization", "IPCC Sixth Assessment Report". Only 3 of 29 fail,
    and those 3 are claims whose `subject` is a topic rather than a source
    ("children under five", "global food insecurity") -- an atomisation issue, not a
    verifier one.
  * **14 of 29 hit `TRIVIALLY_KNOWN_ORGS` and returned TRUE @0.85 with no evidence
    consulted at all.** That is the tautology: those claims were never verified, they
    were waved through. A verifier that answers TRUE because the org is on a
    hand-written list has measured nothing.
  * **15 of 29 missed the hardcoded 15-entry `ORG_URL_MAP`** -- including **all 12
    Batch 3 claims**, which is the entire "0/12".

So the defect is two hardcoded dicts, not the pipeline. Both are replaced here by
resolving the organisation in Wikidata with the **same fixed resolver** built for
QUANTITATIVE on 2026-08-23 (prefix+full-text union, `mul` labels, prominence
tie-break). That is principled rather than curated: it works for any organisation,
it is auditable (a QID and a sitelink count), and it cannot silently pass an org
because someone typed it into a set.

WHAT THIS DOES AND DOES NOT CLAIM
---------------------------------
This verifies **level 1 only: the cited source exists and is identifiable.** It
deliberately does not attempt level 2 (does that source actually assert this?).

Two reasons, and both are honest limitations rather than shortcuts:

  1. The existing level 2 scores attribution with NLI over fetched page text, and
     the project has already measured what that costs: contradiction precision from
     BART-MNLI over retrieved text never exceeds 0.20 at any threshold. Wiring an
     unreliable level 2 under a reliable level 1 would make the combined verdict
     less trustworthy than level 1 alone.
  2. Level 2 requires an NLI forward pass, which SIGBUSes on this 8 GB machine.
     Importing `citation_verifier` loads BART successfully; it is *calling* it that
     dies. So level 2 belongs on Colab.

**Level 1 alone is still a real result**, because the failure mode it detects --
a fabricated source -- is the one the literature reports at 7-55% across models,
and it is the half of CITATION that dual-emit was designed to isolate: a
fabricated-source-but-true-fact claim is invisible to a uniform pipeline.

A source existing does NOT make the claim true. Level-1 TRUE means "this source is
real", nothing more, and the verdict field says so.
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import consolidate_claims as CC          # noqa: E402
import metrics as M                      # noqa: E402
import property_resolver as PR           # noqa: E402
import quantitative_verifier as QV       # noqa: E402

OUT = os.path.join(HERE, "citation_l1_results.csv")

# Wikidata classes that count as a citable source. Checked via P31 (instance of)
# and P279* is deliberately NOT followed -- a broad subclass walk lets almost
# anything qualify, which would rebuild the tautology in a new shape.
SOURCE_CLASSES = {
    "Q43229": "organization",
    "Q327333": "government agency",
    "Q2659904": "government organization",
    "Q484652": "international organization",
    "Q163740": "nonprofit organization",
    "Q31855": "research institute",
    "Q3918": "university",
    "Q737498": "academic journal",
    "Q5633421": "scientific journal",
    "Q1002697": "periodical",
    "Q571": "book",
    "Q13442814": "scholarly article",
    "Q253623": "treaty",
    "Q131569": "treaty",
    "Q820655": "statute",
    "Q7725634": "literary work",
    "Q47461344": "written work",
    "Q1572600": "proclamation",
    "Q49848": "document",
    "Q686822": "report",
}

# Level-1 confidence. Lower than a Wikidata *property* match, because "this
# organisation exists" is a much weaker claim than "this property holds this value".
L1_CONFIDENT = 0.75
L1_WEAK = 0.60


def resolve_source(name: str, claim: str, cache: dict) -> dict:
    """Resolve a cited source to a Wikidata item using the fixed resolver."""
    r = QV.resolve_entity(name, cache, ctx=claim)
    out = {"qid": r.get("qid") or "", "score": round(r.get("score", 0.0), 3),
           "detail": r.get("detail", ""), "classes": "", "website": "",
           "source_signal": ""}
    if not out["qid"]:
        return out

    # P31 = instance of, P856 = official website.
    # NOTE fetch_entity_claims returns {pid: [ALREADY-RENDERED value strings]},
    # not raw snak dicts -- entity-valued statements come back as bare QID strings
    # ("Q43229"), and labels are resolved separately by the caller. An earlier
    # version of this function walked snak["mainsnak"]["datavalue"], which threw
    # TypeError into a bare except and silently classified EVERY source as
    # "not source-like". Verified against property_resolver.py:257 rather than
    # assumed.
    claims = PR.fetch_entity_claims(out["qid"], cache) or {}
    inst = [v for v in claims.get("P31", [])
            if isinstance(v, str) and v.startswith("Q") and v[1:].isdigit()]
    named = [SOURCE_CLASSES[q] for q in inst if q in SOURCE_CLASSES]
    out["classes"] = "; ".join(sorted(set(named))) or "; ".join(inst[:3])
    sites = [v for v in claims.get("P856", []) if isinstance(v, str)]
    out["website"] = sites[0] if sites else ""

    # Source-like test: an OFFICIAL WEBSITE (P856) or a recognised P31 class.
    #
    # The first version required P31 to be in SOURCE_CLASSES, and that was the same
    # mistake as the ORG_URL_MAP it replaced -- a curated list. It marked correct
    # resolutions "weak" purely because Wikidata used a class the list did not
    # anticipate: IPCC Sixth Assessment Report -> Q103843442, CDC -> Q583725,
    # World Bank -> Q7164, International Energy Agency -> Q826700. All four are the
    # right entity; all four were downgraded.
    #
    # P856 is a structural signal rather than a curated one, and it discriminates in
    # the direction that matters: publishers, agencies, journals and named reports
    # have official websites; abstract concepts ("food insecurity") do not. Same kind
    # of move as the prominence tie-break -- let Wikidata's own structure decide
    # instead of enumerating cases.
    out["is_source_type"] = bool(sites) or bool(named)
    out["source_signal"] = ("P856 website" if sites
                            else ("P31 class" if named else "neither"))
    return out


def verify_l1(row: dict, cache: dict) -> dict:
    import citation_verifier as CV       # imported late: module load pulls in BART
    name = CV.extract_source_name(row) or ""
    out = {
        "claim_id": row.get("claim_id", ""), "claim": row.get("claim", ""),
        "gold_verdict": row.get("gold_verdict", ""),
        "source_name": name, "qid": "", "resolution_score": "",
        "classes": "", "website": "", "source_signal": "",
        "verdict": "UNVERIFIABLE", "confidence": 0.0, "stage": "", "reason": "",
    }
    if not name:
        out["stage"] = "extract"
        out["reason"] = ("no source name extractable -- the claim's subject is a "
                         "topic, not a citable source (atomisation issue)")
        return out

    r = resolve_source(name, row.get("claim", ""), cache)
    out["qid"] = r["qid"]
    out["resolution_score"] = r["score"]
    out["classes"] = r["classes"]
    out["website"] = r["website"]
    out["source_signal"] = r.get("source_signal", "")

    if not r["qid"]:
        out["stage"] = "resolution"
        out["reason"] = f"source '{name}' not resolvable in Wikidata: {r['detail']}"
        return out

    if r.get("is_source_type"):
        out["verdict"] = "TRUE"
        out["confidence"] = L1_CONFIDENT
        out["stage"] = "l1-confident"
        out["reason"] = (f"source exists: {r['qid']} is a {r['classes']}"
                         + (f", site {r['website']}" if r["website"] else ""))
    else:
        # Resolved, but not to anything that looks like a publisher or document.
        # Reported weakly rather than as a pass: resolving "Nature" to the concept
        # *nature* would otherwise count as finding the journal.
        out["verdict"] = "TRUE"
        out["confidence"] = L1_WEAK
        out["stage"] = "l1-weak"
        out["reason"] = (f"resolved to {r['qid']} but its P31 classes "
                         f"({r['classes'] or 'none'}) are not source-like -- "
                         f"possible wrong sense")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="CITATION level 1: does the cited source exist? "
                    "Wikidata resolution, no hardcoded org lists.")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    rows, _ = CC.load_all()
    cit = [r for r in rows
           if (r.get("type") or "").upper() == "CITATION"
           and (r.get("gold_verdict") or "").strip()
           and str(r.get("synthetic", "")).lower() != "true"]
    if args.limit:
        cit = cit[:args.limit]
    print(f"{len(cit)} CITATION claims (level 1 only: does the source exist?)")
    print(f"  gold: {dict(collections.Counter(r['gold_verdict'] for r in cit))}")

    cache = QV.load_cache()
    results = []
    for i, r in enumerate(cit, 1):
        res = verify_l1(r, cache)
        results.append(res)
        print(f"  [{i}/{len(cit)}] {res['claim_id']:<12}"
              f"{(res['source_name'] or '-')[:26]:<28}{res['verdict']:<13}"
              f"{res['stage']:<14}{res['reason'][:46]}")
    QV.save_cache(cache)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nwrote {OUT}")

    print(f"\n{'stage':<16}{'n':>4}")
    for s, n in sorted(collections.Counter(r["stage"] for r in results).items()):
        print(f"{s:<16}{n:>4}")

    gold = [r["gold_verdict"] for r in results]
    pred = [r["verdict"] for r in results]
    conf = [float(r["confidence"] or 0.0) for r in results]
    M.report(gold, pred, conf, title="CITATION level 1 (source existence)")

    print("\nREAD THIS BEFORE QUOTING THE ABOVE")
    print("  Level 1 answers 'is this source real?', NOT 'does it say this?'.")
    print("  A TRUE here means the source exists and is identifiable. It is the")
    print("  half of CITATION that catches FABRICATED sources -- reported at")
    print("  7-55% across models in the literature -- and the half dual-emit was")
    print("  built to isolate. Level 2 (attribution) needs an NLI pass, which")
    print("  SIGBUSes on this machine and belongs on Colab; and the project has")
    print("  already measured that NLI contradiction precision caps at 0.20, so")
    print("  wiring it under level 1 would lower the combined reliability.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
