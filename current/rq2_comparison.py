#!/usr/bin/env python3
"""
RQ2: taxonomy-routed verifiers vs the non-routed (uniform) baseline.

WHY THIS SCRIPT EXISTS
----------------------
Three build-phase handoffs independently name this comparison as the project's
central missing result ("the core quantitative proof: ablation of taxonomy-routed
verifiers vs a single generic (uniform) verifier"). The baseline half was run on
2026-08-23 (356 claims, `current/nonrouted_baseline_results.csv`). The routed half
already exists as per-verifier result CSVs. Nothing here calls a model, hits an
API, or touches a cache: it is a join plus `current/metrics.py`.

SCOPE: BATCH 3 ONLY, AND WHY
---------------------------
Batch 3 is the only claim set where all five routed verifiers have results on the
same rows, so it is the only slice where "routed vs non-routed" is a comparison
rather than a mixture. RELATIONAL's pooled-174 figure must NOT share a column
with TEMPORAL's 12 -- different denominators are not a table.

Batch 3 by the `type` column (what the router actually assigned, which is what a
verifier receives -- NOT `gold_type`):
    RELATIONAL 47 · QUANTITATIVE 29 · ENTITY_ATTRIBUTE 22 · TEMPORAL 12 · CITATION 12

PROVENANCE IS PRINTED, NOT ASSUMED
----------------------------------
CLAUDE.md's standing rule is "never trust a filename or a doc's description of a
file". Building this table broke that rule's target case wide open: five files on
disk give five different TEMPORAL/EA coverage figures, and CLAUDE.md's headline
EA number (5/22 = 22.7%) is reproducible from NONE of them. So every routed cell
below records the file, column, mtime and row count it came from, and
`--sources` prints the conflict table. Change ROUTED_SOURCES to re-point a cell;
never edit a number into a doc without re-running this.

USAGE
    python current/rq2_comparison.py                 # the table
    python current/rq2_comparison.py --sources       # provenance + the conflict
    python current/rq2_comparison.py --variant hybrid  # swap in the hybrid files
    python current/rq2_comparison.py --md out.md     # write the markdown report
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import metrics  # noqa: E402  -- the single source of truth for every figure

DECIDED = ("TRUE", "FALSE")
TYPES = ("RELATIONAL", "QUANTITATIVE", "ENTITY_ATTRIBUTE", "TEMPORAL", "CITATION")

BASELINE = "current/nonrouted_baseline_results.csv"

# --------------------------------------------------------------------------
# Routed sources. (file, verdict column, confidence column or None, note)
#
# DEFAULT variant = the files CLAUDE.md's QID-fix section explicitly names as
# "Results:" for TEMPORAL/EA. Those are the post-fix files and they report 0%
# coverage -- which is what the QID-fix narrative says should have happened
# ("coverage moved 8.3%->0% because the only covered claims had been the wrong
# ones"). The table row elsewhere in CLAUDE.md claiming 8.3%/22.7% post-fix
# contradicts both that section and every file on disk.
# --------------------------------------------------------------------------
ROUTED_SOURCES = {
    "default": {
        "RELATIONAL": ("current/relational_b3_verified_results.csv",
                       "verified_verdict", "verified_conf",
                       "Phase 3e, thresholds 0.55/0.45 + margin 0.15"),
        "QUANTITATIVE": ("current/quantitative_b3_results.csv",
                         "q_verdict", "q_confidence",
                         "structured extract-and-compare vs Wikidata quantity"),
        "ENTITY_ATTRIBUTE": ("current/entity_attribute_b3_verified_results_phase4.csv",
                             "verified_verdict", "verified_conf",
                             "cell 69 Phase 4, post-QID-fix"),
        "TEMPORAL": ("current/temporal_b3_verified_results_phase2.csv",
                     "verified_verdict", "verified_conf",
                     "cell 75 Phase 2, post-QID-fix"),
        "CITATION": ("current/citation_l1_results.csv",
                     "verdict", "confidence",
                     "Level 1 only (source existence); L2 attribution unbuilt"),
    },
    "hybrid": {
        "ENTITY_ATTRIBUTE": ("current/temporal_ea_hybrid_b3.csv", "verdict",
                             "confidence", "hybrid fall-through (UNREVIEWED)"),
        "TEMPORAL": ("current/temporal_ea_hybrid_b3.csv", "verdict",
                     "confidence", "hybrid fall-through (UNREVIEWED)"),
    },
    "prefix": {  # pre-QID-fix, kept only to reproduce the 8.3%/4.5% figures
        "ENTITY_ATTRIBUTE": ("current/entity_attribute_b3_verified_results.csv",
                             "verified_verdict", "verified_conf", "PRE-fix"),
        "TEMPORAL": ("current/temporal_b3_verified_results.csv",
                     "verified_verdict", "verified_conf", "PRE-fix"),
    },
}

# Files that disagree about the same quantity -- printed by --sources so the
# conflict is impossible to overlook.
CONFLICT_FILES = [
    ("current/temporal_b3_verified_results.csv", "TEMPORAL", "pre-QID-fix"),
    ("current/temporal_b3_verified_results_phase2.csv", "TEMPORAL", "post-fix, named in CLAUDE.md as Results"),
    ("current/entity_attribute_b3_verified_results.csv", "ENTITY_ATTRIBUTE", "pre-QID-fix"),
    ("current/entity_attribute_b3_verified_results_phase4.csv", "ENTITY_ATTRIBUTE", "post-fix, named in CLAUDE.md as Results"),
    ("current/temporal_ea_hybrid_b3.csv", "both", "hybrid fall-through, 34 rows = B3 T+EA"),
    ("current/temporal_ea_results.csv", "both", "58 rows -- NOT Batch 3"),
]


# --------------------------------------------------------------------------
# io
# --------------------------------------------------------------------------

def load(rel: str) -> list[dict]:
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def stamp(rel: str) -> str:
    p = os.path.join(ROOT, rel)
    st = os.stat(p)
    import datetime
    mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{st.st_size:>8} B  {mt}"


def norm(v: str | None) -> str:
    """Blank / missing -> UNVERIFIABLE. A verifier that wrote nothing did not
    answer, which is an abstention, not a silent TRUE."""
    v = (v or "").strip().upper()
    return v if v in ("TRUE", "FALSE", "UNVERIFIABLE") else "UNVERIFIABLE"


def conf_of(row: dict, col: str | None) -> float:
    if not col:
        return 0.0
    try:
        return float(row.get(col) or 0.0)
    except ValueError:
        return 0.0


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def build(variant: str):
    base = load(BASELINE)
    b3 = [r for r in base if r["claim_id"].startswith("B3_")]
    assert len(b3) == 122, f"expected 122 Batch-3 baseline rows, got {len(b3)}"

    srcs = dict(ROUTED_SOURCES["default"])
    if variant != "default":
        srcs.update(ROUTED_SOURCES[variant])

    out = {}
    for t in TYPES:
        rows = [r for r in b3 if r["type"] == t]
        ids = [r["claim_id"] for r in rows]
        idset = set(ids)

        path, vcol, ccol, note = srcs[t]
        rrows = load(path)
        rmap = {r["claim_id"]: r for r in rrows if r["claim_id"] in idset}

        gold, routed, d3, d3e, rconf, bconf = [], [], [], [], [], []
        for r in rows:
            cid = r["claim_id"]
            gold.append(norm(r["gold_verdict"]))
            d3.append(norm(r["verdict"]))
            d3e.append(norm(r["verdict_margin"]))
            bconf.append(conf_of(r, "verdict_confidence"))
            rr = rmap.get(cid)
            routed.append(norm(rr.get(vcol)) if rr else "UNVERIFIABLE")
            rconf.append(conf_of(rr, ccol) if rr else 0.0)

        out[t] = {
            "n": len(rows), "gold": gold, "routed": routed,
            "d3": d3, "d3e": d3e, "rconf": rconf, "bconf": bconf,
            "src": path, "vcol": vcol, "note": note,
            "matched": len(rmap), "src_rows": len(rrows),
        }
    return out


def sel(gold, pred):
    s = metrics.selective(gold, pred)
    prf = metrics.per_class_prf(gold, pred)
    return {
        "cov": s["coverage"], "cov_ci": s["coverage_ci"], "covered": s["covered"],
        "acc": s["accuracy"], "acc_ci": s["accuracy_ci"], "correct": s["correct"],
        "f1F": prf["FALSE"]["f1"], "mcc": metrics.mcc(gold, pred),
        "overreach": s["overreach"],
        "nFALSE_pred": prf["FALSE"]["predicted"], "nFALSE_tp": prf["FALSE"]["tp"],
    }


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def print_sources(data):
    print("\n" + "=" * 78)
    print("  PROVENANCE -- every routed cell's source file, verified on disk")
    print("=" * 78)
    for t in TYPES:
        d = data[t]
        print(f"\n{t}  (n={d['n']} Batch-3 claims routed here)")
        print(f"  file   {d['src']}")
        print(f"  stat   {stamp(d['src'])}   rows={d['src_rows']}")
        print(f"  column {d['vcol']}   matched {d['matched']}/{d['n']} claim_ids")
        print(f"  note   {d['note']}")
        if d["matched"] < d["n"]:
            print(f"  !! {d['n'] - d['matched']} claim(s) absent from the routed file "
                  f"-> counted as abstentions, which is the honest reading")

    print("\n" + "-" * 78)
    print("  CONFLICT: five files, five different TEMPORAL/EA coverage figures")
    print("-" * 78)
    for rel, which, why in CONFLICT_FILES:
        try:
            rows = load(rel)
        except OSError:
            print(f"  {rel}: MISSING"); continue
        vcol = ("verified_verdict" if "verified_verdict" in rows[0]
                else "verdict")
        parts = []
        for t in ("TEMPORAL", "ENTITY_ATTRIBUTE"):
            sub = [r for r in rows if r.get("type") == t]
            if not sub:
                continue
            dec = sum(1 for r in sub if norm(r.get(vcol)) in DECIDED)
            parts.append(f"{t[:4]} {dec}/{len(sub)} = {dec/len(sub):.1%}")
        print(f"  {rel}")
        print(f"      rows={len(rows):3d}  {stamp(rel)}  [{why}]")
        print(f"      {'  |  '.join(parts) if parts else 'no type column'}")
    print("\n  CLAUDE.md's table row states post-fix TEMPORAL 1/12 = 8.3% and")
    print("  EA 5/22 = 22.7%. NO file above yields EA 5/22. The 8.3% figure comes")
    print("  from the PRE-fix file, whose one covered claim is a FALSE -- i.e. the")
    print("  confident-wrong verdict the QID fix was written to remove. CLAUDE.md's")
    print("  own QID-fix section agrees with the files (8.3% -> 0%), so the table")
    print("  row is the error. AUTHOR DECISION: correct the row, or point it at a")
    print("  run that produced 5/22 and commit that file.")


def print_table(data, variant):
    print("\n" + "=" * 78)
    print(f"  RQ2 -- ROUTED vs NON-ROUTED, Batch 3 (n=122)      variant={variant}")
    print("=" * 78)
    print("  Non-routed = every claim -> Wikipedia retrieval + DeBERTa-v3, no type")
    print("  filter. Same claims, same gold, same evidence. Routing is the only")
    print("  variable. 3d = 0.50/0.40 (verified: reproduces stored verdicts 356/356)")
    print("  3e = 3d + margin >= 0.15.")

    hdr = (f"\n  {'type':<17}{'n':>4} | {'ROUTED':>21} | {'BASELINE 3d':>21} | "
           f"{'BASELINE 3e':>21}")
    print(hdr)
    print(f"  {'':<17}{'':>4} | {'cov':>7}{'sel-acc':>9}{'F1F':>5} | "
          f"{'cov':>7}{'sel-acc':>9}{'F1F':>5} | {'cov':>7}{'sel-acc':>9}{'F1F':>5}")
    print("  " + "-" * 74)

    def cell(s):
        """Zero coverage means NO ACCURACY EXISTS. Printing 0.0% there invites the
        worst possible misread -- a verifier that abstained on everything looking
        like one that got everything wrong -- so print a dash instead."""
        acc = f"{'--':>9}" if s["covered"] == 0 else f"{s['acc']:>9.1%}"
        return f"{s['cov']:>7.1%}{acc}{s['f1F']:>5.2f}"

    agg = {k: {"gold": [], "pred": [], "conf": []} for k in ("routed", "d3", "d3e")}
    for t in TYPES:
        d = data[t]
        r, a, b = sel(d["gold"], d["routed"]), sel(d["gold"], d["d3"]), sel(d["gold"], d["d3e"])
        print(f"  {t:<17}{d['n']:>4} | {cell(r)} | {cell(a)} | {cell(b)}")
        for key, pred, cf in (("routed", d["routed"], d["rconf"]),
                              ("d3", d["d3"], d["bconf"]),
                              ("d3e", d["d3e"], d["bconf"])):
            agg[key]["gold"] += d["gold"]
            agg[key]["pred"] += pred
            agg[key]["conf"] += cf

    print("  " + "-" * 74)
    gold_all = agg["routed"]["gold"]
    r, a, b = (sel(gold_all, agg["routed"]["pred"]),
               sel(gold_all, agg["d3"]["pred"]), sel(gold_all, agg["d3e"]["pred"]))
    print(f"  {'POOLED B3':<17}{len(gold_all):>4} | {cell(r)} | {cell(a)} | {cell(b)}")

    gc = Counter(gold_all)
    at = gc["TRUE"] / len(gold_all)
    print(f"\n  Always-True on the same 122: accuracy {at:.1%}  F1(FALSE) 0.00  MCC 0.000")
    print(f"  Gold mix: {gc['TRUE']} TRUE / {gc['FALSE']} FALSE / "
          f"{gc['UNVERIFIABLE']} UNVERIFIABLE")

    # --- the numbers that actually decide RQ2 -----------------------------
    print("\n" + "-" * 78)
    print("  DETECTION -- the only column that separates these systems")
    print("-" * 78)
    print(f"  {'system':<14}{'FALSE pred':>12}{'of which right':>16}"
          f"{'precision':>11}{'MCC':>9}{'AURAC':>8}")
    for name, key in (("routed", "routed"), ("baseline 3d", "d3"), ("baseline 3e", "d3e")):
        s = sel(gold_all, agg[key]["pred"])
        prec = (s["nFALSE_tp"] / s["nFALSE_pred"]) if s["nFALSE_pred"] else float("nan")
        au = metrics.aurac(gold_all, agg[key]["pred"], agg[key]["conf"])
        ps = "   n/a" if s["nFALSE_pred"] == 0 else f"{prec:>11.3f}"
        print(f"  {name:<14}{s['nFALSE_pred']:>12}{s['nFALSE_tp']:>16}{ps}"
              f"{s['mcc']:>+9.3f}{au:>8.3f}")
    print(f"\n  Only {gc['FALSE']} gold negatives in Batch 3. Every F1(FALSE) and MCC")
    print("  above is high-variance -- read the FALSE-prediction counts, not the")
    print("  ratios, and see --sources for what a false-alarm rate here means.")

    # --- overlap check: can these numbers separate the systems at all? ----
    print("\n" + "-" * 78)
    print("  CAN THIS TABLE SEPARATE ROUTED FROM NON-ROUTED? (Wilson, per type)")
    print("-" * 78)
    for t in TYPES:
        d = data[t]
        r, a = sel(d["gold"], d["routed"]), sel(d["gold"], d["d3"])
        if r["covered"] == 0:
            print(f"  {t:<17} routed covers 0/{d['n']} -> no accuracy exists to compare")
            continue
        rl, rh = r["acc_ci"]; al, ah = a["acc_ci"]
        overlap = not (rh < al or ah < rl)
        print(f"  {t:<17} routed {r['acc']:.0%} [{rl:.0%},{rh:.0%}] n={r['covered']:<3} "
              f"vs 3d {a['acc']:.0%} [{al:.0%},{ah:.0%}] n={a['covered']:<3} "
              f"-> {'OVERLAP: cannot separate' if overlap else 'separated'}")


def write_md(data, variant, path):
    lines = []
    A = lines.append
    A("# RQ2 — routed vs non-routed, Batch 3\n")
    A(f"Generated by `current/rq2_comparison.py --variant {variant}`. "
      "Zero model calls: a join over existing CSVs plus `current/metrics.py`.\n")
    A("Scope is **Batch 3 only (n=122)** — the sole claim set where all five routed "
      "verifiers have results on the same rows. Counts are by the **`type`** column "
      "(what the router assigned, i.e. what a verifier receives), not `gold_type`.\n")
    gold_all = [g for t in TYPES for g in data[t]["gold"]]
    gc = Counter(gold_all)
    A(f"Gold mix: **{gc['TRUE']} TRUE / {gc['FALSE']} FALSE / "
      f"{gc['UNVERIFIABLE']} UNVERIFIABLE**, so Always-True scores "
      f"**{gc['TRUE']/len(gold_all):.1%}** with F1(FALSE) = 0.00.\n")

    A("| type | n | routed cov | routed acc | 3d cov | 3d acc | 3e cov | 3e acc |")
    A("|---|---|---|---|---|---|---|---|")
    for t in TYPES:
        d = data[t]
        r, a, b = sel(d["gold"], d["routed"]), sel(d["gold"], d["d3"]), sel(d["gold"], d["d3e"])
        racc = "—" if r["covered"] == 0 else f"{r['acc']:.1%}"
        A(f"| {t} | {d['n']} | {r['cov']:.1%} | {racc} | {a['cov']:.1%} | "
          f"{a['acc']:.1%} | {b['cov']:.1%} | {b['acc']:.1%} |")

    A("\n## Provenance\n")
    A("| type | routed source | rows | matched | note |")
    A("|---|---|---|---|---|")
    for t in TYPES:
        d = data[t]
        A(f"| {t} | `{d['src']}` | {d['src_rows']} | {d['matched']}/{d['n']} | "
          f"{d['note']} |")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="default",
                    choices=sorted(ROUTED_SOURCES))
    ap.add_argument("--sources", action="store_true")
    ap.add_argument("--md")
    args = ap.parse_args()

    data = build(args.variant)
    if args.sources:
        print_sources(data)
    print_table(data, args.variant)
    if args.md:
        write_md(data, args.variant, args.md)


if __name__ == "__main__":
    main()
