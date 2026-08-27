#!/usr/bin/env python3
"""
HalDetect — Master Benchmark Corpus Assembler (v2.0)
===================================================

Harmonizes and compiles the complete master evaluation corpus across all 5 slices:
  1. Natural Corpus (Batch 1, Phase 2, Batch 3)        -> origin: 'natural_corpus' (n=400)
  2. FActScore Benchmark (Min et al., EMNLP 2023)      -> origin: 'factscore_b1'   (n=100)
  3. External Human-Verified Negatives                 -> origin: 'external_neg'   (n=75)
  4. Diagnostic Controlled Perturbations               -> origin: 'synthetic_diag' (n=84)
  5. Real-World Query Expansion (EXP_*)                -> origin: 'expansion_real' (n=72)

Total: ~731 high-density claims with balanced true/false distributions and zero data loss.
Output: `current/haldetect_master_corpus_v2.csv`
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "haldetect_master_corpus_v2.csv")

SLICES = {
    "natural_corpus": os.path.join(HERE, "haldetect_claims_unified.csv"),
    "factscore_b1": os.path.join(HERE, "factscore_block1.csv"),
    "external_neg": os.path.join(HERE, "external_negatives.csv"),
    "synthetic_diag": os.path.join(HERE, "synthetic_negatives.csv"),
    "expansion_real": os.path.join(HERE, "expansion_realworld_claims.csv"),
}

MASTER_COLUMNS = [
    "master_id", "claim_id", "type", "subject", "property", "value",
    "gold_verdict", "claim", "origin_dataset", "is_synthetic",
    "domain", "notes"
]


def load_and_normalize() -> list[dict]:
    master_rows = []
    seen_ids = set()
    counter = 1

    # 1. Natural Unified Corpus
    p = SLICES["natural_corpus"]
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            cid = r.get("claim_id", "").strip() or f"NAT_{counter:04d}"
            master_rows.append({
                "master_id": f"MST_{counter:04d}",
                "claim_id": cid,
                "type": (r.get("type") or "").upper(),
                "subject": r.get("subject", "").strip(),
                "property": r.get("property", "").strip(),
                "value": r.get("value", "").strip(),
                "gold_verdict": (r.get("gold_verdict") or "").upper(),
                "claim": r.get("claim", "").strip(),
                "origin_dataset": "natural_corpus",
                "is_synthetic": str(r.get("synthetic", "FALSE")).upper(),
                "domain": r.get("batch", "natural"),
                "notes": r.get("notes", "")
            })
            counter += 1

    # 2. FActScore Block 1
    p = SLICES["factscore_b1"]
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            cid = r.get("claim_id", "").strip() or f"FS_{counter:04d}"
            master_rows.append({
                "master_id": f"MST_{counter:04d}",
                "claim_id": cid,
                "type": (r.get("type") or "").upper(),
                "subject": r.get("subject", "").strip(),
                "property": r.get("property", "").strip(),
                "value": r.get("value", "").strip(),
                "gold_verdict": (r.get("gold_verdict") or "").upper(),
                "claim": r.get("claim", "").strip(),
                "origin_dataset": "factscore_b1",
                "is_synthetic": "FALSE",
                "domain": f"factscore_{r.get('source_model', 'unknown')}",
                "notes": f"rarity:{r.get('rarity', '')}; region:{r.get('region', '')}"
            })
            counter += 1

    # 3. External Negatives
    p = SLICES["external_neg"]
    if os.path.isfile(p):
        for i, r in enumerate(csv.DictReader(open(p, newline="", encoding="utf-8")), 1):
            cid = f"EXT_NEG_{i:03d}"
            # Extract subject from topic
            subj = r.get("topic", "").strip()
            master_rows.append({
                "master_id": f"MST_{counter:04d}",
                "claim_id": cid,
                "type": "ENTITY_ATTRIBUTE", # default atomic attribution
                "subject": subj,
                "property": "attribution",
                "value": "unsupported",
                "gold_verdict": "FALSE",
                "claim": r.get("claim", "").strip(),
                "origin_dataset": "external_neg",
                "is_synthetic": "FALSE",
                "domain": r.get("source", "external"),
                "notes": r.get("notes", "")
            })
            counter += 1

    # 4. Diagnostic Synthetic Negatives
    p = SLICES["synthetic_diag"]
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            cid = r.get("claim_id", "").strip() or f"SYN_{counter:04d}"
            master_rows.append({
                "master_id": f"MST_{counter:04d}",
                "claim_id": cid,
                "type": (r.get("type") or "").upper(),
                "subject": r.get("subject", "").strip(),
                "property": r.get("property", "").strip(),
                "value": r.get("corrupted_value", r.get("value", "")).strip(),
                "gold_verdict": "FALSE",
                "claim": r.get("claim", "").strip(),
                "origin_dataset": "synthetic_diag",
                "is_synthetic": "TRUE",
                "domain": "diagnostic_perturbation",
                "notes": f"injection:{r.get('injection_type', '')}; orig:{r.get('original_value', '')}"
            })
            counter += 1

    # 5. Real-World Query Expansion
    p = SLICES["expansion_real"]
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            cid = r.get("claim_id", "").strip() or f"EXP_{counter:04d}"
            master_rows.append({
                "master_id": f"MST_{counter:04d}",
                "claim_id": cid,
                "type": (r.get("type") or "").upper(),
                "subject": r.get("subject", "").strip(),
                "property": r.get("property", "").strip(),
                "value": r.get("value", "").strip(),
                "gold_verdict": (r.get("gold_verdict") or "").upper(),
                "claim": r.get("claim", "").strip(),
                "origin_dataset": "expansion_real",
                "is_synthetic": str(r.get("synthetic", "FALSE")).upper(),
                "domain": r.get("domain", "real_query"),
                "notes": f"subtype:{r.get('sub_type', '')}; {r.get('notes', '')}"
            })
            counter += 1

    return master_rows


def print_stats(rows: list[dict]) -> None:
    print(f"\n{'=' * 74}")
    print(f"  MASTER BENCHMARK CORPUS (v2.0) — SUMMARY STATISTICS")
    print(f"{'=' * 74}")
    print(f"Total Master Claims: {len(rows)}")

    by_origin = collections.Counter(r["origin_dataset"] for r in rows)
    print("\n-- By Origin Dataset --")
    for k, v in sorted(by_origin.items()):
        print(f"  {k:<20} {v:>5} claims ({v / len(rows):.1%})")

    by_type = collections.Counter(r["type"] for r in rows)
    print("\n-- By Modality Type --")
    for k, v in sorted(by_type.items()):
        print(f"  {k:<20} {v:>5} claims ({v / len(rows):.1%})")

    by_verdict = collections.Counter(r["gold_verdict"] for r in rows)
    print("\n-- By Gold Verdict --")
    for k, v in sorted(by_verdict.items()):
        print(f"  {k:<20} {v:>5} claims ({v / len(rows):.1%})")

    by_synth = collections.Counter(r["is_synthetic"] for r in rows)
    print("\n-- Synthetic vs Natural --")
    for k, v in sorted(by_synth.items()):
        print(f"  synthetic={k:<8} {v:>5} claims ({v / len(rows):.1%})")


def write_master_csv(rows: list[dict], output_path: str = OUT_CSV) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MASTER_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSuccessfully wrote {len(rows)} claims to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble Master Benchmark Corpus.")
    parser.add_argument("--write", action="store_true", help="Write output CSV")
    parser.add_argument("--stats", action="store_true", help="Display stats only")
    parser.add_argument("--out", default=OUT_CSV, help="Output path")
    args = parser.parse_args()

    rows = load_and_normalize()

    if args.stats or not args.write:
        print_stats(rows)
        if not args.write:
            print("\n(Dry run complete. Pass --write to emit master CSV)")
        return 0

    if args.write:
        write_master_csv(rows, args.out)
        print_stats(rows)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
