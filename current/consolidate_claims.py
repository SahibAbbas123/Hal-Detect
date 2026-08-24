#!/usr/bin/env python3
"""
Consolidate all four HalDetect gold claim sets into one unified CSV.

WHY THIS EXISTS
---------------
The project had been evaluating on Batch 3's 122 claims while **356 real labeled
claims** existed across three disjoint batches, plus 27 synthetic negatives.
Batch 1's 125 labels were stranded in `archive/` inside a file that the
2026-08-21 reorg had filed as a `(1)`/`(2)` browser-download duplicate — but the
`_1`/`_2` variants are the *only* labeled copies of Batch 1.

Full rationale, verified counts and the schema decisions:
`reference/claim_set_inventory_2026-08-22.md`

WHAT IT GUARDS AGAINST
----------------------
Four separate traps found by direct inspection, each of which a naive
`pd.concat` would hit silently:

1.  **Four different schemas** (14 / 15 / 19 / 12 columns) and Batch 3
    interleaves `pair_id`/`pair_incomplete` *between* `flagged` and `subject`.
    => Column position is NOT stable. This script uses `csv.DictReader` only and
    never indexes by position.
2.  **`flagged` has three encodings**: `TRUE`/`FALSE` (Batch 1),
    `True`/`False` (Phase 2, Batch 3), absent (negatives).
    => Normalised to lowercase `true`/`false`/`""`.
3.  **`TRUE`/`FALSE` is overloaded** across `flagged` and `gold_verdict`, which
    already produced one wrong row count in this project.
    => Verdicts are read by column name, never by regex.
4.  **`gold_type` is not an independent label in Phase 2 or Batch 3** — it was
    seeded from the classifier's own `type` and never reviewed (109/109 and
    122/122 agreement, identical distributions). Only Batch 1 has reviewed
    types.
    => Emitted as an explicit `gold_type_independent` column, and
    `--routing` REFUSES to score any batch where it is false. The constraint is
    executable, not just documented.

Batch 1 authority: `_1` and `_2` differ in exactly 8 rows, all `gold_type`,
verdicts identical. `_1` has 6 router disagreements, `_2` has 14 — so `_2` holds
8 *additional* type corrections and is the later, authoritative pass.

USAGE
-----
    python current/consolidate_claims.py --verify     # check only, write nothing
    python current/consolidate_claims.py --write      # emit the unified CSV
    python current/consolidate_claims.py --stats      # pooled distributions + Wilson CIs
    python current/consolidate_claims.py --routing    # Batch 1 confusion matrix (only legal batch)

Nothing existing is modified. `--write` creates exactly one new file.
Reverse with: rm current/haldetect_claims_unified.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

OUT_PATH = os.path.join(HERE, "haldetect_claims_unified.csv")

TYPES = ("RELATIONAL", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "QUANTITATIVE")
VERDICTS = ("TRUE", "FALSE", "UNVERIFIABLE")

# ---------------------------------------------------------------------------
# Source definitions. `expect` values were verified by grep before this script
# was written -- they are ground truth, and a mismatch means either the file
# changed or this loader is wrong. Either way it must fail loudly.
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "batch": "b1",
        "path": os.path.join(ROOT, "archive", "csvs",
                             "haldetect_claims_20260524_045439_2.csv"),
        "gold_type_independent": True,   # the ONLY batch with reviewed types
        "synthetic": False,
        # Corrected 2026-08-22 (evening): was `rows: 126`, which came from
        # `wc -l` minus one. Verified directly instead: `grep -c "^Q[0-9]"`
        # returns 125, the file has no trailing newline, and two rows carry
        # embedded newlines inside quoted fields -- so 127 newlines describe
        # 125 logical rows. DictReader's 125 was right and the expectation was
        # wrong. The labeled count and verdict split were always correct, so
        # the pooled 356 total is unaffected.
        "expect": {"rows": 125, "labeled": 125,
                   "verdicts": {"TRUE": 112, "FALSE": 8, "UNVERIFIABLE": 5}},
        "note": "authoritative pass (_2); 8 more type corrections than _1",
    },
    {
        "batch": "p2",
        "path": os.path.join(HERE, "haldetect_phase2_goldlabeled (3).csv"),
        "gold_type_independent": False,  # gold_type seeded from `type`
        "synthetic": False,
        "expect": {"rows": 126, "labeled": 109,
                   "verdicts": {"TRUE": 87, "FALSE": 1, "UNVERIFIABLE": 21}},
        "note": "17 rows unlabeled; gold_type NOT independent",
    },
    {
        "batch": "b3",
        "path": os.path.join(HERE, "haldetect_claims_b3_gold.csv"),
        "gold_type_independent": False,  # gold_type seeded from `type`
        "synthetic": False,
        "expect": {"rows": 122, "labeled": 122,
                   "verdicts": {"TRUE": 115, "FALSE": 4, "UNVERIFIABLE": 3}},
        "note": "gold_type NOT independent",
    },
    {
        "batch": "b3neg",
        "path": os.path.join(HERE, "relational_negatives_batch3_merged.csv"),
        "gold_type_independent": False,
        "synthetic": True,
        "expect": {"rows": 27, "labeled": 27,
                   "verdicts": {"TRUE": 0, "FALSE": 27, "UNVERIFIABLE": 0}},
        "note": "synthetic; typed by injection_type; no q_id/drift/flagged",
    },
]

# Unified schema. Core first, provenance next, batch-specific nullable last.
CORE = ["batch", "q_id", "claim_id", "claim", "type", "drift", "flagged",
        "subject", "property", "value", "secondary",
        "gold_type", "gold_verdict", "gold_type_independent",
        "synthetic", "injection_type", "notes"]
EXTRA = ["pair_id", "pair_incomplete", "extraction_failed",
         "classification_fallback_used", "triage_flag", "triage_reason",
         "source_q"]
UNIFIED = CORE + EXTRA


def norm_bool(raw: str) -> str:
    """Collapse the three `flagged` encodings to one. Empty stays empty."""
    s = (raw or "").strip()
    if not s:
        return ""
    low = s.lower()
    if low in ("true", "1", "yes"):
        return "true"
    if low in ("false", "0", "no"):
        return "false"
    return s  # preserve anything unexpected rather than silently dropping it


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval. Returns (point, lo, hi)."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, max(0.0, c - h), min(1.0, c + h)


def load(src: dict) -> tuple[list[dict], list[str]]:
    """Read one source into unified-schema dicts. DictReader only: never by position."""
    if not os.path.exists(src["path"]):
        raise SystemExit(f"MISSING: {src['path']}")

    problems: list[str] = []
    rows: list[dict] = []
    with open(src["path"], newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        unknown = [c for c in header if c not in UNIFIED and c is not None]
        if unknown:
            problems.append(f"{src['batch']}: unmapped source columns {unknown}")

        for raw in reader:
            out = {c: "" for c in UNIFIED}
            for col in UNIFIED:
                if col in raw and raw[col] is not None:
                    out[col] = (raw[col] or "").strip()

            out["batch"] = src["batch"]
            out["flagged"] = norm_bool(out["flagged"])
            out["pair_incomplete"] = norm_bool(out["pair_incomplete"])
            out["extraction_failed"] = norm_bool(out["extraction_failed"])
            out["classification_fallback_used"] = norm_bool(
                out["classification_fallback_used"])
            out["gold_type_independent"] = ("true" if src["gold_type_independent"]
                                            else "false")
            # negatives set carries its own `synthetic` column; trust the source
            # where present, else stamp from the source definition.
            out["synthetic"] = (norm_bool(out["synthetic"])
                                or ("true" if src["synthetic"] else "false"))
            rows.append(out)

    exp = src["expect"]
    if len(rows) != exp["rows"]:
        problems.append(f"{src['batch']}: expected {exp['rows']} rows, got {len(rows)}")

    labeled = [r for r in rows if r["gold_verdict"] in VERDICTS]
    if len(labeled) != exp["labeled"]:
        problems.append(
            f"{src['batch']}: expected {exp['labeled']} labeled, got {len(labeled)}")

    got = Counter(r["gold_verdict"] for r in labeled)
    for v, n in exp["verdicts"].items():
        if got.get(v, 0) != n:
            problems.append(
                f"{src['batch']}: expected {n} {v}, got {got.get(v, 0)}")

    return rows, problems


def load_all() -> tuple[list[dict], list[str]]:
    allrows: list[dict] = []
    problems: list[str] = []
    for src in SOURCES:
        rows, probs = load(src)
        allrows.extend(rows)
        problems.extend(probs)

    # Disjointness: verified by inspection, enforced here.
    seen: dict[str, str] = {}
    for r in allrows:
        cid = r["claim_id"]
        if not cid:
            problems.append(f"{r['batch']}: row with empty claim_id")
            continue
        if cid in seen:
            problems.append(
                f"claim_id collision {cid}: {seen[cid]} and {r['batch']}")
        seen[cid] = r["batch"]

    return allrows, problems


def report_sources(rows: list[dict]) -> None:
    print("\n=== Per-source ===")
    print(f"{'batch':<8}{'rows':>6}{'labeled':>9}{'TRUE':>7}{'FALSE':>7}{'UNVER':>7}"
          f"  gold_type_independent")
    for src in SOURCES:
        sub = [r for r in rows if r["batch"] == src["batch"]]
        lab = [r for r in sub if r["gold_verdict"] in VERDICTS]
        c = Counter(r["gold_verdict"] for r in lab)
        print(f"{src['batch']:<8}{len(sub):>6}{len(lab):>9}"
              f"{c.get('TRUE', 0):>7}{c.get('FALSE', 0):>7}"
              f"{c.get('UNVERIFIABLE', 0):>7}"
              f"  {str(src['gold_type_independent']).lower()}"
              f"   ({src['note']})")


def report_stats(rows: list[dict]) -> None:
    lab = [r for r in rows if r["gold_verdict"] in VERDICTS]
    real = [r for r in lab if r["synthetic"] != "true"]

    print("\n=== Pooled ===")
    for name, pool in (("real gold", real), ("real + synthetic", lab)):
        c = Counter(r["gold_verdict"] for r in pool)
        n = len(pool)
        always_true = c.get("TRUE", 0) / n if n else 0.0
        print(f"{name:<18} n={n:<5} TRUE={c.get('TRUE', 0):<4} "
              f"FALSE={c.get('FALSE', 0):<4} UNVER={c.get('UNVERIFIABLE', 0):<4} "
              f"Always-True baseline = {always_true:.1%}")

    print("\n=== Per gold_type (real gold only) ===")
    print(f"{'gold_type':<20}{'n':>5}{'TRUE':>7}{'FALSE':>7}{'UNVER':>7}   by batch")
    by = defaultdict(list)
    for r in real:
        by[r["gold_type"]].append(r)
    for t in TYPES:
        sub = by.get(t, [])
        c = Counter(r["gold_verdict"] for r in sub)
        b = Counter(r["batch"] for r in sub)
        spread = " ".join(f"{k}={v}" for k, v in sorted(b.items()))
        print(f"{t:<20}{len(sub):>5}{c.get('TRUE', 0):>7}{c.get('FALSE', 0):>7}"
              f"{c.get('UNVERIFIABLE', 0):>7}   {spread}")
        if c.get("FALSE", 0) == 0 and sub:
            print(f"{'':<20}  ^ ZERO gold negatives -- accuracy here is "
                  f"uninformative; use controlled perturbation")

    # The headline CI win, computed rather than hand-derived.
    print("\n=== Interval width: what pooling buys RELATIONAL ===")
    rel = len(by.get("RELATIONAL", []))
    b3_rel = len([r for r in by.get("RELATIONAL", []) if r["batch"] == "b3"])
    cov, acc = 0.5532, 0.8077
    for label, raw_n in (("Batch 3 only", b3_rel), ("pooled", rel)):
        covered = max(1, round(raw_n * cov))
        k = round(covered * acc)
        p, lo, hi = wilson(k, covered)
        print(f"  {label:<14} raw n={raw_n:<4} covered~{covered:<4} "
              f"acc {p:.1%}  95% CI [{lo:.1%}, {hi:.1%}]  "
              f"+/-{(hi - lo) / 2 * 100:.1f}pp")
    print("  (projection at measured coverage/accuracy -- a sample-size estimate,")
    print("   NOT a result. Re-run the verifiers on the pooled set to measure.)")


def report_routing(rows: list[dict]) -> None:
    """Routing accuracy. Refuses batches whose gold_type was seeded."""
    print("\n=== Routing (classifier `type` vs human `gold_type`) ===")
    legal = [r for r in rows
             if r["gold_type_independent"] == "true"
             and r["gold_verdict"] in VERDICTS
             and r["type"] and r["gold_type"]]
    refused = sorted({r["batch"] for r in rows
                      if r["gold_type_independent"] != "true"})
    print(f"REFUSED batches (gold_type seeded from `type`, so any score is 100% "
          f"by construction): {', '.join(refused)}")
    if not legal:
        print("No batch with independent gold_type. Nothing scoreable.")
        return

    batches = sorted({r["batch"] for r in legal})
    correct = sum(1 for r in legal if r["type"] == r["gold_type"])
    p, lo, hi = wilson(correct, len(legal))
    print(f"Scoreable batches: {', '.join(batches)}  (n={len(legal)})")
    print(f"Router accuracy = {correct}/{len(legal)} = {p:.1%}  "
          f"95% CI [{lo:.1%}, {hi:.1%}]")

    conf = Counter((r["type"], r["gold_type"]) for r in legal
                   if r["type"] != r["gold_type"])
    print("\nConfusions (classifier -> gold):")
    for (a, b), n in conf.most_common():
        print(f"  {n:>3}  {a} -> {b}")

    print(f"\n{'route':<20}{'n':>5}{'correct':>9}{'precision':>11}"
          f"{'recall':>9}   95% CI on precision")
    for t in TYPES:
        pred = [r for r in legal if r["type"] == t]
        gold = [r for r in legal if r["gold_type"] == t]
        hit = sum(1 for r in pred if r["gold_type"] == t)
        if not pred and not gold:
            continue
        pp, plo, phi = wilson(hit, len(pred)) if pred else (0.0, 0.0, 0.0)
        rec = hit / len(gold) if gold else 0.0
        flag = "   <-- OVER-FIRING" if pred and pp < 0.75 else ""
        print(f"{t:<20}{len(pred):>5}{hit:>9}{pp:>10.1%}{rec:>9.1%}"
              f"   [{plo:.1%}, {phi:.1%}]{flag}")


def write_out(rows: list[dict]) -> None:
    if os.path.exists(OUT_PATH):
        raise SystemExit(f"REFUSING to overwrite existing {OUT_PATH}\n"
                         f"Delete it first if you really mean to regenerate.")
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=UNIFIED)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWROTE {OUT_PATH}  ({len(rows)} rows, {len(UNIFIED)} columns)")
    print("Reverse with: rm current/haldetect_claims_unified.csv")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="check only, write nothing")
    ap.add_argument("--write", action="store_true", help="emit the unified CSV")
    ap.add_argument("--stats", action="store_true", help="pooled distributions + Wilson CIs")
    ap.add_argument("--routing", action="store_true",
                    help="routing confusion matrix (independent-gold_type batches only)")
    args = ap.parse_args()

    if not any((args.verify, args.write, args.stats, args.routing)):
        ap.print_help()
        return 1

    rows, problems = load_all()
    report_sources(rows)

    if problems:
        print("\n!!! INTEGRITY PROBLEMS -- expected counts were verified by grep "
              "before this script existed, so a mismatch means the files changed "
              "or this loader is wrong. Not writing anything.")
        for p in problems:
            print(f"  - {p}")
        return 2
    print("\nAll expected row counts, labeled counts and verdict distributions match.")
    print("All claim_ids disjoint across the four sets.")

    if args.stats:
        report_stats(rows)
    if args.routing:
        report_routing(rows)
    if args.write:
        write_out(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
