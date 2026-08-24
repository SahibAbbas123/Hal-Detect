#!/usr/bin/env python3
"""
Generate gold-FALSE claims by systematically corrupting gold-TRUE ones.

WHY THIS EXISTS
---------------
The pooled gold set is 314 TRUE / 13 FALSE / 29 UNVERIFIABLE. Thirteen negatives
across 356 claims caps everything: no accuracy figure can distinguish a verifier
that detects hallucinations from one that agrees with whatever it is shown, since
"always TRUE" already scores 88.2%.

Worse, the 27 existing synthetic negatives (`relational_negatives_batch3_merged.csv`)
are **all typed RELATIONAL**. So TEMPORAL, ENTITY_ATTRIBUTE, QUANTITATIVE and
CITATION have *zero* negatives of any kind, which is precisely why QUANTITATIVE
needed `--sensitivity` to be validated at all and why the other three have no
discrimination measurement.

This closes that gap for the four uncovered types.

THE CENTRAL DESIGN CHOICE: CROSS-SUBSTITUTION, NOT INVENTION
------------------------------------------------------------
The obvious approach -- perturb a number, or substitute a value from a hardcoded
table -- has two problems. Random perturbation can land on a value that is *also*
true (or within tolerance), and a hardcoded table encodes the author's assumptions
about what a plausible wrong answer looks like.

So the primary operator here is **cross-substitution**: give claim A the value that
truly belongs to claim B, where A and B share a property. Kilimanjaro's elevation
becomes Mount Elbrus's. This is:

  * **guaranteed plausible** -- it is a real, correctly-formatted value of exactly
    that kind, which is what makes it a good model of an LLM hallucination. LLMs
    do not emit `elevation = "purple"`; they emit a confident wrong number.
  * **guaranteed false** -- it is the value of a *different* entity, so unless two
    entities genuinely share the value (checked and skipped) the claim is wrong.
  * **assumption-free** -- every substituted value comes from the corpus itself.

Numeric scaling is kept as a secondary operator because it gives a *graded*
magnitude, which is what produces a flip-point curve rather than a pass/fail.

WHAT IS RECORDED, AND WHY
-------------------------
Every row carries `injection_type`, `magnitude`, `original_value` and
`corrupted_value`. Without magnitude you get one number ("caught 8/10"); with it
you get the curve that made the QUANTITATIVE validation credible ("flips at <=1%,
never inside tolerance"). Provenance (`base_claim_id`) means any negative can be
traced back and re-derived.

HONESTY CONSTRAINTS -- these are not optional
---------------------------------------------
1. **Synthetic negatives are not natural hallucinations.** They are corruptions of
   true statements, which is a narrower and easier distribution than what an LLM
   actually gets wrong. `synthetic=TRUE` on every row, and results on them must be
   reported separately from results on the 13 natural gold negatives, never pooled
   into one headline.
2. **A verifier that scores well here has shown it can detect a *substituted
   value*.** That is necessary but not sufficient evidence of hallucination
   detection. Say so.
3. **Only claims whose value appears verbatim in the claim text are corrupted**, so
   the output is always a grammatical sentence with exactly one thing wrong. Claims
   where the value cannot be located are skipped rather than mangled -- a garbled
   sentence would test the parser, not the verifier.
4. **Accidental-truth guard**: a substitution is rejected if the donor value equals
   the original, or (for numbers) falls within the verifier's own tolerance of it.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import consolidate_claims as CC   # noqa: E402

OUT = os.path.join(HERE, "synthetic_negatives.csv")
OUT_EXT = os.path.join(HERE, "external_negatives.csv")
OUT_MANUAL = os.path.join(HERE, "negatives_needing_manual_authoring.csv")

# Types that currently have zero negatives of any kind.
TARGET_TYPES = ("TEMPORAL", "ENTITY_ATTRIBUTE", "QUANTITATIVE", "CITATION")

# Numeric scale factors. Chosen to straddle the QUANTITATIVE verifier's own
# EXACT_TOLERANCE (0.5%) and APPROX_TOLERANCE (5%) so the curve has points on
# both sides of each threshold.
SCALES = [1.01, 1.05, 1.25, 1.5, 2.0, 10.0]
# +1y is DELIBERATELY EXCLUDED. Found 2026-08-23: shifting Einstein's Nobel Prize
# from 1921 to 1922 produced a claim that is still TRUE -- he was awarded the 1921
# prize and received it in 1922. The same trap exists for construction-start vs
# opening, announcement vs ratification, and discovery vs publication, all of which
# routinely sit one year apart.
#
# `validate()` cannot catch this: it detects identity and format-only edits, not
# accidental truth, and detecting accidental truth would require the knowledge base
# the verifier is being tested against. So the mitigation is to avoid the
# highest-risk magnitude rather than to filter afterwards. >=2y is materially safer,
# though not provably safe -- any surviving row is a candidate for the same error.
YEAR_SHIFTS = [2, 5, 10, 100]

_NUM = re.compile(r"\d[\d,]*\.?\d*")
_YEAR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")

# Below this relative difference a numeric substitution is treated as possibly
# still-true and rejected (mirrors quantitative_verifier.EXACT_TOLERANCE).
MIN_REL_DIFF = 0.005


def norm_num(s: str) -> float | None:
    m = _NUM.search(s or "")
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def fmt_like(original: str, new_val: float) -> str:
    """Render `new_val` in the same surface form as `original`.

    Preserves thousands separators and decimal places, so "8,848.86" -> "9,733.75"
    rather than "9733.746". A corrupted claim that *looks* differently formatted
    from the original would let a verifier cheat on formatting alone.
    """
    m = _NUM.search(original or "")
    if not m:
        return str(new_val)
    tok = m.group(0)
    dec = len(tok.split(".")[1]) if "." in tok else 0
    body = f"{new_val:,.{dec}f}" if "," in tok else f"{new_val:.{dec}f}"
    return original[:m.start()] + body + original[m.end():]


def substitute_in_claim(claim: str, old: str, new: str) -> str | None:
    """Replace `old` with `new` in the claim text. None if `old` isn't present."""
    if not claim or not old:
        return None
    if old in claim:
        return claim.replace(old, new, 1)
    # Numbers often differ in separator style between `value` and `claim`.
    a = norm_num(old)
    if a is None:
        return None
    for cand in {f"{a:,.0f}", f"{a:.0f}", f"{a:,.2f}".rstrip("0").rstrip("."),
                 f"{a:g}"}:
        if cand and cand in claim:
            nn = norm_num(new)
            rep = fmt_like(cand, nn) if nn is not None else new
            return claim.replace(cand, rep, 1)
    return None


def load_true_claims() -> list[dict]:
    rows, problems = CC.load_all()
    out = []
    for r in rows:
        if str(r.get("synthetic", "")).lower() == "true":
            continue                       # never corrupt a corruption
        if (r.get("gold_verdict") or "").strip() != "TRUE":
            continue
        if not (r.get("claim") or "").strip():
            continue
        out.append(r)
    if problems:
        print(f"  loader warnings: {len(problems)}")
    return out


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def functional_properties(claims: list[dict]) -> set[tuple[str, str]]:
    """Find (type, property) pairs holding at most ONE value per subject.

    This is what makes text cross-substitution safe again for part of the corpus.
    The first version banned all text values because swapping them produced
    nonsense or accidental truth. But the real distinction is not text-vs-number,
    it is **functional vs multi-valued**:

      * `highest_peak_in` — each mountain has exactly one continent. Give Elbrus
        Oceania and the claim is plausible and definitively FALSE.
      * `includes_vaccine_for` — the CDC schedule includes polio AND measles AND
        mumps AND rubella. Swapping any two leaves the claim TRUE.
      * `written_in_language` — the Rosetta Stone is written in hieroglyphs AND
        Ancient Greek AND Demotic. Same trap.
      * `consists_of` — the liver has lobes AND lobules; lobules have hepatocytes
        AND a central vein. Same trap.

    A property counts as functional only if **no subject in the corpus carries more
    than one distinct value for it**. Deliberately conservative: it may wrongly
    exclude a functional property whose subject happens to appear twice, but it
    never wrongly *includes* a multi-valued one — and the cost of a false include
    is a mislabelled gold row, which is the one error that cannot be detected
    downstream.
    """
    vals: dict[tuple[str, str, str], set[str]] = collections.defaultdict(set)
    for r in claims:
        prop = (r.get("property") or "").strip().lower()
        subj = (r.get("subject") or "").strip().lower()
        val = (r.get("value") or "").strip()
        if prop and subj and val:
            vals[(r.get("type", ""), prop, subj)].add(val)
    multi = {(t, p) for (t, p, _s), vs in vals.items() if len(vs) > 1}
    return {(t, p) for (t, p, _s) in vals} - multi


def op_cross_substitute(claims: list[dict]) -> tuple[list[dict], list[dict]]:
    """Primary operator. Swap values between claims sharing a property.

    RESTRICTED TO NUMERIC VALUES (2026-08-23). The first version accepted text
    values too, and the output was unusable:

        "The human liver is divided into right and left lobes."   <-- TRUE
        "The Rosetta Stone is a two primary lobes."               <-- broken
        "The CRISPR-Cas9 system consists of the granodiorite stele."

    The cause is that grouping by property *name* is not grouping by *domain*.
    Freeform properties like `composition` collect the liver, the Rosetta Stone
    and CRISPR into one pool, so a swap yields nonsense — or, worse, an
    accidentally TRUE sentence when the two values happen to be synonyms
    ("two primary lobes" / "right and left lobes"). Emitting either into a gold
    set is the single most damaging thing this script could do: a false negative
    label is indistinguishable from a verifier bug when the numbers come in.

    For numbers, format compatibility really does imply plausibility — swapping
    Kilimanjaro's elevation for Elbrus's gives a confident wrong number, which is
    exactly how LLMs fail. For text it does not, and no property-name heuristic
    recovers it. So text-valued claims are returned as a `needs_manual` list
    rather than silently corrupted or silently dropped.
    """
    by_prop: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in claims:
        prop = (r.get("property") or "").strip().lower()
        val = (r.get("value") or "").strip()
        if prop and val:
            by_prop[(r.get("type", ""), prop)].append(r)

    out, needs_manual = [], []
    functional = functional_properties(claims)
    for (ctype, prop), group in sorted(by_prop.items()):
        if ctype not in TARGET_TYPES:
            continue
        is_func = (ctype, prop) in functional
        numeric = [r for r in group if norm_num(r.get("value") or "") is not None]
        # Numbers are always eligible (format compatibility implies plausibility).
        # Text is eligible ONLY when the property is functional -- see
        # functional_properties().
        eligible = numeric if not is_func else group
        for r in group:
            if r not in eligible:
                needs_manual.append({
                    "claim_id": r["claim_id"], "type": ctype,
                    "subject": r.get("subject", ""),
                    "property": r.get("property", ""),
                    "value": r.get("value", ""), "claim": r.get("claim", ""),
                    "reason": ("text-valued AND property is multi-valued in the "
                               "corpus, so a swap risks producing a still-TRUE "
                               "claim; author a negative by hand"),
                })
        if len(eligible) < 2:
            continue
        for i, r in enumerate(eligible):
            donor = eligible[(i + 1) % len(eligible)]
            old, new = r["value"].strip(), donor["value"].strip()
            if old == new:
                continue
            if ((r.get("subject") or "").strip().lower()
                    == (donor.get("subject") or "").strip().lower()):
                continue                  # same subject: donor value may also be true
            a, b = norm_num(old), norm_num(new)
            if a is not None and b is not None:
                if a == 0 or abs(b - a) / abs(a) < MIN_REL_DIFF:
                    continue              # too close to be reliably false
                mag = f"{abs(b - a) / abs(a):.1%}"
            elif a is not None or b is not None:
                continue                  # never swap a number for a text value
            else:
                mag = "categorical"
            text = substitute_in_claim(r["claim"], old, new)
            if not text:
                continue
            out.append({
                "base_claim_id": r["claim_id"], "type": ctype,
                "subject": r.get("subject", ""), "property": r.get("property", ""),
                "injection_type": ("cross_substitute" if a is not None
                                   else "cross_substitute_categorical"),
                "magnitude": mag,
                "original_value": old, "corrupted_value": new, "claim": text,
                "_base_claim": r.get("claim", ""),
                "notes": (f"{'numeric' if a is not None else 'categorical'} value "
                          f"of {donor['claim_id']} ({donor.get('subject','?')}) "
                          f"substituted for {r.get('subject','?')}'s; property "
                          f"'{prop}' is single-valued per subject in this corpus"),
            })
    return out, needs_manual


_MONTHS = ("january february march april may june july august september october "
           "november december jan feb mar apr jun jul aug sep sept oct nov dec")
_MONTH_SET = set(_MONTHS.split())


def is_pure_quantity(val: str) -> bool:
    """True only for a value that is a single number plus optional unit words.

    Guards `op_scale_number`, which previously accepted anything containing a
    digit. That let two classes of garbage through:

      * `"Cas9 protein and a guide RNA"` — the scaler found the 9 in "Cas9",
        multiplied it by 1.01, rounded back to 9, and emitted a claim IDENTICAL
        to the original but labelled FALSE.
      * `"September 15, 2008"` — scaling the 15 by 1.01 rounded back to 15 and
        only the comma changed, so again a still-TRUE claim labelled FALSE.

    A mislabelled gold row is worse than no row: when a verifier disagrees with
    it, there is no way to tell a verifier bug from a label bug. So this is
    deliberately strict, and rejects anything it is not sure about.
    """
    s = (val or "").strip().lower()
    if not s:
        return False
    nums = _NUM.findall(s)
    if len(nums) != 1:
        return False                      # dates, ranges, compound values
    words = re.findall(r"[a-z]+", s)
    if any(w in _MONTH_SET for w in words):
        return False                      # a date, not a magnitude
    allowed = {"million", "billion", "trillion", "thousand", "percent", "pct",
               "m", "bn", "km", "kg", "cm", "mm", "meters", "metres", "meter",
               "metre", "feet", "ft", "years", "year", "days", "day", "hours",
               "hour", "seconds", "second", "tonnes", "tons", "usd", "eur",
               "degrees", "celsius", "over", "about", "approximately", "under",
               "up", "to", "than", "more", "less", "at", "least", "most"}
    return all(w in allowed for w in words)


def op_scale_number(claims: list[dict]) -> list[dict]:
    """Graded numeric corruption -- this is what yields a flip-point curve."""
    out = []
    for r in claims:
        if r.get("type") not in ("QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE"):
            continue
        old = (r.get("value") or "").strip()
        if not is_pure_quantity(old):
            continue
        a = norm_num(old)
        if a is None or a == 0:
            continue
        if _YEAR.fullmatch(old.strip()):
            continue                       # a year is not a magnitude; see below
        for s in SCALES:
            new = fmt_like(old, a * s)
            text = substitute_in_claim(r["claim"], old, new)
            if not text:
                continue
            out.append({
                "base_claim_id": r["claim_id"], "type": r["type"],
                "subject": r.get("subject", ""), "property": r.get("property", ""),
                "injection_type": "scale", "magnitude": f"+{(s - 1) * 100:.0f}%",
                "original_value": old, "corrupted_value": new, "claim": text,
                "_base_claim": r.get("claim", ""),
                "notes": f"claimed value multiplied by {s}",
            })
    return out


def op_shift_year(claims: list[dict]) -> list[dict]:
    """Year shifts, graded. Kept separate from scaling: shifting 1914 by +5 is a
    5-year error, not a 0.26% error, and reporting it as the latter would be
    meaningless."""
    out = []
    for r in claims:
        if r.get("type") not in ("TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION"):
            continue
        claim = r.get("claim") or ""
        m = _YEAR.search((r.get("value") or "")) or _YEAR.search(claim)
        if not m:
            continue
        y = int(m.group(0))
        for d in YEAR_SHIFTS:
            new = str(y + d)
            if new in claim:
                continue                   # the shifted year already appears
            text = claim.replace(str(y), new, 1)
            if text == claim:
                continue
            out.append({
                "base_claim_id": r["claim_id"], "type": r["type"],
                "subject": r.get("subject", ""), "property": r.get("property", ""),
                "injection_type": "year_shift", "magnitude": f"+{d}y",
                "original_value": str(y), "corrupted_value": new, "claim": text,
                "notes": f"year shifted {y} -> {new}",
            })
    return out


def op_swap_source(claims: list[dict]) -> list[dict]:
    """CITATION: attribute the claim to a different real organisation.

    Tests the failure mode dual-emit exists to isolate -- real source, wrong
    attribution -- rather than a fabricated source.
    """
    orgs = ["WHO", "CDC", "IPCC", "FAO", "World Bank", "UNICEF", "IMF",
            "Lancet", "IRENA", "UNFCCC"]
    out = []
    for r in claims:
        if r.get("type") != "CITATION":
            continue
        claim = r.get("claim") or ""
        present = [o for o in orgs if o in claim]
        if not present:
            continue
        old = present[0]
        new = next((o for o in orgs if o != old and o not in claim), None)
        if not new:
            continue
        out.append({
            "base_claim_id": r["claim_id"], "type": "CITATION",
            "subject": r.get("subject", ""), "property": r.get("property", ""),
            "injection_type": "source_swap", "magnitude": "n/a",
            "original_value": old, "corrupted_value": new,
            "claim": claim.replace(old, new, 1),
            "notes": f"attribution moved {old} -> {new}; assertion unchanged",
        })
    return out


# ---------------------------------------------------------------------------
# External negatives: real, human-verified hallucinations
# ---------------------------------------------------------------------------

def sample_external(n_factscore: int, n_fever: int) -> list[dict]:
    """Pull genuinely-natural negatives from FActScore and FEVER.

    These matter because every synthetic negative above is a corruption of a true
    statement, which is a narrower distribution than real model error. FActScore's
    NS facts are actual LLM hallucinations that humans marked unsupported -- the
    closest available match to the target phenomenon.

    Caveats to carry into any result: FActScore is biography-only, so entity
    resolution is easier there than on this project's multi-domain corpus; and its
    labels are relative to a 2023 Wikipedia snapshot, not live sources. FEVER's
    REFUTES are human-written *mutations* of Wikipedia sentences -- large-scale and
    standard, but a different distribution again.
    """
    out = []
    fs = os.path.join(ROOT, "data", "factscore", "annotations", "factscore",
                      "data", "labeled")
    if os.path.isdir(fs):
        for fn in sorted(os.listdir(fs)):
            if not fn.endswith(".jsonl"):
                continue
            model = fn[:-6]
            taken = 0
            for line in open(os.path.join(fs, fn), encoding="utf-8"):
                if taken >= n_factscore:
                    break
                rec = json.loads(line)
                for ann in (rec.get("annotations") or []):
                    for fact in (ann.get("human-atomic-facts") or []):
                        if fact.get("label") == "NS" and taken < n_factscore:
                            out.append({
                                "source": f"factscore/{model}",
                                "claim": fact.get("text", ""),
                                "topic": rec.get("topic", ""),
                                "cat": ";".join(rec.get("cat") or []),
                                "label_native": "NS", "gold_verdict": "FALSE",
                                "notes": "human-verified unsupported atomic fact; "
                                         "biography domain; 2023 snapshot",
                            })
                            taken += 1
    fever = os.path.join(ROOT, "data", "fever", "raw", "paper_dev.jsonl")
    if os.path.isfile(fever):
        taken = 0
        for line in open(fever, encoding="utf-8"):
            if taken >= n_fever:
                break
            rec = json.loads(line)
            if rec.get("label") == "REFUTES":
                out.append({
                    "source": "fever/paper_dev", "claim": rec.get("claim", ""),
                    "topic": "", "cat": "", "label_native": "REFUTES",
                    "gold_verdict": "FALSE",
                    "notes": "human-written mutation of a Wikipedia sentence",
                })
                taken += 1
    return out


# ---------------------------------------------------------------------------

def validate(rows: list[dict],
             base_text: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """Reject any candidate that is not demonstrably a CHANGED claim.

    Last line of defence against the worst bug this script can have: emitting a
    row that is still TRUE while labelling it FALSE. When a verifier later
    disagrees with such a row, there is no way to tell a verifier bug from a label
    bug — so it would silently corrupt every downstream measurement.

    Three rejections, all found in real output:
      * claim identical to its base — the `"Cas9 protein and a guide RNA"` case,
        where the scaler found the 9 in "Cas9", multiplied by 1.01 and rounded
        back to 9;
      * claim differing only in whitespace/punctuation — `"September 15, 2008"`
        -> `"September 15 2008"`, where only a comma moved;
      * value unchanged after numeric normalisation, e.g. `"8,848"` -> `"8848"`.
    """
    def squash(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

    kept, rejected = [], []
    for r in rows:
        base = r.get("_base_claim") or base_text.get(r.get("base_claim_id", ""), "")
        why = None
        if not base:
            why = "base claim text not found"
        elif r["claim"].strip() == base.strip():
            why = "claim identical to base"
        elif squash(r["claim"]) == squash(base):
            why = "differs from base only in punctuation/whitespace"
        else:
            a, b = norm_num(r["original_value"]), norm_num(r["corrupted_value"])
            if a is not None and b is not None and a == b:
                why = "value unchanged after numeric normalisation"
            elif squash(r["original_value"]) == squash(r["corrupted_value"]):
                why = "value unchanged after normalisation"
            elif a is None and b is None:
                # Categorical swap: reject when one value CONTAINS the other, which
                # means they are near-synonyms rather than alternatives. Caught
                # "permanent member of the United Nations Security Council" ->
                # "permanent member", which left "China is a permanent member."
                # still TRUE. Applied to categorical values only: for numbers,
                # squash("6,190") is legitimately a substring of squash("61,900").
                so, sn = squash(r["original_value"]), squash(r["corrupted_value"])
                if so and sn and (so in sn or sn in so):
                    why = ("categorical values are nested (near-synonyms), so the "
                           "result may still be TRUE")
        (rejected if why else kept).append({**r, "_reject": why} if why else r)
    return kept, rejected


def write(rows: list[dict], per_type_cap: int | None) -> list[dict]:
    if per_type_cap:
        seen: collections.Counter = collections.Counter()
        kept = []
        for r in rows:
            k = (r["type"], r["injection_type"])
            if seen[k] < per_type_cap:
                kept.append(r)
                seen[k] += 1
        rows = kept
    for i, r in enumerate(rows, start=1):
        r["claim_id"] = f"SYN_{r['type'][:4]}_{i:03d}"
        r["synthetic"] = "TRUE"
        r["gold_type"] = r["type"]
        r["gold_verdict"] = "FALSE"
        r["secondary"] = "{}"
    cols = ["claim_id", "claim", "type", "subject", "property",
            "original_value", "corrupted_value", "injection_type", "magnitude",
            "secondary", "synthetic", "gold_type", "gold_verdict",
            "base_claim_id", "notes"]
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate gold-FALSE claims by corrupting gold-TRUE ones.")
    ap.add_argument("--cap", type=int, default=12,
                    help="max rows per (type, operator) pair (default 12)")
    ap.add_argument("--factscore", type=int, default=15,
                    help="natural negatives to sample per FActScore model")
    ap.add_argument("--fever", type=int, default=30,
                    help="natural negatives to sample from FEVER paper_dev")
    ap.add_argument("--show", type=int, default=8, help="examples to print")
    args = ap.parse_args()

    print("loading gold-TRUE claims...")
    claims = load_true_claims()
    print(f"  {len(claims)} gold-TRUE, non-synthetic claims available")
    d = collections.Counter(c.get("type", "?") for c in claims)
    print("  by type: " + ", ".join(f"{k} {v}" for k, v in sorted(d.items())))

    rows_cs, needs_manual = op_cross_substitute(claims)
    rows = (rows_cs + op_scale_number(claims)
            + op_shift_year(claims) + op_swap_source(claims))
    print(f"\ngenerated {len(rows)} candidate negatives before validation")

    base_text = {c["claim_id"]: c.get("claim", "") for c in claims}
    rows, rejected = validate(rows, base_text)
    print(f"validation: kept {len(rows)}, REJECTED {len(rejected)}")
    if rejected:
        for why, n in sorted(collections.Counter(
                r["_reject"] for r in rejected).items(), key=lambda x: -x[1]):
            print(f"   {n:>4}  {why}")
        print("  (each rejected row would have been a still-TRUE claim labelled "
              "FALSE)")
    rows = write(rows, args.cap)

    print(f"\nwrote {OUT}  ({len(rows)} rows)")
    print(f"  {'type':<18}{'operator':<20}{'n':>4}")
    for (t, op), n in sorted(collections.Counter(
            (r["type"], r["injection_type"]) for r in rows).items()):
        print(f"  {t:<18}{op:<20}{n:>4}")

    if needs_manual:
        seen = set()
        uniq = []
        for r in needs_manual:
            if r["claim_id"] not in seen:
                seen.add(r["claim_id"])
                uniq.append(r)
        with open(OUT_MANUAL, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(uniq[0].keys())
                               + ["AUTHORED_FALSE_CLAIM", "AUTHOR_NOTE"])
            w.writeheader()
            for r in uniq:
                w.writerow({**r, "AUTHORED_FALSE_CLAIM": "", "AUTHOR_NOTE": ""})
        print(f"\nwrote {OUT_MANUAL}  ({len(uniq)} text-valued claims)")
        print("  These CANNOT be corrupted automatically -- swapping text values")
        print("  across subjects yields nonsense or accidental truth. Author a")
        print("  false variant by hand in the AUTHORED_FALSE_CLAIM column.")
        for t, n in sorted(collections.Counter(r["type"] for r in uniq).items()):
            print(f"    {t:<20}{n:>4}")

    ext = sample_external(args.factscore, args.fever)
    if ext:
        with open(OUT_EXT, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(ext[0].keys()))
            w.writeheader()
            w.writerows(ext)
        print(f"\nwrote {OUT_EXT}  ({len(ext)} natural negatives)")
        for s, n in sorted(collections.Counter(r["source"] for r in ext).items()):
            print(f"  {s:<28}{n:>4}")

    print(f"\n--- {min(args.show, len(rows))} examples ---")
    for r in rows[:args.show]:
        print(f"\n[{r['claim_id']}] {r['type']} / {r['injection_type']} "
              f"({r['magnitude']})")
        print(f"  {r['original_value']!r} -> {r['corrupted_value']!r}")
        print(f"  {r['claim'][:118]}")

    print("\nREMINDER: every row here is synthetic=TRUE. Report results on these "
          "SEPARATELY\nfrom the 13 natural gold negatives -- a verifier that "
          "catches a substituted value\nhas shown something necessary but not "
          "sufficient for hallucination detection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
