#!/usr/bin/env python3
"""
McNemar's test: paired comparison of routed vs non-routed verifiers (RQ2).

WHY THIS TEST AND NOT SOMETHING ELSE
-------------------------------------
We have TWO systems evaluated on the SAME claims. Unpaired tests (two-proportion
z, chi-squared on independent samples) would be wrong -- they assume the samples
are independent, but they're not: the same 266 claims were scored by both systems.

McNemar's test is the paired binary analog of the paired t-test. It uses only the
DISCORDANT pairs (claims where one system is correct and the other isn't) and asks
whether their ratio departs significantly from 50:50.

    H0: P(routed correct, baseline wrong) = P(baseline correct, routed wrong)
    H1: they differ

With only 25 discordant pairs, we use the EXACT binomial test (not the chi-squared
approximation, which requires n_discordant >= 25 and is unreliable below that).

THREE-WAY CORRECTNESS
--------------------
Both systems emit 3 verdicts: TRUE, FALSE, UNVERIFIABLE. "Correct" means the
predicted verdict exactly matches the gold label. A predicted UNVERIFIABLE on a
gold-TRUE claim counts as WRONG (the system missed something verifiable). A
predicted TRUE on a gold-UNVERIFIABLE claim also counts as WRONG (overreach).

This is the same correctness rule used in metrics.py's selective view.

ADDITIONAL TESTS
----------------
1. Per-type McNemar: does routing help for specific claim types?
2. Binarised McNemar on the FALSE class only: does routing improve hallucination
   detection specifically? (The one a reviewer will ask about.)
3. Effect size: odds ratio of discordant pairs.

USAGE
-----
    python current/mcnemar_test.py              # full run
    python current/mcnemar_test.py --selftest   # sanity checks
    python current/mcnemar_test.py --with-negatives  # include synthetic negatives

OUTPUT
------
    current/mcnemar_results.csv     -- machine-readable results
    Printed tables to stdout

Nothing existing is modified.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
UNIFIED = os.path.join(HERE, "haldetect_claims_unified.csv")
BASELINE_CSV = os.path.join(HERE, "nonrouted_baseline_results.csv")
NEGATIVES_CSV = os.path.join(HERE, "nonrouted_negatives_results.csv")
OUT_CSV = os.path.join(HERE, "mcnemar_results.csv")

ROUTED_SOURCES = [
    ("nonrouted_baseline_results.csv", "verdict", {"RELATIONAL"}),
    ("temporal_ea_hybrid_b3.csv", "verdict", {"TEMPORAL", "ENTITY_ATTRIBUTE"}),
    ("quantitative_b3_results.csv", "q_verdict", {"QUANTITATIVE"}),
    ("citation_l1_results.csv", "verdict", {"CITATION"}),
]

# Synthetic negatives routed sources — use the same NLI baseline for
# RELATIONAL (B3N negatives), and the non-routed baseline for others since
# those are all non-RELATIONAL synthetics evaluated by NLI
NEGATIVES_ROUTED_SOURCES = [
    # For synthetics, the "routed" system would use the type-specific verifier
    # but we only have NLI baseline results for them. The routed verifiers
    # (quantitative, temporal, citation-l1b) were evaluated on the synthetic
    # negatives set separately. We load from the negatives CSV for both sides.
]

DECIDED = ("TRUE", "FALSE")
VERDICTS = ("TRUE", "FALSE", "UNVERIFIABLE")


# ---------------------------------------------------------------------------
# Exact binomial test (no scipy dependency)
# ---------------------------------------------------------------------------

def _binom_cdf(k: int, n: int, p: float = 0.5) -> float:
    """Exact CDF of Binomial(n, p) at k. Uses log-space for numerical stability."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    total = 0.0
    log_p = math.log(p)
    log_q = math.log(1 - p)
    # log(C(n,i)) computed incrementally
    log_c = 0.0  # log(C(n,0)) = 0
    for i in range(k + 1):
        if i > 0:
            log_c += math.log(n - i + 1) - math.log(i)
        total += math.exp(log_c + i * log_p + (n - i) * log_q)
    return min(1.0, total)


def mcnemar_exact(b: int, c: int) -> dict:
    """Exact McNemar test using the binomial distribution.

    b = number of claims where baseline correct, routed wrong
    c = number of claims where routed correct, baseline wrong
    n = b + c (discordant pairs)

    Under H0: b ~ Binomial(n, 0.5)

    Returns two-sided p-value, odds ratio, and interpretation.
    """
    n = b + c
    if n == 0:
        return {
            "b": b, "c": c, "n_discordant": 0,
            "p_value": 1.0, "odds_ratio": float("nan"),
            "direction": "no discordant pairs",
            "significant_005": False, "significant_010": False,
        }

    # Two-sided p-value: P(X <= min(b,c)) + P(X >= max(b,c))
    # = 2 * P(X <= min(b,c))  when the distribution is symmetric (p=0.5)
    p_value = 2.0 * _binom_cdf(min(b, c), n, 0.5)
    p_value = min(1.0, p_value)  # cap at 1.0

    odds_ratio = c / b if b > 0 else float("inf")

    if c > b:
        direction = "routed better"
    elif b > c:
        direction = "baseline better"
    else:
        direction = "no difference"

    return {
        "b": b, "c": c, "n_discordant": n,
        "p_value": p_value, "odds_ratio": odds_ratio,
        "direction": direction,
        "significant_005": p_value < 0.05,
        "significant_010": p_value < 0.10,
    }


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_type_map() -> dict[str, str]:
    """Load claim_id -> type from the unified CSV."""
    type_of = {}
    with open(UNIFIED, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cid = (r.get("claim_id") or "").strip()
            t = (r.get("type") or "").strip().upper()
            if cid and t:
                type_of[cid] = t
    return type_of


def load_routed(type_of: dict[str, str]) -> dict[str, str]:
    """Load routed verdicts. Each source only supplies the types it owns."""
    routed = {}
    for fname, col, types in ROUTED_SOURCES:
        p = os.path.join(HERE, fname)
        if not os.path.isfile(p):
            print(f"  !! routed source missing: {fname}")
            continue
        taken = 0
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                cid = (r.get("claim_id") or "").strip()
                if not cid or cid in routed:
                    continue
                ctype = type_of.get(cid, (r.get("type") or "").upper())
                if ctype not in types:
                    continue
                v = (r.get(col) or "").strip().upper()
                if v:
                    routed[cid] = v
                    taken += 1
        print(f"  {fname:<38} supplied {taken:>4} routed verdicts "
              f"for {sorted(types)}")
    return routed


def load_nonrouted() -> tuple[dict[str, str], dict[str, str]]:
    """Load non-routed verdicts and gold labels."""
    nr = {}
    gold = {}
    with open(BASELINE_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cid = (r.get("claim_id") or "").strip()
            v = (r.get("verdict") or "").strip().upper()
            g = (r.get("gold_verdict") or "").strip().upper()
            if cid and v:
                nr[cid] = v
            if cid and g in VERDICTS:
                gold[cid] = g
    return nr, gold


def load_negatives_nonrouted() -> tuple[dict[str, str], dict[str, str]]:
    """Load synthetic negatives non-routed verdicts and gold."""
    nr = {}
    gold = {}
    if not os.path.isfile(NEGATIVES_CSV):
        return nr, gold
    with open(NEGATIVES_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cid = (r.get("claim_id") or "").strip()
            v = (r.get("verdict") or "").strip().upper()
            g = (r.get("gold_verdict") or "").strip().upper()
            if cid and v:
                nr[cid] = v
            if cid and g in VERDICTS:
                gold[cid] = g
    return nr, gold


# ---------------------------------------------------------------------------
# Contingency builder
# ---------------------------------------------------------------------------

def build_contingency(
    paired_ids: list[str],
    routed: dict[str, str],
    nonrouted: dict[str, str],
    gold: dict[str, str],
    binarise_on: str | None = None,
) -> tuple[int, int, int, int, list[dict]]:
    """Build the 2x2 contingency table.

    If binarise_on is set (e.g. "FALSE"), correctness is judged only on that
    class: correct = (pred == binarise_on) == (gold == binarise_on).

    Returns (both_correct, both_wrong, nr_correct_r_wrong, r_correct_nr_wrong,
             detail_rows).
    """
    a = b = c = d = 0  # a=both correct, d=both wrong, b=NR+/R-, c=R+/NR-
    details = []
    for cid in paired_ids:
        g = gold.get(cid, "")
        rv = routed.get(cid, "")
        nv = nonrouted.get(cid, "")
        if not g or not rv or not nv:
            continue

        if binarise_on:
            r_ok = (rv == binarise_on) == (g == binarise_on)
            n_ok = (nv == binarise_on) == (g == binarise_on)
        else:
            r_ok = (rv == g)
            n_ok = (nv == g)

        if r_ok and n_ok:
            a += 1
        elif not r_ok and not n_ok:
            d += 1
        elif n_ok and not r_ok:
            b += 1
        else:
            c += 1

        if r_ok != n_ok:
            details.append({
                "claim_id": cid, "gold": g,
                "routed": rv, "nonrouted": nv,
                "routed_correct": r_ok, "nonrouted_correct": n_ok,
            })

    return a, d, b, c, details


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report_mcnemar(label: str, a: int, d: int, b: int, c: int,
                   show_detail: list[dict] | None = None) -> dict:
    """Print and return McNemar test results."""
    result = mcnemar_exact(b, c)
    n_total = a + b + c + d
    print(f"\n{'=' * 72}")
    print(f"  McNEMAR TEST — {label}")
    print(f"{'=' * 72}")
    print(f"  Paired claims: {n_total}")
    print(f"\n  {'':>30}{'Routed correct':>16}{'Routed wrong':>14}")
    print(f"  {'Baseline correct':>30}{a:>16}{b:>14}")
    print(f"  {'Baseline wrong':>30}{c:>16}{d:>14}")
    print(f"\n  Discordant pairs: {result['n_discordant']} "
          f"(b={b}, c={c})")
    print(f"  Direction: {result['direction']}")
    if not math.isnan(result['odds_ratio']) and not math.isinf(result['odds_ratio']):
        print(f"  Odds ratio (c/b): {result['odds_ratio']:.2f}")
    elif math.isinf(result['odds_ratio']):
        print(f"  Odds ratio (c/b): ∞ (b=0)")
    print(f"  p-value (exact binomial, 2-sided): {result['p_value']:.4f}")
    if result['significant_005']:
        print(f"  *** Significant at α=0.05 ***")
    elif result['significant_010']:
        print(f"  *   Significant at α=0.10 (marginal) *")
    else:
        print(f"      Not significant at α=0.10")

    if show_detail and len(show_detail) <= 30:
        print(f"\n  Discordant pair details:")
        print(f"  {'claim_id':<20}{'gold':<15}{'routed':<15}{'nonrouted':<15}"
              f"{'winner':<10}")
        for dd in sorted(show_detail, key=lambda x: x["claim_id"]):
            winner = "routed" if dd["routed_correct"] else "baseline"
            print(f"  {dd['claim_id']:<20}{dd['gold']:<15}"
                  f"{dd['routed']:<15}{dd['nonrouted']:<15}{winner:<10}")

    result["label"] = label
    result["n_total"] = n_total
    result["both_correct"] = a
    result["both_wrong"] = d
    return result


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def selftest() -> int:
    print("=== selftest ===")
    checks = 0

    # 1. Exact binomial CDF
    assert abs(_binom_cdf(5, 10, 0.5) - 0.623046875) < 1e-6
    checks += 1
    print(f"  [1/5] binomial CDF correct")

    # 2. McNemar exact on known data: b=2, c=8 -> p ≈ 0.1094
    r = mcnemar_exact(2, 8)
    assert abs(r["p_value"] - 0.109375) < 1e-4, f"got {r['p_value']}"
    assert r["direction"] == "routed better"
    assert not r["significant_005"]
    checks += 1
    print(f"  [2/5] McNemar exact p-value correct (b=2,c=8 -> p={r['p_value']:.4f})")

    # 3. Symmetric case b=c -> p=1.0
    r = mcnemar_exact(5, 5)
    assert abs(r["p_value"] - 1.0) < 1e-6
    assert r["direction"] == "no difference"
    checks += 1
    print(f"  [3/5] symmetric case p=1.0")

    # 4. Extreme case b=0, c=5 -> p = 2*(0.5^5) = 0.0625
    r = mcnemar_exact(0, 5)
    assert abs(r["p_value"] - 0.0625) < 1e-4
    assert r["direction"] == "routed better"
    checks += 1
    print(f"  [4/5] extreme case b=0,c=5 -> p={r['p_value']:.4f}")

    # 5. Build contingency on synthetic data
    ids = ["c1", "c2", "c3", "c4"]
    routed = {"c1": "TRUE", "c2": "FALSE", "c3": "TRUE", "c4": "FALSE"}
    nonrouted = {"c1": "TRUE", "c2": "TRUE", "c3": "FALSE", "c4": "FALSE"}
    gold = {"c1": "TRUE", "c2": "FALSE", "c3": "TRUE", "c4": "TRUE"}
    a, d, b, c, det = build_contingency(ids, routed, nonrouted, gold)
    assert a == 1  # c1: both correct
    assert d == 1  # c3 is wrong for routed (TRUE=TRUE), wait...
    # c1: g=TRUE, r=TRUE, n=TRUE -> both correct (a)
    # c2: g=FALSE, r=FALSE, n=TRUE -> r correct, n wrong (c)
    # c3: g=TRUE, r=TRUE, n=FALSE -> r correct, n wrong (c)
    # c4: g=TRUE, r=FALSE, n=FALSE -> both wrong (d)
    assert a == 1 and d == 1 and b == 0 and c == 2, f"got a={a},d={d},b={b},c={c}"
    checks += 1
    print(f"  [5/5] contingency builder correct")

    print(f"\n  All {checks}/5 checks passed.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--with-negatives", action="store_true",
                    help="include synthetic negatives in the analysis")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    # Load data
    for path in (UNIFIED, BASELINE_CSV):
        if not os.path.isfile(path):
            print(f"FATAL: {path} not found.")
            return 1

    type_of = load_type_map()
    routed = load_routed(type_of)
    nonrouted, gold = load_nonrouted()

    if args.with_negatives:
        neg_nr, neg_gold = load_negatives_nonrouted()
        # For synthetic negatives, "routed" would use type-specific verifiers.
        # We don't have paired routed verdicts for all of them, so we only
        # include those that have both routed and non-routed verdicts.
        nonrouted.update(neg_nr)
        gold.update(neg_gold)

    # Paired claims = those with verdicts from both systems + gold label
    paired = sorted([cid for cid in routed
                     if cid in nonrouted and cid in gold])
    print(f"\nPaired claims (both systems + gold): {len(paired)}")
    tc = Counter(type_of.get(cid, "?") for cid in paired)
    print(f"By type: {dict(sorted(tc.items()))}")
    gc = Counter(gold[cid] for cid in paired)
    print(f"By gold: {dict(sorted(gc.items()))}")

    all_results = []

    # -----------------------------------------------------------------------
    # 1. Overall McNemar (3-way exact match)
    # -----------------------------------------------------------------------
    a, d, b, c, det = build_contingency(paired, routed, nonrouted, gold)
    res = report_mcnemar("Overall (3-way exact match)", a, d, b, c, det)
    all_results.append(res)

    # -----------------------------------------------------------------------
    # 2. Binarised on FALSE class
    # -----------------------------------------------------------------------
    a, d, b, c, det = build_contingency(
        paired, routed, nonrouted, gold, binarise_on="FALSE")
    res = report_mcnemar("Binarised on FALSE (hallucination detection)", a, d, b, c, det)
    all_results.append(res)

    # -----------------------------------------------------------------------
    # 3. Per-type McNemar
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  PER-TYPE McNEMAR TESTS")
    print(f"{'=' * 72}")

    types_order = ["RELATIONAL", "TEMPORAL", "ENTITY_ATTRIBUTE",
                   "QUANTITATIVE", "CITATION"]
    print(f"\n  {'Type':<20}{'n':>5}{'disc.':>7}{'b(NR+)':>8}{'c(R+)':>8}"
          f"{'p-value':>10}{'direction':>18}{'sig':>6}")
    print(f"  {'─' * 82}")

    for t in types_order:
        sub = [cid for cid in paired if type_of.get(cid) == t]
        if not sub:
            continue
        a, d, b, c, det = build_contingency(sub, routed, nonrouted, gold)
        r = mcnemar_exact(b, c)
        sig = "**" if r["significant_005"] else "*" if r["significant_010"] else ""
        print(f"  {t:<20}{len(sub):>5}{r['n_discordant']:>7}{b:>8}{c:>8}"
              f"{r['p_value']:>10.4f}{r['direction']:>18}{sig:>6}")
        r["label"] = f"per-type: {t}"
        r["n_total"] = len(sub)
        r["both_correct"] = a
        r["both_wrong"] = d
        all_results.append(r)

        # Show details for types with few discordant pairs
        if det and len(det) <= 15:
            for dd in sorted(det, key=lambda x: x["claim_id"]):
                winner = "R" if dd["routed_correct"] else "NR"
                print(f"    {dd['claim_id']:<18} gold={dd['gold']:<14}"
                      f"R={dd['routed']:<14} NR={dd['nonrouted']:<14} → {winner}")

    # -----------------------------------------------------------------------
    # 4. Non-RELATIONAL subset (where routing actually differs)
    # -----------------------------------------------------------------------
    non_rel = [cid for cid in paired if type_of.get(cid) != "RELATIONAL"]
    if non_rel:
        a, d, b, c, det = build_contingency(non_rel, routed, nonrouted, gold)
        res = report_mcnemar(
            "Non-RELATIONAL only (where routing actually differs)", a, d, b, c, det)
        all_results.append(res)

    # -----------------------------------------------------------------------
    # 5. Summary interpretation
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  SUMMARY & INTERPRETATION")
    print(f"{'=' * 72}")
    overall = all_results[0]
    print(f"\n  Overall: {overall['c']} claims improved by routing vs "
          f"{overall['b']} worsened (p={overall['p_value']:.4f})")
    if overall["significant_005"]:
        print("  → The routed system is SIGNIFICANTLY better at α=0.05.")
    elif overall["significant_010"]:
        print("  → MARGINAL significance at α=0.10. More data needed for α=0.05.")
    else:
        print("  → NOT significant. The difference could be due to chance.")
        print("  → This does NOT mean the systems are equivalent — it means")
        print("    we lack statistical power to detect the difference with")
        print(f"    only {overall['n_discordant']} discordant pairs.")
        if overall["n_discordant"] < 30:
            # Power analysis hint
            needed = _estimate_needed(overall["c"], overall["b"])
            print(f"  → Rough power estimate: ~{needed} discordant pairs needed")
            print("    for 80% power at α=0.05 (given the observed ratio).")

    # -----------------------------------------------------------------------
    # Write CSV
    # -----------------------------------------------------------------------
    fields = ["label", "n_total", "n_discordant", "b", "c",
              "both_correct", "both_wrong", "odds_ratio",
              "p_value", "direction", "significant_005", "significant_010"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in all_results:
            row = {k: r.get(k, "") for k in fields}
            for k in ("odds_ratio", "p_value"):
                if k in row and isinstance(row[k], float):
                    row[k] = f"{row[k]:.6f}"
            w.writerows([row])
    print(f"\n  Results written: {OUT_CSV}")

    return 0


def _estimate_needed(c: int, b: int) -> int:
    """Rough estimate of discordant pairs needed for 80% power at α=0.05.

    Uses the formula: n = ((z_α + z_β)^2) / (p1 - 0.5)^2
    where p1 = c/(b+c) is the observed proportion of discordant pairs
    favouring the routed system.
    """
    n = b + c
    if n == 0:
        return 999
    p1 = c / n
    if abs(p1 - 0.5) < 0.01:
        return 999  # effect too small to estimate
    z_a = 1.96   # α=0.05, two-sided
    z_b = 0.842  # β=0.20 (80% power)
    needed = ((z_a + z_b) ** 2) / (4 * (p1 - 0.5) ** 2)
    return max(n, int(math.ceil(needed)))


if __name__ == "__main__":
    sys.exit(main())
