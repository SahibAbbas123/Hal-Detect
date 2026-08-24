#!/usr/bin/env python3
"""
Faithful reproduction of the project's ORIGINAL claim classifier and extractor.

WHY THIS EXISTS
---------------
Block D (FActScore out-of-domain) was run with a *reconstruction* of the classifier
that I wrote from the rule document. Measured against Batch 1's human `gold_type` on a
contamination-free question split, that reconstruction scored **83.1%** while the
project's original pipeline scored **93.8%** on the same held-out claims.

So Block D charged the verifiers for roughly 17% extra mis-typing that the real pipeline
would not have produced. Its numbers are a lower bound with an avoidable confound. This
module removes that confound by running the actual original classifier.

NO RETYPING — THE PROMPTS ARE PARSED OUT OF THE ARCHIVED SOURCE
---------------------------------------------------------------
`CLASSIFICATION_PROMPT_TEMPLATE` and `EXTRACTION_PROMPT_TEMPLATE` are read verbatim
from `archive/experiments/currentcode.txt` at import time rather than copied into this
file. Retyping a 30-line prompt is exactly how a "faithful reproduction" silently stops
being faithful, and this project has already lost time to copies drifting apart.

If the archived file is missing or the markers move, this raises rather than falling
back to an approximation.

CONFIGURATION, taken from the same source
-----------------------------------------
    OLLAMA_URL  http://localhost:11434/api/generate
    MODEL       gemma4:31b-cloud
    options     temperature=0, seed=42, num_ctx=8192

`classify_claim()` reproduces the original control flow exactly, including its two
quirks, which are behaviour and not bugs to be improved here:

  1. It asks for **one bare word**, not JSON. That is why the original has no parse
     failures where my JSON-based reconstruction had 2 UNPARSED on 65 claims.
  2. On an unrecognisable reply it **falls back to RELATIONAL** rather than erroring.
     RELATIONAL is ~48% of the corpus, so this fallback is also a majority-class prior.

A TAXONOMY CONTRADICTION WORTH RECORDING
----------------------------------------
The original prompt states:

    "WHO exists" is NOT a CITATION claim. "The WHO reported X" IS.

`reference/taxonomy_rules_extracted.txt` says the opposite. Its Rule 8 (dual-emit)
extracts "The World Health Organization exists. [CITATION]" as a CITATION claim, and
§3.2 lists pure source-existence claims as CITATION — the 140-claim corpus contains
nine of them, all labelled CITATION ("The 2023 IPCC Sixth Assessment Report exists").

So the deployed classifier and the authoritative rule document disagree on how to type
source-existence claims. That is a genuine taxonomy loophole of exactly the kind the
author asked about, and it is discoverable only by comparing the two artefacts. It
matters because dual-emit deliberately manufactures such claims, so the disagreement
applies to a whole class rather than an edge case.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SOURCE = os.path.join(ROOT, "archive", "experiments", "currentcode.txt")
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:31b-cloud"
TYPES = ("CITATION", "TEMPORAL", "QUANTITATIVE", "ENTITY_ATTRIBUTE", "RELATIONAL")
CACHE = os.path.join(HERE, "original_classifier_cache.json")
POLITE = 0.15


def _extract_template(name: str) -> str:
    """Pull a triple-quoted prompt template verbatim out of the archived source."""
    if not os.path.isfile(SOURCE):
        raise SystemExit(f"FATAL: {SOURCE} not found -- cannot reproduce the "
                         f"original classifier without its prompt.")
    text = open(SOURCE, encoding="utf-8", errors="replace").read()
    m = re.search(rf'{name}\s*=\s*"""(.*?)"""', text, re.S)
    if not m:
        raise SystemExit(f"FATAL: {name} not found in {SOURCE}. Do not substitute "
                         f"an approximation -- that is what this module exists to "
                         f"avoid.")
    return m.group(1)


CLASSIFICATION_PROMPT_TEMPLATE = _extract_template("CLASSIFICATION_PROMPT_TEMPLATE")
EXTRACTION_PROMPT_TEMPLATE = _extract_template("EXTRACTION_PROMPT_TEMPLATE")


def load_cache() -> dict:
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE, encoding="utf-8"))
        except (OSError, ValueError):
            return {}
    return {}


def save_cache(cache: dict) -> None:
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cache, fh)
    os.replace(tmp, CACHE)


def call_llm(prompt: str, expect_json: bool = False) -> str:
    """Same payload as the original: temperature 0, seed 42, num_ctx 8192."""
    import requests
    payload = {
        "model": MODEL_NAME, "prompt": prompt, "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_ctx": 8192},
    }
    if expect_json:
        payload["format"] = "json"
    r = requests.post(OLLAMA_URL, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["response"].strip()


def classify_claim(claim: str, cache: dict | None = None) -> str:
    """Original control flow: first matching type keyword, else RELATIONAL."""
    ck = f"origcls__{claim[:160]}"
    if cache is not None and ck in cache:
        return cache[ck]
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(claim=claim)
    try:
        raw = call_llm(prompt).upper().strip()
    except Exception as exc:                        # noqa: BLE001
        return f"ERROR:{exc.__class__.__name__}"    # never cached
    out = "RELATIONAL"
    for cat in TYPES:
        if cat in raw:
            out = cat
            break
    if cache is not None:
        cache[ck] = out
        time.sleep(POLITE)
    return out


def extract_fields(claim: str, cache: dict | None = None) -> dict:
    """Original structured extraction. Returns {subject, property, value}."""
    ck = f"origext__{claim[:160]}"
    if cache is not None and ck in cache:
        return cache[ck]
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(claim=claim)
    try:
        raw = call_llm(prompt, expect_json=True)
        obj = json.loads(raw)
        out = {"subject": (obj.get("subject") or "").strip(),
               "property": (obj.get("property") or "").strip(),
               "value": (obj.get("value") or "").strip()}
    except Exception:                               # noqa: BLE001
        return {"subject": "", "property": "", "value": ""}
    if cache is not None:
        cache[ck] = out
        time.sleep(POLITE)
    return out


# ---------------------------------------------------------------------------
# Validation: does this reproduction match the recorded 93.8%?
# ---------------------------------------------------------------------------

B1 = os.path.join(ROOT, "archive", "csvs",
                  "haldetect_claims_20260524_045439_2.csv")
TEST_Q = ["Q10", "Q11", "Q12", "Q13", "Q14"]


def validate(limit: int | None) -> int:
    """Re-classify the same held-out claims and compare to the recorded output.

    This is the load-bearing check. If the reproduction is faithful it should land
    near 93.8% against human `gold_type` AND agree closely with the `type` column
    the original pipeline actually produced. Divergence means something in the
    environment differs (model version, ollama build) and the reproduction should
    not be trusted for Block D.
    """
    import metrics as M
    rows = [r for r in csv.DictReader(open(B1, newline="", encoding="utf-8"))
            if (r.get("q_id") or "").strip() in TEST_Q
            and (r.get("gold_type") or "").strip().upper() in TYPES
            and (r.get("claim") or "").strip()]
    if limit:
        rows = rows[:limit]
    print(f"validating on {len(rows)} held-out Batch 1 claims "
          f"({'/'.join(TEST_Q)})")
    print(f"  model {MODEL_NAME}, temperature 0, seed 42\n")

    cache = load_cache()
    gold, mine, orig = [], [], []
    for i, r in enumerate(rows, 1):
        p = classify_claim(r["claim"], cache)
        if p.startswith("ERROR:"):
            print(f"  !! {p} -- is ollama running?")
            return 1
        gold.append(r["gold_type"].strip().upper())
        mine.append(p)
        orig.append((r.get("type") or "").strip().upper())
        if i % 10 == 0:
            print(f"  {i}/{len(rows)}")
    save_cache(cache)

    def acc(pred, label):
        ok = sum(1 for g, p in zip(gold, pred) if g == p)
        _, lo, hi = M.wilson(ok, len(gold))
        print(f"  {label:<44}{ok}/{len(gold)} = {ok/len(gold):>6.1%}  "
              f"[{lo:.1%}, {hi:.1%}]")
        return ok

    print()
    acc(mine, "this reproduction vs human gold_type")
    acc(orig, "recorded original output vs human gold_type")
    same = sum(1 for a, b in zip(mine, orig) if a == b)
    print(f"  {'reproduction agrees with recorded output':<44}"
          f"{same}/{len(gold)} = {same/len(gold):>6.1%}")
    if same / len(gold) < 0.85:
        print("\n  !! LOW AGREEMENT with the recorded output. The reproduction is")
        print("     NOT faithful enough to re-run Block D with. Likely causes: a")
        print("     different gemma build, or ollama options differing from")
        print("     temperature=0/seed=42/num_ctx=8192.")
    else:
        print("\n  Agreement is high enough to treat this as the original")
        print("  classifier for Block D purposes.")
    dis = collections.Counter((p, g) for g, p in zip(gold, mine) if g != p)
    if dis:
        print("\n  this reproduction's errors (predicted -> human gold):")
        for (p, g), n in dis.most_common():
            print(f"    {n:>3}  said {p:<18} human said {g}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reproduce the original classifier; validate before reuse.")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--show-prompt", action="store_true")
    args = ap.parse_args()

    if args.show_prompt:
        print("CLASSIFICATION_PROMPT_TEMPLATE (verbatim from the archive):")
        print("=" * 70)
        print(CLASSIFICATION_PROMPT_TEMPLATE)
        return 0
    if args.validate:
        return validate(args.limit)
    print(f"prompts loaded verbatim from {os.path.relpath(SOURCE, ROOT)}")
    print(f"  classification: {len(CLASSIFICATION_PROMPT_TEMPLATE)} chars")
    print(f"  extraction    : {len(EXTRACTION_PROMPT_TEMPLATE)} chars")
    print(f"  model         : {MODEL_NAME} (temperature 0, seed 42)")
    print("\nrun --validate before using this for any measurement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
