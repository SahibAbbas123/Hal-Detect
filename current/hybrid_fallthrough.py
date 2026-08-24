#!/usr/bin/env python3
"""
Hybrid fall-through for TEMPORAL and ENTITY_ATTRIBUTE -- step (a).

Tier 1: Wikidata structured lookup (entity resolution -> `property_resolver`
        -> value comparison).
Tier 2: the notebook's existing Wikipedia-passage + NLI verifier (cell 57),
        consulted ONLY when tier 1 abstains.

WHY THIS EXISTS
---------------
After the 2026-08-21 entity-resolution fix, TEMPORAL and ENTITY_ATTRIBUTE both
sit at **0% coverage / 0% accuracy on Batch 3**. Every one of their 34 claims is
now an honest UNVERIFIABLE. That is a correct state -- the confident-wrong
verdicts are gone -- but neither verifier currently answers anything.
`property_resolver` lifts property coverage to 6/34. The remaining 28 are not
mapping failures; many are claims Wikidata simply does not model (durations,
sprint records, aggregate statistics). RELATIONAL already has a working text path
(80.8% on ~26 covered), so the obvious move is to let it catch what the knowledge
graph cannot reach.

NO REIMPLEMENTATION -- THIS IS AN ORCHESTRATOR
----------------------------------------------
Three things are injected rather than copied:

    verify_hybrid(row, cache, resolve_fn=..., tier2_fn=..., compare_fn=...)

* `resolve_fn(subject, ctx, cache) -> qid|None` -- the notebook's **fixed**
  `resolve_entity` (scored on the candidate's own label/alias/description,
  `RESOLUTION_THRESHOLD = 0.60`).
* `tier2_fn(row) -> dict|str|None` -- cell 57's `verify_relational`.
* `compare_fn` -- optional override for the tier-1 value comparison.

The NLI logic and the entity resolver are not duplicated here. Cell 57 and cells
69/75 own them, and this module must not become a second definition: the project
has already lost time to copies drifting apart (`temporal_verifier.py` vs cell
75; cells 67/69 and 73/75 still sitting side by side). `_read_verdict()` is
deliberately permissive about key names so cell 57 can change shape without
breaking this file.

**`resolve_fn` has no default, and that is a safety property, not an omission.**
`property_resolver.diagnose` resolves QIDs by taking the *first
`wbsearchentities` hit* -- fine inside a property-layer diagnostic, which is all
it claims to measure, but it is a close cousin of the heuristic that caused the
QID bug (Panama Canal -> Q498979 *Panama Canal Zone*; Rosetta Stone -> a British
punk band). If no resolver is supplied, tier 1 is **skipped entirely** rather
than falling back to first-hit. Never re-add a default here.

THE RISK THIS MODULE EXISTS TO CONTAIN
--------------------------------------
A fall-through's entire effect is **converting abstentions into verdicts** -- the
move that has damaged this project twice:

* the QID bug -- "accept the first candidate that has the property" bought
  coverage and produced confidently wrong verdicts on gold-TRUE claims;
* `property_resolver`'s first pass -- 47.1% coverage at ~31% precision,
  re-introducing ~11 confident-wrong verdicts.

Both times **coverage rose and precision collapsed**, and both times coverage was
the number looked at first. This module is therefore built to make the trade
visible rather than to maximise coverage.

There is also a hazard RELATIONAL does not face. TEMPORAL/EA claims are
`(subject, property, value)` assertions, and a Wikipedia lead paragraph about the
subject typically contains **several** dates or values. NLI models entail on
topical overlap, so a passage mentioning "Panama Canal", "1903" and "1914" can
entail *both* "completed in 1914" and "completed in 1903". Call this the
**date-adjacency trap**: the model is scored on relevance, not on which value the
claim picked. Three cheap non-NLI gates contain it:

1.  **Value-presence gate.** The claim's `value` must actually occur in the
    winning passage. Entailment without it is topical overlap -> UNVERIFIABLE.
2.  **Distractor gate.** If same-shape competing values also occur in that
    passage (other years; other numbers of similar magnitude), the evidence does
    not single out the claim -> UNVERIFIABLE.
3.  **Confidence ceiling.** `TIER2_CEILING < TIER1_FLOOR`, so risk-coverage
    curves rank structured evidence above textual inference and an operating
    point can be chosen that takes tier 1 only.

Tier 1 always wins; tier 2 may never overturn it. A Wikidata statement is
structured evidence, an entailment score is an inference over prose.

ACCURACY CANNOT VALIDATE THIS -- READ BEFORE QUOTING ANY NUMBER
--------------------------------------------------------------
TEMPORAL and ENTITY_ATTRIBUTE have **zero gold negatives across all 34 Batch 3
claims.** A fall-through that simply emitted TRUE for everything it touched would
score **100% accuracy**; coverage would look transformed and nothing would have
been learned.

So `--sensitivity` is not an extra, it is the only real test here. It perturbs
the value of each verified claim (1914 -> 1919, 8848 -> 12387) and requires the
verdict to **flip**. A path that still says TRUE after the value is wrong by
construction is measuring topical relevance and must not ship. Same reasoning as
`quantitative_verifier.py --sensitivity`, for the same structural reason: there
are no gold negatives to borrow.

STATUS: written 2026-08-22, **NEVER EXECUTED** (Bash classifier unavailable).
DELIBERATELY NOT INTEGRATED into cells 69/75 -- same hold-back as
`property_resolver.py`, and for the same reason: measure `--sensitivity` first.

USAGE
-----
    python current/hybrid_fallthrough.py --selftest      # offline, no network
    python current/hybrid_fallthrough.py --diagnose      # gates only (no resolver)
    python current/hybrid_fallthrough.py --sensitivity

A live end-to-end run happens by importing this module **in the notebook** and
passing the real `resolve_entity` and `verify_relational` in. The CLI cannot do
that, by design -- see the `resolve_fn` note above.

Reverse with: rm current/hybrid_fallthrough.py current/hybrid_b3_*.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter

import property_resolver as pr

HERE = os.path.dirname(os.path.abspath(__file__))
B3 = os.path.join(HERE, "haldetect_claims_b3_gold.csv")

# Tier-2 verdicts are capped below tier 1 so the two are separable on a
# risk-coverage curve and an operating point can exclude tier 2 entirely.
TIER1_FLOOR = 0.80
TIER1_MISMATCH = 0.70        # a mismatch is weaker than a match: see compare_tier1
TIER2_CEILING = 0.65
TIER2_CONTRADICTION = 0.60

# Semantic tier for ENTITY_ATTRIBUTE comparison, added 2026-08-24.
# EA_SEMANTIC_MATCH -> accept as a paraphrase match (TRUE).
# EA_SEMANTIC_NEAR  -> too close to call FALSE; abstain instead.
# The match confidence sits BELOW TIER1_FLOOR because a paraphrase match is
# weaker evidence than a lexical one: the graph asserts something related, not
# the claim verbatim.
EA_SEMANTIC_MATCH = 0.55
EA_SEMANTIC_NEAR = 0.33
EA_SEMANTIC_CONF = 0.74

HANDLED = ("TEMPORAL", "ENTITY_ATTRIBUTE")

_YEAR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
_NUM = re.compile(r"\b\d[\d,]*\.?\d*\b")

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"])}
_MONTHS.update({m[:3]: i + 1 for i, m in enumerate(list(_MONTHS))})


def _month_day(text: str):
    """(month, day) as ints from free text or an ISO timestamp; None if absent.

    Handles the three shapes that actually occur: "May 5, 1987", "5 March 2009",
    and Wikidata's "1987-03-05T00:00:00Z".
    """
    t = (text or "").lower()
    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})", t)
    if iso:
        mm, dd = int(iso.group(2)), int(iso.group(3))
        return (mm or None), (dd or None)
    for name, num in _MONTHS.items():
        m = re.search(rf"\b{name}[a-z]*\.?\s+(\d{{1,2}})\b", t)
        if m:
            return num, int(m.group(1))
        m = re.search(rf"\b(\d{{1,2}})\s+{name}[a-z]*\b", t)
        if m:
            return num, int(m.group(1))
    return None, None


# ---------------------------------------------------------------------------
# reading tier 2's answer without depending on its exact shape
# ---------------------------------------------------------------------------

VERDICT_KEYS = ("verdict", "label", "result", "prediction", "pred")
CONF_KEYS = ("confidence", "conf", "score", "entailment", "entail_score")
PASSAGE_KEYS = ("passage", "evidence", "evidence_text", "best_passage",
                "passages", "context", "retrieved")

_NORMALISE = {
    "SUPPORTED": "TRUE", "SUPPORT": "TRUE", "ENTAILMENT": "TRUE",
    "ENTAILED": "TRUE", "TRUE": "TRUE",
    "REFUTED": "FALSE", "CONTRADICTION": "FALSE", "CONTRADICTED": "FALSE",
    "FALSE": "FALSE",
    "NEI": "UNVERIFIABLE", "NOT ENOUGH INFO": "UNVERIFIABLE",
    "NEUTRAL": "UNVERIFIABLE", "UNVERIFIABLE": "UNVERIFIABLE",
    "UNKNOWN": "UNVERIFIABLE", "ABSTAIN": "UNVERIFIABLE",
}


def _read_verdict(res) -> tuple[str, float, str]:
    """Pull (verdict, confidence, passage) out of whatever tier 2 returned.

    Permissive by design: cell 57 owns that shape. An unrecognised verdict
    becomes UNVERIFIABLE -- failing closed, never open.
    """
    if res is None:
        return "UNVERIFIABLE", 0.0, ""
    if isinstance(res, str):
        return _NORMALISE.get(res.strip().upper(), "UNVERIFIABLE"), 0.0, ""
    if not isinstance(res, dict):
        return "UNVERIFIABLE", 0.0, ""

    verdict = "UNVERIFIABLE"
    for k in VERDICT_KEYS:
        if k in res and res[k] is not None:
            verdict = _NORMALISE.get(str(res[k]).strip().upper(), "UNVERIFIABLE")
            break

    conf = 0.0
    for k in CONF_KEYS:
        if k in res and res[k] is not None:
            try:
                conf = float(res[k])
                break
            except (TypeError, ValueError):
                continue
    conf = min(1.0, max(0.0, conf))

    passage = ""
    for k in PASSAGE_KEYS:
        if k in res and res[k]:
            v = res[k]
            if isinstance(v, str):
                passage = v
            elif isinstance(v, (list, tuple)):
                parts = []
                for item in v:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, (list, tuple)) and item:
                        parts.append(str(item[0]))
                    elif isinstance(item, dict):
                        parts.append(str(item.get("text") or item.get("passage") or ""))
                passage = "\n".join(p for p in parts if p)
            if passage:
                break
    return verdict, conf, passage


# ---------------------------------------------------------------------------
# tier 1: turning matched statement values into a verdict
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def compare_tier1(claimed: str, values: list[str],
                  claim_type: str, sim_fn=None) -> tuple[str, float, str]:
    """Compare the claimed value against a matched property's Wikidata values.

    `property_resolver` stops at "here are the values for the matched PID" -- it
    never produces a verdict. This is that missing step, kept deliberately
    conservative.

    On the asymmetry: a **match** is strong evidence (the graph asserts exactly
    this), but a **mismatch** is weaker, because Wikidata is incomplete and
    properties are often multi-valued -- the claim can be true and simply absent.
    So a mismatch returns FALSE at `TIER1_MISMATCH`, below a match's
    `TIER1_FLOOR`, and says so in the reason. Cells 69/75 already take this risk;
    this only makes it explicit and ranks it lower on the risk-coverage curve.

    `sim_fn(a, b) -> float` is an OPTIONAL semantic similarity function, injected
    rather than imported so this module's 35 offline selftests need no model. When
    it is None the comparator behaves exactly as before.
    """
    vals = [str(v) for v in (values or []) if str(v).strip()]
    if not vals:
        return "UNVERIFIABLE", 0.0, "property matched but has no value"
    shown = ", ".join(vals[:3])[:80]

    if claim_type == "TEMPORAL":
        want = set(_YEAR.findall(claimed or ""))
        got: set[str] = set()
        for v in vals:
            got |= set(_YEAR.findall(v))
        if not want:
            return ("UNVERIFIABLE", 0.0,
                    f"no year in the claimed value {claimed!r} -- not a date "
                    f"claim; check routing (TEMPORAL over-fires at 55.6% precision)")
        if not got:
            return "UNVERIFIABLE", 0.0, f"no year in Wikidata values [{shown}]"
        if want & got:
            # FIX 2026-08-24: a year match alone is NOT enough when the claim
            # asserts a full date. FS_0094 said "born on May 5, 1987" while
            # Wikidata holds 1987-03-05 -- same year, different month -- and the
            # year-only comparison returned TRUE on a genuinely false claim.
            #
            # The comparison precision is set by the CLAIM's precision, not by
            # Wikidata's: if the claim only asserts a year, demanding month/day
            # agreement would invent a requirement the claim never made.
            cm, cd = _month_day(claimed)
            if cm:
                yr = sorted(want & got)[0]
                for v in vals:
                    if yr not in v:
                        continue
                    vm, vd = _month_day(v)
                    if not vm:
                        continue              # Wikidata has year granularity only
                    if vm == cm and (cd is None or vd is None or cd == vd):
                        return ("TRUE", TIER1_FLOOR,
                                f"full date matches Wikidata {v!r}")
                    return ("FALSE", TIER1_MISMATCH,
                            f"year {yr} matches but the date does not: claimed "
                            f"month/day {cm}/{cd} vs Wikidata {vm}/{vd} [{shown}]")
            return ("TRUE", TIER1_FLOOR,
                    f"year {sorted(want & got)[0]} matches Wikidata [{shown}]")
        return ("FALSE", TIER1_MISMATCH,
                f"claimed year(s) {sorted(want)} not among Wikidata "
                f"{sorted(got)} [{shown}] -- note Wikidata may be incomplete")

    # ENTITY_ATTRIBUTE: lexical containment either direction.
    c = _norm(claimed)
    if not c:
        return "UNVERIFIABLE", 0.0, "claimed value is empty after normalisation"
    for v in vals:
        n = _norm(v)
        if not n:
            continue
        if c == n or c in n or n in c:
            return "TRUE", TIER1_FLOOR, f"value matches Wikidata {v!r}"
    ctoks = {t for t in c.split() if len(t) > 3}
    for v in vals:
        vtoks = {t for t in _norm(v).split() if len(t) > 3}
        if ctoks and vtoks and len(ctoks & vtoks) >= max(1, len(ctoks) // 2):
            return ("TRUE", TIER1_FLOOR,
                    f"value overlaps Wikidata {v!r} on {sorted(ctoks & vtoks)}")

    # FIX 2026-08-24: semantic tier before declaring FALSE.
    #
    # Token matching produced 7 of 12 wrong verdicts on the FActScore block, all
    # the same shape -- the claim states an INSTANCE or PARAPHRASE, Wikidata
    # stores a CATEGORY, and they share no token:
    #     "He was a columnist."      vs  journalist, opinion journalist
    #     "He sang in a group."      vs  singer
    #     "had a political career."  vs  politician
    #     "a fervent mix of rap"     vs  hip-hop
    # Every one of those is semantically TRUE and was reported FALSE.
    #
    # So a near-miss is treated as UNVERIFIABLE, not FALSE. That is the honest
    # reading: "Wikidata says something closely related but not identical" is
    # evidence of a granularity mismatch, not evidence of falsehood -- the same
    # principle as the ISRO mismatch guard.
    if sim_fn is not None:
        best, best_v = 0.0, ""
        for v in vals:
            try:
                s = float(sim_fn(claimed, v))
            except Exception:      # noqa: BLE001
                continue
            if s > best:
                best, best_v = s, v
        if best >= EA_SEMANTIC_MATCH:
            return ("TRUE", EA_SEMANTIC_CONF,
                    f"semantic match to Wikidata {best_v!r} (sim {best:.2f}) -- "
                    f"paraphrase, not lexical")
        if best >= EA_SEMANTIC_NEAR:
            return ("UNVERIFIABLE", 0.0,
                    f"claimed {claimed!r} is semantically near Wikidata "
                    f"{best_v!r} (sim {best:.2f}) -- category-vs-instance "
                    f"granularity, too close to call FALSE")

    return ("FALSE", TIER1_MISMATCH,
            f"claimed {claimed!r} does not match Wikidata [{shown}] -- note "
            f"Wikidata may be incomplete or the property multi-valued")


# ---------------------------------------------------------------------------
# tier 2: the three non-NLI gates
# ---------------------------------------------------------------------------

def _digits(s: str) -> str:
    return re.sub(r"[,\s]", "", s or "")


def value_grounded(value: str, passage: str) -> tuple[bool, str]:
    """Gate 1. Does the claim's asserted value actually occur in the evidence?

    An entailment with the asserted value absent from the passage is topical
    overlap, not verification.
    """
    v, p = (value or "").strip(), (passage or "")
    if not v or not p:
        return False, "no value or no passage"

    years = _YEAR.findall(v)
    if years:
        hit = [y for y in years if y in p]
        if hit:
            return True, f"year {hit[0]} present in passage"
        return False, f"year(s) {years} absent from passage"

    nums = _NUM.findall(v)
    if nums:
        pd_ = _digits(p)
        hit = [n for n in nums if _digits(n) in pd_]
        if hit:
            return True, f"number {hit[0]} present in passage"
        return False, f"number(s) {nums} absent from passage"

    words = re.findall(r"[a-z]{4,}", v.lower())
    if not words:
        return False, "value has no comparable content"
    pl = p.lower()
    present = [w for w in words if w in pl]
    if len(present) >= max(1, (len(words) + 1) // 2):
        return True, f"{len(present)}/{len(words)} value terms present"
    return False, f"only {len(present)}/{len(words)} value terms present"


def distractors(value: str, passage: str, claim_type: str) -> tuple[int, str]:
    """Gate 2 -- the date-adjacency trap. Same-shape competing values in the same
    passage mean the evidence does not single out this claim, however confident
    the NLI score."""
    v, p = (value or "").strip(), (passage or "")
    if not v or not p:
        return 0, ""

    years = set(_YEAR.findall(v))
    if years or claim_type == "TEMPORAL":
        others = sorted(set(_YEAR.findall(p)) - years)
        if others:
            shown = ", ".join(others[:6]) + ("..." if len(others) > 6 else "")
            return len(others), f"{len(others)} other year(s) in passage: {shown}"
        return 0, ""

    nums = _NUM.findall(v)
    if nums:
        try:
            target = float(_digits(nums[0]))
        except ValueError:
            return 0, ""
        near = []
        for cand in _NUM.findall(p):
            try:
                c = float(_digits(cand))
            except ValueError:
                continue
            if c == target or target == 0:
                continue
            if 0.2 <= c / target <= 5.0:      # same order of magnitude
                near.append(cand)
        near = sorted(set(near))
        if near:
            return len(near), (f"{len(near)} same-magnitude number(s): "
                               f"{', '.join(near[:6])}")
    return 0, ""


def gate_tier2(row: dict, verdict: str, conf: float,
               passage: str) -> tuple[str, float, str]:
    """Apply gates 1-3. Fails closed in every ambiguous case."""
    ctype = (row.get("gold_type") or row.get("type") or "").strip().upper()
    value = row.get("value", "")

    if verdict == "UNVERIFIABLE":
        return "UNVERIFIABLE", 0.0, "tier2 abstained"

    if not passage:
        return ("UNVERIFIABLE", 0.0,
                "tier2 returned no passage -- gates cannot be applied, so the "
                "verdict is not trusted")

    grounded, gdetail = value_grounded(value, passage)

    if verdict == "FALSE":
        # Contradiction with the value absent is the coherent FALSE case: we
        # reached the subject's own page and the claimed value is not there.
        if not grounded:
            return ("FALSE", min(TIER2_CONTRADICTION, max(conf, 0.5)),
                    f"tier2 contradiction, value absent from evidence ({gdetail})")
        return ("UNVERIFIABLE", 0.0,
                f"tier2 said FALSE but the claimed value IS present ({gdetail}) "
                f"-- incoherent, not trusted")

    if not grounded:
        return ("UNVERIFIABLE", 0.0,
                f"gate 1: entailment without the asserted value in evidence "
                f"({gdetail}) -- topical-overlap risk")

    n_dist, ddetail = distractors(value, passage, ctype)
    if n_dist:
        return ("UNVERIFIABLE", 0.0,
                f"gate 2: evidence does not single out the claim -- {ddetail}")

    return ("TRUE", min(TIER2_CEILING, max(conf, 0.4)),
            f"gate 1+2 passed ({gdetail}); confidence capped at "
            f"{TIER2_CEILING} because evidence is textual, not structured")


# ---------------------------------------------------------------------------
# the orchestrator
# ---------------------------------------------------------------------------

def verify_hybrid(row: dict, cache: dict, resolve_fn=None, tier2_fn=None,
                  compare_fn=None) -> dict:
    """Tier 1 (Wikidata) then, only on abstention, tier 2 (injected NLI path).

    `resolve_fn` and `tier2_fn` both default to None, and with both None this
    reduces to a pure abstain -- which is what makes staged integration safe.
    Do NOT add a first-search-hit default for `resolve_fn`; see module docstring.
    """
    ctype = (row.get("gold_type") or row.get("type") or "").strip().upper()
    compare = compare_fn or compare_tier1
    out = {
        "claim_id": row.get("claim_id", ""),
        "claim_type": ctype,
        "subject": row.get("subject", ""),
        "property": row.get("property", ""),
        "value": row.get("value", ""),
        "gold_verdict": row.get("gold_verdict", ""),
        "tier": "none",
        "verdict": "UNVERIFIABLE",
        "confidence": 0.0,
        "reason": "",
        "qid": "",
        "pid": "",
        "tier1_gap": "",
        "tier2_raw": "",
    }
    if ctype not in HANDLED:
        out["reason"] = f"{ctype} is not routed here"
        return out

    # --- tier 1 -----------------------------------------------------------
    if resolve_fn is None:
        out["tier1_gap"] = ("no resolver supplied -- tier 1 skipped by design "
                            "(never fall back to first-search-hit)")
    else:
        try:
            qid = resolve_fn(row.get("subject", ""), row.get("claim", ""), cache)
            if isinstance(qid, (tuple, list)) and qid:
                qid = qid[0]
            qid = (qid or "") if isinstance(qid, str) else ""
            out["qid"] = qid
            if not qid:
                out["tier1_gap"] = "entity not resolved above threshold"
            else:
                t1 = pr.resolve_property_values(
                    qid, row.get("property", ""), ctype, cache,
                    row.get("claim", ""))
                out["pid"] = t1.get("pid") or ""
                if not t1.get("pid"):
                    out["tier1_gap"] = f"property not matched: {t1.get('detail', '')}"
                else:
                    v, c, r = compare(row.get("value", ""),
                                      t1.get("values", []), ctype)
                    if v in ("TRUE", "FALSE"):
                        out.update(tier="wikidata", verdict=v, confidence=c,
                                   reason=f"{t1['pid']}: {r}")
                        return out
                    out["tier1_gap"] = f"{t1['pid']}: {r}"
        except Exception as exc:                # noqa: BLE001
            out["tier1_gap"] = f"tier1 error: {type(exc).__name__}: {exc}"

    # --- tier 2 -----------------------------------------------------------
    if tier2_fn is None:
        out["reason"] = (f"tier1 gap; tier2 not supplied "
                         f"({out['tier1_gap']})")
        return out

    try:
        raw = tier2_fn(row)
    except Exception as exc:                    # noqa: BLE001
        out["reason"] = f"tier2 error: {type(exc).__name__}: {exc}"
        return out

    t2v, t2c, passage = _read_verdict(raw)
    out["tier2_raw"] = f"{t2v}@{t2c:.2f}"
    gv, gc, gr = gate_tier2(row, t2v, t2c, passage)
    out.update(tier="nli" if gv in ("TRUE", "FALSE") else "none",
               verdict=gv, confidence=gc, reason=gr)
    return out


# ---------------------------------------------------------------------------
# diagnose / sensitivity
# ---------------------------------------------------------------------------

def _load_b3() -> list[dict]:
    with open(B3, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows
            if (r.get("gold_type") or "").strip().upper() in HANDLED]


def diagnose(resolve_fn=None, tier2_fn=None, limit: int | None = None) -> int:
    rows = _load_b3()
    rows = rows[:limit] if limit else rows
    print(f"{len(rows)} TEMPORAL+EA claims from Batch 3")
    if resolve_fn is None and tier2_fn is None:
        print("NOTE: neither tier is wired from the CLI, so every claim must")
        print("      abstain. This run checks plumbing and the tier1_gap")
        print("      taxonomy, NOT coverage. A live run happens in the notebook.")

    cache = pr.load_cache()
    out = []
    for i, r in enumerate(rows, 1):
        res = verify_hybrid(r, cache, resolve_fn, tier2_fn)
        out.append(res)
        print(f"  [{i}/{len(rows)}] {res['claim_id']:<12} {res['claim_type'][:4]} "
              f"{res['tier']:<9} {res['verdict']:<13} {res['confidence']:.2f}  "
              f"{(res['reason'] or res['tier1_gap'])[:66]}")
    pr.save_cache(cache)

    path = os.path.join(HERE, "hybrid_b3_diagnostic.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\nwrote {path}")

    tiers = Counter(r["tier"] for r in out)
    n = len(out)
    covered = [r for r in out if r["verdict"] in ("TRUE", "FALSE")]
    print("\n-- Coverage attribution (action item #8: tiers reported separately) --")
    for label, key in (("tier1 wikidata", "wikidata"), ("tier2 nli", "nli"),
                       ("abstained", "none")):
        print(f"  {label:<16}{tiers[key]:>3}/{n}  ({tiers[key]/n:.1%})")
    print(f"  {'total coverage':<16}{len(covered):>3}/{n}  ({len(covered)/n:.1%})")

    print("\n-- Why tier 1 abstained (the actionable list) --")
    for reason, c in Counter(
            (r["tier1_gap"].split(":")[0] or "n/a") for r in out
            if r["tier"] != "wikidata").most_common():
        print(f"  {c:>3}  {reason}")

    gold_neg = sum(1 for r in out if r["gold_verdict"] == "FALSE")
    correct = sum(1 for r in covered if r["verdict"] == r["gold_verdict"])
    if covered:
        print(f"\n  accuracy on covered = {correct}/{len(covered)} "
              f"= {correct/len(covered):.1%}")
    print(f"  gold negatives in this slice = {gold_neg}")
    if gold_neg == 0:
        print("\n  !! THAT ACCURACY IS NOT EVIDENCE. Zero gold negatives here, so")
        print("     an always-TRUE fall-through scores 100%. Run --sensitivity.")

    try:
        import metrics
        metrics.report([r["gold_verdict"] for r in out],
                       [r["verdict"] for r in out],
                       [r["confidence"] for r in out],
                       title="Hybrid TEMPORAL+EA on Batch 3")
    except ImportError:
        print("  (metrics.py not importable; skipped the full table)")
    return 0


def _perturb(value: str) -> str | None:
    """Change the value to something certainly wrong, preserving its shape."""
    years = _YEAR.findall(value or "")
    if years:
        y = years[0]
        return value.replace(y, str(int(y) + 5), 1)
    nums = _NUM.findall(value or "")
    if nums:
        n = nums[0]
        try:
            scaled = float(_digits(n)) * 1.4
        except ValueError:
            return None
        rep = f"{scaled:,.0f}" if "," in n else (
            f"{scaled:.0f}" if "." not in n else f"{scaled:.2f}")
        return value.replace(n, rep, 1)
    return None


def sensitivity(resolve_fn=None, tier2_fn=None, limit: int | None = None) -> int:
    """THE test. Perturb each verified value; the verdict must flip.

    A perturbed claim's label is certain by construction, so this measures
    discrimination with zero gold negatives. If a path keeps returning TRUE after
    the value is changed, it is scoring topical relevance and must not ship.
    """
    rows = _load_b3()
    rows = rows[:limit] if limit else rows
    cache = pr.load_cache()

    print("Baseline pass (which claims are verified at all)...")
    base = [verify_hybrid(r, cache, resolve_fn, tier2_fn) for r in rows]
    verified = [(r, b) for r, b in zip(rows, base) if b["verdict"] == "TRUE"]
    print(f"  {len(verified)} claim(s) returned TRUE and can be perturbed")
    if not verified:
        pr.save_cache(cache)
        print("\nNothing verified TRUE -- no discrimination to measure yet.")
        print("Coverage must exist before sensitivity means anything. From the")
        print("CLI that is expected: neither tier is wired. Run this from the")
        print("notebook with resolve_entity and verify_relational passed in.")
        return 0

    print("\nPerturbed pass (each value changed to a certainly-wrong one)...")
    results = []
    for r, b in verified:
        bad = _perturb(r.get("value", ""))
        if bad is None:
            print(f"  {r.get('claim_id',''):<12} SKIP (not perturbable: "
                  f"{r.get('value','')!r})")
            continue
        prow = dict(r)
        prow["value"] = bad
        if prow.get("claim") and r.get("value"):
            prow["claim"] = prow["claim"].replace(r["value"], bad, 1)
        after = verify_hybrid(prow, cache, resolve_fn, tier2_fn)
        flipped = after["verdict"] != "TRUE"
        results.append({
            "claim_id": r.get("claim_id", ""), "tier": b["tier"],
            "value": r.get("value", ""), "perturbed": bad,
            "before": b["verdict"], "after": after["verdict"],
            "flipped": str(flipped).lower(), "after_reason": after["reason"],
        })
        print(f"  {r.get('claim_id',''):<12} {b['tier']:<9} "
              f"{r.get('value','')!r:>22} -> {bad!r:<22} "
              f"{b['verdict']} -> {after['verdict']}  "
              f"{'FLIP' if flipped else '*** NO FLIP ***'}")
    pr.save_cache(cache)

    if not results:
        print("\nNo perturbable values. Inconclusive.")
        return 0

    path = os.path.join(HERE, "hybrid_b3_sensitivity.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nwrote {path}")

    for tier in ("wikidata", "nli"):
        sub = [r for r in results if r["tier"] == tier]
        if not sub:
            continue
        flips = sum(1 for r in sub if r["flipped"] == "true")
        print(f"\n  {tier:<9} flip rate {flips}/{len(sub)} = {flips/len(sub):.1%}")
        if tier == "nli" and flips < len(sub):
            print("     *** The tier-2 path returned TRUE for a value wrong by")
            print("         construction. It is scoring topical relevance, not")
            print("         truth. DO NOT INTEGRATE.")
    print("\n  Caveat: synthetic perturbations are not real hallucinations. A high")
    print("  flip rate is necessary for shipping, not sufficient.")
    return 0


# ---------------------------------------------------------------------------
# selftest -- fully offline
# ---------------------------------------------------------------------------

PANAMA = ("The Panama Canal is an artificial waterway in Panama. The Panama "
          "Canal Zone was created in 1903. Construction was completed and the "
          "canal opened on August 15, 1914.")
ROSETTA = ("The Rosetta Stone is a stele of granodiorite inscribed with three "
           "versions of a decree issued in 196 BC.")


def _selftest() -> int:
    fails = 0

    def check(name, got, want):
        nonlocal fails
        ok = got == want
        fails += (not ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got!r}"
              f"{'' if ok else f'  (want {want!r})'}")

    print("=== _read_verdict tolerance (cell 57 owns its own shape) ===")
    check("dict verdict", _read_verdict({"verdict": "TRUE", "confidence": 0.9})[0], "TRUE")
    check("label key", _read_verdict({"label": "SUPPORTED"})[0], "TRUE")
    check("NLI contradiction", _read_verdict({"verdict": "CONTRADICTION"})[0], "FALSE")
    check("neutral", _read_verdict({"verdict": "NEUTRAL"})[0], "UNVERIFIABLE")
    check("bare string", _read_verdict("REFUTED")[0], "FALSE")
    check("None", _read_verdict(None)[0], "UNVERIFIABLE")
    check("junk fails closed", _read_verdict({"verdict": "WAT"})[0], "UNVERIFIABLE")
    check("passage from (text, score) list", _read_verdict(
        {"verdict": "TRUE", "passages": [("hello world", 0.9)]})[2], "hello world")

    print("\n=== compare_tier1 -- the step property_resolver does NOT do ===")
    check("year match", compare_tier1("1914", ["1914-08-15"], "TEMPORAL")[0], "TRUE")
    check("year mismatch", compare_tier1("1903", ["1914-08-15"], "TEMPORAL")[0], "FALSE")
    check("mismatch ranked below match",
          compare_tier1("1903", ["1914-08-15"], "TEMPORAL")[1] < TIER1_FLOOR, True)
    check("empty values abstain", compare_tier1("1914", [], "TEMPORAL")[0],
          "UNVERIFIABLE")
    check("non-date TEMPORAL claim abstains (routing smell)",
          compare_tier1("1,500 years", ["1914"], "TEMPORAL")[0], "UNVERIFIABLE")
    check("EA exact", compare_tier1("granodiorite", ["granodiorite"],
                                    "ENTITY_ATTRIBUTE")[0], "TRUE")
    check("EA substring", compare_tier1("granodiorite",
                                        ["dark grey granodiorite stele"],
                                        "ENTITY_ATTRIBUTE")[0], "TRUE")
    check("EA mismatch", compare_tier1("limestone", ["granodiorite"],
                                       "ENTITY_ATTRIBUTE")[0], "FALSE")

    print("\n=== gate 1: value-presence ===")
    check("year present", value_grounded("1914", PANAMA)[0], True)
    check("year absent", value_grounded("1888", PANAMA)[0], False)
    check("string present", value_grounded("granodiorite", ROSETTA)[0], True)
    check("string absent", value_grounded("limestone", ROSETTA)[0], False)
    check("comma number", value_grounded("8,848 m", "rises to 8848 metres")[0], True)

    print("\n=== gate 2: the date-adjacency trap ===")
    n, d = distractors("1914", PANAMA, "TEMPORAL")
    check("competing years found", n > 0, True)
    print(f"        detail: {d}")
    check("clean passage has no competitors",
          distractors("1914", "The canal opened in 1914.", "TEMPORAL")[0], 0)

    print("\n=== the trap, end to end ===")
    # The real regression this module exists to prevent: NLI entails a WRONG
    # year off a passage that happens to contain it.
    wrong = {"gold_type": "TEMPORAL", "value": "1903", "subject": "Panama Canal"}
    v, _, r = gate_tier2(wrong, "TRUE", 0.95, PANAMA)
    check("wrong-but-present year REFUSED", v, "UNVERIFIABLE")
    print(f"        reason: {r}")

    ok = {"gold_type": "TEMPORAL", "value": "1914", "subject": "Panama Canal"}
    v2, c2, _ = gate_tier2(ok, "TRUE", 0.95, "The canal opened in 1914.")
    check("clean evidence ACCEPTED", v2, "TRUE")
    check("tier2 confidence capped", c2 <= TIER2_CEILING, True)
    check("ceiling below tier-1 floor", TIER2_CEILING < TIER1_FLOOR, True)
    check("no passage => not trusted",
          gate_tier2(ok, "TRUE", 0.99, "")[0], "UNVERIFIABLE")
    check("coherent FALSE accepted",
          gate_tier2({"gold_type": "ENTITY_ATTRIBUTE", "value": "limestone"},
                     "FALSE", 0.8, ROSETTA)[0], "FALSE")
    check("incoherent FALSE refused",
          gate_tier2({"gold_type": "ENTITY_ATTRIBUTE", "value": "granodiorite"},
                     "FALSE", 0.8, ROSETTA)[0], "UNVERIFIABLE")

    print("\n=== perturbation preserves shape ===")
    check("year +5", _perturb("1914"), "1919")
    check("date string", _perturb("August 15, 1914"), "August 15, 1919")
    check("comma number scaled", _perturb("8,848"), "12,387")
    check("unperturbable string", _perturb("granodiorite"), None)

    print("\n=== no tiers wired => must abstain, never invent coverage ===")
    res = verify_hybrid({"gold_type": "TEMPORAL", "subject": "Panama Canal",
                         "property": "opening_year", "value": "1914"}, {})
    check("verdict", res["verdict"], "UNVERIFIABLE")
    check("tier", res["tier"], "none")
    check("gap names the reason", "no resolver supplied" in res["tier1_gap"], True)

    print(f"\n{'ALL PASS' if not fails else f'{fails} FAILURE(S)'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="offline, no network")
    ap.add_argument("--diagnose", action="store_true",
                    help="plumbing + tier1_gap taxonomy (tiers not wired from CLI)")
    ap.add_argument("--sensitivity", action="store_true",
                    help="perturbation test -- the only real validation here")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    limit = args.limit or None
    if args.selftest:
        return _selftest()
    # Both tiers are None from the CLI by design. `resolve_entity` (cells 69/75)
    # and `verify_relational` (cell 57) live in the notebook; a live run happens
    # by importing this module there and passing them in. Defaulting `resolve_fn`
    # to a first-search-hit lookup would reintroduce the QID bug.
    if args.diagnose:
        return diagnose(None, None, limit)
    if args.sensitivity:
        return sensitivity(None, None, limit)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
