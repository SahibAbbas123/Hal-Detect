#!/usr/bin/env python3
"""
Reusable evaluation metrics for HalDetect. Import this from any verifier or
baseline; do not re-implement these per-verifier.

WHY THIS EXISTS
---------------
`reference/paper_findings_2026-08-22.md` action items #3, #4 and #5 all say the
same thing: the project's headline numbers are reported in a form that a reviewer
can dismantle.

* **#3 Per-class F1 + degenerate baselines.** Factcheck-Bench Table 5 shows
  Always-True scoring **F1 = 0.88 on the True class and 0.00 on False**. Our gold
  set is 314 TRUE / 13 FALSE / 29 UNVERIFIABLE, so an unconditional "TRUE" scores
  **88.2%** accuracy. Accuracy alone is therefore uninterpretable here.
* **#4 Wilson CIs.** RELATIONAL's "80.77%" rests on ~26 covered claims -> 95% CI
  [62.1%, 91.5%], which cannot separate 80% from 65%.
* **#5 Risk-coverage curve + AURAC.** Our system abstains by design; a verifier
  answering 55% of claims is not comparable *at a point* to one answering 100%.
  AURAC (from the semantic-entropy Nature paper) is the citable scalar that
  rewards correct abstention.

THE ABSTENTION SUBTLETY -- READ BEFORE USING
--------------------------------------------
`UNVERIFIABLE` means two different things in this project and conflating them is
a real methodological error:

* **gold UNVERIFIABLE** (29 claims) = not checkable even in principle.
* **predicted UNVERIFIABLE** = this verifier could not reach evidence (abstention).

So two views are reported side by side, never merged:

1.  **Selective view** (the one our design is built for). Coverage = fraction
    predicted TRUE/FALSE. Selective accuracy is computed on covered claims only.
    A confident TRUE/FALSE on a *gold-UNVERIFIABLE* claim counts as an **error** --
    the verifier claimed to know something unknowable.
2.  **Three-way view** (for comparability with RealFactBench, which reports
    Macro-F1 + MCC + Unknown Rate). UNVERIFIABLE is treated as a real class.

Note what we deliberately do NOT do: Factcheck-Bench and OpenFactCheck fold NEI
into the False class, which makes honest abstention unscoreable. Do not frame
our results against those.
"""

from __future__ import annotations

import math
from collections import Counter

LABELS = ("TRUE", "FALSE", "UNVERIFIABLE")
DECIDED = ("TRUE", "FALSE")


# ---------------------------------------------------------------------------
# Intervals
# ---------------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval -> (point, lo, hi). Correct at small n, unlike normal
    approximation, which is why it is used throughout."""
    if n <= 0:
        return 0.0, 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, max(0.0, c - h), min(1.0, c + h)


def fmt_ci(k: int, n: int) -> str:
    p, lo, hi = wilson(k, n)
    return f"{p:6.1%}  [{lo:5.1%}, {hi:5.1%}]  n={n}"


# ---------------------------------------------------------------------------
# Per-class P/R/F1
# ---------------------------------------------------------------------------

def per_class_prf(gold: list[str], pred: list[str],
                  labels: tuple[str, ...] = LABELS) -> dict[str, dict[str, float]]:
    """Per-class precision / recall / F1 / support. No averaging -- averaging is
    what hides a 0.00 on the minority class."""
    assert len(gold) == len(pred), "gold/pred length mismatch"
    out: dict[str, dict[str, float]] = {}
    for lab in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == lab and p == lab)
        fp = sum(1 for g, p in zip(gold, pred) if g != lab and p == lab)
        fn = sum(1 for g, p in zip(gold, pred) if g == lab and p != lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out[lab] = {"precision": prec, "recall": rec, "f1": f1,
                    "support": tp + fn, "predicted": tp + fp, "tp": tp}
    return out


def macro_f1(gold: list[str], pred: list[str],
             labels: tuple[str, ...] = LABELS) -> float:
    """Macro-F1 over classes that actually occur in gold. Classes with zero gold
    support are skipped rather than contributing a spurious 0.0."""
    prf = per_class_prf(gold, pred, labels)
    present = [lab for lab in labels if prf[lab]["support"] > 0]
    if not present:
        return 0.0
    return sum(prf[lab]["f1"] for lab in present) / len(present)


def mcc(gold: list[str], pred: list[str], positive: str = "FALSE") -> float:
    """Matthews correlation, binarised on `positive` (default FALSE = "is a
    hallucination"). RealFactBench reports MCC; it is far more honest than
    accuracy under our 24:1 class imbalance."""
    tp = sum(1 for g, p in zip(gold, pred) if g == positive and p == positive)
    tn = sum(1 for g, p in zip(gold, pred) if g != positive and p != positive)
    fp = sum(1 for g, p in zip(gold, pred) if g != positive and p == positive)
    fn = sum(1 for g, p in zip(gold, pred) if g == positive and p != positive)
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn - fp * fn) / denom) if denom else 0.0


def unknown_rate(pred: list[str]) -> float:
    """RealFactBench's UnR. Framed there as two-sided -- it measures
    "over-conservatism or over-confidence", so a nonzero UnR is not automatically
    bad. Do not report it as a penalty."""
    if not pred:
        return 0.0
    return sum(1 for p in pred if p not in DECIDED) / len(pred)


# ---------------------------------------------------------------------------
# Degenerate baselines -- the point of #3
# ---------------------------------------------------------------------------

def degenerate_baselines(gold: list[str]) -> dict[str, dict]:
    """Always-True / Always-False / Random, scored the same way as a real system.
    If a real system does not clearly beat these, it has shown nothing."""
    n = len(gold)
    res: dict[str, dict] = {}

    for name, const in (("Always-True", "TRUE"), ("Always-False", "FALSE"),
                        ("Always-UNVERIFIABLE", "UNVERIFIABLE")):
        pred = [const] * n
        prf = per_class_prf(gold, pred)
        res[name] = {
            "accuracy": sum(1 for g in gold if g == const) / n if n else 0.0,
            "macro_f1": macro_f1(gold, pred),
            "mcc": mcc(gold, pred),
            "f1_TRUE": prf["TRUE"]["f1"],
            "f1_FALSE": prf["FALSE"]["f1"],
        }

    # Random: analytic expectation over a uniform draw from the 3 labels, so it
    # is deterministic and needs no seed.
    counts = Counter(gold)
    exp_acc = sum(counts[lab] for lab in LABELS) / (3 * n) if n else 0.0
    res["Random (uniform, analytic)"] = {
        "accuracy": exp_acc, "macro_f1": float("nan"), "mcc": 0.0,
        "f1_TRUE": float("nan"), "f1_FALSE": float("nan"),
    }
    return res


# ---------------------------------------------------------------------------
# Selective prediction: risk-coverage + AURAC
# ---------------------------------------------------------------------------

def risk_coverage(gold: list[str], pred: list[str],
                  conf: list[float]) -> list[tuple[float, float, int]]:
    """Rejection-accuracy curve. Sort by confidence descending; at each prefix
    report (coverage, accuracy_on_that_prefix, n). Abstentions (pred not in
    TRUE/FALSE) are treated as zero-confidence and land at the tail.

    A confident verdict on a gold-UNVERIFIABLE claim counts as WRONG.
    """
    rows = []
    for g, p, c in zip(gold, pred, conf):
        eff = c if p in DECIDED else -1.0
        rows.append((eff, g, p))
    rows.sort(key=lambda r: r[0], reverse=True)

    n = len(rows)
    curve: list[tuple[float, float, int]] = []
    correct = 0
    for i, (_, g, p) in enumerate(rows, start=1):
        if p in DECIDED and p == g:
            correct += 1
        curve.append((i / n, correct / i, i))
    return curve


def aurac(gold: list[str], pred: list[str], conf: list[float]) -> float:
    """Area under the rejection-accuracy curve (semantic-entropy paper). Scalar
    that REWARDS correct abstention -- unlike accuracy, which is blind to it, and
    unlike coverage, which is blind to correctness."""
    curve = risk_coverage(gold, pred, conf)
    if not curve:
        return 0.0
    return sum(a for _, a, _ in curve) / len(curve)


def selective(gold: list[str], pred: list[str]) -> dict:
    """The selective view: coverage, and accuracy on covered claims only."""
    n = len(gold)
    covered = [(g, p) for g, p in zip(gold, pred) if p in DECIDED]
    k = sum(1 for g, p in covered if g == p)
    cov_p, cov_lo, cov_hi = wilson(len(covered), n)
    acc_p, acc_lo, acc_hi = wilson(k, len(covered))
    # How much of the error is "confidently answered something unknowable"
    overreach = sum(1 for g, p in covered if g == "UNVERIFIABLE")
    return {
        "n": n, "covered": len(covered), "correct": k,
        "coverage": cov_p, "coverage_ci": (cov_lo, cov_hi),
        "accuracy": acc_p, "accuracy_ci": (acc_lo, acc_hi),
        "overreach": overreach,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(gold: list[str], pred: list[str], conf: list[float] | None = None,
           title: str = "") -> None:
    """Print the full table. This is the format every HalDetect result should be
    reported in from now on -- never a bare accuracy figure."""
    if conf is None:
        conf = [1.0 if p in DECIDED else 0.0 for p in pred]
    n = len(gold)
    if n == 0:
        print(f"\n=== {title} === (no rows)")
        return

    print(f"\n{'=' * 72}")
    print(f"  {title}   (n={n})")
    print(f"{'=' * 72}")

    sel = selective(gold, pred)
    print("\n-- Selective view (our design's own terms) --")
    print(f"  Coverage          {sel['coverage']:6.1%}  "
          f"[{sel['coverage_ci'][0]:.1%}, {sel['coverage_ci'][1]:.1%}]  "
          f"({sel['covered']}/{n} answered)")
    print(f"  Selective acc.    {sel['accuracy']:6.1%}  "
          f"[{sel['accuracy_ci'][0]:.1%}, {sel['accuracy_ci'][1]:.1%}]  "
          f"({sel['correct']}/{sel['covered']} correct)")
    if sel["covered"]:
        eff = sel["covered"]
        print(f"  Effective n for that accuracy = {eff}  "
              f"(coverage x n, NOT dataset size)")
    if sel["overreach"]:
        print(f"  !! {sel['overreach']} confident verdict(s) on gold-UNVERIFIABLE "
              f"claims -- answered something unknowable, counted as errors")
    print(f"  AURAC             {aurac(gold, pred, conf):6.3f}   "
          f"(area under rejection-accuracy curve; rewards correct abstention)")

    print("\n-- Three-way view (UNVERIFIABLE as a real class; RealFactBench-style) --")
    prf = per_class_prf(gold, pred)
    print(f"  {'class':<14}{'P':>8}{'R':>8}{'F1':>8}{'support':>9}{'predicted':>11}")
    for lab in LABELS:
        d = prf[lab]
        print(f"  {lab:<14}{d['precision']:>8.2f}{d['recall']:>8.2f}"
              f"{d['f1']:>8.2f}{d['support']:>9}{d['predicted']:>11}")
    print(f"  Macro-F1 {macro_f1(gold, pred):.3f}   "
          f"MCC(FALSE=positive) {mcc(gold, pred):+.3f}   "
          f"UnR {unknown_rate(pred):.1%}")

    print("\n-- Degenerate baselines (must be beaten to have shown anything) --")
    print(f"  {'baseline':<28}{'acc':>8}{'macroF1':>9}{'F1(TRUE)':>10}"
          f"{'F1(FALSE)':>11}{'MCC':>8}")
    for name, d in degenerate_baselines(gold).items():
        mf = "  n/a" if math.isnan(d["macro_f1"]) else f"{d['macro_f1']:.2f}"
        ft = "  n/a" if math.isnan(d["f1_TRUE"]) else f"{d['f1_TRUE']:.2f}"
        ff = "  n/a" if math.isnan(d["f1_FALSE"]) else f"{d['f1_FALSE']:.2f}"
        print(f"  {name:<28}{d['accuracy']:>8.1%}{mf:>9}{ft:>10}{ff:>11}"
              f"{d['mcc']:>+8.2f}")

    gold_counts = Counter(gold)
    if gold_counts.get("FALSE", 0) == 0:
        print("\n  !! ZERO gold negatives. Accuracy and F1(FALSE) here are "
              "uninformative by construction.")
        print("     Measure discrimination by controlled perturbation instead.")
    elif gold_counts.get("FALSE", 0) < 10:
        print(f"\n  !! Only {gold_counts['FALSE']} gold negative(s). F1(FALSE) is "
              f"extremely high-variance; report its CI or don't report it.")


def curve_table(gold: list[str], pred: list[str], conf: list[float],
                steps: int = 10) -> None:
    """Print the risk-coverage curve at `steps` operating points. This is the
    shape to compare a baseline against -- per paper_findings section 7, an
    abstaining system and a always-answering one are comparable as CURVES, not
    at a point."""
    curve = risk_coverage(gold, pred, conf)
    if not curve:
        return
    print(f"\n-- Risk-coverage curve --")
    print(f"  {'coverage':>10}{'accuracy':>10}{'n':>7}")
    for i in range(1, steps + 1):
        target = i / steps
        pick = min(curve, key=lambda r: abs(r[0] - target))
        print(f"  {pick[0]:>10.1%}{pick[1]:>10.1%}{pick[2]:>7}")


if __name__ == "__main__":
    # Self-check on the project's own real pooled distribution:
    # 314 TRUE / 13 FALSE / 29 UNVERIFIABLE = 356.
    gold = ["TRUE"] * 314 + ["FALSE"] * 13 + ["UNVERIFIABLE"] * 29
    print("Sanity check against the pooled real gold set (356 claims).")
    print("Expect Always-True accuracy = 88.2% with F1(FALSE) = 0.00 --")
    print("this is the number every HalDetect accuracy claim must beat.\n")
    report(gold, ["TRUE"] * len(gold), title="Always-True on pooled real gold")
