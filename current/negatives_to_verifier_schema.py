#!/usr/bin/env python3
"""Adapt `synthetic_negatives.csv` to the schema the routed verifiers read.

WHY AN ADAPTER AND NOT A DIRECT RUN
-----------------------------------
`quantitative_verifier.py` reads the claimed number from a column called
`value` (line 855). `synthetic_negatives.csv` has no such column -- it carries
`original_value` and `corrupted_value`, because a perturbation-based negative is
defined by the pair. Pointing `--diagnose` straight at it leaves `value` empty
and silently falls through to `parse_quantity`'s claim-text route.

That fallback would *probably* work, and "probably" is the problem. A sentence
like "The war resulted in approximately over 20,000 deaths" contains one number,
but others in the set contain several, and which one a text parser picks is not
something the measurement should depend on. Mapping `corrupted_value -> value`
explicitly makes the comparison unambiguous: we assert exactly the number the
perturbation injected, and nothing else.

THE TWO POPULATIONS, WHICH ARE NOT THE SAME
-------------------------------------------
12 of the 85 negatives were proven (2026-08-25) to have read their *base claim's*
cached NLI scores, via the `claim[:60]` cache-key collision in phase3d --
bit-identical entail/contradict floats, with 0 of 69 non-colliding rows matching
as a control. Those rows are not evidence about the baseline.

But the corruption is in the *NLI cache*, and the routed QUANTITATIVE verifier
never touches NLI -- it compares against Wikidata `quantity` statements. So:

  * `--all`   (default) : all 24 QUANTITATIVE negatives. Valid for the ROUTED
                          verifier's standalone capability.
  * `--clean`           : the 15 whose baseline verdict is uncorrupted. This is
                          the only population a PAIRED routed-vs-baseline
                          comparison may use.

Emitting both, and labelling which is which, is the point of the script. Writes
CSVs only; makes no network or model calls.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SRC = os.path.join(HERE, "synthetic_negatives.csv")

# Proven cache-corrupt on 2026-08-25: collided key AND bit-identical entail/
# contradict against the base claim. See WORKLOG Step 33.
CACHE_CORRUPT = {
    "SYN_QUAN_027", "SYN_QUAN_028", "SYN_QUAN_032", "SYN_QUAN_033",
    "SYN_QUAN_034", "SYN_QUAN_035", "SYN_QUAN_036", "SYN_QUAN_037",
    "SYN_QUAN_038", "SYN_TEMP_056", "SYN_TEMP_057", "SYN_TEMP_058",
}

# Columns the routed verifiers read, in the order the gold CSVs use them.
OUT_COLS = [
    "claim_id", "claim", "type", "gold_type", "subject", "property", "value",
    "secondary", "gold_verdict",
    # provenance, carried through so a result row can be traced back
    "original_value", "corrupted_value", "injection_type", "magnitude",
    "base_claim_id", "cache_corrupt",
]


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def adapt(rows: list[dict], claim_type: str | None, clean_only: bool) -> list[dict]:
    out = []
    for r in rows:
        if claim_type and r.get("type") != claim_type:
            continue
        corrupt = r["claim_id"] in CACHE_CORRUPT
        if clean_only and corrupt:
            continue
        out.append({
            "claim_id": r["claim_id"],
            "claim": r["claim"],
            "type": r["type"],
            "gold_type": r.get("gold_type") or r["type"],
            "subject": r["subject"],
            "property": r["property"],
            # The whole point of the adapter.
            "value": r["corrupted_value"],
            "secondary": r.get("secondary", ""),
            "gold_verdict": r["gold_verdict"],
            "original_value": r["original_value"],
            "corrupted_value": r["corrupted_value"],
            "injection_type": r.get("injection_type", ""),
            "magnitude": r.get("magnitude", ""),
            "base_claim_id": r.get("base_claim_id", ""),
            "cache_corrupt": "1" if corrupt else "0",
        })
    return out


def write(rows: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--type", default="QUANTITATIVE",
                    help="claim type to emit, or ALL for every type")
    ap.add_argument("--out-dir", default=HERE)
    args = ap.parse_args()

    if not os.path.isfile(SRC):
        print(f"missing {SRC}", file=sys.stderr)
        return 1

    rows = load(SRC)
    ct = None if args.type.upper() == "ALL" else args.type.upper()
    tag = (ct or "all").lower()

    every = adapt(rows, ct, clean_only=False)
    clean = adapt(rows, ct, clean_only=True)

    if not every:
        print(f"no rows of type {ct!r} in {os.path.basename(SRC)}", file=sys.stderr)
        return 1

    p_all = os.path.join(args.out_dir, f"negatives_verifier_{tag}_all.csv")
    p_cln = os.path.join(args.out_dir, f"negatives_verifier_{tag}_clean.csv")
    write(every, p_all)
    write(clean, p_cln)

    ncorr = sum(1 for r in every if r["cache_corrupt"] == "1")
    print(f"source            : {os.path.relpath(SRC, ROOT)}")
    print(f"type              : {ct or 'ALL'}")
    print(f"rows (all)        : {len(every):>3}  -> {os.path.relpath(p_all, ROOT)}")
    print(f"rows (clean)      : {len(clean):>3}  -> {os.path.relpath(p_cln, ROOT)}")
    print(f"cache-corrupt     : {ncorr:>3}  (excluded from the clean file)")
    print(f"all gold FALSE    : {all(r['gold_verdict'] == 'FALSE' for r in every)}")
    print(f"empty value cells : {sum(1 for r in every if not r['value'].strip())}")
    print()
    print("  Use the *_all file for the routed verifier's standalone number")
    print("  (it never reads the NLI cache). Use the *_clean file for any")
    print("  PAIRED comparison against the non-routed baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
