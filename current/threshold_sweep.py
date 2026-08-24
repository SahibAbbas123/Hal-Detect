#!/usr/bin/env python3
"""
Threshold sweep over the non-routed baseline's cached NLI scores. ZERO model calls.

WHY
---
The completed baseline run produced 81 FALSE predictions of which only 8 were
correct -- precision 0.099, with 67 gold-TRUE false alarms. The suspected cause is
that `CONTRADICT_THRESHOLD = 0.40` treats "the passage does not support this" as
"the passage contradicts this".

That is a claim about a constant, and the raw `entail` / `contradict` scores are
already in `nonrouted_baseline_results.csv`. So the entire threshold surface is
recomputable arithmetically -- no Wikipedia, no Gemini, no BART. This turns "0.40
is too low" from an assertion into a measured curve.

THE DECISION RULE BEING SWEPT (copied from phase3d, order matters)
------------------------------------------------------------------
    if   best_entail     >= ENTAIL_THRESHOLD:      TRUE
    elif best_contradict >= CONTRADICT_THRESHOLD:  FALSE
    else:                                          UNVERIFIABLE

Entailment is tested FIRST, so a passage scoring entail 0.6 / contradict 0.9
returns TRUE. That asymmetry is part of the rule and is preserved here.

THE COVERAGE CEILING -- WHY THRESHOLDS CANNOT REACH EVERY CLAIM
---------------------------------------------------------------
A row with `scored_passages == 0` abstained *before* NLI ever ran: no Wikipedia
page resolved, or no passage cleared the SBERT similarity threshold. Those rows
have entail = contradict = 0 and **cannot become TRUE or FALSE at any threshold.**
They are held at UNVERIFIABLE throughout, which is what makes the reported
coverage honest rather than an artifact of treating 0.0 as a real score.

WHAT TO LOOK FOR
----------------
1. Does raising the contradiction threshold trade the 67 false alarms for the 8
   real catches, or does it kill precision and recall together? If FALSE recall
   collapses before precision rises, the threshold is not the real problem and the
   contradiction signal itself is uninformative -- a much stronger claim.
2. **Do different claim types want different thresholds?** If they do, that is a
   quantitative argument for routing from *inside* a single verifier, independent
   of whether the per-type verifiers work. It would be the cleanest RQ2 evidence
   available while TEMPORAL/EA/QUANTITATIVE remain at 0% coverage.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import metrics as M   # noqa: E402

RESULTS = os.path.join(HERE, "nonrouted_baseline_results.csv")
OUT_CSV = os.path.join(HERE, "threshold_sweep.csv")

# phase3d's shipped values, for reference lines in the output.
SHIPPED_ENTAIL = 0.50
SHIPPED_CONTRADICT = 0.40

TYPES = ("RELATIONAL", "TEMPORAL", "QUANTITATIVE", "ENTITY_ATTRIBUTE", "CITATION")


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        if not (r.get("gold_verdict") or "").strip():
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


def verdicts(rows: list[dict], et: float, ct: float) -> list[str]:
    """Recompute verdicts under (entail, contradict) thresholds."""
    out = []
    for r in rows:
        if r["_n"] == 0:
            out.append("UNVERIFIABLE")      # never reached NLI; cannot be moved
        elif r["_e"] >= et:
            out.append("TRUE")
        elif r["_c"] >= ct:
            out.append("FALSE")
        else:
            out.append("UNVERIFIABLE")
    return out


def score(rows: list[dict], et: float, ct: float) -> dict:
    gold = [r["gold_verdict"] for r in rows]
    pred = verdicts(rows, et, ct)
    sel = M.selective(gold, pred)
    prf = M.per_class_prf(gold, pred)
    return {
        "entail_t": et, "contradict_t": ct,
        "coverage": sel["coverage"], "accuracy": sel["accuracy"],
        "covered": sel["covered"], "correct": sel["correct"],
        "overreach": sel["overreach"],
        "f1_TRUE": prf["TRUE"]["f1"],
        "p_FALSE": prf["FALSE"]["precision"],
        "r_FALSE": prf["FALSE"]["recall"],
        "f1_FALSE": prf["FALSE"]["f1"],
        "n_pred_FALSE": prf["FALSE"]["predicted"],
        "tp_FALSE": prf["FALSE"]["tp"],
        "macro_f1": M.macro_f1(gold, pred),
        "mcc": M.mcc(gold, pred),
    }


def sweep_contradict(rows: list[dict], et: float, label: str) -> list[dict]:
    print(f"\n{'=' * 78}")
    print(f"  CONTRADICTION THRESHOLD SWEEP -- {label}  (entail fixed at {et})")
    print(f"{'=' * 78}")
    print(f"  {'ct':>5} {'cov':>7} {'acc':>7} | {'nFALSE':>7} {'tp':>3} "
          f"{'P':>6} {'R':>6} {'F1':>6} | {'MCC':>7} {'macroF1':>8}")
    grid = [round(0.30 + 0.05 * i, 2) for i in range(15)]   # 0.30 .. 1.00
    out = []
    for ct in grid:
        s = score(rows, et, ct)
        out.append(s)
        mark = "  <-- shipped" if abs(ct - SHIPPED_CONTRADICT) < 1e-9 else ""
        print(f"  {ct:>5.2f} {s['coverage']:>7.1%} {s['accuracy']:>7.1%} | "
              f"{s['n_pred_FALSE']:>7} {s['tp_FALSE']:>3} "
              f"{s['p_FALSE']:>6.3f} {s['r_FALSE']:>6.3f} {s['f1_FALSE']:>6.3f} | "
              f"{s['mcc']:>+7.3f} {s['macro_f1']:>8.3f}{mark}")
    return out


def sweep_grid(rows: list[dict]) -> list[dict]:
    # Entail grid starts at 0.20, not 0.35: in the first run every per-type
    # optimum landed exactly on the old 0.35 floor, which is the signature of a
    # grid that is too narrow to contain the optimum.
    ets = [round(0.20 + 0.05 * i, 2) for i in range(15)]     # 0.20 .. 0.90
    cts = [round(0.30 + 0.05 * i, 2) for i in range(15)]     # 0.30 .. 1.00
    return [score(rows, et, ct) for et in ets for ct in cts]


def best(results: list[dict], key: str, min_cov: float = 0.0) -> dict:
    pool = [r for r in results if r["coverage"] >= min_cov]
    return max(pool, key=lambda r: r[key]) if pool else {}


def report_best(results: list[dict], label: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  BEST OPERATING POINTS -- {label}")
    print(f"{'=' * 78}")
    shipped = next((r for r in results
                    if abs(r["entail_t"] - SHIPPED_ENTAIL) < 1e-9
                    and abs(r["contradict_t"] - SHIPPED_CONTRADICT) < 1e-9), None)
    rows = []
    if shipped:
        rows.append(("shipped (0.50/0.40)", shipped))
    for crit, lab in (("mcc", "max MCC"), ("f1_FALSE", "max F1(FALSE)"),
                      ("macro_f1", "max macro-F1")):
        b = best(results, crit)
        if b:
            rows.append((f"{lab} ({b['entail_t']:.2f}/{b['contradict_t']:.2f})", b))
    b = best(results, "mcc", min_cov=0.70)
    if b:
        rows.append((f"max MCC, cov>=70% ({b['entail_t']:.2f}/{b['contradict_t']:.2f})", b))

    print(f"  {'point':<34}{'cov':>7}{'acc':>7}{'F1(F)':>7}{'P(F)':>7}"
          f"{'R(F)':>7}{'MCC':>8}")
    for lab, s in rows:
        print(f"  {lab:<34}{s['coverage']:>7.1%}{s['accuracy']:>7.1%}"
              f"{s['f1_FALSE']:>7.3f}{s['p_FALSE']:>7.3f}{s['r_FALSE']:>7.3f}"
              f"{s['mcc']:>+8.3f}")


def report_per_type(rows: list[dict]) -> None:
    """The question that matters for RQ2: does the optimum move by claim type?"""
    print(f"\n{'=' * 78}")
    print("  PER-TYPE OPTIMA -- does each type want a different threshold?")
    print(f"{'=' * 78}")
    print(f"  {'type':<18}{'n':>4} | {'best e/c':>11}{'cov':>7}{'acc':>7}"
          f"{'MCC':>8} | {'shipped MCC':>12}{'delta':>8}")
    for t in TYPES:
        sub = [r for r in rows if (r.get("type") or "").upper() == t]
        if len(sub) < 5:
            continue
        res = sweep_grid(sub)
        b = best(res, "mcc")
        sh = next((r for r in res
                   if abs(r["entail_t"] - SHIPPED_ENTAIL) < 1e-9
                   and abs(r["contradict_t"] - SHIPPED_CONTRADICT) < 1e-9), None)
        shmcc = sh["mcc"] if sh else float("nan")
        print(f"  {t:<18}{len(sub):>4} | "
              f"{b['entail_t']:>5.2f}/{b['contradict_t']:<5.2f}"
              f"{b['coverage']:>7.1%}{b['accuracy']:>7.1%}{b['mcc']:>+8.3f} | "
              f"{shmcc:>+12.3f}{b['mcc'] - shmcc:>+8.3f}")
    print("\n  If the best e/c column is NOT constant down the rows, a single")
    print("  global threshold is leaving performance on the table -- which is a")
    print("  routing argument measurable from inside one verifier, and does not")
    print("  depend on the per-type verifiers working.")


def report_ceiling(rows: list[dict]) -> None:
    reached = sum(1 for r in rows if r["_n"] > 0)
    print(f"\n{'=' * 78}")
    print("  COVERAGE CEILING (thresholds cannot move these)")
    print(f"{'=' * 78}")
    print(f"  NLI actually scored a passage : {reached}/{len(rows)} "
          f"({reached / len(rows):.1%})")
    print(f"  abstained before NLI          : {len(rows) - reached} "
          f"(no page, or no passage cleared the SBERT gate)")
    print("  No threshold change can lift coverage above the first number.")
    print("  Raising it is a RETRIEVAL problem, not a threshold problem.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sweep NLI thresholds over cached baseline scores. "
                    "No model calls.")
    ap.add_argument("--results", default=RESULTS)
    ap.add_argument("--human-only", action="store_true",
                    help="restrict to b1+b3 (human-labeled) as a robustness check")
    ap.add_argument("--write", action="store_true",
                    help=f"write the full grid to {os.path.basename(OUT_CSV)}")
    args = ap.parse_args()

    if not os.path.isfile(args.results):
        print(f"FATAL: {args.results} not found. Run the baseline first.")
        return 1

    rows = load(args.results)
    label = "all labeled"
    if args.human_only:
        rows = [r for r in rows if r.get("batch") in ("b1", "b3")]
        label = "human-labeled only (b1+b3)"
    print(f"loaded {len(rows)} rows -- {label}")
    print(f"shipped thresholds: entail {SHIPPED_ENTAIL}, "
          f"contradict {SHIPPED_CONTRADICT}")

    report_ceiling(rows)
    sweep_contradict(rows, SHIPPED_ENTAIL, label)
    grid = sweep_grid(rows)
    report_best(grid, label)
    report_per_type(rows)

    if args.write:
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(grid[0].keys()))
            w.writeheader()
            w.writerows(grid)
        print(f"\nwrote {OUT_CSV} ({len(grid)} grid points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
