#!/usr/bin/env python3
"""
Router ablation: does the taxonomy's own tie-break rule fix TEMPORAL over-firing?

THE DEFECT
----------
The deployed classifier's TEMPORAL precision is **0.57 at recall 1.00** on held-out
Batch 1 claims — it catches every temporal claim and over-predicts by 75%. Reproduced
three independent times (full 125, the held-out 65, and the reproduction's own errors).

THE SUSPECTED CAUSE — A ONE-LINE OMISSION
-----------------------------------------
The deployed prompt says:

    PRIORITY ORDER (apply top-down, stop at first match)

But `reference/taxonomy_rules_extracted.txt` §4 says the priority list is **overridden**
by which element is most contested:

    QUANTITATIVE vs TEMPORAL | QUANTITATIVE wins when number is more specific than date
                             | "Emissions must fall 43% by 2030" -> QUANTITATIVE
    EA vs RELATIONAL         | RELATIONAL wins when the verb describes action/process
                             | "DNA replicates by separating strands" -> RELATIONAL

Under strict stop-at-first, TEMPORAL (rank 2) beats QUANTITATIVE (rank 3) whenever a date
is present anywhere. That is exactly the observed failure: the deployed classifier's
errors on the held-out set were 2x TEMPORAL->QUANTITATIVE and 1x TEMPORAL->EA.

So the rule document already contains the fix; the prompt never received it.

WHY THREE VARIANTS
------------------
    V0  the deployed prompt, verbatim                      (baseline)
    V1  V0 + the QUANTITATIVE-beats-TEMPORAL override only  (targets the defect)
    V2  V1 + the RELATIONAL-beats-EA override               (the full §4 tie-break)

V1 isolates the single rule aimed at the known defect. V2 adds the second override. If
V1 fixes TEMPORAL and V2 adds nothing, the credit belongs to one specific rule rather
than to "more prompt text" — which is the difference between an ablation and a tweak.

Everything else is held constant: same model, temperature 0, seed 42, same examples,
same held-out claims, same fallback behaviour. Only the inserted text varies.

THE DEPLOYED PROMPT IS TREATED AS FROZEN
----------------------------------------
This measures a *proposed* improvement. It does not change the pipeline. Adopting V1 or
V2 would alter the system under test and invalidate the type column every downstream
number was computed from, so that decision belongs to the author, not to this script.
"""

from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M                # noqa: E402
import original_classifier as OC   # noqa: E402

B1 = os.path.join(ROOT, "archive", "csvs",
                  "haldetect_claims_20260524_045439_2.csv")
TEST_Q = ["Q10", "Q11", "Q12", "Q13", "Q14"]
OUT = os.path.join(HERE, "router_ablation_results.csv")

# Inserted verbatim from the rule document's §4 tie-break table.
QUANT_OVERRIDE = """
TIE-BREAKING OVERRIDE (taxonomy rules, Section 4):
The priority order above is the DEFAULT, not absolute. The governing principle is the
MOST CONTESTABLE ELEMENT — whichever fact is most specific and most checkable decides.
- QUANTITATIVE BEATS TEMPORAL when the number is more specific or more contested than
  the date. A date present only as context does not win.
    "Air pollution caused 4.2 million deaths in 2019." -> QUANTITATIVE (4.2 million
      dominates; 2019 is context)
    "Emissions must fall 43% by 2030." -> QUANTITATIVE (43% dominates; 2030 is context)
    "Albert Einstein was born on 14 March 1879." -> TEMPORAL (no competing number)
"""

REL_OVERRIDE = """- RELATIONAL BEATS ENTITY_ATTRIBUTE when the dominant verb describes an action, process
  or mechanism rather than a static property.
    "DNA replicates by separating its strands." -> RELATIONAL (mechanism)
    "DNA has a double-helix structure."         -> ENTITY_ATTRIBUTE (property)
"""

MARKER = "\nExamples from annotated corpus:"


def build(variant: str) -> str:
    base = OC.CLASSIFICATION_PROMPT_TEMPLATE
    if variant == "V0":
        return base
    if MARKER not in base:
        raise SystemExit("FATAL: examples marker not found; refusing to guess where "
                         "to insert the override.")
    ins = QUANT_OVERRIDE if variant == "V1" else QUANT_OVERRIDE + REL_OVERRIDE
    return base.replace(MARKER, "\n" + ins + MARKER, 1)


def classify(claim: str, template: str, variant: str, cache: dict) -> str:
    ck = f"abl__{variant}__{claim[:150]}"
    if ck in cache:
        return cache[ck]
    import time
    # Retry with backoff. gemma4:31b-cloud is CLOUD-hosted and throttles: a prior
    # run died on HTTPError at ~130 calls and another on ReadTimeout at ~30. A
    # single transient failure must not end a 125-claim run, and because the cache
    # is checkpointed every 10 calls a resume costs almost nothing.
    last = None
    for attempt in range(5):
        try:
            raw = OC.call_llm(template.format(claim=claim)).upper().strip()
            out = "RELATIONAL"                  # same fallback as the original
            for cat in OC.TYPES:
                if cat in raw:
                    out = cat
                    break
            cache[ck] = out                     # only successes are cached
            time.sleep(OC.POLITE)
            return out
        except Exception as exc:                # noqa: BLE001
            last = exc
            time.sleep(2.0 * (2 ** attempt))    # 2, 4, 8, 16, 32s
    return f"ERROR:{last.__class__.__name__}"


def report(gold: list[str], pred: list[str], label: str) -> dict:
    ok = sum(1 for g, p in zip(gold, pred) if g == p)
    _, lo, hi = M.wilson(ok, len(gold))
    print(f"\n{label}")
    print(f"  accuracy {ok}/{len(gold)} = {ok/len(gold):.1%}  [{lo:.1%}, {hi:.1%}]")
    print(f"  {'type':<18}{'P':>6}{'R':>6}{'F1':>6}{'gold':>6}{'pred':>6}")
    out = {}
    for t in OC.TYPES:
        tp = sum(1 for g, p in zip(gold, pred) if g == t and p == t)
        fp = sum(1 for g, p in zip(gold, pred) if g != t and p == t)
        fn = sum(1 for g, p in zip(gold, pred) if g == t and p != t)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        out[t] = (pr, rc, f1)
        if tp + fn or tp + fp:
            print(f"  {t:<18}{pr:>6.2f}{rc:>6.2f}{f1:>6.2f}{tp+fn:>6}{tp+fp:>6}")
    errs = collections.Counter((p, g) for g, p in zip(gold, pred) if g != p)
    if errs:
        print("  errors (predicted -> human gold):")
        for (p, g), n in errs.most_common():
            print(f"    {n:>3}  said {p:<18} human said {g}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Router tie-break ablation.")
    ap.add_argument("--variants", default="V0,V1,V2")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--all", action="store_true",
                    help="use ALL 125 Batch 1 claims, not just the held-out 65. "
                         "Legitimate for the DEPLOYED classifier: its 10 few-shot "
                         "examples are part of the system under test, not something "
                         "chosen here, and the 88.8%/55.6% figures on record were "
                         "derived this way. Gives 27 TEMPORAL predictions instead "
                         "of 6.")
    ap.add_argument("--delay", type=float, default=None,
                    help="seconds between calls; raise it if the cloud model "
                         "rate-limits (an HTTPError killed a prior V2 run at ~130 "
                         "calls)")
    args = ap.parse_args()

    if args.delay is not None:
        OC.POLITE = args.delay
    rows = [r for r in csv.DictReader(open(B1, newline="", encoding="utf-8"))
            if (args.all or (r.get("q_id") or "").strip() in TEST_Q)
            and (r.get("gold_type") or "").strip().upper() in OC.TYPES
            and (r.get("claim") or "").strip()]
    if args.limit:
        rows = rows[:args.limit]
    gold = [r["gold_type"].strip().upper() for r in rows]
    scope = "ALL Batch 1" if args.all else f"held-out ({'/'.join(TEST_Q)})"
    print(f"{len(rows)} claims — {scope}")
    if args.all:
        print("  NOTE: not a held-out split. Valid for comparing the DEPLOYED")
        print("  classifier against a prompt variant, since its examples are part")
        print("  of the system; NOT valid for claiming generalisation.")
    print(f"gold mix: {dict(collections.Counter(gold))}")
    print(f"model {OC.MODEL_NAME}, temperature 0, seed 42 — only the prompt varies\n")

    cache = OC.load_cache()
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    preds, summaries = {}, {}
    for v in variants:
        tmpl = build(v)
        print(f"-- {v}: prompt {len(tmpl)} chars --")
        p = []
        for i, r in enumerate(rows, 1):
            got = classify(r["claim"], tmpl, v, cache)
            if got.startswith("ERROR:"):
                print(f"  !! {got} — is ollama running?")
                OC.save_cache(cache)
                return 1
            p.append(got)
            if i % 10 == 0:
                OC.save_cache(cache)
                print(f"    {i}/{len(rows)}", flush=True)
        preds[v] = p
        OC.save_cache(cache)

    names = {"V0": "V0 — deployed prompt (baseline)",
             "V1": "V1 — + QUANTITATIVE beats TEMPORAL",
             "V2": "V2 — + RELATIONAL beats ENTITY_ATTRIBUTE"}
    for v in variants:
        summaries[v] = report(gold, preds[v], names.get(v, v))

    print(f"\n{'=' * 66}")
    print("  THE TARGETED NUMBER: TEMPORAL precision")
    print(f"{'=' * 66}")
    for v in variants:
        pr, rc, f1 = summaries[v]["TEMPORAL"]
        acc = sum(1 for g, p in zip(gold, preds[v]) if g == p) / len(gold)
        print(f"  {v}  TEMPORAL P={pr:.2f} R={rc:.2f} F1={f1:.2f}   "
              f"overall accuracy {acc:.1%}")
    changed = sum(1 for a, b in zip(preds[variants[0]], preds[variants[-1]]) if a != b)
    print(f"\n  {variants[0]} vs {variants[-1]}: {changed}/{len(rows)} claims re-typed")

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        cols = ["claim_id", "q_id", "claim", "gold_type"] + variants
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(rows):
            w.writerow({**{k: r.get(k, "") for k in
                           ("claim_id", "q_id", "claim", "gold_type")},
                        **{v: preds[v][i] for v in variants}})
    print(f"\nwrote {OUT}")
    print("\nThe deployed prompt is unchanged. This measures a PROPOSED fix; adopting")
    print("it would alter the type column every downstream number rests on.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
