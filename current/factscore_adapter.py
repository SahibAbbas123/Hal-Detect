#!/usr/bin/env python3
"""
Adapter: FActScore human-annotated atomic facts -> HalDetect claim schema.

WHY AN ADAPTER IS NEEDED
------------------------
FActScore atomic facts are bare sentences plus a `topic` and a `cat` (rarity, region).
They carry **no `subject` / `property` / `value`**, which every Wikidata-backed verifier
in this project depends on. Two specific mismatches:

  1. **Pronouns.** "He has appeared in numerous films." The subject is not in the
     sentence. It is the entry's `topic`, so `subject` is taken from there rather than
     parsed out — which is both more accurate and avoids inventing a coreference step.
  2. **No predicate.** "Lanny Flaherty was born in Pensacola" has to become
     `property=place_of_birth, value=Pensacola` before a Wikidata lookup can happen.

TWO EXTRACTORS, AND WHY `--gemini` IS THE FAITHFUL ONE
-----------------------------------------------------
`extract()` is a small transparent rule set over the biography patterns FActScore
contains. On the 20-claim pilot it captured a predicate for only **4 of 20** — 16 fell
through to RELATIONAL, including "Vincenzo Tusa died on 5 March 2009", which a date
rule expecting "December 18, 1949" cannot see.

`extract_gemini()` (via `--gemini`) classifies and extracts with
`gemini-3.1-flash-lite-preview` at temperature 0. On the same 20 claims it succeeded
**20/20** and produced RELATIONAL 9 / ENTITY_ATTRIBUTE 9 / TEMPORAL 2 instead of
RELATIONAL 16.

**`--gemini` is the faithful option, not the convenient one.** The project's documented
pipeline uses LLM few-shot classification plus structured JSON extraction at
temperature 0, precisely because rule extraction is unreliable on open prose. Measuring
with rules would test a pipeline this thesis does not have — and it would make the
out-of-domain numbers incomparable to the in-domain ones, which carry the LLM-extraction
confound already.

Either way, extraction quality remains a **confound**: a mis-typed claim is scored
against the verifier, so out-of-domain figures are a lower bound on verifier quality
rather than a clean measurement of it. `extractor` is recorded per row so the path that
fired is auditable, and Gemini failures fall back to rules **visibly**
(`rules(gemini-failed:...)`) rather than silently. Extraction is cached by claim text,
so a re-run neither pays twice nor produces different fields on the second pass.

WHY THIS DATASET IS THE RIGHT TEST, AND WHY IT MIGHT FLATTER US
---------------------------------------------------------------
FActScore is biography-only, and biography facts — birth date, birth place,
nationality, occupation — are **exactly what Wikidata models best** (P569, P19, P27,
P106). So the earlier prediction that out-of-domain coverage would fall may be wrong
for TEMPORAL and ENTITY_ATTRIBUTE. Two counterweights to report alongside:

  * Every claim has one clear named person as its subject, so entity resolution is
    **easier** here than on this project's multi-domain corpus. Resolution numbers
    will look better than they deserve.
  * `cat` carries a rarity tier (`very rare` -> `very freq`). FActScore's own paper
    reports ChatGPT factuality falling from ~80% on frequent entities to ~16% on very
    rare ones. That gives a **rarity axis** this project has never had: does our
    resolver's coverage degrade with entity obscurity? That is a genuinely new
    analysis, and a real limitation if it does.

LABEL MAPPING — fixed by prior decision, not chosen here
--------------------------------------------------------
    S  -> TRUE
    NS -> FALSE
    IR -> EXCLUDED entirely, never mapped to UNVERIFIABLE

The IR rule matters: "not worth verifying" and "tried but found no evidence" are
different things, and merging them corrupts the coverage metric. Recorded in the
taxonomy handoff as a standing commitment.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LABELED = os.path.join(ROOT, "data", "factscore", "annotations", "factscore",
                       "data", "labeled")
OUT = os.path.join(HERE, "factscore_adapted.csv")

GEMINI_DELAY = 1.2   # polite spacing; the pilot hit rate limits at 0

RARITY = ("very rare", "rare", "medium", "freq", "very freq")

# Ordered rules. First match wins, so the more specific patterns come first.
# Each entry: (regex, property, claim_type, value-from-group)
RULES = [
    (r"\bwas born (?:on|in) ((?:January|February|March|April|May|June|July|August|"
     r"September|October|November|December)\s+\d{1,2},?\s*\d{4})",
     "date_of_birth", "TEMPORAL", 1),
    (r"\bwas born in (\d{4})\b", "date_of_birth", "TEMPORAL", 1),
    (r"\bdied (?:on|in) ((?:January|February|March|April|May|June|July|August|"
     r"September|October|November|December)\s+\d{1,2},?\s*\d{4})",
     "date_of_death", "TEMPORAL", 1),
    (r"\bdied in (\d{4})\b", "date_of_death", "TEMPORAL", 1),
    (r"\bwas born in ([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)",
     "place_of_birth", "ENTITY_ATTRIBUTE", 1),
    (r"\bdied in ([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)",
     "place_of_death", "ENTITY_ATTRIBUTE", 1),
    (r"\bgraduated from ([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)",
     "educated_at", "ENTITY_ATTRIBUTE", 1),
    (r"\battended ([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)",
     "educated_at", "ENTITY_ATTRIBUTE", 1),
    (r"\bis an? (American|British|Canadian|Australian|French|German|Italian|Spanish|"
     r"Indian|Japanese|Chinese|Russian|Brazilian|Mexican|Dutch|Swedish|Norwegian|"
     r"Danish|Polish|Irish|Scottish|Nigerian|Egyptian|Israeli|Turkish|Korean)\b",
     "nationality", "ENTITY_ATTRIBUTE", 1),
    (r"\bis (?:a|an) ([a-z][a-z\- ]{2,30}?)(?:\.|,| who| that| in | for | at |$)",
     "occupation", "ENTITY_ATTRIBUTE", 1),
    (r"\bwon (?:the )?([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)",
     "award_received", "ENTITY_ATTRIBUTE", 1),
]


def extract(text: str, topic: str) -> dict:
    """Return {property, value, type, extractor}. Falls back to RELATIONAL."""
    for i, (pat, prop, ctype, grp) in enumerate(RULES):
        m = re.search(pat, text)
        if m:
            return {"property": prop, "value": m.group(grp).strip(" .,"),
                    "type": ctype, "extractor": f"rule{i}:{prop}"}
    return {"property": "", "value": "", "type": "RELATIONAL",
            "extractor": "fallback:RELATIONAL"}


# ---------------------------------------------------------------------------
# Gemini extraction — what the real pipeline actually does
# ---------------------------------------------------------------------------

GEMINI_PROMPT = """You classify atomic factual claims for a taxonomy-routed hallucination-detection system. Follow these rules exactly; they are taken from the project's authoritative rule document.

The claim is one sentence from a biography of: {topic}
Pronouns refer to that person.

STEP 1 — classify into exactly one of five types.

Work down this list, but the governing principle is THE MOST CONTESTABLE ELEMENT: whichever fact in the claim is the most specific and most checkable decides the type. Position in the list only breaks a genuine tie.

1. CITATION — names a specific, independently lookable source (a named organisation, named report, journal, or named author + year).
   CITATION ALWAYS WINS when it qualifies.
   Qualifies: "The WHO reports...", "The IPCC AR6 Synthesis Report states...", "NASA data shows...", "Smith et al. (2020) found..."
   Does NOT qualify: "Scientists conclude...", "Research suggests...", "Studies show...", "According to experts..."
   If attribution language is present but the source is vague, DOWNGRADE to the type of the embedded fact.

2. TEMPORAL — a date, year, duration or time-ordered event is the primary verifiable element.
   "Albert Einstein was born on 14 March 1879." -> TEMPORAL (date is primary; no competing number)
   A date present merely as context does NOT make a claim TEMPORAL.

3. QUANTITATIVE — a number, measurement, percentage or statistic is the primary verifiable element.
   QUANTITATIVE BEATS TEMPORAL whenever the number is more specific or more contested than the date:
     "Air pollution caused 4.2 million deaths in 2019." -> QUANTITATIVE (4.2 million dominates; 2019 is context)
     "Emissions must fall 43% by 2030."               -> QUANTITATIVE (43% dominates; 2030 is context)
     "The Silk Road stretched roughly 4,000 miles."    -> QUANTITATIVE

4. ENTITY_ATTRIBUTE — assigns a property, role, nationality, descriptor or structural characteristic. Dominant verb is IS / WAS / HAS or a state verb, with no process or causal chain.
   "Nikola Tesla was a Serbian-American inventor." -> ENTITY_ATTRIBUTE
   "DNA has a double-helix structure."             -> ENTITY_ATTRIBUTE

5. RELATIONAL — asserts a causal, functional or mechanistic relationship: what something DOES, CAUSES, LEADS TO, ENABLES or WORKS BY.
   RELATIONAL BEATS ENTITY_ATTRIBUTE whenever the dominant verb describes an action, process or mechanism:
     "DNA replicates by separating its strands." -> RELATIONAL (mechanism, not attribute)
     "Adenine pairs with thymine."               -> RELATIONAL (process)
     "The Treaty of Versailles contributed to the rise of fascism." -> RELATIONAL

THE EA vs RELATIONAL TEST (the most common source of error) — ask which question the claim answers:
   "What IS X?" or "What does X HAVE?"                    -> ENTITY_ATTRIBUTE
   "What does X DO?", "How does X WORK?", "What did X CAUSE?" -> RELATIONAL

Modal qualifiers do not disqualify a claim: "could prevent 45% of cases" is still QUANTITATIVE.

STEP 2 — extract subject / property / value.
- subject: "{topic}" unless the claim is plainly about someone or something else.
- property: short snake_case predicate — date_of_birth, date_of_death, place_of_birth, nationality, occupation, position_held, educated_at, award_received, spouse, child, employer, member_of.
- value: the specific value asserted, copied verbatim from the claim.

Return ONLY a JSON object: {{"type": "...", "subject": "...", "property": "...", "value": "..."}}

Claim: {claim}"""

# Bumped whenever GEMINI_PROMPT changes. The cache is keyed by claim text, so
# without this a prompt fix would be invisible on every previously-seen claim --
# the same trap as the cmeta__/meta__ cache keys elsewhere in this project.
#
# v1: five prose definitions written from handoff summaries. No priority order.
# v2: added priority order as strict stop-at-first + CITATION specificity.
# v3: rewritten from the AUTHORITATIVE reference/taxonomy_rules_extracted.txt.
#     v2 was materially WRONG: it treated the priority list as stop-at-first,
#     but the rule document's governing principle is "most contestable element",
#     and it specifies two explicit inversions of that list --
#     QUANTITATIVE beats TEMPORAL when the number dominates, and RELATIONAL
#     beats ENTITY_ATTRIBUTE when the verb is a process. Under v2,
#     "Air pollution caused 4.2 million deaths in 2019" classified TEMPORAL;
#     the rule document says QUANTITATIVE.
PROMPT_VERSION = "v3-authoritative"

# v4: few-shot. Loads 15 worked examples from the project's own 140-claim corpus
#     via taxonomy_fewshot, matching the documented pipeline (LLM few-shot at
#     temperature 0 with the 140-corpus as demonstrations) rather than
#     approximating it zero-shot. Selected with --fewshot.
FEWSHOT_VERSION = "v4-fewshot-140corpus"


def _fewshot_template():
    """Cached few-shot template. Imported lazily so zero-shot runs stay cheap."""
    global _FEWSHOT_CACHE
    try:
        return _FEWSHOT_CACHE
    except NameError:
        pass
    import taxonomy_fewshot as TF
    _FEWSHOT_CACHE = TF.build_prompt_template()
    return _FEWSHOT_CACHE


def extract_gemini(text: str, topic: str, cache: dict,
                   fewshot: bool = False) -> dict:
    """Classify + extract with Gemini, mirroring the project's real pipeline.

    The rule-based `extract()` above captured a predicate for only 4 of 20 pilot
    claims -- 16 fell through to RELATIONAL, including "Vincenzo Tusa died on 5 March
    2009", which a date rule expecting "December 18, 1949" cannot see. Chasing more
    regexes would improve that number while measuring a pipeline this thesis does not
    have: the documented system uses **LLM few-shot classification plus structured
    JSON extraction at temperature 0**, precisely because rule extraction is
    unreliable on open prose.

    So Gemini is the faithful choice, not the convenient one. It also keeps the
    confound identical to the one the in-domain results already carry, which is what
    makes in-domain and out-of-domain numbers comparable at all.

    Cached by claim text: extraction is deterministic per claim and a re-run must not
    pay for it twice, nor produce different fields on the second pass.
    """
    import gemini_key
    import json as _json
    import urllib.error
    import urllib.request

    key = gemini_key.get()
    if not key:
        return {**extract(text, topic), "extractor": "rules(no-gemini-key)"}

    ver = FEWSHOT_VERSION if fewshot else PROMPT_VERSION
    ck = f"fsx__{ver}__{text[:120]}"
    if ck in cache:
        return cache[ck]

    tmpl = _fewshot_template() if fewshot else GEMINI_PROMPT
    body = _json.dumps({
        "contents": [{"parts": [{"text": tmpl.format(topic=topic,
                                                     claim=text)}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 200,
                             "responseMimeType": "application/json"},
    }).encode()

    # Retry with backoff. The 20-claim pilot lost 4 rows to HTTPError (rate
    # limiting); at 100+ claims that would be a large silent hole in the type mix,
    # and a claim dropped to the rules fallback is scored against the verifier.
    last = None
    for attempt in range(4):
        req = urllib.request.Request(gemini_key.endpoint(key=key), data=body,
                                     method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = _json.loads(resp.read().decode())
            txt = "".join(part.get("text", "")
                          for c in payload.get("candidates", [])
                          for part in c.get("content", {}).get("parts", []))
            obj = _json.loads(txt)
            out = {
                "type": (obj.get("type") or "RELATIONAL").upper().strip(),
                "property": (obj.get("property") or "").strip(),
                "value": (obj.get("value") or "").strip(),
                "gemini_subject": (obj.get("subject") or "").strip(),
                "extractor": "gemini",
            }
            if out["type"] not in ("TEMPORAL", "QUANTITATIVE", "ENTITY_ATTRIBUTE",
                                   "CITATION", "RELATIONAL"):
                out["type"] = "RELATIONAL"
            cache[ck] = out          # only successes are cached
            time.sleep(GEMINI_DELAY)
            return out
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError,
                KeyError) as exc:
            last = exc
            time.sleep(GEMINI_DELAY * (2 ** attempt))

    # Never cache a failure, and fall back visibly rather than silently.
    return {**extract(text, topic),
            "extractor": f"rules(gemini-failed:{last.__class__.__name__})"}


def load_facts(models: list[str]) -> list[dict]:
    out = []
    for fn in sorted(os.listdir(LABELED)):
        if not fn.endswith(".jsonl"):
            continue
        model = fn[:-6]
        if models and model not in models:
            continue
        for line in open(os.path.join(LABELED, fn), encoding="utf-8"):
            rec = json.loads(line)
            topic = rec.get("topic", "")
            cats = rec.get("cat") or []
            rarity = next((c for c in cats if c in RARITY), "")
            region = next((c for c in cats if c not in RARITY), "")
            for ann in (rec.get("annotations") or []):
                for f in (ann.get("human-atomic-facts") or []):
                    lab = f.get("label")
                    if lab not in ("S", "NS"):
                        continue            # IR excluded, never mapped
                    text = (f.get("text") or "").strip()
                    if not text:
                        continue
                    out.append({
                        "claim_id": "",          # assigned after sampling
                        "claim": text,
                        "subject": topic,        # from `topic`: handles pronouns
                        "gold_verdict": "TRUE" if lab == "S" else "FALSE",
                        "factscore_label": lab,
                        "source_model": model,
                        "rarity": rarity, "region": region,
                        "secondary": "{}", "synthetic": "FALSE",
                        "type": "", "property": "", "value": "", "extractor": "",
                    })
    return out


def sample(facts: list[dict], n: int, seed: int,
           balance: bool) -> list[dict]:
    """Stratify by gold verdict, then spread across rarity tiers."""
    rng = random.Random(seed)
    if not balance:
        rng.shuffle(facts)
        return facts[:n]
    pos = [f for f in facts if f["gold_verdict"] == "TRUE"]
    neg = [f for f in facts if f["gold_verdict"] == "FALSE"]
    half = n // 2
    picked = []
    for pool in (pos, neg):
        by_r: dict[str, list[dict]] = collections.defaultdict(list)
        for f in pool:
            by_r[f["rarity"] or "?"].append(f)
        for lst in by_r.values():
            rng.shuffle(lst)
        take, i = [], 0
        tiers = [t for t in RARITY if by_r.get(t)] or list(by_r)
        while len(take) < half and any(by_r[t] for t in tiers):
            t = tiers[i % len(tiers)]
            if by_r[t]:
                take.append(by_r[t].pop())
            i += 1
        picked.extend(take[:half])
    rng.shuffle(picked)
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Adapt FActScore atomic facts into the HalDetect claim schema.")
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--models", default="",
                    help="comma-separated subset, e.g. ChatGPT")
    ap.add_argument("--no-balance", action="store_true")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--fewshot", action="store_true",
                    help="use the FEW-SHOT prompt built from the project's own "
                         "140-claim corpus (matches the documented pipeline). "
                         "Implies --gemini.")
    ap.add_argument("--gemini", action="store_true",
                    help="classify + extract with Gemini (what the real pipeline "
                         "does) instead of the narrow rule set")
    args = ap.parse_args()

    if not os.path.isdir(LABELED):
        print(f"FATAL: {LABELED} not found")
        return 1
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    facts = load_facts(models)
    print(f"loaded {len(facts)} S/NS atomic facts (IR excluded)")
    print(f"  gold: {dict(collections.Counter(f['gold_verdict'] for f in facts))}")

    picked = sample(facts, args.n, args.seed, not args.no_balance)

    # Extract AFTER sampling: Gemini costs one call per claim, so extracting all
    # 14,525 facts to use 20 of them would be absurd.
    xcache_path = os.path.join(HERE, "factscore_extract_cache.json")
    xcache = {}
    if args.gemini and os.path.exists(xcache_path):
        try:
            xcache = json.load(open(xcache_path, encoding="utf-8"))
        except (OSError, ValueError):
            xcache = {}
    if args.fewshot:
        args.gemini = True
    for f in picked:
        ex = (extract_gemini(f["claim"], f["subject"], xcache, args.fewshot)
              if args.gemini
              else extract(f["claim"], f["subject"]))
        f.update({k: v for k, v in ex.items() if k != "gemini_subject"})
    if args.gemini:
        tmp = xcache_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(xcache, fh)
        os.replace(tmp, xcache_path)
        print(f"extraction cache: {len(xcache)} entries -> "
              f"{os.path.basename(xcache_path)}")

    for i, f in enumerate(picked, 1):
        f["claim_id"] = f"FS_{i:04d}"
        f["q_id"] = f"FS_{f['subject'].replace(' ', '_')[:24]}"
    print(f"\nsampled {len(picked)}")
    print(f"  gold   : {dict(collections.Counter(f['gold_verdict'] for f in picked))}")
    print(f"  types  : {dict(collections.Counter(f['type'] for f in picked))}")
    print(f"  rarity : {dict(collections.Counter(f['rarity'] for f in picked))}")
    print(f"  models : {dict(collections.Counter(f['source_model'] for f in picked))}")

    cols = ["claim_id", "q_id", "claim", "type", "subject", "property", "value",
            "secondary", "gold_verdict", "gold_type", "synthetic",
            "factscore_label", "source_model", "rarity", "region", "extractor"]
    for f in picked:
        f["gold_type"] = ""      # FActScore has no type labels; never fabricate one
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(picked)
    print(f"\nwrote {args.out}")

    print("\n-- extraction audit (the confound) --")
    for ex, k in collections.Counter(f["extractor"] for f in picked).most_common():
        print(f"  {k:>3}  {ex}")
    print("\n-- sample rows --")
    for f in picked[:8]:
        print(f"  [{f['gold_verdict']:<5}] {f['type'][:4]:<5} "
              f"{f['property'][:16]:<17}{(f['value'] or '-')[:22]:<24}{f['claim'][:52]}")
    print("\nNOTE: `gold_type` is intentionally EMPTY. FActScore carries no claim-type")
    print("labels, so routing accuracy CANNOT be scored on this set — only verifier")
    print("coverage and verdict accuracy can.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
