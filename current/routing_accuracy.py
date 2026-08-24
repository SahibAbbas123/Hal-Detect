#!/usr/bin/env python3
"""
Routing accuracy (RQ1) on Batch 1, measured with a contamination-free split.

WHY THIS IS THE ONLY PLACE RQ1 CAN BE MEASURED
----------------------------------------------
Routing accuracy needs claims whose type a human assigned independently of the
classifier. That exists for exactly one claim set:

    Batch 1   125 claims   gold_type independently labelled   <- the only one
    Phase 2   109 claims   gold_type SEEDED from classifier output
    Batch 3   122 claims   gold_type SEEDED from classifier output
    FActScore   any        no claim types at all
    FEVER       any        no claim types at all

Scoring against Phase 2 or Batch 3 returns ~100% by construction, because their
`gold_type` *is* the classifier's own output. FActScore and FEVER simply have no type
labels — so an earlier claim in this project's worklog that "FEVER is the only way to
measure routing at scale" was wrong, and is corrected here.

THE CONTAMINATION PROBLEM, AND THE SPLIT THAT SOLVES IT
-------------------------------------------------------
Few-shot classification needs demonstration examples. The obvious source — the
140-claim corpus — is drawn from **Batch 1's own questions** (Einstein, FinCrisis,
IPCC, SilkRoad, QC, WWI). Using it to classify Batch 1 would be training and testing on
the same claims.

Using the rule document's worked examples instead does not fully fix it either: the doc
uses "Albert Einstein was born on 14 March 1879" as its TEMPORAL example, which is
essentially a Batch 1 claim.

So the split is **by question**, not by claim:

    exemplars from   Q1, Q2, Q5, Q7, Q9      (60 claims available)
    tested on        Q10, Q11, Q12, Q13, Q14 (65 claims)

No claim, and no *topic*, appears in both roles. Splitting by claim would still leak,
because two claims from the same question share subject matter and phrasing.

Exemplars use Batch 1's **human** `gold_type`, which is better provenance than the
140-corpus labels (those were AI-assigned during a formatting pass and never reviewed
claim-by-claim, per the "Sorting the 140 claims" handoff).

WHAT THE NUMBER MEANS, AND WHAT IT DOES NOT
-------------------------------------------
It measures: can an LLM few-shot classifier reproduce a human's taxonomy assignment on
unseen questions, using the project's own rule set.

It does NOT measure: whether the taxonomy itself is well-defined. A claim both humans
and the classifier find ambiguous will be counted as a classifier error even when the
real fault is an underspecified rule. Instability across prompts is the better probe
for that, and it is reported separately.

Reference point: the project's ORIGINAL classifier scores **111/125 = 88.8%** on the
full 125, with **12 of its 14 errors over-predicting TEMPORAL** (8 -> RELATIONAL,
3 -> QUANTITATIVE, 1 -> ENTITY_ATTRIBUTE) because it routes on the presence of a date
rather than on whether the date is the contested element. Any number here should be
read against that, not against zero.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

B1 = os.path.join(ROOT, "archive", "csvs",
                  "haldetect_claims_20260524_045439_2.csv")
OUT = os.path.join(HERE, "routing_batch1_results.csv")
CACHE = os.path.join(HERE, "routing_extract_cache.json")

TRAIN_Q = ["Q1", "Q2", "Q5", "Q7", "Q9"]
TEST_Q = ["Q10", "Q11", "Q12", "Q13", "Q14"]
TYPES = ("CITATION", "TEMPORAL", "QUANTITATIVE", "ENTITY_ATTRIBUTE", "RELATIONAL")
PER_TYPE = 3
PROMPT_VERSION = "routing-v1-b1split"


def load() -> list[dict]:
    rows = []
    for r in csv.DictReader(open(B1, newline="", encoding="utf-8")):
        g = (r.get("gold_type") or "").strip().upper()
        c = (r.get("claim") or "").strip()
        if g in TYPES and c:
            rows.append({"claim_id": r.get("claim_id", ""),
                         "q_id": (r.get("q_id") or "").strip(),
                         "claim": c, "gold_type": g,
                         "orig_type": (r.get("type") or "").strip().upper()})
    return rows


def pick_exemplars(train: list[dict], per_type: int) -> list[dict]:
    """Balanced by type, not proportional.

    Batch 1 is ~48% RELATIONAL. A proportional sample would teach the classifier
    "when unsure, say RELATIONAL", which is the opposite of what a router needs.
    """
    by_t: dict[str, list[dict]] = collections.defaultdict(list)
    for r in train:
        by_t[r["gold_type"]].append(r)
    out = []
    for t in TYPES:
        out.extend(by_t.get(t, [])[:per_type])
    return sorted(out, key=lambda r: TYPES.index(r["gold_type"]))


HEADER = """You classify atomic factual claims into a five-type taxonomy for a hallucination-detection system.

The governing principle is THE MOST CONTESTABLE ELEMENT: whichever fact in the claim is most specific and most checkable decides the type. Priority order only breaks a genuine tie.

1. CITATION — names a specific, independently lookable source (named organisation, named report, journal, author + year). Always wins when it qualifies. Vague attributions ("scientists say", "studies show", "research suggests") do NOT qualify -- use the type of the embedded fact instead.
2. TEMPORAL — a date, year, duration or time-ordered event is the primary verifiable element. A date present only as CONTEXT does not make a claim TEMPORAL.
3. QUANTITATIVE — a number, measurement, percentage or statistic is primary. QUANTITATIVE BEATS TEMPORAL when the number is more specific or contested than the date.
4. ENTITY_ATTRIBUTE — assigns a property, role, nationality, descriptor or structure. Dominant verb is IS / WAS / HAS, no process or causal chain.
5. RELATIONAL — asserts what something DOES, CAUSES, LEADS TO, ENABLES or WORKS BY. RELATIONAL BEATS ENTITY_ATTRIBUTE when the dominant verb is an action, process or mechanism.

THE EA vs RELATIONAL TEST — which question does the claim answer?
   "What IS X?" / "What does X HAVE?"                          -> ENTITY_ATTRIBUTE
   "What does X DO?" / "How does X WORK?" / "What did X CAUSE?" -> RELATIONAL

Modal qualifiers do not disqualify a claim: "could prevent 45% of cases" is still QUANTITATIVE.

EXAMPLES (human-annotated):
"""

FOOTER = """
Classify this claim. Return ONLY a JSON object: {{"type": "..."}}

Claim: {claim}"""


def build_prompt(exemplars: list[dict]) -> str:
    body = "\n".join(f'  Claim: {e["claim"]}\n  -> {e["gold_type"]}'
                     for e in exemplars)
    return HEADER + body + FOOTER


def classify(claim: str, template: str, cache: dict) -> str:
    import urllib.error
    import urllib.request
    import time
    import gemini_key

    ck = f"rt__{PROMPT_VERSION}__{claim[:120]}"
    if ck in cache:
        return cache[ck]
    key = gemini_key.get()
    if not key:
        return ""
    body = json.dumps({
        "contents": [{"parts": [{"text": template.format(claim=claim)}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 40,
                             "responseMimeType": "application/json"},
    }).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                gemini_key.endpoint(key=key), data=body, method="POST",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode())
            txt = "".join(p.get("text", "")
                          for c in payload.get("candidates", [])
                          for p in c.get("content", {}).get("parts", []))
            t = (json.loads(txt).get("type") or "").upper().strip()
            if t in TYPES:
                cache[ck] = t          # only cache a valid answer
                time.sleep(1.2)
                return t
            return ""
        except Exception:              # noqa: BLE001
            time.sleep(1.2 * (2 ** attempt))
    return ""


def report(rows: list[dict], pred_key: str, title: str) -> None:
    gold = [r["gold_type"] for r in rows]
    pred = [r[pred_key] for r in rows]
    ok = sum(1 for g, p in zip(gold, pred) if g == p)
    import metrics as M
    _, lo, hi = M.wilson(ok, len(rows))
    print(f"\n{title}")
    print(f"  accuracy {ok}/{len(rows)} = {ok/len(rows):.1%}  [{lo:.1%}, {hi:.1%}]")
    print(f"  {'type':<18}{'P':>6}{'R':>6}{'F1':>6}{'gold':>6}{'pred':>6}")
    for t in TYPES:
        tp = sum(1 for g, p in zip(gold, pred) if g == t and p == t)
        fp = sum(1 for g, p in zip(gold, pred) if g != t and p == t)
        fn = sum(1 for g, p in zip(gold, pred) if g == t and p != t)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        if tp + fn or tp + fp:
            print(f"  {t:<18}{pr:>6.2f}{rc:>6.2f}{f1:>6.2f}{tp+fn:>6}{tp+fp:>6}")
    dis = collections.Counter((p, g) for g, p in zip(gold, pred) if g != p)
    if dis:
        print("  disagreements (predicted -> human gold):")
        for (p, g), n in dis.most_common():
            print(f"    {n:>3}  said {p:<18} human said {g}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="RQ1 routing accuracy on Batch 1, question-split.")
    ap.add_argument("--per-type", type=int, default=PER_TYPE)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    rows = load()
    train = [r for r in rows if r["q_id"] in TRAIN_Q]
    test = [r for r in rows if r["q_id"] in TEST_Q]
    print(f"Batch 1: {len(rows)} claims with human gold_type")
    print(f"  exemplar pool ({'/'.join(TRAIN_Q)}): {len(train)}")
    print(f"  held-out test ({'/'.join(TEST_Q)}): {len(test)}")
    assert not ({r["claim_id"] for r in train} & {r["claim_id"] for r in test})

    ex = pick_exemplars(train, args.per_type)
    print(f"\n{len(ex)} exemplars (balanced by type, from the training questions only):")
    for e in ex:
        print(f"  [{e['gold_type'][:12]:<13}] {e['q_id']:<4}{e['claim'][:60]}")
    tmpl = build_prompt(ex)

    if args.limit:
        test = test[:args.limit]
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}
    print(f"\nclassifying {len(test)} held-out claims...")
    for i, r in enumerate(test, 1):
        r["pred_type"] = classify(r["claim"], tmpl, cache) or "UNPARSED"
        if i % 10 == 0:
            print(f"  {i}/{len(test)}")
    tmp = CACHE + ".tmp"
    json.dump(cache, open(tmp, "w"))
    os.replace(tmp, CACHE)

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["claim_id", "q_id", "claim",
                                           "gold_type", "orig_type", "pred_type"])
        w.writeheader()
        w.writerows(test)
    print(f"wrote {OUT}")

    report(test, "pred_type",
           "=== FEW-SHOT CLASSIFIER (this run) vs human gold_type, HELD-OUT ===")
    report(test, "orig_type",
           "=== ORIGINAL PIPELINE CLASSIFIER vs human gold_type, same claims ===")
    print("\nBoth blocks score the SAME held-out claims, so they are directly")
    print("comparable. The original classifier's number here is its performance on")
    print("this subset, not the 88.8% it scores on all 125.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
