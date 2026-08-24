#!/usr/bin/env python3
"""
Re-classify a FActScore block with the ORIGINAL pipeline classifier.

WHY
---
Block D was classified with a reconstruction that scored 83.1% against Batch 1's human
`gold_type`, where the original pipeline scored 93.8% on the same held-out claims. That
put ~17% avoidable mis-typing upstream of every verifier, and the verifiers were charged
for it. `current/original_classifier.py` now reproduces the real classifier and has been
validated at **95.4% agreement** with its recorded output, so Block D can be re-typed
properly.

TWO DELIBERATE DEVIATIONS, BOTH REQUIRED
----------------------------------------
1. **Coreference is resolved before classification.** FActScore atomic facts are
   atomised but NOT coreference-resolved -- "He has appeared in numerous films" carries
   no subject. The original pipeline resolves coreference at Rule 6, *before* extraction,
   so doing it here is faithful rather than an addition. Without it the original
   extraction prompt returns subject="He", which no entity resolver can use.
   The replacement uses the entry's `topic`, which is the person the biography is about.

2. **Subject comes from `topic`, not from the extractor.** Even after pronoun
   substitution, letting the LLM re-derive the subject risks it picking a secondary
   entity mentioned in the sentence. `topic` is ground truth about who the biography
   concerns, so using it is strictly better information, not a shortcut.

Property and value DO come from the original extraction prompt, so the fields the
Wikidata verifiers consume are the pipeline's own.

WHAT THIS CHANGES AND WHAT IT DOES NOT
--------------------------------------
It removes the classifier confound. It does not remove the others: FActScore remains
biography-only (so entity resolution is easier here than on this project's multi-domain
corpus), and its labels remain fixed against a 2023 Wikipedia snapshot while the
verifiers query Wikidata live.
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

import original_classifier as OC   # noqa: E402

IN = os.path.join(HERE, "factscore_block1.csv")
OUT = os.path.join(HERE, "factscore_block1_origcls.csv")

# Leading-pronoun substitution only. A blanket replace would corrupt claims where the
# pronoun refers to someone else ("His son said he would...") -- restricting to the
# sentence-initial subject position is the conservative choice, and it covers the
# actual FActScore shape ("He has appeared...", "She was born...").
_PRON = re.compile(r"^(He|She|They|His|Her|Their|Him|Them)\b")


def resolve_coref(claim: str, topic: str) -> tuple[str, bool]:
    """Replace a leading pronoun with the biography's subject. Rule 6."""
    m = _PRON.match(claim or "")
    if not m or not topic:
        return claim, False
    word = m.group(1)
    poss = word in ("His", "Her", "Their")
    repl = f"{topic}'s" if poss else topic
    return _PRON.sub(repl, claim, count=1), True


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Re-type a FActScore block with the original classifier.")
    ap.add_argument("--in", dest="inp", default=IN)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-extract", action="store_true",
                    help="re-classify only; keep the existing property/value")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.inp, newline="", encoding="utf-8")))
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} claims from {os.path.basename(args.inp)}")
    print(f"classifier: original pipeline, {OC.MODEL_NAME}, temp 0 / seed 42")
    print(f"  prompts parsed verbatim from archive/experiments/currentcode.txt\n")

    cache = OC.load_cache()
    n_coref = 0
    for i, r in enumerate(rows, 1):
        claim, did = resolve_coref(r["claim"], r.get("subject", ""))
        n_coref += did
        r["claim_resolved"] = claim
        r["old_type"] = r.get("type", "")
        t = OC.classify_claim(claim, cache)
        if t.startswith("ERROR:"):
            print(f"  !! {t} at row {i} -- is ollama running?")
            OC.save_cache(cache)
            return 1
        r["type"] = t
        if not args.no_extract:
            ex = OC.extract_fields(claim, cache)
            # subject stays from `topic`; property/value come from the pipeline
            if ex.get("property"):
                r["old_property"], r["property"] = r.get("property", ""), ex["property"]
            if ex.get("value"):
                r["old_value"], r["value"] = r.get("value", ""), ex["value"]
        if i % 20 == 0:
            print(f"  {i}/{len(rows)}")
            OC.save_cache(cache)
    OC.save_cache(cache)

    cols = list(rows[0].keys())
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {args.out}")
    print(f"coreference resolved on {n_coref}/{len(rows)} claims")

    print(f"\n{'type':<20}{'few-shot (old)':>16}{'original (new)':>16}")
    old = collections.Counter(r["old_type"] for r in rows)
    new = collections.Counter(r["type"] for r in rows)
    for t in OC.TYPES:
        print(f"{t:<20}{old.get(t,0):>16}{new.get(t,0):>16}")
    changed = [r for r in rows if r["old_type"] != r["type"]]
    print(f"\n{len(changed)}/{len(rows)} claims re-typed "
          f"({len(changed)/len(rows):.0%})")
    c = collections.Counter((r["old_type"], r["type"]) for r in changed)
    for (a, b), n in c.most_common(8):
        print(f"  {n:>3}  {a:<18} -> {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
