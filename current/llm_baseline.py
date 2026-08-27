#!/usr/bin/env python3
"""
LLM baseline for HalDetect -- step (c). Runs a local/cloud LLM over our own gold
claims via ollama, and scores it with the SAME metrics as our verifiers.

WHY THIS EXISTS
---------------
`reference/paper_findings_2026-08-22.md` section 7: chasing "beat 0.63" is invalid,
because 0.63 is Factcheck-GPT's false-claim F1 **on Factcheck-Bench's data**.
Cross-dataset F1 comparison gets rejected on sight. There are exactly two valid
routes, and this file is the cheaper one: **run an LLM baseline on OUR claims.**

It is also the direct test of the project's central research bet -- that
structured, evidence-grounded verification beats open-ended LLM self-checking.
Without this baseline that bet is asserted, not measured.

THE EXPERIMENT THAT MATTERS
---------------------------
Our pooled real gold set is 313 TRUE / 14 FALSE / 29 UNVERIFIABLE, so an
unconditional "TRUE" scores **87.9%**. That makes a naive baseline number
worthless. So this harness runs the LLM two ways and the *contrast* is the result:

* `--mode closed`            no evidence, may abstain -> the honest "just ask an LLM" baseline
* `--mode closed --force-binary`   no evidence, abstention FORBIDDEN

The prediction is that forcing a binary answer collapses the model toward the
majority class, scoring high accuracy with **F1(FALSE) near zero** -- i.e. exactly
the Always-True degenerate pattern Factcheck-Bench Table 5 documents. If that
happens, it is evidence that accuracy is the wrong axis and that an abstention
option is not a handicap but a requirement. `metrics.py` prints the degenerate
baselines alongside, so the comparison is unavoidable.

THE WORKED IN-CORPUS EXAMPLE -- quote this in the RQ2 discussion
---------------------------------------------------------------
`Q22_C01`: *"The FAO reported in 2023 that global food insecurity increased during
2022."* Gold FALSE (SOFI 2023 `cc3017en` p. 10 says the prevalence "remained
unchanged for the second year in a row"; the +391M is vs 2019, not across 2022).

This harness returned **TRUE**, and its stated reason asserts the SOFI 2023 report
**"confirmed"** the increase -- i.e. asked to check a misattribution, the LLM
reproduced the misattribution with confidence. That is the exact failure mode the
whole project is built around, occurring inside our own corpus rather than in a
cited example. Three of four systems said TRUE here; only CITATION L1b abstained,
and it abstained for a *stated structural reason* (`'FAO'` is an organisation, not
a cited work). Note the honest framing: **that is abstention, not detection** --
L1b earns no true positive, it earns zero confident errors.
`reference/sofi_abstention_entity_linking_assessed_2026-08-26.md` sections 1 and 5.

Modes:
  closed    claim only. Tests parametric knowledge -- what our system is bet against.
  evidence  claim + evidence text supplied in a CSV column. Isolates reasoning from retrieval.
  wiki      claim + Wikipedia lead passages this script retrieves. The nearest
            like-for-like against RELATIONAL, which is Wikipedia-passage-based.

FAIRNESS NOTES (do not remove -- a reviewer will ask)
-----------------------------------------------------
1.  The LLM is given the SAME three-way verdict vocabulary as our verifiers, with
    UNVERIFIABLE defined the same way. Denying it abstention while our system has
    it would be a rigged comparison; that is why forced-binary is a separate,
    explicitly-labelled run rather than the default.
2.  temperature = 0 and recorded in the output. This project has already been
    bitten once by a temperature reproducibility bug (see current/README.md, the
    relational "post temperature-fix" rerun).
3.  Failed calls are NEVER cached. Cache poisoning has been fixed twice in this
    project already (RELATIONAL retrieval, then property_resolver search).
4.  Self-reported confidence is not calibrated. It is used only to order the
    risk-coverage curve, never quoted as a probability.

USAGE
-----
    python current/llm_baseline.py --check
    python current/llm_baseline.py --selftest
    python current/llm_baseline.py --mode closed --limit 20
    python current/llm_baseline.py --mode closed
    python current/llm_baseline.py --mode closed --force-binary
    python current/llm_baseline.py --mode wiki

Nothing existing is modified. Creates: llm_baseline_cache.json,
llm_baseline_results_<mode>.csv
Reverse with: rm current/llm_baseline_cache.json current/llm_baseline_results_*.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time

import requests

import metrics

HERE = os.path.dirname(os.path.abspath(__file__))

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = "gemma4:31b-cloud"
CACHE_PATH = os.path.join(HERE, "llm_baseline_cache.json")

# Prefer the unified set if consolidate_claims.py has been run; else Batch 3.
UNIFIED = os.path.join(HERE, "haldetect_claims_unified.csv")
FALLBACK = os.path.join(HERE, "haldetect_claims_b3_gold.csv")

VERDICTS = ("TRUE", "FALSE", "UNVERIFIABLE")
TIMEOUT = 180
POLITE_DELAY = 0.2
WIKI_API = "https://en.wikipedia.org/w/api.php"
UA = "HalDetect-thesis-baseline/1.0 (CSE700 research; contact via repo)"

# Definitions copied to match our own gold-labeling guidance, so the baseline is
# scored against the same target concept our verifiers are.
SYSTEM = """You are a careful fact-checking assistant. You judge one atomic claim at a time.

Reply with EXACTLY one JSON object and nothing else:
{"verdict": "TRUE" | "FALSE" | "UNVERIFIABLE", "confidence": <0.0-1.0>, "reason": "<one sentence>"}

Verdict definitions:
- TRUE: the claim is factually accurate.
- FALSE: the claim is factually inaccurate, in whole or in a material part.
- UNVERIFIABLE: the claim cannot be established either way -- no authoritative
  source settles it, it is a prediction or opinion, or it is too vague to check.

Rules:
- Judge ONLY the claim as written. Do not judge a charitable rephrasing of it.
- A claim with a correct main fact but a wrong number, date, or direction is FALSE.
- confidence is your own certainty in your verdict, not the claim's plausibility."""

BINARY_SUFFIX = """

OVERRIDE: UNVERIFIABLE is NOT permitted in this run. You must answer TRUE or FALSE
even when uncertain. Use confidence to express your uncertainty."""


# ---------------------------------------------------------------------------
# cache
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  warn: cache unreadable ({exc}); starting empty")
    return {}


def save_cache(cache: dict) -> None:
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=1, sort_keys=True)
    os.replace(tmp, CACHE_PATH)


def cache_key(model: str, mode: str, binary: bool, claim_id: str, prompt: str) -> str:
    h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    return f"{model}|{mode}|{'bin' if binary else '3way'}|{claim_id}|{h}"


# ---------------------------------------------------------------------------
# ollama
# ---------------------------------------------------------------------------

def ollama_check(model: str) -> bool:
    try:
        r = requests.get(f"{OLLAMA}/api/tags", timeout=15)
        r.raise_for_status()
    except requests.RequestException as exc:
        print(f"FAIL: cannot reach ollama at {OLLAMA} -- {exc}")
        print("      Start it with:  ollama serve")
        return False
    names = [m.get("name", "") for m in (r.json().get("models") or [])]
    print(f"ollama OK at {OLLAMA}")
    print(f"  models installed: {', '.join(names) if names else '(none)'}")
    if model in names:
        print(f"  requested model '{model}' is present")
        return True
    loose = [n for n in names if n.split(":")[0] == model.split(":")[0]]
    print(f"  NOTE: '{model}' not in the list.")
    if loose:
        print(f"        similar: {', '.join(loose)}")
    if model.endswith("-cloud"):
        print("        '-cloud' models are served through Ollama's cloud and may not")
        print("        appear in /api/tags. If calls fail, run:  ollama signin")
    return True  # let the call attempt decide


def ask(model: str, prompt: str, binary: bool) -> tuple[dict | None, str]:
    """One chat call. Returns (parsed_or_None, raw_or_error). Never caches here."""
    system = SYSTEM + (BINARY_SUFFIX if binary else "")
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "seed": 7, "num_predict": 400},
    }
    try:
        r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        raw = (r.json().get("message") or {}).get("content", "")
    except requests.RequestException as exc:
        return None, f"HTTP_ERROR: {exc}"
    except (ValueError, KeyError) as exc:
        return None, f"BAD_RESPONSE: {exc}"
    return parse(raw), raw


def parse(raw: str) -> dict | None:
    """Extract the verdict object. Tolerant of prose wrapping and code fences,
    because `format=json` is a request, not a guarantee."""
    if not raw:
        return None
    txt = raw.strip()
    txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.MULTILINE).strip()
    obj = None
    try:
        obj = json.loads(txt)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", txt, flags=re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                obj = None
    if not isinstance(obj, dict):
        # last resort: a bare verdict word
        m = re.search(r"\b(TRUE|FALSE|UNVERIFIABLE)\b", txt.upper())
        if not m:
            return None
        return {"verdict": m.group(1), "confidence": 0.5,
                "reason": "recovered from unstructured reply"}

    v = str(obj.get("verdict", "")).strip().upper()
    v = {"SUPPORTED": "TRUE", "REFUTED": "FALSE",
         "NOT ENOUGH INFO": "UNVERIFIABLE", "NEI": "UNVERIFIABLE"}.get(v, v)
    if v not in VERDICTS:
        return None
    try:
        conf = float(obj.get("confidence", 0.5))
    except (TypeError, ValueError):
        conf = 0.5
    return {"verdict": v, "confidence": min(1.0, max(0.0, conf)),
            "reason": str(obj.get("reason", ""))[:400]}


# ---------------------------------------------------------------------------
# evidence
# ---------------------------------------------------------------------------

def wiki_evidence(subject: str, claim: str, cache: dict) -> str:
    """Lead extracts for the best-matching Wikipedia page. Deliberately simple:
    this is a BASELINE's retrieval, and making it stronger than RELATIONAL's own
    retrieval would confound the comparison."""
    query = (subject or claim)[:250]
    key = f"wiki__{query}"
    if key in cache:
        return cache[key]
    try:
        r = requests.get(WIKI_API, headers={"User-Agent": UA}, timeout=30, params={
            "action": "query", "format": "json", "prop": "extracts",
            "exintro": 1, "explaintext": 1, "redirects": 1,
            "generator": "search", "gsrsearch": query, "gsrlimit": 2,
        })
        r.raise_for_status()
        pages = ((r.json().get("query") or {}).get("pages") or {})
    except (requests.RequestException, ValueError):
        return ""  # NOT cached -- failures must never poison the cache
    parts = []
    for p in pages.values():
        title, extract = p.get("title", ""), (p.get("extract") or "").strip()
        if extract:
            parts.append(f"[{title}] {extract[:1200]}")
    text = "\n\n".join(parts)
    if text:
        cache[key] = text
    time.sleep(POLITE_DELAY)
    return text


def build_prompt(row: dict, mode: str, cache: dict) -> str:
    claim = row.get("claim", "")
    if mode == "closed":
        return f"Claim: {claim}\n\nJudge this claim."
    if mode == "evidence":
        ev = (row.get("evidence") or row.get("notes") or "").strip()
        return (f"Claim: {claim}\n\nEvidence:\n{ev or '(none supplied)'}\n\n"
                f"Judge the claim using the evidence. If the evidence does not "
                f"settle it, answer UNVERIFIABLE.")
    if mode == "wiki":
        ev = wiki_evidence(row.get("subject", ""), claim, cache)
        return (f"Claim: {claim}\n\nWikipedia evidence:\n{ev or '(retrieval returned nothing)'}\n\n"
                f"Judge the claim using the evidence. If the evidence does not "
                f"settle it, answer UNVERIFIABLE.")
    raise ValueError(f"unknown mode {mode}")


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

def load_claims(path: str, limit: int, include_synthetic: bool) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    keep = []
    for r in rows:
        if (r.get("gold_verdict") or "").strip() not in VERDICTS:
            continue
        if not include_synthetic and (r.get("synthetic") or "").lower() == "true":
            continue
        keep.append(r)
    return keep[:limit] if limit else keep


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    path = args.claims or (UNIFIED if os.path.exists(UNIFIED) else FALLBACK)
    if not os.path.exists(path):
        print(f"FAIL: no claims file at {path}")
        return 2
    rows = load_claims(path, args.limit, args.include_synthetic)
    if not rows:
        print(f"FAIL: no labeled rows in {path}")
        return 2
    print(f"claims: {path}  ({len(rows)} labeled rows"
          f"{'' if args.include_synthetic else ', synthetic excluded'})")
    print(f"model : {args.model}   mode: {args.mode}"
          f"{'   FORCED BINARY' if args.force_binary else ''}   temperature: 0.0")
    if path == FALLBACK:
        print("  note: using Batch 3 only. Run consolidate_claims.py --write first")
        print("        to evaluate on all 356 real claims (much tighter CIs).")

    cache = load_cache()
    out: list[dict] = []
    fresh = failed = 0

    for i, r in enumerate(rows, start=1):
        cid = r.get("claim_id", f"row{i}")
        prompt = build_prompt(r, args.mode, cache)
        key = cache_key(args.model, args.mode, args.force_binary, cid, prompt)

        if key in cache:
            res = cache[key]
        else:
            res, raw = ask(args.model, prompt, args.force_binary)
            if res is None:
                failed += 1
                print(f"  [{i}/{len(rows)}] {cid}: CALL FAILED -- {raw[:120]}")
                if failed >= 5 and fresh == 0:
                    print("\nFAIL: 5 consecutive failures with no successes. "
                          "Aborting rather than burning the run.")
                    save_cache(cache)
                    return 3
                continue
            cache[key] = res            # only successes are cached
            fresh += 1
            if fresh % 10 == 0:
                save_cache(cache)
            print(f"  [{i}/{len(rows)}] {cid}: {res['verdict']} "
                  f"({res['confidence']:.2f})")

        out.append({
            "claim_id": cid,
            "batch": r.get("batch", ""),
            "gold_type": r.get("gold_type", ""),
            "gold_verdict": r.get("gold_verdict", ""),
            "pred_verdict": res["verdict"],
            "confidence": res["confidence"],
            "reason": res.get("reason", ""),
            "mode": args.mode,
            "model": args.model,
            "force_binary": str(args.force_binary).lower(),
            "temperature": "0.0",
        })

    save_cache(cache)
    if not out:
        print("\nFAIL: no usable predictions.")
        return 3
    if failed:
        print(f"\n  {failed} call(s) failed and are EXCLUDED (not counted as "
              f"abstentions -- that would flatter the baseline).")

    suffix = f"{args.mode}{'_binary' if args.force_binary else ''}"
    res_path = os.path.join(HERE, f"llm_baseline_results_{suffix}.csv")
    with open(res_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\nwrote {res_path}")

    gold = [d["gold_verdict"] for d in out]
    pred = [d["pred_verdict"] for d in out]
    conf = [d["confidence"] for d in out]
    title = (f"LLM baseline -- {args.model}, mode={args.mode}"
             f"{', FORCED BINARY' if args.force_binary else ''}")
    metrics.report(gold, pred, conf, title=title)
    metrics.curve_table(gold, pred, conf)

    types = sorted({d["gold_type"] for d in out if d["gold_type"]})
    for t in types:
        sub = [d for d in out if d["gold_type"] == t]
        if len(sub) < 5:
            continue
        metrics.report([d["gold_verdict"] for d in sub],
                       [d["pred_verdict"] for d in sub],
                       [d["confidence"] for d in sub],
                       title=f"{title}  --  {t} only")

    print("\nREAD THIS BEFORE QUOTING ANYTHING ABOVE")
    print("  A high accuracy with F1(FALSE) near 0.00 is the Always-True")
    print("  degenerate pattern, not a working fact-checker. Compare against the")
    print("  degenerate baselines printed in each block, and compare this run to")
    print("  our verifiers as CURVES at matched coverage -- never at a point.")
    return 0


# ---------------------------------------------------------------------------
# selftest -- no ollama required
# ---------------------------------------------------------------------------

def selftest() -> int:
    print("=== parse() ===")
    cases = [
        ('{"verdict":"TRUE","confidence":0.9,"reason":"ok"}', "TRUE"),
        ('```json\n{"verdict":"FALSE","confidence":0.4}\n```', "FALSE"),
        ('Sure! {"verdict":"UNVERIFIABLE","confidence":0.2} hope that helps', "UNVERIFIABLE"),
        ('{"verdict":"supported","confidence":1}', "TRUE"),
        ('{"verdict":"NOT ENOUGH INFO","confidence":0.1}', "UNVERIFIABLE"),
        ("I think this is FALSE.", "FALSE"),
        ('{"verdict":"MAYBE"}', None),
        ("", None),
        ('{"verdict":"TRUE","confidence":"high"}', "TRUE"),   # bad conf -> 0.5
        ('{"verdict":"TRUE","confidence":9.9}', "TRUE"),       # clamped
    ]
    ok = 0
    for raw, want in cases:
        got = parse(raw)
        gotv = got["verdict"] if got else None
        good = gotv == want
        ok += good
        print(f"  {'PASS' if good else 'FAIL'}  {raw[:46]!r:<50} -> {gotv}")
        if got:
            assert 0.0 <= got["confidence"] <= 1.0, "confidence not clamped"
    print(f"  {ok}/{len(cases)} passed")

    print("\n=== metrics on a synthetic Always-True predictor ===")
    gold = ["TRUE"] * 88 + ["FALSE"] * 8 + ["UNVERIFIABLE"] * 4
    metrics.report(gold, ["TRUE"] * 100, title="synthetic Always-True (n=100)")
    print("\n  Expect accuracy 88.0%, F1(FALSE) 0.00, MCC 0.00 -- i.e. the trap.")

    print("\n=== cache key stability ===")
    a = cache_key("m", "closed", False, "C1", "p")
    b = cache_key("m", "closed", False, "C1", "p")
    c = cache_key("m", "closed", True, "C1", "p")
    print(f"  same inputs identical: {a == b}")
    print(f"  binary flag changes key: {a != c}")
    assert a == b and a != c
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=("closed", "evidence", "wiki"), default="closed")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--claims", default="", help="claims CSV (default: unified, else b3)")
    ap.add_argument("--limit", type=int, default=0, help="first N claims (smoke test)")
    ap.add_argument("--force-binary", action="store_true",
                    help="forbid UNVERIFIABLE -- run this AS A CONTRAST, labelled")
    ap.add_argument("--include-synthetic", action="store_true",
                    help="include the 27 synthetic negatives")
    ap.add_argument("--check", action="store_true", help="ping ollama, list models")
    ap.add_argument("--selftest", action="store_true", help="offline tests, no ollama")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.check:
        return 0 if ollama_check(args.model) else 2
    if not ollama_check(args.model):
        return 2
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
