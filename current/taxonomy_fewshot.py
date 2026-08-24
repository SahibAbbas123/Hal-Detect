#!/usr/bin/env python3
"""
Few-shot taxonomy classification, built from the project's own 140-claim corpus.

WHY FEW-SHOT
------------
The project's documented pipeline classifies claims with **LLM few-shot prompting at
temperature 0, using the 140-claim corpus as demonstrations**, with
`taxonomy_rules.docx` serving as the prompt spec. A zero-shot prompt — however
carefully it paraphrases the rules — is a different classifier, and the difference is
not cosmetic: on a 20-claim FActScore pilot, prompt wording alone moved 11 of 20 type
assignments.

So this module exists to make the classifier used in out-of-domain experiments the
same *kind* of classifier the thesis describes, rather than an approximation of it.

WHERE THE EXEMPLARS COME FROM
-----------------------------
`reference/all-140-claims.txt` — 138 of 140 parse cleanly into
(id, topic, claim, type, justification). The parsed distribution corroborates the rule
document's own §10 table, which is a useful integrity check on the parse:

    parsed            doc §10
    RELATIONAL  48%   ~48%
    ENTITY_ATTR 20%   ~17%
    TEMPORAL    14%   ~16%
    QUANTITATIVE 11%  ~11%
    CITATION     6%    ~7%

Each exemplar carries a one-line justification written in the rule document's own
vocabulary ("Date is primary verifiable element", "43% is primary verifiable element;
2030 is context"). Including those is the point: they teach the *reasoning*, and the
reasoning is what the hard cases turn on.

TWO CAVEATS THAT MUST TRAVEL WITH ANY RESULT
--------------------------------------------
1. **These type labels are not verified gold.** The "Sorting the 140 claims" handoff is
   explicit: *"This session's classifications are NOT gold labels... produced by Claude
   during a formatting task, not verified... and not reviewed claim-by-claim by the
   author."* So a few-shot prompt built from them propagates whatever errors they
   contain. They are consistent with the rule document, which is the best available
   guarantee, but it is not human verification.

2. **CONTAMINATION RISK — do not measure routing on Batch 1 with this prompt.** The
   corpus topics are Einstein, FinCrisis, DNA, Tesla, IPCC, Immune, SilkRoad, Rome, QC,
   WWI — i.e. **Batch 1's own questions**. Batch 1 is also the *only* claim set whose
   `gold_type` is independently labelled, and therefore the only set on which routing
   accuracy can legitimately be scored. Using these exemplars to classify Batch 1 would
   be training and testing on the same claims. It is safe for FActScore and FEVER, which
   are disjoint.

EXEMPLAR SELECTION
------------------
Deterministic, and deliberately weighted toward the boundaries rather than a random
sample. The rule document names three hard cases, and each gets explicit coverage:

  * **QUANTITATIVE beats TEMPORAL** when the number is the more contested element
    (G4: "reduced by 43% by 2030").
  * **RELATIONAL beats ENTITY_ATTRIBUTE** when the verb is a process or mechanism.
  * **CITATION specificity** — a named lookable source qualifies, and pure
    source-existence claims from dual-emit are their own recognisable shape.

A uniformly random sample would under-represent all three, because RELATIONAL is 48%
of the corpus and would dominate.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(ROOT, "reference", "all-140-claims.txt")
PARSED = os.path.join(HERE, "taxonomy_exemplars_raw.json")

TYPES = ("CITATION", "TEMPORAL", "QUANTITATIVE", "ENTITY_ATTRIBUTE", "RELATIONAL")
_ID = re.compile(r"^(?:\d+|G\d+|Gr\d+)$")

# Exemplars chosen by claim id where a specific boundary must be demonstrated.
# Anything not pinned here is filled in deterministically by corpus order.
PINNED = [
    "G1",    # CITATION: named source attribution
    "G3",    # CITATION: pure source-existence (dual-emit shape)
    "G4",    # QUANTITATIVE beating TEMPORAL: "43% by 2030"
]
PER_TYPE = 3


def parse_corpus(path: str = CORPUS) -> list[dict]:
    lines = [l.strip() for l in open(path, encoding="utf-8-sig")]
    rows, topic, i = [], "", 0
    while i < len(lines):
        l = lines[i]
        m = re.match(r"^(Q\d+|Gemini|Grok)\s*[—-]*\s*(.*?)\(?\d* ?claims?\)?$", l)
        if m and "claims" in l:
            topic = m.group(1)
        if _ID.match(l) and i + 3 < len(lines):
            claim, ctype, just = lines[i + 1], lines[i + 2], lines[i + 3]
            if ctype in TYPES and len(claim) > 15:
                rows.append({"id": l, "topic": topic, "claim": claim,
                             "type": ctype, "justification": just})
                i += 4
                continue
        i += 1
    return rows


def select(rows: list[dict], per_type: int = PER_TYPE) -> list[dict]:
    by_id = {r["id"]: r for r in rows}
    chosen: list[dict] = [by_id[i] for i in PINNED if i in by_id]
    have = collections.Counter(r["type"] for r in chosen)
    for t in TYPES:
        for r in rows:
            if have[t] >= per_type:
                break
            if r["type"] == t and r not in chosen:
                chosen.append(r)
                have[t] += 1
    # Present grouped by taxonomy priority so the ordering itself reinforces it.
    return sorted(chosen, key=lambda r: TYPES.index(r["type"]))


HEADER = """You classify atomic factual claims for a taxonomy-routed hallucination-detection system, using the project's own rule set.

FIVE TYPES, in priority order. The governing principle is THE MOST CONTESTABLE ELEMENT: whichever fact in the claim is most specific and most checkable decides the type. Priority only breaks a genuine tie.

1. CITATION — names a specific, independently lookable source (named organisation, named report, journal, or author + year). CITATION always wins when it qualifies.
   Vague attributions do NOT qualify: "Scientists conclude", "Research suggests", "Studies show", "According to experts" -> classify as the type of the embedded fact instead.
2. TEMPORAL — a date, year, duration or time-ordered event is the primary verifiable element. A date present only as context does not make a claim TEMPORAL.
3. QUANTITATIVE — a number, measurement, percentage or statistic is primary. QUANTITATIVE BEATS TEMPORAL when the number is more specific or contested than the date.
4. ENTITY_ATTRIBUTE — assigns a property, role, nationality, descriptor or structure. Dominant verb is IS / WAS / HAS, with no process or causal chain.
5. RELATIONAL — asserts what something DOES, CAUSES, LEADS TO, ENABLES or WORKS BY. RELATIONAL BEATS ENTITY_ATTRIBUTE when the dominant verb is an action, process or mechanism.

THE EA vs RELATIONAL TEST — which question does the claim answer?
   "What IS X?" / "What does X HAVE?"                        -> ENTITY_ATTRIBUTE
   "What does X DO?" / "How does X WORK?" / "What did X CAUSE?" -> RELATIONAL

Modal qualifiers do not disqualify a claim: "could prevent 45% of cases" is still QUANTITATIVE.

WORKED EXAMPLES from the project's annotated corpus:
"""

FOOTER = """
Now classify this claim and extract its fields.

The claim is one sentence from a biography of: {topic}
Pronouns refer to that person.

- subject: "{topic}" unless the claim is plainly about someone or something else.
- property: short snake_case predicate — date_of_birth, date_of_death, place_of_birth, nationality, occupation, position_held, educated_at, award_received, spouse, child, employer, member_of.
- value: the specific value asserted, copied verbatim from the claim.

Return ONLY a JSON object: {{"type": "...", "subject": "...", "property": "...", "value": "..."}}

Claim: {claim}"""


def build_prompt_template(exemplars: list[dict] | None = None) -> str:
    """Header + worked examples + footer, with {topic}/{claim} left for .format()."""
    if exemplars is None:
        rows = (json.load(open(PARSED, encoding="utf-8"))
                if os.path.exists(PARSED) else parse_corpus())
        exemplars = select(rows)
    body = "\n".join(
        f'  Claim: {e["claim"]}\n  -> {e["type"]}  ({e["justification"]})'
        for e in exemplars)
    return HEADER + body + FOOTER


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build the few-shot taxonomy prompt from the 140-claim corpus.")
    ap.add_argument("--per-type", type=int, default=PER_TYPE)
    ap.add_argument("--show", action="store_true", help="print the full prompt")
    args = ap.parse_args()

    if not os.path.isfile(CORPUS):
        print(f"FATAL: {CORPUS} not found")
        return 1
    rows = parse_corpus()
    print(f"parsed {len(rows)}/140 claims from {os.path.relpath(CORPUS, ROOT)}")
    dist = collections.Counter(r["type"] for r in rows)
    print("  corpus distribution (vs rule doc §10):")
    doc = {"RELATIONAL": "~48%", "ENTITY_ATTRIBUTE": "~17%", "TEMPORAL": "~16%",
           "QUANTITATIVE": "~11%", "CITATION": "~7%"}
    for t in TYPES:
        print(f"    {t:<18}{dist[t]:>4}  {dist[t]/len(rows):>6.1%}   doc {doc[t]}")
    json.dump(rows, open(PARSED, "w"), indent=1)

    ex = select(rows, args.per_type)
    print(f"\nselected {len(ex)} exemplars:")
    for e in ex:
        print(f"  [{e['type'][:12]:<13}] {e['id']:<5}{e['claim'][:62]}")
    tmpl = build_prompt_template(ex)
    print(f"\nprompt template: {len(tmpl)} chars")
    if args.show:
        print("\n" + "=" * 70 + "\n" + tmpl)
    print("\nCONTAMINATION WARNING: these exemplars come from Batch 1's own topics")
    print("(Einstein, FinCrisis, IPCC, SilkRoad, QC, WWI...). Batch 1 is the ONLY set")
    print("with independently labelled gold_type, so it is the only set routing")
    print("accuracy can be scored on -- and scoring it with THIS prompt would be")
    print("training and testing on the same claims. Safe for FActScore and FEVER.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
