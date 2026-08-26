#!/usr/bin/env python3
"""RQ2 for QUANTITATIVE: routed verifier vs non-routed baseline, both classes.

WHY THIS SCRIPT EXISTS
----------------------
RQ2 asks whether taxonomy routing beats one generic verifier. Until now the
QUANTITATIVE answer was unquotable for a specific reason: the routed verifier had
been measured only on Batch 3, whose 29 QUANTITATIVE claims are 28 TRUE / 1 FALSE
(and that one FALSE is Wikidata-unreachable in principle). A verifier scoring 8/8
on an all-positive covered set cannot be distinguished from an unconditional
"TRUE". The number was real but carried no information about detection.

The synthetic negatives close that gap: 24 gold-FALSE QUANTITATIVE claims, on
which an unconditional "TRUE" scores 0.0%. Running the routed verifier there, and
combining with the Batch 3 positives, gives the first QUANTITATIVE measurement in
the project where both classes are represented.

THREE POPULATIONS, WHICH ARE NOT INTERCHANGEABLE
------------------------------------------------
  [1] all 24 negatives      -- valid for the ROUTED verifier alone. It reads
                               Wikidata `quantity` statements and never touches
                               the NLI cache, so the cache collision below cannot
                               reach it.
  [2] the 15 cache-clean    -- the only population a PAIRED routed-vs-baseline
      negatives                comparison may use. 9 of the 24 were proven
                               (2026-08-25) to have read their *base claim's*
                               cached NLI scores through phase3d's
                               `nli__{claim[:60]}__{passage[:40]}` key: the
                               perturbed claim and its original share a key
                               whenever the changed number sits past character 60.
                               Confirmed by bit-identical entail/contradict
                               floats, with 0 of 69 non-colliding rows matching as
                               a control. Those 9 rows are not evidence about the
                               baseline.
  [3] 29 positives + 24     -- both classes present. This is the only population
      negatives                that can support an F1(FALSE) or an MCC.

DIRECTION OF THE CORRECTION
---------------------------
Every corrupt QUANTITATIVE row inherited a gold-TRUE original's TRUE verdict, so
it was scored as a baseline MISS the baseline never actually made. The
uncorrected column therefore UNDERSTATES the baseline and flatters routing.
Correcting it moves the comparison against our own system -- which is why it is
corrected here rather than left alone.

BASELINE OPERATING POINT
------------------------
The baseline is reported at BOTH phase3d's shipped (0.50/0.40) and the swept
optimum (0.35/0.30). The shipped point is strictly dominated on the natural 356
(threshold_sweep, 2026-08-23), so quoting only it would credit routing with a gap
that is really one badly set constant -- a strawman the committed spec forbids.
The threshold rule itself is IMPORTED from threshold_sweep, not retyped, so both
systems' verdicts come from one implementation.

Offline. Zero model calls, zero network. Recomputes everything from cached CSVs.
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M                          # noqa: E402
from threshold_sweep import verdicts as bl_verdicts   # noqa: E402  (one impl only)

ROOT = os.path.dirname(HERE)

# Routed verifier output. The Batch 3 file prefixes its own columns with `q_`;
# the negatives file does the same. Both are normalised through `pred()`.
ROUTED_POS = os.path.join(HERE, "quantitative_b3_results.csv")
ROUTED_NEG = os.path.join(
    HERE, "quantitative_negatives_verifier_quantitative_all_results.csv")

# Non-routed baseline output (phase3d code path, no type filter).
BASE_POS = os.path.join(HERE, "nonrouted_baseline_results.csv")
BASE_NEG = os.path.join(HERE, "nonrouted_negatives_results.csv")

SHIPPED = (0.50, 0.40)
TUNED = (0.35, 0.30)

# A SECOND collision class, found 2026-08-25 after the first audit.
#
# That audit asked "did this negative inherit its BASE claim's scores?" It never
# asked whether two NEGATIVES collide with each other -- and they do: two
# perturbations of one base, both changing a number past character 60, share a
# `claim[:60]` and therefore a cache key. SYN_QUAN_030 and 031 both carry
# entail=0.3594 contradict=0.4227 and both come from base Q2_C11, while neither
# matches Q2_C11's own scores (0.7222/0.4430).
#
# These rows are not WRONG -- one of them is a genuine NLI answer -- but they are
# not INDEPENDENT. The baseline was asked once and the answer counted twice, so a
# detection count built from both overstates its effective n by one. Which of the
# pair populated the cache is not recoverable from the artifact, so one is dropped
# arbitrarily and the figure is reported both ways.
#
# COMPUTED as of Step 34, not hardcoded. This was `{"SYN_QUAN_031"}` written by
# hand, which happened to be right only because the class-(a) rows are already
# excluded upstream -- 7 QUANTITATIVE rows are duplicate reads, but 6 of them are
# also fabricated and gone by the time this set is applied. Relying on that
# coincidence is how the count drifted across three audits.
# `negatives_cache_audit.py --selftest` asserts this still resolves to {031}.
from negatives_cache_audit import Audit  # noqa: E402

_AUDIT = Audit()
DUP_READ = {r["claim_id"] for r in _AUDIT.tier("clean")
            if r["type"] == "QUANTITATIVE" and r["claim_id"] in _AUDIT.duplicate}

VERDICTS = ("TRUE", "FALSE", "UNVERIFIABLE")


# --------------------------------------------------------------------------- io

def load(path: str) -> list[dict]:
    if not os.path.isfile(path):
        raise SystemExit(f"missing input: {os.path.relpath(path, ROOT)}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pred(row: dict) -> str:
    """The verifier's verdict, whichever column the file happens to use.

    `quantitative_verifier.py` writes `q_verdict`; the baseline writes `verdict`.
    Reading one and assuming the other is how this comparison first crashed.
    """
    v = (row.get("q_verdict") or row.get("verdict") or "").strip().upper()
    return v if v in VERDICTS else "UNVERIFIABLE"


def gold(row: dict) -> str:
    return (row.get("gold_verdict") or "").strip().upper()


def prep_baseline(rows: list[dict]) -> list[dict]:
    """Attach the float fields `bl_verdicts` needs, dropping unlabeled rows."""
    out = []
    for r in rows:
        if not gold(r):
            continue
        try:
            r["_e"] = float(r.get("entail") or 0.0)
            r["_c"] = float(r.get("contradict") or 0.0)
            r["_n"] = int(float(r.get("scored_passages") or 0))
        except ValueError:
            r["_e"] = r["_c"] = 0.0
            r["_n"] = 0
        out.append(r)
    return out


# ---------------------------------------------------------------- presentation

def hdr(t: str) -> None:
    print()
    print("=" * 78)
    print(t)
    print("=" * 78)


def sub(t: str) -> None:
    print()
    print(f"--- {t} " + "-" * max(0, 72 - len(t)))


def ci(k: int, n: int) -> str:
    if n == 0:
        return "     n=0"
    p, lo, hi = M.wilson(k, n)
    return f"{100*p:5.1f}% [{100*lo:5.1f}, {100*hi:5.1f}]"


def counts(g: list[str], p: list[str]) -> dict:
    """Detection bookkeeping on a gold-FALSE-only population."""
    return {
        "n": len(g),
        "detected": sum(1 for a, b in zip(g, p) if a == "FALSE" and b == "FALSE"),
        "asserted_true": sum(1 for a, b in zip(g, p)
                             if a == "FALSE" and b == "TRUE"),
        "abstained": sum(1 for b in p if b == "UNVERIFIABLE"),
    }


def detect_row(label: str, c: dict) -> None:
    n = c["n"]
    print(f"  {label:<34} {c['detected']:>3}/{n:<3} {ci(c['detected'], n)}"
          f"   {c['asserted_true']:>3}      {c['abstained']:>3}")


# ------------------------------------------------------------------- sections

def section_standalone(neg_routed: list[dict]) -> None:
    hdr("[1] ROUTED QUANTITATIVE, STANDALONE, on all 24 gold negatives")
    print()
    print("  Valid on all 24: the routed verifier compares against Wikidata")
    print("  `quantity` statements and never reads the NLI cache, so the")
    print("  collision that corrupts 9 baseline rows cannot reach it.")

    g = [gold(r) for r in neg_routed]
    p = [pred(r) for r in neg_routed]
    assert set(g) == {"FALSE"}, f"expected all gold FALSE, got {set(g)}"

    cov = [(a, b) for a, b in zip(g, p) if b != "UNVERIFIABLE"]
    ok = sum(1 for a, b in cov if a == b)

    sub("headline")
    print(f"  coverage             {len(cov):>3}/{len(g):<3} {ci(len(cov), len(g))}")
    print(f"  accuracy on covered  {ok:>3}/{len(cov):<3} {ci(ok, len(cov))}")
    print(f"  confident wrong      {len(cov)-ok:>3}"
          f"      (a gold-FALSE claim asserted TRUE)")
    print()
    print("  Always-True on this set    0.0%   <-- every row is gold FALSE, so")
    print("  the degenerate strategy that scores 87.9% on the natural 356 scores")
    print("  ZERO here. That is what makes the accuracy above informative.")

    sub("what the 18 abstentions say (each names its own gap)")
    reasons: collections.Counter = collections.Counter()
    for r in neg_routed:
        if pred(r) != "UNVERIFIABLE":
            continue
        d = (r.get("q_detail") or r.get("q_subtype_reason") or "").strip()
        # Collapse to the leading clause; the tail carries per-claim specifics.
        key = d.split(" -- ")[0].split(";")[0][:64] or "(no reason recorded)"
        reasons[key] += 1
    for k, v in reasons.most_common():
        print(f"    {v:>3}  {k}")

    sub("the 6 detected")
    for r in neg_routed:
        if pred(r) != "FALSE":
            continue
        print(f"    {r['claim_id']:<14} {r.get('subject','')[:22]:<22} "
              f"claimed {r.get('q_claimed_value',''):>10} vs actual "
              f"{r.get('q_actual_value',''):>10}  "
              f"[{r.get('q_property_pid','')}]  {r.get('injection_type','')}")


def section_paired(neg_routed: list[dict], neg_base: list[dict]) -> None:
    hdr("[2] PAIRED on the 15 cache-clean negatives (routed vs baseline)")
    print()
    print("  9 of the 24 read their base claim's cached NLI scores and are")
    print("  excluded. This is the ONLY population where the two systems may be")
    print("  compared row-for-row.")

    clean = {r["claim_id"] for r in neg_routed
             if (r.get("cache_corrupt") or "0") != "1"}
    rr = [r for r in neg_routed if r["claim_id"] in clean]
    bb = [r for r in neg_base if r["claim_id"] in clean]
    print(f"\n  clean rows: routed {len(rr)}, baseline {len(bb)}"
          f"   (ids match: {sorted(r['claim_id'] for r in rr) == sorted(r['claim_id'] for r in bb)})")

    gr = [gold(r) for r in rr]
    gb = [gold(r) for r in bb]

    print()
    print(f"  {'system':<34} {'detected FALSE':>14} {'95% CI':>16}"
          f"  {'ASSERTED':>8} {'abstain':>8}")
    print(f"  {'':<34} {'':>14} {'':>16}  {'TRUE':>8} {'':>8}")
    print("  " + "-" * 74)
    detect_row("routed QUANTITATIVE", counts(gr, [pred(r) for r in rr]))
    detect_row(f"baseline 3d @shipped {SHIPPED}",
               counts(gb, bl_verdicts(bb, *SHIPPED)))
    detect_row(f"baseline 3d @tuned   {TUNED}",
               counts(gb, bl_verdicts(bb, *TUNED)))
    detect_row("baseline 3e (margin >= 0.15)",
               counts(gb, [(r.get("verdict_margin") or "UNVERIFIABLE").upper()
                           for r in bb]))

    print()
    print("  The column that matters for a detector is ASSERTED TRUE: a")
    print("  hallucination the system positively vouched for. Routing abstains")
    print("  where it cannot check; the baseline guesses and is sometimes wrong")
    print("  in the one direction a hallucination detector must not be.")

    # Independence correction. Only the baseline is affected: the duplicate rows
    # are abstentions for the routed verifier, which never reads the NLI cache.
    ind = [r for r in bb if r["claim_id"] not in DUP_READ]
    if len(ind) != len(bb):
        sub(f"independence correction: {len(bb) - len(ind)} duplicate NLI read(s)")
        print(f"  {sorted(DUP_READ)} duplicates SYN_QUAN_030's cache entry, so the")
        print("  baseline's count above includes one answer twice. Re-reported on")
        print(f"  the {len(ind)} independent rows:")
        print()
        print(f"  {'system':<34} {'detected FALSE':>14} {'95% CI':>16}"
              f"  {'ASSERTED':>8} {'abstain':>8}")
        print("  " + "-" * 74)
        gi = [gold(r) for r in ind]
        detect_row(f"baseline 3d @shipped {SHIPPED}",
                   counts(gi, bl_verdicts(ind, *SHIPPED)))
        detect_row(f"baseline 3d @tuned   {TUNED}",
                   counts(gi, bl_verdicts(ind, *TUNED)))
        rr_i = [r for r in rr if r["claim_id"] not in DUP_READ]
        detect_row("routed QUANTITATIVE (same rows)",
                   counts([gold(r) for r in rr_i], [pred(r) for r in rr_i]))
        print()
        print("  This correction moves the baseline DOWN, i.e. it happens to")
        print("  favour the system this project argues for -- the opposite")
        print("  direction from the base-inheritance correction above, which")
        print("  moved against us. Both are applied, because whether a")
        print("  correction is convenient has no bearing on whether it is right.")

    # The sharpest comparison in the whole table: same claim, same gold, and the
    # two systems return opposite confident verdicts.
    sub("direct disagreement -- same claim, opposite confident verdicts")
    bmap = {r["claim_id"]: r for r in bb}
    bl_at_shipped = dict(zip([r["claim_id"] for r in bb],
                             bl_verdicts(bb, *SHIPPED)))
    rows = []
    for r in rr:
        cid = r["claim_id"]
        pr_, pb_ = pred(r), bl_at_shipped.get(cid, "UNVERIFIABLE")
        if pr_ == "UNVERIFIABLE" or pb_ == "UNVERIFIABLE" or pr_ == pb_:
            continue
        rows.append((cid, r, pr_, pb_))
    if not rows:
        print("  none")
    else:
        print(f"  {'claim_id':<14} {'subject':<20} {'claimed':>10} "
              f"{'actual':>10}  {'routed':<7} {'baseline':<9} gold")
        print("  " + "-" * 76)
        for cid, r, pr_, pb_ in rows:
            print(f"  {cid:<14} {r.get('subject','')[:20]:<20} "
                  f"{r.get('q_claimed_value',''):>10} "
                  f"{r.get('q_actual_value',''):>10}  {pr_:<7} {pb_:<9} "
                  f"{gold(r)}")
        rw = sum(1 for _, r, pr_, _ in rows if pr_ == gold(r))
        print()
        print(f"  routed correct on these {rw}/{len(rows)}; "
              f"baseline correct {len(rows)-rw}/{len(rows)}")
        print()
        print("  These are hallucinated elevations the baseline positively")
        print("  vouched for -- entail 0.53-0.65 against retrieved Wikipedia")
        print("  passages that DO mention the mountain, just not that number.")
        print("  A Wikidata quantity comparison cannot make this error: the")
        print("  value either matches the stored one within tolerance or it")
        print("  does not. There is no inference step to be fooled.")


def section_combined(pos_routed: list[dict], neg_routed: list[dict],
                     pos_base: list[dict], neg_base: list[dict]) -> None:
    hdr("[3] BOTH CLASSES: Batch 3 positives + synthetic negatives")
    print()
    print("  The only QUANTITATIVE population in the project with gold TRUE and")
    print("  gold FALSE both present, so the only one that can carry an")
    print("  F1(FALSE) or an MCC.")

    rows_r = pos_routed + neg_routed
    gr = [gold(r) for r in rows_r]
    pr = [pred(r) for r in rows_r]

    ids = {r["claim_id"] for r in rows_r}
    rows_b = [r for r in pos_base + neg_base if r["claim_id"] in ids]

    print(f"\n  routed   n={len(rows_r)}   gold {dict(collections.Counter(gr))}")
    print(f"  baseline n={len(rows_b)}   "
          f"(ids present in baseline output: {len(rows_b)}/{len(rows_r)})")

    sub("routed QUANTITATIVE")
    M.report(gr, pr, title="routed QUANTITATIVE (positives + negatives)")

    for label, pv in (("baseline 3d @shipped", bl_verdicts(rows_b, *SHIPPED)),
                      ("baseline 3d @tuned", bl_verdicts(rows_b, *TUNED))):
        sub(label)
        M.report([gold(r) for r in rows_b], pv, title=label)

    sub("head to head, one line each")
    print(f"  {'system':<24} {'cov':>7} {'sel acc':>16} {'F1(F)':>7} "
          f"{'MCC':>7} {'conf-wrong':>11}")
    print("  " + "-" * 74)

    def line(label: str, g: list[str], p: list[str]) -> None:
        sel = M.selective(g, p)
        prf = M.per_class_prf(g, p)
        cw = sum(1 for a, b in zip(g, p)
                 if b != "UNVERIFIABLE" and a != b)
        print(f"  {label:<24} {100*sel['coverage']:>6.1f}% "
              f"{ci(sel['correct'], sel['covered'])} "
              f"{prf['FALSE']['f1']:>7.3f} {M.mcc(g, p):>+7.3f} {cw:>11}")

    line("routed", gr, pr)
    gb = [gold(r) for r in rows_b]
    line("baseline 3d @shipped", gb, bl_verdicts(rows_b, *SHIPPED))
    line("baseline 3d @tuned", gb, bl_verdicts(rows_b, *TUNED))
    line("Always-True", gr, ["TRUE"] * len(gr))
    line("Always-False", gr, ["FALSE"] * len(gr))


def section_pairs(pos_routed: list[dict], neg_routed: list[dict]) -> None:
    """The strongest control available: a claim and its own perturbation."""
    hdr("[4] MATCHED PAIRS -- the same fact, true and corrupted")
    print()
    print("  Where a negative's base claim is itself in the Batch 3 positives")
    print("  and BOTH are covered, the verifier is asked about one fact twice:")
    print("  once with the real number, once with a wrong one. Agreeing with")
    print("  gold on both is discrimination that no unconditional strategy and")
    print("  no plausibility heuristic can fake.")

    posmap = {r["claim_id"]: r for r in pos_routed}
    pairs = []
    for r in neg_routed:
        b = posmap.get(r.get("base_claim_id", ""))
        if b:
            pairs.append((b, r))

    print(f"\n  negatives whose base is in the positives : {len(pairs)}")
    both = [(b, n) for b, n in pairs
            if pred(b) != "UNVERIFIABLE" and pred(n) != "UNVERIFIABLE"]
    print(f"  pairs where BOTH sides are covered       : {len(both)}")

    if not both:
        print("\n  none -- no matched-pair evidence available")
        return

    print()
    print(f"  {'base':<13} {'true val':>11} {'->':^4} {'verdict':<8} | "
          f"{'negative':<14} {'bad val':>11} {'->':^4} {'verdict':<8} ok")
    print("  " + "-" * 96)
    nok = 0
    for b, n in both:
        good = pred(b) == gold(b) and pred(n) == gold(n)
        nok += good
        print(f"  {b['claim_id']:<13} {b.get('q_claimed_value',''):>11} "
              f"{'':^4} {pred(b):<8} | {n['claim_id']:<14} "
              f"{n.get('q_claimed_value',''):>11} {'':^4} {pred(n):<8} "
              f"{'YES' if good else 'NO'}")
    print()
    print(f"  pairs correct on BOTH sides: {nok}/{len(both)} {ci(nok, len(both))}")
    print()
    print("  An unconditional TRUE scores 0/{0} here; an unconditional FALSE also"
          .format(len(both)))
    print("  scores 0/{0}. Only a real lookup can score above zero."
          .format(len(both)))


def section_samenumber(pos_routed: list[dict], neg_routed: list[dict]) -> None:
    """The strongest result in the table, and it needs no statistics.

    `cross_substitute` injects another real entity's true value in a rotation, so
    every claimed number in this set is a genuine mountain elevation. Where one
    value appears with a TRUE verdict under one subject and a FALSE verdict under
    another, the number itself carries ZERO signal -- the verdict can only have
    come from a subject-conditioned lookup.

    This is what no text-only method can reproduce. A plausibility heuristic, an
    LLM's prior over "does 6961 m sound like a mountain", or an NLI model matching
    surface numerals against a passage all see the same digits both times.
    """
    hdr("[5] THE SAME NUMBER, OPPOSITE VERDICTS")
    print()
    print("  Every value below is a real mountain's real elevation, injected by")
    print("  `cross_substitute` in a rotation. A value that is TRUE of one peak")
    print("  and FALSE of another contains no information on its own.")

    covered = [r for r in pos_routed + neg_routed
               if pred(r) != "UNVERIFIABLE"]
    byval: dict[str, list[dict]] = collections.defaultdict(list)
    for r in covered:
        v = (r.get("q_claimed_value") or "").strip()
        if v:
            byval[v].append(r)

    both = {v: rs for v, rs in byval.items()
            if {pred(r) for r in rs} == {"TRUE", "FALSE"}}

    print(f"\n  distinct claimed values among the {len(covered)} covered : "
          f"{len(byval)}")
    print(f"  values receiving BOTH a TRUE and a FALSE verdict     : "
          f"{len(both)}")

    if not both:
        print("\n  none")
        return

    print()
    print(f"  {'value':>11}  {'verdict':<8} {'subject':<24} {'claim_id':<14} "
          f"{'actual':>11}")
    print("  " + "-" * 74)
    for v in sorted(both, key=lambda x: -float(x)):
        for r in sorted(both[v], key=lambda r: pred(r)):
            print(f"  {v:>11}  {pred(r):<8} {r.get('subject','')[:24]:<24} "
                  f"{r['claim_id']:<14} {r.get('q_actual_value',''):>11}")
        print()

    print("  Read one block: the identical number, the identical property")
    print("  (P2044), opposite verdicts. The only differing input is the")
    print("  SUBJECT, which is exactly what a knowledge-graph lookup conditions")
    print("  on and what a surface-form method cannot condition on.")


def section_prior(neg_base: list[dict], base_pos_all: list[dict]) -> None:
    """Why the swept 'optimum' is worse here: it was fit to the class prior.

    threshold_sweep (2026-08-23) found (0.35/0.30) STRICTLY dominates the shipped
    (0.50/0.40) on the natural 356 -- every metric improved at once -- and CLAUDE.md
    accordingly directs that RQ2 quote the baseline at the tuned point, so as not
    to strawman it. On this negatives-enriched population the tuned point is much
    WORSE. Both observations are correct; the reconciliation is the finding.

    The entail threshold is, in effect, a knob on how often the system says TRUE.
    Rows whose entail falls in [tuned, shipped) are TRUE under tuning and not TRUE
    under shipping. On a set that is 88% gold TRUE those rows are mostly free
    accuracy. On a set that is all gold FALSE every one of them is a new confident
    miss. So the sweep did not find a better DISCRIMINATOR -- it found a better
    fit to the natural set's 24:1 class imbalance.

    This is the project's own class-imbalance trap operating one level up: not on
    the metric being reported, but on the hyperparameter being selected. The
    remedy is the same -- state the class prior of the set a threshold was tuned
    on, and never carry that threshold to a set with a different prior.
    """
    hdr("[6] THE SWEPT OPTIMUM IS FIT TO THE CLASS PRIOR, NOT TO DISCRIMINATION")

    lo, hi = TUNED[0], SHIPPED[0]

    def band(rows: list[dict], label: str) -> None:
        n = len(rows)
        if not n:
            return
        flip = [r for r in rows if lo <= r["_e"] < hi]
        gf = sum(1 for r in flip if gold(r) == "FALSE")
        gt = sum(1 for r in flip if gold(r) == "TRUE")
        prior = collections.Counter(gold(r) for r in rows)
        pf = 100 * prior["FALSE"] / n
        print(f"  {label:<38} n={n:<4} gold FALSE {pf:>5.1f}%")
        print(f"    entail in [{lo}, {hi}) -> flips to TRUE under tuning: "
              f"{len(flip):>3}/{n}")
        print(f"      of those, gold TRUE  (tuning HELPS) : {gt:>3}")
        print(f"      of those, gold FALSE (tuning HURTS) : {gf:>3}")
        print()

    print()
    print(f"  Rows with entail in [{lo}, {hi}) are the ones the tuned threshold")
    print("  converts into TRUE. Whether that helps depends entirely on how many")
    print("  of them are gold FALSE -- i.e. on the class prior of the set.")
    print()
    band(base_pos_all, "natural 356 (all types, what was swept)")
    band(neg_base, "the 24 QUANTITATIVE negatives")

    print("  Consequence for RQ2 reporting: there is no single baseline operating")
    print("  point that is fair on both populations, so the baseline is quoted at")
    print("  whichever point is STRONGER on the population being reported")
    print("  (shipped, here). The routed verifier has no threshold at all -- it")
    print("  finds a Wikidata quantity statement and compares, or abstains -- so")
    print("  there is no operating point in it to fit to a class prior. That is")
    print("  an architectural difference, and it is now measured rather than")
    print("  asserted.")


# ----------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--section", default="all",
                    choices=["all", "standalone", "paired", "combined", "pairs",
                             "samenumber", "prior"])
    args = ap.parse_args()

    pos_routed = [r for r in load(ROUTED_POS) if gold(r)]
    neg_routed = [r for r in load(ROUTED_NEG) if gold(r)]
    base_pos_all = prep_baseline(load(BASE_POS))
    base_neg_all = prep_baseline(load(BASE_NEG))

    # The baseline files hold every type; this comparison is QUANTITATIVE only.
    pos_ids = {r["claim_id"] for r in pos_routed}
    neg_ids = {r["claim_id"] for r in neg_routed}
    pos_base = [r for r in base_pos_all if r["claim_id"] in pos_ids]
    neg_base = [r for r in base_neg_all if r["claim_id"] in neg_ids]

    hdr("RQ2 -- QUANTITATIVE: taxonomy-routed verifier vs non-routed baseline")
    print()
    print(f"  routed positives   {len(pos_routed):>3}  "
          f"{os.path.relpath(ROUTED_POS, ROOT)}")
    print(f"  routed negatives   {len(neg_routed):>3}  "
          f"{os.path.relpath(ROUTED_NEG, ROOT)}")
    print(f"  baseline positives {len(pos_base):>3}  "
          f"{os.path.relpath(BASE_POS, ROOT)} (QUANTITATIVE slice)")
    print(f"  baseline negatives {len(neg_base):>3}  "
          f"{os.path.relpath(BASE_NEG, ROOT)} (QUANTITATIVE slice)")
    missing = pos_ids - {r["claim_id"] for r in pos_base}
    if missing:
        print(f"\n  !! {len(missing)} routed positives absent from baseline output;")
        print("     the combined head-to-head is over the intersection only.")

    if args.section in ("all", "standalone"):
        section_standalone(neg_routed)
    if args.section in ("all", "paired"):
        section_paired(neg_routed, neg_base)
    if args.section in ("all", "combined"):
        section_combined(pos_routed, neg_routed, pos_base, neg_base)
    if args.section in ("all", "pairs"):
        section_pairs(pos_routed, neg_routed)
    if args.section in ("all", "samenumber"):
        section_samenumber(pos_routed, neg_routed)
    if args.section in ("all", "prior"):
        section_prior(neg_base, base_pos_all)

    print()
    print("=" * 78)
    print("Read every figure with its coverage. A verifier that abstains on")
    print("three quarters of a set is not thereby accurate; it is narrow. The")
    print("claim RQ2 can support here is about the ERROR PROFILE at equal")
    print("evidence, not about breadth.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
