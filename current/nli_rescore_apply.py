#!/usr/bin/env python3
"""Apply Colab-computed NLI scores under collision-free keys and report movement.

This is step 3 of the #16 rescore:

    1. current/nli_rescore_prep.py   (Mac, offline)  -> work-list JSON
    2. Colab notebook                (GPU-class box) -> scores JSON
    3. THIS SCRIPT                   (Mac, offline)  -> new results CSV + report

WHY THE VERDICT RULE IS NOT REIMPLEMENTED HERE
----------------------------------------------
It would be four lines to copy phase3d's threshold ladder, and copying it is
exactly how `property_resolver.py` came to hold 1 of 3 resolver fixes. So this
script calls phase3d's OWN `run_nli_on_passages()` and the baseline's OWN
`margin_verdict()`. The only thing it does itself is decide which cache entry
each (claim, passage) pair reads.

HOW THE COLLISION IS ELIMINATED WITHOUT TOUCHING phase3d
--------------------------------------------------------
The collision is a property of a SHARED cache: two claims whose `claim[:60]`
agree land on one entry. So each claim is scored against a FRESH single-claim
cache, seeded only with its own passages. A one-claim cache cannot collide with
another claim, by construction -- no key format change is needed inside phase3d
for the rescore to be correct. (The `nli2__` hashed keys live in the work-list
and the scores file, which is where the fix has to be permanent.)

THREE GUARDS, BECAUSE A SILENT MISS WOULD LOOK LIKE A RESULT
-----------------------------------------------------------
`run_nli_on_passages` calls `get_nli()` unconditionally at line 186 -- before it
ever checks the cache -- and its per-passage `except Exception: continue` would
swallow a failure and silently drop that passage from the max. On this Mac a
BART load SIGBUSes, so a miss would not even fail cleanly. Therefore:

  (a) completeness is asserted BEFORE the call, so a miss is impossible;
  (b) `get_nli` is replaced by a sentinel that RECORDS every invocation, and any
      recorded invocation aborts the run -- the `except` can swallow the raise,
      but it cannot unrecord it (R1a: make the silent skip loud);
  (c) `save_cache` is replaced by a raiser, so nothing can write to the shipped
      12 MB cache from here.

R19: a NEW CSV is written. `nonrouted_baseline_results.csv` and
`nonrouted_negatives_results.csv` are quoted baselines and are never rewritten;
adopting the rescored numbers is a separate, explicit author decision.

USAGE
-----
    # prove the whole path works before Colab, using the RECORDED scores.
    # This must reproduce the recorded verdicts exactly -- if it does, then when
    # the real scores arrive the scores are the only thing that changed.
    python3 current/nli_rescore_apply.py --set both --simulate

    # the real thing
    python3 current/nli_rescore_apply.py --set both \\
        --scores ~/Downloads/nli_rescore_scores_both.json

    python3 current/nli_rescore_apply.py --selftest

Offline. No API key, no network, no model.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from nli_rescore_prep import (           # noqa: E402  (path set above)
    import_phase3d, legacy_key, fixed_key,
)

OUT_COLS = [
    "claim_id", "population", "type", "gold_type", "gold_verdict",
    "base_claim_id", "injection_type", "collision_group",
    "old_entail", "old_contradict", "new_entail", "new_contradict",
    "d_entail", "d_contradict",
    "old_verdict", "new_verdict", "verdict_moved",
    "old_verdict_confidence", "new_verdict_confidence",
    "old_verdict_margin", "new_verdict_margin", "margin_moved",
    "old_correct", "new_correct", "correctness_delta",
    "query_source", "title", "n_passages", "claim",
]


class _NliSentinel:
    """Stands in for the BART pipeline. Records rather than scores."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, passage, **kw):
        self.calls.append(str(passage)[:80])
        raise RuntimeError(
            "BART was invoked -- a (claim, passage) pair was missing from the "
            "seeded cache. This run is void.")


def _seed_for(item: dict, scores: dict, missing: list) -> dict:
    """A fresh one-claim cache, keyed the way phase3d reads keys.

    Reading is by legacy key (phase3d is unmodified); the SOURCE of each score is
    the collision-free hashed key. Within a single-claim cache the legacy key is
    unique, so nothing can be inherited.
    """
    cache: dict = {}
    for p in item["passages"]:
        got = scores.get(p["fixed_key"])
        if not isinstance(got, dict) or "entail" not in got or "contradict" not in got:
            missing.append((item["claim_id"], p["idx"], p["fixed_key"]))
            continue
        cache[legacy_key(item["claim"], p["text"])] = {
            "entail": float(got["entail"]),
            "contradict": float(got["contradict"]),
        }
    return cache


def _correct(gold: str, pred: str) -> bool | None:
    """Selective correctness. UNVERIFIABLE predictions are abstentions.

    R7: a gold-UNVERIFIABLE claim is not made correct by a confident verdict, and
    predicted-UNVERIFIABLE is not the same class as gold-UNVERIFIABLE. Rows that
    abstain return None and are excluded from accuracy, never scored as wrong.
    """
    if pred == "UNVERIFIABLE":
        return None
    return gold == pred


def run(which: str, scores_path: str | None, simulate: bool,
        out_path: str | None) -> int:
    wl_path = os.path.join(HERE, f"nli_rescore_worklist_{which}.json")
    if not os.path.exists(wl_path):
        raise SystemExit(f"work-list not found: {wl_path}\n"
                         f"Run:  python3 current/nli_rescore_prep.py --set {which}")
    with open(wl_path, encoding="utf-8") as fh:
        wl = json.load(fh)
    items = wl["items"]

    if simulate:
        if scores_path:
            raise SystemExit("--simulate and --scores are mutually exclusive")
        # Stand-ins: the RECORDED legacy scores, re-addressed under hashed keys.
        # Feeding the old numbers through the new path must reproduce the old
        # verdicts; that is this mode's entire purpose.
        nb0, p30 = import_phase3d()
        p30.CACHE_FILE = wl["meta"]["cache_used"]
        shipped = p30.load_cache()
        scores = {}
        for it in items:
            for p in it["passages"]:
                got = shipped.get(p["legacy_key"])
                if isinstance(got, dict):
                    scores[p["fixed_key"]] = got
        src_label = "SIMULATED (recorded legacy scores re-addressed)"
    else:
        if not scores_path:
            raise SystemExit("pass --scores <file from Colab>, or --simulate")
        with open(scores_path, encoding="utf-8") as fh:
            blob = json.load(fh)
        scores = blob.get("scores", blob)
        src_label = scores_path
        meta = blob.get("meta", {})
        if meta:
            print(f"scores meta: device={meta.get('device')!r} "
                  f"model={meta.get('model')!r} pairs={meta.get('pairs')} "
                  f"gemini_key_present={meta.get('gemini_key_present')}")
            if meta.get("gemini_key_present"):
                print("  !! a Gemini key was present in the scoring environment. "
                      "That does not affect\n     these scores (retrieval was done "
                      "on the Mac), but note it in any write-up.")

    print(f"work-list  : {wl_path}")
    print(f"             {len(items)} rows / "
          f"{sum(len(i['passages']) for i in items)} pairs, set={wl['meta']['set']}")
    print(f"scores     : {src_label}   ({len(scores)} entries)")

    nb, p3 = import_phase3d()

    # Guards (b) and (c). Installed before any verdict is computed.
    sentinel = _NliSentinel()
    p3.get_nli = lambda: sentinel

    def _no_write(_cache):
        raise RuntimeError("save_cache called -- this script must never write a cache")
    p3.save_cache = _no_write

    # Guard (a): completeness first, so a miss is impossible rather than silent.
    missing: list = []
    seeds = {it["claim_id"]: _seed_for(it, scores, missing) for it in items}
    if missing:
        print(f"\n!! {len(missing)} (claim, passage) pairs have no score:")
        for cid, idx, key in missing[:20]:
            print(f"   {cid:<14} passage {idx}  {key}")
        if len(missing) > 20:
            print(f"   ... and {len(missing) - 20} more")
        raise SystemExit(
            "ABORT. An unscored pair would be dropped by phase3d's per-passage "
            "`except: continue`, silently lowering the max and changing the "
            "verdict for a reason unrelated to the cache key. Re-run the Colab "
            "cell over the full work-list.")

    rows, moved, margin_moved = [], [], []
    for it in items:
        passages = [(p["text"], p["sbert"]) for p in it["passages"]]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):        # phase3d prints per passage
            verdict, conf, _ev = p3.run_nli_on_passages(
                it["claim"], passages, seeds[it["claim_id"]])
        if sentinel.calls:
            raise SystemExit(
                f"ABORT: BART was invoked while scoring {it['claim_id']}. "
                "Completeness was asserted, so this indicates a key-derivation "
                f"bug, not a missing score.\n{buf.getvalue()[-500:]}")

        seed = seeds[it["claim_id"]]
        new_e = max((v["entail"] for v in seed.values()), default=0.0)
        new_c = max((v["contradict"] for v in seed.values()), default=0.0)
        mv, mc = nb.margin_verdict(new_e, new_c, p3)

        rec = it["recorded"]
        old_e = float(rec["entail"] or 0.0)
        old_c = float(rec["contradict"] or 0.0)
        gold = it["gold_verdict"]
        oc, nc_ = _correct(gold, rec["verdict"]), _correct(gold, verdict)

        rows.append({
            "claim_id": it["claim_id"], "population": it["population"],
            "type": it["type"], "gold_type": it["gold_type"], "gold_verdict": gold,
            "base_claim_id": it["base_claim_id"],
            "injection_type": it["injection_type"],
            "collision_group": it["collision_group"],
            "old_entail": round(old_e, 4), "old_contradict": round(old_c, 4),
            "new_entail": round(new_e, 4), "new_contradict": round(new_c, 4),
            "d_entail": round(new_e - old_e, 4),
            "d_contradict": round(new_c - old_c, 4),
            "old_verdict": rec["verdict"], "new_verdict": verdict,
            "verdict_moved": "YES" if verdict != rec["verdict"] else "",
            "old_verdict_confidence": rec["verdict_confidence"],
            "new_verdict_confidence": conf,
            "old_verdict_margin": rec["verdict_margin"], "new_verdict_margin": mv,
            "margin_moved": "YES" if mv != rec["verdict_margin"] else "",
            "old_correct": "" if oc is None else ("Y" if oc else "N"),
            "new_correct": "" if nc_ is None else ("Y" if nc_ else "N"),
            "correctness_delta": _delta(oc, nc_),
            "query_source": it["query_source"], "title": it["title"],
            "n_passages": len(it["passages"]), "claim": it["claim"],
        })
        if verdict != rec["verdict"]:
            moved.append(rows[-1])
        if mv != rec["verdict_margin"]:
            margin_moved.append(rows[-1])

    _report(rows, moved, margin_moved, simulate)

    out = out_path or os.path.join(
        HERE, f"nli_rescore_{which}_{'simulated' if simulate else 'results'}.csv")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out}  ({len(rows)} rows)")
    print("R19: the quoted baselines were not touched. Adopting these numbers is "
          "a separate decision.")
    return 0


def _delta(old: bool | None, new: bool | None) -> str:
    if old == new:
        return ""
    names = {True: "correct", False: "wrong", None: "abstain"}
    return f"{names[old]}->{names[new]}"


def _report(rows: list[dict], moved: list[dict], margin_moved: list[dict],
            simulate: bool) -> None:
    print()
    print("=" * 78)
    print("RESCORE RESULT" + ("  [SIMULATION -- must show ZERO movement]" if simulate else ""))
    print("=" * 78)

    changed_scores = [r for r in rows if r["d_entail"] or r["d_contradict"]]
    print(f"rows whose (entail, contradict) changed : {len(changed_scores)} of {len(rows)}")
    print(f"rows whose 3d verdict moved            : {len(moved)}")
    print(f"rows whose 3e margin verdict moved     : {len(margin_moved)}")

    if simulate:
        if changed_scores or moved or margin_moved:
            print("\n!! SIMULATION SHOWED MOVEMENT. The apply path is not faithful: "
                  "feeding the\n   recorded scores back through it must reproduce the "
                  "recorded verdicts. Fix that\n   before trusting a real run.")
        else:
            print("\nsimulation clean: recorded scores in -> recorded verdicts out. "
                  "The apply path\nadds nothing of its own, so a real run's movement "
                  "is attributable to the scores.")

    if moved:
        print("\n-- 3d verdict movements " + "-" * 54)
        for r in moved:
            print(f"  {r['claim_id']:<14} {r['population']:<8} gold={r['gold_verdict']:<12} "
                  f"{r['old_verdict']:<12} -> {r['new_verdict']:<12} "
                  f"e {r['old_entail']:.4f}->{r['new_entail']:.4f} "
                  f"c {r['old_contradict']:.4f}->{r['new_contradict']:.4f}"
                  + (f"   [{r['correctness_delta']}]" if r["correctness_delta"] else ""))

    # Which member of each group had been inheriting? Whoever's score moved.
    print("\n-- inheritance direction, per collision group " + "-" * 32)
    print("   (the member whose score MOVED is the one that had been inheriting;")
    print("    the member that stayed put is the one that wrote the entry.)")
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        groups[r["collision_group"]].append(r)
    for g, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        wrote = [r["claim_id"] for r in rs if not (r["d_entail"] or r["d_contradict"])]
        inherit = [r["claim_id"] for r in rs if r["d_entail"] or r["d_contradict"]]
        print(f"  n={len(rs)}  wrote={wrote or '-'}")
        print(f"         inherited={inherit or '-'}")

    # Detection / false-positive movement, reported separately per population.
    # R5/R6: never a detection rate on negatives alone, and never without saying
    # which population and prior it came from.
    for pop, label in (("negative", "negatives (all gold FALSE -> TPR side)"),
                       ("natural", "natural (gold-TRUE rows -> FPR side)")):
        sub = [r for r in rows if r["population"] == pop]
        if not sub:
            continue
        print(f"\n-- {label} " + "-" * max(4, 60 - len(label)))
        for tag, key in (("3d", "verdict"), ("3e", "verdict_margin")):
            o = sum(1 for r in sub if r[f"old_{key}"] == "FALSE")
            n = sum(1 for r in sub if r[f"new_{key}"] == "FALSE")
            print(f"  {tag}: FALSE predictions among these {len(sub)} rows: "
                  f"{o} -> {n}   (delta {n - o:+d})")
        if pop == "negative":
            print("  CAVEAT: these rows are all gold FALSE, so a FALSE count here is a")
            print("  numerator only. Pair it with the natural-set FPR before quoting a J.")
        else:
            gt = [r for r in sub if r["gold_verdict"] == "TRUE"]
            fp_o = sum(1 for r in gt if r["old_verdict"] == "FALSE")
            fp_n = sum(1 for r in gt if r["new_verdict"] == "FALSE")
            print(f"  gold-TRUE rows here: {len(gt)}; predicted FALSE (a confident "
                  f"error): {fp_o} -> {fp_n}")

    print("\n-- what this does NOT do " + "-" * 53)
    print("  These are the collision-affected rows only. The published TPR/FPR/J")
    print("  figures have denominators over the FULL populations (68 strict negatives,")
    print("  313 gold-TRUE natural), so a delta here is a numerator delta. Re-run")
    print("  current/negatives_cache_audit.py against adopted scores to move a")
    print("  published number, and state which set each denominator counts (R1b).")


# --------------------------------------------------------------------------
def selftest() -> int:
    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        if not cond:
            ok = False
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}"
              + (f"   {detail}" if detail and not cond else ""))

    print("nli_rescore_apply selftest")
    print("-" * 74)

    nb, p3 = import_phase3d()
    sentinel = _NliSentinel()
    p3.get_nli = lambda: sentinel
    p3.save_cache = lambda _c: (_ for _ in ()).throw(
        RuntimeError("save_cache must never be called"))

    c_a = "Act of 2008 provided $7" + "0" * 40 + " billion, variant A."
    c_b = "Act of 2008 provided $7" + "0" * 40 + " billion, variant B!"
    check("the two synthetic claims DO share a legacy claim key (non-vacuity)",
          c_a[:60] == c_b[:60])

    pa, pb = "Premise alpha. " * 6, "Premise beta. " * 6

    # 1. a one-claim cache cannot inherit: same key, different caches, own scores
    ca = {legacy_key(c_a, pa): {"entail": 0.91, "contradict": 0.02}}
    cb = {legacy_key(c_b, pa): {"entail": 0.03, "contradict": 0.88}}
    check("colliding claims produce IDENTICAL legacy keys",
          legacy_key(c_a, pa) == legacy_key(c_b, pa))
    with contextlib.redirect_stdout(io.StringIO()):
        va, _, _ = p3.run_nli_on_passages(c_a, [(pa, 0.7)], ca)
        vb, _, _ = p3.run_nli_on_passages(c_b, [(pa, 0.7)], cb)
    check("per-claim caches keep them apart: TRUE vs FALSE",
          (va, vb) == ("TRUE", "FALSE"), f"got {(va, vb)}")
    check("no BART invocation on a complete seeding", not sentinel.calls,
          str(sentinel.calls))

    # 2. threshold ladder, at phase3d's own constants
    for e, c, want in ((0.50, 0.00, "TRUE"), (0.4999, 0.40, "FALSE"),
                       (0.4999, 0.3999, "UNVERIFIABLE"), (0.50, 0.99, "TRUE")):
        seed = {legacy_key(c_a, pa): {"entail": e, "contradict": c}}
        with contextlib.redirect_stdout(io.StringIO()):
            v, _, _ = p3.run_nli_on_passages(c_a, [(pa, 0.7)], seed)
        check(f"ladder e={e} c={c} -> {want}", v == want, f"got {v}")

    # 3. a MISSING score must be recorded, not swallowed
    sentinel.calls.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        v, _, _ = p3.run_nli_on_passages(c_a, [(pa, 0.7), (pb, 0.6)],
                                         {legacy_key(c_a, pa): {"entail": 0.9,
                                                                "contradict": 0.0}})
    check("phase3d SWALLOWS a miss (this is why guard (a) exists)", v == "TRUE")
    check("the sentinel RECORDS the swallowed miss (guard (b) works)",
          len(sentinel.calls) == 1, str(sentinel.calls))

    # 4. _seed_for reports missing pairs rather than seeding a hole
    miss: list = []
    item = {"claim_id": "X", "claim": c_a,
            "passages": [{"idx": 0, "text": pa, "fixed_key": fixed_key(c_a, pa)},
                         {"idx": 1, "text": pb, "fixed_key": fixed_key(c_a, pb)}]}
    seed = _seed_for(item, {fixed_key(c_a, pa): {"entail": 0.5, "contradict": 0.1}}, miss)
    check("_seed_for records the unscored pair", len(miss) == 1 and len(seed) == 1,
          f"miss={miss} seed={len(seed)}")

    # 5. correctness is selective, and abstention is not scored wrong (R7)
    check("_correct: abstention is None, not False",
          _correct("FALSE", "UNVERIFIABLE") is None)
    check("_correct: gold FALSE vs predicted FALSE is correct",
          _correct("FALSE", "FALSE") is True)
    check("_correct: gold TRUE vs predicted FALSE is wrong",
          _correct("TRUE", "FALSE") is False)

    # 6. margin_verdict comes from the baseline, not retyped here
    check("margin_verdict is the baseline's own function",
          nb.margin_verdict.__module__.endswith("nonrouted_baseline"))
    check("3e demands a margin the 3d point does not: e=0.55 c=0.50 -> not TRUE",
          nb.margin_verdict(0.55, 0.50, p3)[0] != "TRUE",
          str(nb.margin_verdict(0.55, 0.50, p3)))

    print("-" * 74)
    print("ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", dest="which", choices=("negatives", "natural", "both"),
                    default="both")
    ap.add_argument("--scores", default=None, help="scores JSON downloaded from Colab")
    ap.add_argument("--simulate", action="store_true",
                    help="feed the RECORDED scores through the apply path; must "
                         "reproduce the recorded verdicts exactly")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    return run(args.which, args.scores, args.simulate, args.out)


if __name__ == "__main__":
    sys.exit(main())
