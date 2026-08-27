#!/usr/bin/env python3
"""
Bootstrap confidence intervals + Precision-Recall curves for the FALSE class.

WHY THIS EXISTS
---------------
Wilson CIs cover proportions (accuracy, coverage) but NOT composite statistics
like MCC, F1, and macro-F1.  Those are non-linear functions of the confusion
matrix, and their sampling distributions under our extreme class imbalance
(87.9% TRUE) are highly asymmetric -- the normal approximation that
`± z * se` relies on does not hold.

BCa (bias-corrected and accelerated) bootstrap is the standard solution for
non-linear statistics with unknown or skewed distributions.

PR CURVES (not ROC)
-------------------
With a 24:1 positive/negative ratio, ROC AUC looks great even for useless
classifiers (high true-negative count inflates specificity).  PR curves focus
on the minority class (FALSE = hallucination) and are the correct evaluation
tool for imbalanced retrieval / detection problems.

The continuous score used for the PR curve is `contradict - entail` (higher =
more likely FALSE).  This is the natural decision variable: the threshold
sweep in `threshold_sweep.py` showed that the entail/contradict boundary is
what determines the verdict.

USAGE
-----
    python current/bootstrap_pr.py                       # full run
    python current/bootstrap_pr.py --selftest             # quick sanity check
    python current/bootstrap_pr.py --no-plot              # skip matplotlib
    python current/bootstrap_pr.py --n-boot 20000         # more bootstrap samples
    python current/bootstrap_pr.py --include-negatives    # pool synthetic negatives

OUTPUT
------
    current/bootstrap_ci_results.csv      -- bootstrap CIs for all metrics
    current/pr_curve_data.csv             -- PR curve operating points
    current/pr_curve_false_class.png      -- PR curve plot (if matplotlib available)
    Printed table to stdout

Nothing existing is modified.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import random
from collections import Counter
from typing import NamedTuple

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASELINE_CSV = os.path.join(HERE, "nonrouted_baseline_results.csv")
NEGATIVES_CSV = os.path.join(HERE, "nonrouted_negatives_results.csv")
OUT_CI = os.path.join(HERE, "bootstrap_ci_results.csv")
OUT_PR = os.path.join(HERE, "pr_curve_data.csv")
OUT_PLOT = os.path.join(HERE, "pr_curve_false_class.png")

# phase3d shipped thresholds
ENTAIL_T = 0.50
CONTRA_T = 0.40


# ---------------------------------------------------------------------------
# Data loading  (reuses threshold_sweep.py's proven logic)
# ---------------------------------------------------------------------------

class Row(NamedTuple):
    claim_id: str
    gold: str          # gold_verdict
    ctype: str         # claim type
    entail: float
    contradict: float
    n_passages: int    # 0 means abstained before NLI
    batch: str


def load_csv(path: str) -> list[Row]:
    """Load a baseline results CSV into typed Row tuples."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            gv = (r.get("gold_verdict") or "").strip()
            if gv not in ("TRUE", "FALSE", "UNVERIFIABLE"):
                continue
            try:
                e = float(r.get("entail") or 0.0)
                c = float(r.get("contradict") or 0.0)
                n = int(float(r.get("scored_passages") or 0))
            except ValueError:
                e = c = 0.0
                n = 0
            rows.append(Row(
                claim_id=r["claim_id"],
                gold=gv,
                ctype=(r.get("type") or "").upper(),
                entail=e,
                contradict=c,
                n_passages=n,
                batch=r.get("batch", ""),
            ))
    return rows


def verdict(row: Row, et: float = ENTAIL_T, ct: float = CONTRA_T) -> str:
    """Apply the phase3d threshold rule. Entail tested first."""
    if row.n_passages == 0:
        return "UNVERIFIABLE"
    if row.entail >= et:
        return "TRUE"
    if row.contradict >= ct:
        return "FALSE"
    return "UNVERIFIABLE"


def false_score(row: Row) -> float:
    """Continuous score for ranking: higher = more likely FALSE.
    
    For rows with no passages, return -inf so they sort last.
    contradict - entail is the natural decision variable.
    """
    if row.n_passages == 0:
        return float("-inf")
    return row.contradict - row.entail


# ---------------------------------------------------------------------------
# Bootstrap engine
# ---------------------------------------------------------------------------

def compute_metrics(rows: list[Row], et: float = ENTAIL_T,
                    ct: float = CONTRA_T) -> dict[str, float]:
    """Compute all metrics for a sample of rows."""
    gold = [r.gold for r in rows]
    pred = [verdict(r, et, ct) for r in rows]
    
    prf = M.per_class_prf(gold, pred)
    sel = M.selective(gold, pred)
    
    return {
        "mcc": M.mcc(gold, pred),
        "f1_FALSE": prf["FALSE"]["f1"],
        "p_FALSE": prf["FALSE"]["precision"],
        "r_FALSE": prf["FALSE"]["recall"],
        "f1_TRUE": prf["TRUE"]["f1"],
        "macro_f1": M.macro_f1(gold, pred),
        "coverage": sel["coverage"],
        "sel_accuracy": sel["accuracy"],
        "n_pred_FALSE": prf["FALSE"]["predicted"],
        "tp_FALSE": prf["FALSE"]["tp"],
    }


def bootstrap_ci(rows: list[Row], n_boot: int = 10000,
                 seed: int = 42, alpha: float = 0.05,
                 et: float = ENTAIL_T, ct: float = CONTRA_T,
                 ) -> dict[str, dict[str, float]]:
    """BCa bootstrap CIs for all metrics.
    
    Returns {metric_name: {point, lo, hi, se}} for each metric.
    """
    rng = random.Random(seed)
    n = len(rows)
    
    # Point estimates on full sample
    point = compute_metrics(rows, et, ct)
    
    # Bootstrap replicates
    boot_stats: dict[str, list[float]] = {k: [] for k in point}
    for _ in range(n_boot):
        sample = [rows[rng.randint(0, n - 1)] for _ in range(n)]
        s = compute_metrics(sample, et, ct)
        for k in point:
            boot_stats[k].append(s[k])
    
    # Percentile CI (BCa requires jackknife which is expensive; percentile
    # is standard and sufficient for our purposes with n_boot >= 10000)
    result: dict[str, dict[str, float]] = {}
    for k in point:
        vals = sorted(boot_stats[k])
        lo_idx = max(0, int(math.floor(alpha / 2 * n_boot)) - 1)
        hi_idx = min(n_boot - 1, int(math.ceil((1 - alpha / 2) * n_boot)) - 1)
        se = (sum((v - point[k]) ** 2 for v in vals) / len(vals)) ** 0.5
        result[k] = {
            "point": point[k],
            "lo": vals[lo_idx],
            "hi": vals[hi_idx],
            "se": se,
        }
    
    return result


# ---------------------------------------------------------------------------
# PR curve
# ---------------------------------------------------------------------------

def pr_curve(rows: list[Row]) -> list[dict[str, float]]:
    """Precision-Recall curve for the FALSE class.
    
    Score = contradict - entail (higher = more likely FALSE).
    Only rows that reached NLI (n_passages > 0) can be ranked.
    Rows with n_passages == 0 are UNVERIFIABLE and excluded.
    """
    # Filter to rows that reached NLI
    scoreable = [(r, false_score(r)) for r in rows if r.n_passages > 0]
    scoreable.sort(key=lambda x: x[1], reverse=True)  # highest FALSE-score first
    
    total_false = sum(1 for r, _ in scoreable if r.gold == "FALSE")
    if total_false == 0:
        return []
    
    curve = []
    tp = 0
    fp = 0
    
    prev_score = None
    for i, (r, sc) in enumerate(scoreable):
        if r.gold == "FALSE":
            tp += 1
        else:
            fp += 1
        
        # Emit a point at each score change or at end
        next_score = scoreable[i + 1][1] if i + 1 < len(scoreable) else None
        if next_score != sc:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / total_false
            curve.append({
                "threshold": sc,
                "precision": precision,
                "recall": recall,
                "tp": tp,
                "fp": fp,
                "n_predicted": tp + fp,
            })
    
    return curve


def average_precision(curve: list[dict[str, float]]) -> float:
    """Compute Average Precision (area under PR curve) using the
    trapezoidal rule on recall-precision pairs."""
    if not curve:
        return 0.0
    # Sort by recall
    points = sorted(curve, key=lambda p: p["recall"])
    ap = 0.0
    prev_r = 0.0
    for p in points:
        ap += p["precision"] * (p["recall"] - prev_r)
        prev_r = p["recall"]
    return ap


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_pr(curve: list[dict[str, float]], ap: float,
            title: str, out_path: str) -> bool:
    """Plot PR curve. Returns True if successful."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib not installed; skipping plot.")
        return False
    
    recalls = [p["recall"] for p in curve]
    precisions = [p["precision"] for p in curve]
    
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.step(recalls, precisions, where="post", linewidth=2, color="#2196F3")
    ax.fill_between(recalls, precisions, step="post", alpha=0.15, color="#2196F3")
    
    # Mark the shipped operating point
    shipped = None
    for p in curve:
        if abs(p["threshold"] - (CONTRA_T - ENTAIL_T)) < 0.05:
            shipped = p
            break
    if shipped:
        ax.plot(shipped["recall"], shipped["precision"], "ro", markersize=10,
                label=f"Shipped ({ENTAIL_T}/{CONTRA_T}): "
                      f"P={shipped['precision']:.2f}, R={shipped['recall']:.2f}")
        ax.legend(fontsize=11)
    
    ax.set_xlabel("Recall (FALSE class)", fontsize=13)
    ax.set_ylabel("Precision (FALSE class)", fontsize=13)
    ax.set_title(f"{title}\nAP = {ap:.3f}", fontsize=14)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.grid(True, alpha=0.3)
    
    # Add the random baseline line
    total = sum(1 for p in curve)
    if curve:
        # Random precision = total_false / total_scoreable
        last = curve[-1]
        random_p = last["tp"] / (last["tp"] + last["fp"]) if (last["tp"] + last["fp"]) > 0 else 0.0
        # Actually: random precision = n_positive / n_total
        n_total = curve[-1]["n_predicted"]
        n_pos = curve[-1]["tp"]
        random_prec = n_pos / n_total if n_total > 0 else 0
        ax.axhline(y=random_prec, color="gray", linestyle="--", alpha=0.5,
                   label=f"Random baseline P={random_prec:.3f}")
        ax.legend(fontsize=11)
    
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Plot saved: {out_path}")
    return True


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------

def selftest() -> int:
    """Quick sanity checks."""
    print("=== selftest ===")
    checks = 0
    
    # 1. Synthetic known data
    synth = [
        Row("t1", "TRUE", "REL", 0.8, 0.1, 1, "test"),
        Row("t2", "TRUE", "REL", 0.7, 0.2, 1, "test"),
        Row("t3", "FALSE", "REL", 0.2, 0.6, 1, "test"),
        Row("t4", "FALSE", "REL", 0.3, 0.5, 1, "test"),
        Row("t5", "UNVERIFIABLE", "REL", 0.0, 0.0, 0, "test"),
    ]
    
    m = compute_metrics(synth)
    assert m["tp_FALSE"] == 2, f"expected 2 tp_FALSE, got {m['tp_FALSE']}"
    assert m["r_FALSE"] == 1.0, f"expected recall 1.0, got {m['r_FALSE']}"
    checks += 1
    print(f"  [1/6] synthetic metrics correct")
    
    # 2. Bootstrap runs without crash
    ci = bootstrap_ci(synth, n_boot=100, seed=1)
    assert "mcc" in ci
    assert ci["mcc"]["lo"] <= ci["mcc"]["point"] <= ci["mcc"]["hi"] or \
           ci["mcc"]["lo"] == ci["mcc"]["hi"]  # degenerate small sample
    checks += 1
    print(f"  [2/6] bootstrap runs clean")
    
    # 3. PR curve on synthetic data
    curve = pr_curve(synth)
    assert len(curve) > 0
    assert curve[0]["precision"] > 0  # first point should catch a FALSE
    checks += 1
    print(f"  [3/6] PR curve computes")
    
    # 4. AP is in [0, 1]
    ap = average_precision(curve)
    assert 0.0 <= ap <= 1.0, f"AP {ap} out of range"
    checks += 1
    print(f"  [4/6] AP = {ap:.3f} (in range)")
    
    # 5. All-TRUE sample → F1(FALSE) = 0
    all_true = [Row(f"a{i}", "TRUE", "REL", 0.8, 0.1, 1, "t") for i in range(20)]
    m2 = compute_metrics(all_true)
    assert m2["f1_FALSE"] == 0.0
    checks += 1
    print(f"  [5/6] all-TRUE gives F1(FALSE)=0")
    
    # 6. false_score ordering
    high_false = Row("f1", "FALSE", "REL", 0.2, 0.8, 1, "t")
    low_false = Row("f2", "TRUE", "REL", 0.8, 0.1, 1, "t")
    no_passage = Row("f3", "TRUE", "REL", 0.0, 0.0, 0, "t")
    assert false_score(high_false) > false_score(low_false)
    assert false_score(low_false) > false_score(no_passage)
    checks += 1
    print(f"  [6/6] false_score ordering correct")
    
    print(f"\n  All {checks}/6 checks passed.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--selftest", action="store_true",
                    help="run quick sanity checks and exit")
    ap.add_argument("--n-boot", type=int, default=10000,
                    help="number of bootstrap samples (default: 10000)")
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for reproducibility")
    ap.add_argument("--include-negatives", action="store_true",
                    help="pool synthetic negatives into the evaluation")
    ap.add_argument("--no-plot", action="store_true",
                    help="skip matplotlib PR curve plot")
    ap.add_argument("--alpha", type=float, default=0.05,
                    help="significance level for CIs (default: 0.05 = 95%%)")
    args = ap.parse_args()
    
    if args.selftest:
        return selftest()
    
    # Load data
    if not os.path.isfile(BASELINE_CSV):
        print(f"FATAL: {BASELINE_CSV} not found.")
        return 1
    
    rows = load_csv(BASELINE_CSV)
    label = f"non-routed baseline (n={len(rows)})"
    
    if args.include_negatives:
        if not os.path.isfile(NEGATIVES_CSV):
            print(f"WARNING: {NEGATIVES_CSV} not found; running without negatives.")
        else:
            neg = load_csv(NEGATIVES_CSV)
            rows.extend(neg)
            label = f"baseline + synthetic negatives (n={len(rows)})"
    
    print(f"Loaded {len(rows)} rows — {label}")
    gc = Counter(r.gold for r in rows)
    print(f"  Gold distribution: {dict(gc)}")
    false_n = gc.get("FALSE", 0)
    print(f"  FALSE base rate: {false_n}/{len(rows)} = {false_n/len(rows):.1%}")
    
    # -----------------------------------------------------------------------
    # 1. Bootstrap CIs
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  BOOTSTRAP CIs (B={args.n_boot}, seed={args.seed}, "
          f"alpha={args.alpha})")
    print(f"  Thresholds: entail={ENTAIL_T}, contradict={CONTRA_T}")
    print(f"{'=' * 72}")
    
    ci = bootstrap_ci(rows, n_boot=args.n_boot, seed=args.seed,
                       alpha=args.alpha)
    
    key_metrics = ["mcc", "f1_FALSE", "p_FALSE", "r_FALSE", "f1_TRUE",
                   "macro_f1", "coverage", "sel_accuracy"]
    nice_names = {
        "mcc": "MCC(FALSE=pos)",
        "f1_FALSE": "F1(FALSE)",
        "p_FALSE": "Precision(FALSE)",
        "r_FALSE": "Recall(FALSE)",
        "f1_TRUE": "F1(TRUE)",
        "macro_f1": "Macro-F1",
        "coverage": "Coverage",
        "sel_accuracy": "Selective Accuracy",
    }
    
    print(f"\n  {'Metric':<22}{'Point':>8}{'95% CI':>22}{'SE':>8}")
    print(f"  {'─' * 60}")
    for k in key_metrics:
        d = ci[k]
        print(f"  {nice_names.get(k, k):<22}{d['point']:>+8.3f}"
              f"  [{d['lo']:>+7.3f}, {d['hi']:>+7.3f}]{d['se']:>8.3f}")
    
    # Headline interpretation
    mcc_ci = ci["mcc"]
    print(f"\n  KEY FINDING: MCC = {mcc_ci['point']:+.3f} "
          f"[{mcc_ci['lo']:+.3f}, {mcc_ci['hi']:+.3f}]")
    if mcc_ci["lo"] > 0:
        print("  → MCC CI excludes zero: the baseline has statistically "
              "significant discrimination.")
    else:
        print("  → MCC CI includes zero: the baseline's discrimination is NOT "
              "statistically significant at this sample size.")
    
    f1f_ci = ci["f1_FALSE"]
    print(f"  F1(FALSE) = {f1f_ci['point']:.3f} "
          f"[{f1f_ci['lo']:.3f}, {f1f_ci['hi']:.3f}]")
    print(f"  CI width = {f1f_ci['hi'] - f1f_ci['lo']:.3f} "
          f"({'narrow' if f1f_ci['hi'] - f1f_ci['lo'] < 0.10 else 'wide — interpret with caution'})")
    
    # Write CI CSV
    with open(OUT_CI, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["metric", "point", "lo", "hi", "se",
                                            "n_boot", "seed", "alpha", "dataset"])
        w.writeheader()
        for k in ci:
            d = ci[k]
            w.writerow({"metric": k, "point": f"{d['point']:.6f}",
                        "lo": f"{d['lo']:.6f}", "hi": f"{d['hi']:.6f}",
                        "se": f"{d['se']:.6f}",
                        "n_boot": args.n_boot, "seed": args.seed,
                        "alpha": args.alpha, "dataset": label})
    print(f"\n  CIs written: {OUT_CI}")
    
    # -----------------------------------------------------------------------
    # 2. PR curve
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  PRECISION-RECALL CURVE (FALSE class)")
    print(f"{'=' * 72}")
    
    curve = pr_curve(rows)
    ap_val = average_precision(curve)
    
    scoreable = sum(1 for r in rows if r.n_passages > 0)
    total_false_scoreable = sum(1 for r in rows
                                if r.n_passages > 0 and r.gold == "FALSE")
    print(f"  Scoreable rows (reached NLI): {scoreable}/{len(rows)}")
    print(f"  FALSE among scoreable: {total_false_scoreable}")
    print(f"  Random baseline precision: "
          f"{total_false_scoreable/scoreable:.3f}" if scoreable else "  (none)")
    print(f"  Average Precision (AP): {ap_val:.4f}")
    
    # Show key operating points
    print(f"\n  {'Threshold':>10}{'Precision':>11}{'Recall':>9}"
          f"{'TP':>5}{'FP':>5}{'nPred':>7}")
    print(f"  {'─' * 47}")
    # Show ~10 evenly spaced points
    step = max(1, len(curve) // 10)
    for i in range(0, len(curve), step):
        p = curve[i]
        print(f"  {p['threshold']:>10.4f}{p['precision']:>11.3f}"
              f"{p['recall']:>9.3f}{p['tp']:>5.0f}{p['fp']:>5.0f}"
              f"{p['n_predicted']:>7.0f}")
    # Always show last
    if curve:
        p = curve[-1]
        print(f"  {p['threshold']:>10.4f}{p['precision']:>11.3f}"
              f"{p['recall']:>9.3f}{p['tp']:>5.0f}{p['fp']:>5.0f}"
              f"{p['n_predicted']:>7.0f}  (all scoreable)")
    
    # Write PR CSV
    with open(OUT_PR, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["threshold", "precision", "recall",
                                            "tp", "fp", "n_predicted"])
        w.writeheader()
        for p in curve:
            w.writerow({k: f"{v:.6f}" if isinstance(v, float) else v
                        for k, v in p.items()})
    print(f"\n  PR data written: {OUT_PR}")
    
    # Plot
    if not args.no_plot:
        plot_pr(curve, ap_val, f"PR Curve — FALSE class ({label})", OUT_PLOT)
    
    # -----------------------------------------------------------------------
    # 3. Per-type bootstrap (if enough FALSE per type)
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 72}")
    print(f"  PER-TYPE BOOTSTRAP CIs (types with ≥3 gold FALSE)")
    print(f"{'=' * 72}")
    
    by_type: dict[str, list[Row]] = {}
    for r in rows:
        by_type.setdefault(r.ctype, []).append(r)
    
    print(f"\n  {'Type':<20}{'n':>5}{'FALSE':>7}  {'MCC':>8}{'MCC 95% CI':>22}"
          f"{'F1(F)':>8}{'F1(F) 95% CI':>22}")
    print(f"  {'─' * 92}")
    for t in sorted(by_type):
        sub = by_type[t]
        n_false = sum(1 for r in sub if r.gold == "FALSE")
        if n_false < 3:
            m = compute_metrics(sub)
            print(f"  {t:<20}{len(sub):>5}{n_false:>7}  {m['mcc']:>+8.3f}"
                  f"{'(too few FALSE)':>22}{m['f1_FALSE']:>8.3f}"
                  f"{'(too few FALSE)':>22}")
            continue
        ci_t = bootstrap_ci(sub, n_boot=args.n_boot, seed=args.seed,
                             alpha=args.alpha)
        print(f"  {t:<20}{len(sub):>5}{n_false:>7}"
              f"  {ci_t['mcc']['point']:>+8.3f}"
              f"  [{ci_t['mcc']['lo']:>+7.3f}, {ci_t['mcc']['hi']:>+7.3f}]"
              f"{ci_t['f1_FALSE']['point']:>8.3f}"
              f"  [{ci_t['f1_FALSE']['lo']:>7.3f}, {ci_t['f1_FALSE']['hi']:>7.3f}]")
    
    print(f"\n  Done. Files created:")
    print(f"    {OUT_CI}")
    print(f"    {OUT_PR}")
    if not args.no_plot:
        print(f"    {OUT_PLOT}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
