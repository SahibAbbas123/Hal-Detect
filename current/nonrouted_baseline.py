#!/usr/bin/env python3
"""
NON-ROUTED BASELINE (RQ2) -- the thesis's core quantitative proof.

WHAT THIS IS
------------
Every claim, regardless of type, through ONE generic pipeline:

    claim -> Gemini-disambiguated query -> Wikipedia full-text search
          -> page text -> paragraph chunks -> SBERT top-k ranking
          -> cross-encoder/nli-deberta-v3-large 3-way NLI -> threshold
          -> TRUE / FALSE / UNVERIFIABLE

Same claims, same gold labels, same evidence sources as the routed system.
**Routing is the only variable.** This is essentially what FActScore does, which
is why it is the natural non-strawman baseline rather than a rigged one.

WHY IT MATTERS
--------------
Three independent session handoffs in `old-chats-handoffs/` name this as the
central missing result, and all three record it as "not started":

  * "Task 6 -- the core quantitative proof: ablation of taxonomy-routed
     verifiers vs a single generic (uniform) verifier."
  * "Non-routed baseline | Ablation | Not started | The core comparison;
     spec is fixed."
  * "Non-routed baseline -- not built. Required for RQ2."

The spec has not changed since May 2026.

Do NOT confuse this with `llm_baseline.py`. That asks an LLM directly and
answers a different question. This one holds evidence and NLI identical and
varies only routing -- it is the comparison the methodology commits to.

DESIGN DECISION THAT MATTERS FOR THE THESIS
-------------------------------------------
This module does **not** reimplement retrieval or NLI. It imports
`archive/scripts/relational_verifier_phase3d.py` -- the code the
RAG-for-fact-verification handoff calls *"the authoritative code for thesis
results"* -- and calls its `verify_relational()` on every claim.

That is deliberate and load-bearing. If the baseline were a fresh
implementation, a reviewer could object that it differs from the routed system
in some incidental detail (chunking, ranking, thresholds, prompt template) and
that the measured gap reflects implementation drift rather than routing. Sharing
one code path makes that objection unavailable. `verify_relational()` already
takes an arbitrary claim dict and applies **no type filter** -- routing was
always imposed by the *caller*, never by the verifier.

Two consequences worth stating plainly:
  * The baseline is expected to look GOOD on RELATIONAL. It is the same code the
    routed system uses there, so on that slice routed and non-routed should
    agree almost exactly. The interesting slices are TEMPORAL / ENTITY_ATTRIBUTE
    / QUANTITATIVE / CITATION, where routing sends claims somewhere else.
  * A gap on those slices is the thesis result. No gap is also a result, and
    would need reporting honestly rather than re-tuning until one appears.

THE COLAB SHIM
--------------
Every Gemini call site in this project opens with `from google.colab import
userdata`, so phase3d raises `ModuleNotFoundError` off Colab and cannot even be
imported. `_install_colab_shim()` installs a stand-in backed by
`gemini_key.resolve()` (env var -> key file -> real Colab). This is why the
authoritative script has been unrunnable locally, and why it is unrunnable no
longer.

BOTH VARIANTS FROM ONE RUN
--------------------------
phase3d caches raw `{"entail": ..., "contradict": ...}` per (claim, passage)
pair. So after the expensive pass, the Phase-3e margin rule (entailment must
beat contradiction by MIN_MARGIN) is recomputable from the cache at zero model
cost. Both variants are therefore reported from a single run:

    3d-style : entail >= 0.50 -> TRUE ; contradict >= 0.40 -> FALSE
    3e-style : as above, but require (entail - contradict) >= 0.15 for TRUE

That is what makes the coverage-accuracy tradeoff table cheap, and the tradeoff
is itself RQ4's answer rather than an awkward inconsistency to hide.

LABEL INTEGRITY -- READ BEFORE QUOTING ANY NUMBER
-------------------------------------------------
Phase 2's 109 gold verdicts were AI-filled and then AI-corrected (31 flipped
UNVERIFIABLE -> TRUE, which moved measured accuracy ~15% -> 61% with no verifier
change). They are not independent ground truth. Every result here is therefore
printed **twice**: over all labeled claims, and over Batch 1 + Batch 3 only
(human-labeled). If those two disagree materially, the pooled number is
load-bearing on unreviewed labels and must not be quoted.

CACHE DISCIPLINE
----------------
Runs against a **copy** of the thesis retrieval cache, never the original, so a
baseline run cannot mutate or corrupt the routed run's reproducibility. Seeding
from the existing cache is intentional: it means shared claims see byte-identical
evidence, which is exactly what "same evidence sources" requires. Failed API
calls are never cached.
"""

from __future__ import annotations

import argparse
import csv
import importlib.machinery
import importlib.util
import json
import os
import shutil
import sys
import types
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


# ---------------------------------------------------------------------------
# Native-crash hardening. MUST run before torch / sentence-transformers load.
# ---------------------------------------------------------------------------
# Observed 2026-08-22 on macOS/arm64: `zsh: bus error` immediately after
# "BART loaded." -- i.e. on the FIRST NLI inference, not during load -- together
# with `resource_tracker: leaked semaphore ... /loky-...`.
#
# phase3d's get_nli() already pins `device=-1`, so this is NOT an MPS bug. The
# two plausible native causes are:
#   (a) two OpenMP runtimes live in one process. torch ships its own libomp, and
#       sentence-transformers pulls in sklearn/joblib -- whose loky pool is
#       visible in the crash output. Duplicate libomp classically manifests as a
#       SIGBUS/SIGSEGV on the first parallel op.
#   (b) mmap'd safetensors pages failing to fault in (low disk, or a partially
#       written cache file), which surfaces as SIGBUS rather than an exception.
#
# Pinning to a single thread before torch is imported addresses (a) and makes
# (b) easier to spot. It costs throughput and buys the run finishing at all.
# `--nli-check` isolates the crash without paying for the whole pipeline.
def harden_native(threads: int = 1) -> None:
    if threads <= 0:
        # 0 means "don't interfere". Pinning to 1 is a macOS-only workaround;
        # applying it on Linux/Colab just throttles an already-slow CPU path.
        return
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[var] = str(threads)
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def limit_torch_threads(threads: int = 1) -> str:
    """Belt-and-braces: env vars are read at import, this catches the rest."""
    try:
        import torch
        gpu = torch.cuda.is_available()
        if threads > 0:
            torch.set_num_threads(threads)
            try:
                torch.set_num_interop_threads(threads)
            except RuntimeError:
                pass          # already initialised; harmless
        return (f"torch {torch.__version__}, "
                f"threads={threads if threads > 0 else 'auto'}, "
                f"cuda={'yes' if gpu else 'no'}"
                + ("  !! CUDA available but device=-1 -- pass --device 0"
                   if gpu else ""))
    except Exception as exc:   # noqa: BLE001
        return f"could not limit torch threads: {exc.__class__.__name__}"


import gemini_key            # noqa: E402
import metrics as M          # noqa: E402
import consolidate_claims as CC   # noqa: E402

PHASE3D_PATH = os.path.join(ROOT, "archive", "scripts",
                            "relational_verifier_phase3d.py")

# Our own cache copy. Merged (never overwritten) from the thesis caches below.
# phase3d's own CACHE_FILE name is `relational_cache.json`, but this workspace
# holds Phase 3e's SPLIT pair instead, so both must be merged -- the retrieval
# half alone leaves every NLI score to be recomputed.
BASELINE_CACHE = os.path.join(HERE, "nonrouted_cache.json")
CACHE_SEEDS = [
    os.path.join(HERE, "relational_cache.json"),            # 3d, if it exists
    os.path.join(HERE, "relational_retrieval_cache.json"),  # 3e: text/llmquery
    os.path.join(HERE, "relational_nli_cache.json"),        # 3e: the NLI scores
]

OUT_CSV = os.path.join(HERE, "nonrouted_baseline_results.csv")
PROGRESS_EVERY = 10

# Phase-3e margin gate, recomputed post-hoc from cached NLI scores.
MIN_MARGIN = 0.15

# Premise length cap, in characters, applied before NLI.
#
# `chunk_passages()` in phase3d filters on a MINIMUM length (50 chars) and has no
# maximum: it keeps every newline-separated paragraph, however long. But
# bart-large-mnli has 1024 learned position embeddings (~4000 chars), so anything
# past that is not read by the model under any circumstances -- it is either
# truncated by the tokenizer or it overruns.
#
# So this cap is not a divergence from the routed system's evidence; it makes
# explicit what the model was already limited to. 3000 chars is ~750 tokens,
# comfortably inside the window with the hypothesis template attached, and above
# the length of the overwhelming majority of Wikipedia paragraphs, so it rarely
# bites at all. Set to 0 to disable.
#
# It is also a plausible fix for the observed SIGBUS. If the crash survives
# `--threads 1`, try lowering this.
#
# NOTE FOR COMPARABILITY: whatever value is used here should be used when the
# routed side is re-run, so both halves of the ablation see identical premises.
# The number is recorded in every result row's `method` field for that reason.
MAX_PASSAGE_CHARS = 3000

TYPES = ("RELATIONAL", "TEMPORAL", "QUANTITATIVE",
         "ENTITY_ATTRIBUTE", "CITATION")

# Routed numbers AS RECORDED in CLAUDE.md / handoffs. NOT re-measured by this
# run -- shown only so the comparison is visible in one place. Re-verify before
# any of these reaches thesis text.
ROUTED_RECORDED = {
    "RELATIONAL":       ("80.77% acc / 55.32% cov", "Batch 3, cell 57 (Phase 3e)"),
    "TEMPORAL":         ("0% acc / 0% cov",         "Batch 3, cell 75, post-QID-fix"),
    "ENTITY_ATTRIBUTE": ("0% acc / 0% cov",         "Batch 3, cell 69, post-QID-fix"),
    "QUANTITATIVE":     ("never executed",          "quantitative_verifier.py"),
    "CITATION":         ("0/12 matched",            "citation_verifier.py, broken"),
}


# ---------------------------------------------------------------------------
# Importing the authoritative verifier off Colab
# ---------------------------------------------------------------------------

def _install_colab_shim() -> str:
    """Make `from google.colab import userdata` work outside Colab.

    Returns a human-readable description of where the key came from. Never
    returns or logs the key itself.
    """
    if "google.colab" in sys.modules:
        return "real google.colab already present"

    key, src = gemini_key.resolve()

    class _UserData:
        @staticmethod
        def get(name: str):
            if name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                return key
            return None

    colab = types.ModuleType("google.colab")
    colab.userdata = _UserData()

    # A module in sys.modules with __spec__ = None makes
    # importlib.util.find_spec("google.colab") raise ValueError under Python
    # 3.13. `accelerate` calls exactly that to detect whether it is running in
    # Colab, so without this the shim crashes HF imports rather than satisfying
    # them. Found on Colab 2026-08-23.
    colab.__spec__ = importlib.machinery.ModuleSpec("google.colab", None)

    google = sys.modules.get("google")
    if google is None:
        google = types.ModuleType("google")
        google.__path__ = []          # mark as package
        sys.modules["google"] = google
    google.colab = colab
    sys.modules["google.colab"] = colab
    return src


def load_phase3d():
    """Import the authoritative RELATIONAL verifier and point it at our cache."""
    if not os.path.isfile(PHASE3D_PATH):
        raise SystemExit(
            f"FATAL: {PHASE3D_PATH} not found.\n"
            "This baseline deliberately reuses the authoritative verifier "
            "rather than reimplementing it. Without that file the ablation "
            "would not be comparing identical code, so it refuses to guess."
        )

    key_src = _install_colab_shim()

    spec = importlib.util.spec_from_file_location(
        "relational_verifier_phase3d", PHASE3D_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["relational_verifier_phase3d"] = mod
    spec.loader.exec_module(mod)

    # Redirect its cache to our copy so the thesis cache is never mutated.
    _seed_cache()
    mod.CACHE_FILE = BASELINE_CACHE
    return mod, key_src


def _seed_cache() -> str:
    """MERGE every available thesis cache into ours; never overwrite our keys.

    Corrected 2026-08-22 late: this used to `shutil.copy2` the first seed file it
    found, which was wrong in two ways.

    First, phase3d's `CACHE_FILE` is `relational_cache.json` -- Phase 3d's single
    combined cache -- but this workspace holds Phase **3e**'s *split* pair
    instead: `relational_retrieval_cache.json` (1.7 MB, page text) and
    `relational_nli_cache.json` (25 KB, NLI scores). Copying only the first meant
    **every NLI score was recomputed**, which is exactly the operation that
    SIGBUSes. Merging the NLI cache means cached (claim, passage) pairs skip the
    BART call entirely -- `run_nli_on_passages` checks the cache before calling
    the model, and `get_nli()` is lazy, so a fully cached claim never loads BART
    at all.

    Second, an existing `nonrouted_cache.json` caused an early return, so a
    partial cache from a crashed run could never be topped up.

    Key-format compatibility was verified against the files, not assumed:
        nli__{claim[:60]}__{passage[:40]}   -> identical in both. transfers.
        text__{title.lower()}              -> identical. transfers (the 1.7 MB).
        llmquery__{claim[:80]}             -> identical. transfers, and this is
                                             what preserves Gemini determinism
                                             for previously-seen claims.
        titles__{query}__3                 -> Phase 3e multi-candidate only.
                                             phase3d wants `title__{subject}`,
                                             so these do NOT transfer. Harmless:
                                             re-running a Wikipedia search is
                                             cheap, unlike NLI or page fetches.
    """
    from collections import Counter

    try:
        with open(BASELINE_CACHE, "r", encoding="utf-8") as fh:
            cache = json.load(fh)
    except (OSError, json.JSONDecodeError):
        cache = {}
    before = len(cache)

    added: Counter = Counter()
    seeded_from = []
    for seed in CACHE_SEEDS:
        if not os.path.isfile(seed):
            continue
        try:
            with open(seed, "r", encoding="utf-8") as fh:
                src = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        seeded_from.append(os.path.basename(seed))
        for k, v in src.items():
            if k not in cache:            # ours always wins
                cache[k] = v
                added[k.split("__")[0]] += 1

    if added or before == 0:
        tmp = BASELINE_CACHE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cache, fh)
        os.replace(tmp, BASELINE_CACHE)

    have = Counter(k.split("__")[0] for k in cache)
    if not seeded_from:
        return f"{len(cache)} entries, no seed cache found"
    return (f"{len(cache)} entries "
            f"(+{sum(added.values())} merged from {', '.join(seeded_from)}); "
            f"nli={have.get('nli', 0)}, text={have.get('text', 0)}, "
            f"llmquery={have.get('llmquery', 0)}, title={have.get('title', 0)}")


# ---------------------------------------------------------------------------
# Recording proxy: capture raw NLI scores without duplicating NLI logic
# ---------------------------------------------------------------------------

class NLIRecorder:
    """Wraps phase3d.run_nli_on_passages to capture best entail/contradict.

    The wrapped function is called unchanged, so the primary verdict remains
    the authoritative one. The raw scores are then read back out of the cache
    the call just populated -- pure dict lookups, no extra model work.

    Only the cache KEY FORMAT is mirrored here, not any scoring logic. If that
    format ever drifts, `available` goes False and the 3e variant is reported as
    unavailable rather than silently wrong.
    """

    def __init__(self, mod, max_chars: int = MAX_PASSAGE_CHARS):
        self.mod = mod
        self.inner = mod.run_nli_on_passages
        self.max_chars = max_chars
        self.last: dict | None = None
        self.hits = 0
        self.misses = 0
        self.truncated = 0

    def __call__(self, claim, passages, cache):
        # Cap premise length. The cache key uses passage[:40], so truncation
        # here cannot change which cache entry a passage maps to.
        if self.max_chars:
            capped = []
            for p, s in passages:
                if len(p) > self.max_chars:
                    self.truncated += 1
                    p = p[:self.max_chars]
                capped.append((p, s))
            passages = capped

        verdict, confidence, evidence = self.inner(claim, passages, cache)

        best_e, best_c, found = 0.0, 0.0, 0
        for passage, _sim in passages:
            k = (f"nli__{claim[:60].replace(' ', '_')}"
                 f"__{passage[:40].replace(' ', '_')}")
            got = cache.get(k)
            if isinstance(got, dict) and "entail" in got:
                found += 1
                best_e = max(best_e, float(got["entail"]))
                best_c = max(best_c, float(got["contradict"]))

        if found:
            self.hits += 1
        else:
            self.misses += 1

        self.last = {"entail": best_e, "contradict": best_c,
                     "scored_passages": found,
                     "n_passages": len(passages)}
        return verdict, confidence, evidence

    def install(self):
        self.mod.run_nli_on_passages = self
        return self

    @property
    def available(self) -> bool:
        return self.hits > 0


def margin_verdict(entail: float, contradict: float, mod,
                   min_margin: float = MIN_MARGIN) -> tuple[str, float]:
    """Phase-3e style: entailment must also beat contradiction by a margin.

    Thresholds are read off the imported module rather than hardcoded, so the
    variant cannot silently disagree with the primary verdict's own settings.
    """
    e_thresh = getattr(mod, "ENTAIL_THRESHOLD", 0.50)
    c_thresh = getattr(mod, "CONTRADICT_THRESHOLD", 0.40)
    if entail >= e_thresh and (entail - contradict) >= min_margin:
        return "TRUE", round(0.5 + entail * 0.4, 3)
    if contradict >= c_thresh and (contradict - entail) >= min_margin:
        return "FALSE", round(0.5 + contradict * 0.3, 3)
    return "UNVERIFIABLE", 0.50


# ---------------------------------------------------------------------------
# Claim loading
# ---------------------------------------------------------------------------

def load_claims_csv(path: str, only_types: list[str] | None,
                    limit: int | None) -> tuple[list[dict], list[str]]:
    """Load an arbitrary claims CSV instead of the consolidated gold set.

    Needed to run the baseline over `synthetic_negatives.csv`, which is not one of
    `consolidate_claims.SOURCES`. Two normalisations:

      * `corrupted_value` -> `value`. The negatives file keeps the original and the
        corrupted value in separate columns; the value *under test* is the corrupted
        one, and phase3d reads `value`.
      * a missing `q_id` is filled from `claim_id`, because
        `generate_search_query` includes it in the Gemini prompt.

    Without this the hybrid has a coverage number and no detection number: tier 2
    keys on `claim_id`, and the synthetic negatives' ids were never in the baseline
    run, so every tier-2 lookup misses.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    problems, kept = [], []
    for r in rows:
        if not (r.get("value") or "").strip() and r.get("corrupted_value"):
            r["value"] = r["corrupted_value"]
        if not (r.get("q_id") or "").strip():
            r["q_id"] = r.get("claim_id", "")
        if only_types and (r.get("type") or "").upper() not in only_types:
            continue
        if not (r.get("gold_verdict") or "").strip():
            continue
        if not (r.get("claim") or "").strip():
            continue
        kept.append(r)
    if not kept:
        problems.append(f"{path}: no usable rows (need claim + gold_verdict)")
    return (kept[:limit] if limit else kept), problems


def load_claims(include_synthetic: bool, only_types: list[str] | None,
                limit: int | None) -> tuple[list[dict], list[str]]:
    rows, problems = CC.load_all()

    kept = []
    for r in rows:
        if not include_synthetic and str(r.get("synthetic", "")).lower() == "true":
            continue
        if only_types and (r.get("type") or "").upper() not in only_types:
            continue
        if not (r.get("gold_verdict") or "").strip():
            continue                      # unlabeled -- cannot be scored
        if not (r.get("claim") or "").strip():
            continue
        kept.append(r)

    if limit:
        # Stratify the smoke test across types so a --limit run still exercises
        # every route, rather than 20 consecutive RELATIONAL claims from Q1.
        by_type: dict[str, list[dict]] = defaultdict(list)
        for r in kept:
            by_type[(r.get("type") or "?").upper()].append(r)
        out, i = [], 0
        while len(out) < limit and any(by_type.values()):
            for t in list(by_type):
                if by_type[t] and len(out) < limit:
                    out.append(by_type[t].pop(0))
            i += 1
            if i > limit + 5:
                break
        kept = out[:limit]

    return kept, problems


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _slice_report(results: list[dict], key: str, title: str) -> None:
    gold = [r["gold_verdict"] for r in results]
    pred = [r[key] for r in results]
    conf = [r[f"{key}_confidence"] for r in results]
    if not gold:
        print(f"\n=== {title} === (no rows)")
        return
    M.report(gold, pred, conf, title=title)


def per_type_table(results: list[dict], key: str) -> None:
    print(f"\n{'=' * 72}")
    print("  PER-TYPE: non-routed baseline vs routed (recorded)")
    print(f"{'=' * 72}")
    print(f"  {'type':<18}{'n':>5}{'cov':>9}{'acc':>9}{'acc 95% CI':>20}"
          f"   routed (recorded)")
    for t in TYPES:
        sub = [r for r in results if (r.get("type") or "").upper() == t]
        if not sub:
            continue
        sel = M.selective([r["gold_verdict"] for r in sub],
                          [r[key] for r in sub])
        _, lo, hi = M.wilson(sel["correct"], sel["covered"])
        ci = f"[{lo:5.1%}, {hi:5.1%}]" if sel["covered"] else "n/a"
        rec = ROUTED_RECORDED.get(t, ("", ""))[0]
        print(f"  {t:<18}{len(sub):>5}{sel['coverage']:>9.1%}"
              f"{sel['accuracy']:>9.1%}{ci:>20}   {rec}")
    print("\n  Routed figures are AS RECORDED in CLAUDE.md, not re-measured by")
    print("  this run. Re-verify before any of them reaches thesis text.")
    print("  RELATIONAL is expected to match closely -- it is the same code")
    print("  path. The other four rows are where routing actually differs.")


def variant_table(results: list[dict], mod) -> None:
    print(f"\n{'=' * 72}")
    print("  COVERAGE-ACCURACY TRADEOFF (both variants, one run)")
    print(f"{'=' * 72}")
    for key, label in (("verdict", "3d-style (threshold only)"),
                       ("verdict_margin", f"3e-style (margin >= {MIN_MARGIN})")):
        sel = M.selective([r["gold_verdict"] for r in results],
                          [r[key] for r in results])
        _, lo, hi = M.wilson(sel["correct"], sel["covered"])
        print(f"  {label:<34} cov {sel['coverage']:6.1%}   "
              f"acc {sel['accuracy']:6.1%}  [{lo:.1%}, {hi:.1%}]  "
              f"n_covered={sel['covered']}")
    print("\n  This is the tradeoff the thesis reports as a table rather than")
    print("  choosing one -- coverage is what RQ4 measures, accuracy is what")
    print("  RQ2 compares, and the shape of the tradeoff is itself a finding.")


def write_csv(results: list[dict]) -> None:
    if not results:
        return
    cols = ["claim_id", "batch", "type", "gold_type", "gold_verdict",
            "subject", "property", "value",
            "verdict", "verdict_confidence",
            "verdict_margin", "verdict_margin_confidence",
            "entail", "contradict", "scored_passages",
            "evidence", "method", "claim"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"\nwrote {OUT_CSV}  ({len(results)} rows)")


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def run(args) -> int:
    only = [t.upper() for t in args.types.split(",")] if args.types else None
    if getattr(args, "claims_csv", None):
        claims, problems = load_claims_csv(args.claims_csv, only, args.limit)
    else:
        claims, problems = load_claims(args.include_synthetic, only, args.limit)
    if getattr(args, "out", None):
        globals()["OUT_CSV"] = args.out

    print(f"{'=' * 72}")
    print("  NON-ROUTED BASELINE (RQ2)")
    print(f"{'=' * 72}")
    print(f"  claims to verify : {len(claims)}")
    dist = defaultdict(int)
    for c in claims:
        dist[(c.get("type") or "?").upper()] += 1
    print(f"  type mix         : "
          + ", ".join(f"{k} {v}" for k, v in sorted(dist.items())))
    if problems:
        print(f"  loader warnings  : {len(problems)}")
        for p in problems[:5]:
            print(f"     - {p}")

    if args.dry_run:
        print("\n--dry-run: plumbing only, no model or network calls made.")
        print("Claims loaded and stratified successfully. Remove --dry-run "
              "to verify.")
        return 0

    mod, key_src = load_phase3d()
    print(f"  verifier         : {os.path.relpath(PHASE3D_PATH, ROOT)} "
          f"(authoritative; imported, not reimplemented)")
    print(f"  gemini key       : {key_src} -> {gemini_key.describe()}")
    print(f"  cache            : {_seed_cache()}")
    if gemini_key.get() is None:
        print("  !! NO GEMINI KEY -- query generation will fall back to the "
              "bare subject.\n     That measurably degrades coverage, so any "
              "number from this run carries an asterisk.")

    if args.safe_load:
        # phase3d memoises into a module global, so seeding it means get_nli()
        # never builds the mmap-backed pipeline at all.
        _nli = safe_nli(args.threads, args.device)
        mod._nli_classifier = _nli
        mod.get_nli = lambda: _nli
        print(f"  nli loader        : safe (no mmap), device={args.device}")

    rec = NLIRecorder(mod, max_chars=args.max_passage_chars).install()
    print(f"  native            : {limit_torch_threads(args.threads)}")
    print(f"  premise cap       : {args.max_passage_chars or 'off'} chars "
          f"(bart-large-mnli reads ~4000 max regardless)")

    results: list[dict] = []
    failures = 0
    for i, row in enumerate(claims, start=1):
        if i % PROGRESS_EVERY == 0 or i == 1:
            print(f"\n--- [{i}/{len(claims)}] {row['claim_id']} "
                  f"({(row.get('type') or '?')}) ---")
        rec.last = None
        try:
            res = mod.verify_relational(row)
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"    [ERROR] {exc.__class__.__name__}: {exc}")
            if failures >= 8 and not results:
                print("\nAborting: 8 consecutive failures with zero successes. "
                      "Fix the environment before burning more API calls.")
                return 1
            continue

        raw = rec.last or {"entail": 0.0, "contradict": 0.0,
                           "scored_passages": 0, "n_passages": 0}
        mv, mc = margin_verdict(raw["entail"], raw["contradict"], mod)

        results.append({
            **{k: row.get(k, "") for k in
               ("claim_id", "batch", "type", "gold_type", "gold_verdict",
                "subject", "property", "value", "claim")},
            "verdict": res["verdict"],
            "verdict_confidence": res["confidence"],
            "verdict_margin": mv,
            "verdict_margin_confidence": mc,
            "entail": round(raw["entail"], 4),
            "contradict": round(raw["contradict"], 4),
            "scored_passages": raw["scored_passages"],
            "evidence": res.get("evidence", ""),
            "method": f"{res.get('method', '')}|cap={args.max_passage_chars}",
        })

        if i % PROGRESS_EVERY == 0:
            write_csv(results)      # checkpoint: a long run must survive a crash

    if not results:
        print("\nNo claims verified. Nothing to report.")
        return 1

    write_csv(results)

    print(f"\n{len(results)} verified, {failures} failed "
          f"(failures excluded from scoring, not counted as abstentions).")
    if rec.truncated:
        print(f"{rec.truncated} passage(s) exceeded the "
              f"{args.max_passage_chars}-char cap and were truncated. "
              f"Apply the same cap when re-running the routed side.")
    if not rec.available:
        print("!! Raw NLI scores were never recoverable from the cache, so the "
              "3e-style variant below is NOT trustworthy.\n"
              "   The cache key format in phase3d has probably changed.")

    _slice_report(results, "verdict",
                  "NON-ROUTED baseline, 3d-style, ALL labeled claims")

    human = [r for r in results if r.get("batch") in ("b1", "b3")]
    if human and len(human) != len(results):
        _slice_report(
            human, "verdict",
            "NON-ROUTED baseline, 3d-style, HUMAN-LABELED ONLY (b1+b3)")
        print("\n  The two blocks above must be read together. Phase 2's 109 "
              "verdicts were AI-filled then AI-corrected;\n  if the numbers "
              "diverge, the pooled figure leans on unreviewed labels and is "
              "not quotable.")

    if rec.available:
        variant_table(results, mod)
    per_type_table(results, "verdict")
    return 0


def nli_check(threads: int, max_chars: int, safe_load: bool = False,
              device: int = -1) -> int:
    """Isolate the SIGBUS: load BART, run three inferences of growing size.

    This exists so the crash can be bisected in seconds rather than by re-running
    a 10-claim smoke test that first pays for Gemini, Wikipedia and SBERT. If it
    dies at 'short', the problem is the OpenMP/threading collision or the model
    files themselves. If it survives 'short' but dies at 'long', the problem is
    premise length overrunning bart-large-mnli's 1024 position embeddings, and
    --max-passage-chars is the fix.
    """
    harden_native(threads)
    print(f"threads pinned to {threads}; "
          f"OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS')}, "
          f"KMP_DUPLICATE_LIB_OK={os.environ.get('KMP_DUPLICATE_LIB_OK')}")
    print(limit_torch_threads(threads))

    print("\nloading bart-large-mnli (device=-1, CPU)...", flush=True)
    if safe_load:
        nli = safe_nli(threads, device)
    else:
        from transformers import pipeline
        nli = pipeline("zero-shot-classification",
                       model="cross-encoder/nli-deberta-v3-large", device=device)
    print("loaded.", flush=True)

    claim = "Albert Einstein published four papers in 1905."
    cases = [
        ("short  (~120 chars)", "Albert Einstein published four groundbreaking "
                                "papers in 1905, his annus mirabilis."),
        ("medium (~1200 chars)", ("Einstein's 1905 papers transformed physics. " * 27)),
        ("long   (~6000 chars, past the 1024-token window)",
         ("The annus mirabilis papers were published in Annalen der Physik. " * 94)),
    ]
    for label, premise in cases:
        n = len(premise)
        shown = premise[:max_chars] if max_chars else premise
        print(f"\n-- {label}  [{n} chars"
              f"{f' -> capped to {len(shown)}' if len(shown) != n else ''}]",
              flush=True)
        try:
            r = nli(shown, candidate_labels=["entailment", "contradiction",
                                             "neutral"],
                    hypothesis_template="This passage {}s that " + claim)
            top = dict(zip(r["labels"], r["scores"]))
            print(f"   OK  entail={top.get('entailment', 0):.3f} "
                  f"contradict={top.get('contradiction', 0):.3f}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"   EXCEPTION {exc.__class__.__name__}: {exc}", flush=True)
            return 1

    print("\nAll three survived. NLI is usable on this machine at "
          f"--threads {threads} --max-passage-chars {max_chars}.")
    print("If the full run still dies, the crash is NOT in NLI -- suspect SBERT "
          "encoding a large passage batch in rank_passages().")
    return 0


def doctor() -> int:
    """Diagnose the SIGBUS without loading a model. Cheap and decisive.

    `--nli-check` dying on an 82-char premise ruled out premise length. SBERT
    encoding 55 passages successfully ruled out torch being broken generally.
    What is left is specific to bart-large-mnli, and the crash ordering is the
    tell: "Loading weights: 100%" completes, "loaded." prints, and the crash
    happens on the FIRST forward pass.

    That is the mmap signature. safetensors are memory-mapped, so the bytes are
    not actually read at load time -- only when a forward pass touches the pages.
    A short/corrupt file mmaps happily and then delivers SIGBUS on read, which is
    a hardware fault, not a Python exception, so no traceback is possible.

    Given the "unauthenticated requests to the HF Hub" warning in the log, a
    rate-limited download that ended early is the leading hypothesis. This checks
    for exactly that, plus the two other things that cause SIGBUS on mmap: no
    disk space and no memory.
    """
    import glob
    import shutil as _sh

    print("=" * 68)
    print("  SIGBUS DOCTOR")
    print("=" * 68)

    # --- interpreter / library versions -----------------------------------
    print("\n-- versions --")
    print(f"  python       {sys.version.split()[0]}  ({sys.platform})")
    try:
        import torch
        print(f"  torch        {torch.__version__}")
    except Exception as exc:      # noqa: BLE001
        print(f"  torch        FAILED to import: {exc}")
    for name in ("transformers", "sentence_transformers", "safetensors"):
        try:
            m = __import__(name)
            print(f"  {name:<12} {getattr(m, '__version__', '?')}")
        except Exception:         # noqa: BLE001
            print(f"  {name:<12} not importable")

    # --- memory / disk ----------------------------------------------------
    print("\n-- resources --")
    ram = 0
    try:
        if sys.platform == "darwin":
            import subprocess
            ram = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"]).decode().strip())
        else:
            # Linux/Colab: sysctl hw.memsize does not exist.
            ram = (os.sysconf("SC_PAGE_SIZE")
                   * os.sysconf("SC_PHYS_PAGES"))
    except Exception:             # noqa: BLE001
        pass
    if ram:
        print(f"  RAM          {ram / 1024**3:.1f} GB")
        if ram < 9 * 1024**3:
            print("               !! bart-large-mnli is ~1.6 GB fp32 plus "
                  "activations, and MiniLM is\n"
                  "                  already resident. On 8 GB this is tight; "
                  "memory pressure on an\n"
                  "                  mmap'd file surfaces as SIGBUS, not "
                  "MemoryError.")
    else:
        print("  RAM          could not determine")
    try:
        import torch
        print(f"  GPU          {torch.cuda.get_device_name(0)}"
              if torch.cuda.is_available() else "  GPU          none (CPU only)")
    except Exception:             # noqa: BLE001
        print("  GPU          unknown")
    try:
        du = _sh.disk_usage(os.path.expanduser("~"))
        print(f"  disk free    {du.free / 1024**3:.1f} GB of "
              f"{du.total / 1024**3:.1f} GB")
        if du.free < 5 * 1024**3:
            print("               !! low free space -- a partially written "
                  "cache file is very likely")
    except Exception:             # noqa: BLE001
        print("  disk free    unknown")

    # --- the HF cache: the leading hypothesis -----------------------------
    print("\n-- huggingface cache --")
    hub = os.path.expanduser(
        os.environ.get("HF_HOME", "~/.cache/huggingface"))
    if not os.path.isdir(hub):
        hub = os.path.expanduser("~/.cache/huggingface")
    print(f"  root         {hub}")

    EXPECTED = {          # approximate on-disk sizes, bytes
        "facebook--bart-large-mnli": 1_600_000_000,
        "sentence-transformers--all-MiniLM-L6-v2": 80_000_000,
    }

    incomplete = glob.glob(os.path.join(hub, "**", "*.incomplete"),
                           recursive=True)
    if incomplete:
        print(f"\n  !! {len(incomplete)} INCOMPLETE download(s) found. "
              f"This is almost certainly the crash:")
        for p in incomplete[:8]:
            try:
                print(f"     {os.path.getsize(p) / 1024**2:9.1f} MB  "
                      f"{os.path.relpath(p, hub)}")
            except OSError:
                print(f"     ?           {os.path.relpath(p, hub)}")
    else:
        print("  no *.incomplete files")

    problems = []
    for model_dir, expect in EXPECTED.items():
        base = os.path.join(hub, "hub", f"models--{model_dir}")
        if not os.path.isdir(base):
            base = os.path.join(hub, f"models--{model_dir}")
        if not os.path.isdir(base):
            print(f"\n  {model_dir}: NOT CACHED (will download on first use)")
            continue
        weights = []
        for pat in ("*.safetensors", "*.bin"):
            weights += glob.glob(os.path.join(base, "**", pat), recursive=True)
        # Follow symlinks into blobs/ and report the real byte size.
        total = 0
        print(f"\n  {model_dir}:")
        for w in sorted(set(os.path.realpath(p) for p in weights)):
            try:
                sz = os.path.getsize(w)
            except OSError as exc:
                print(f"     UNREADABLE ({exc.__class__.__name__}) "
                      f"{os.path.basename(w)}")
                problems.append(model_dir)
                continue
            total += sz
            print(f"     {sz / 1024**2:9.1f} MB  {os.path.basename(w)}")
        print(f"     {'-' * 30}\n     {total / 1024**2:9.1f} MB total "
              f"(expected ~{expect / 1024**2:.0f} MB)")
        if total < expect * 0.9:
            print("     !! SHORT BY MORE THAN 10% -- truncated download. "
                  "This mmaps fine and\n"
                  "        then SIGBUSes on the first forward pass, exactly "
                  "as observed.")
            problems.append(model_dir)

    print("\n" + "=" * 68)
    if incomplete or problems:
        print("  VERDICT: the model cache looks damaged. Fix it with:\n")
        print("    rm -rf ~/.cache/huggingface/hub/models--facebook--bart-large-mnli")
        print("    .venv/bin/python current/nonrouted_baseline.py --nli-check\n")
        print("  Set HF_TOKEN first if you have one -- the log showed "
              "unauthenticated\n  requests, which are rate limited and are how "
              "a download ends up short.")
    else:
        print("  VERDICT: cache is intact and complete, so the crash is NOT a "
              "truncated file.")
        tight_ram, tight_disk = False, False
        if ram:
            tight_ram = ram <= 9 * 1024**3
        try:
            tight_disk = _sh.disk_usage(
                os.path.expanduser("~")).free < 20 * 1024**3
        except Exception:      # noqa: BLE001
            pass

        if tight_ram or tight_disk:
            print("\n  It is memory. macOS answers memory pressure by "
                  "compressing and swapping,\n  but swap cannot grow into disk "
                  "that isn't free. When an mmap'd page can be\n  neither "
                  "faulted in nor swapped, the kernel raises SIGBUS -- which is "
                  "why there\n  is never a Python traceback, and why it is "
                  "deterministic, happens on the FIRST\n  forward pass (when "
                  "pages are actually touched), and only for the large model.\n")
            print("  DO NOT use --safe-load here. low_cpu_mem_usage=False holds "
                  "the state dict AND\n  the model at once -- peak goes from "
                  "~1.6 GB to ~3 GB. On this machine that\n  makes the failure "
                  "worse, not better. It only helps a CORRUPT file, which is\n"
                  "  already ruled out above.\n")
            print("  Cheapest local shot: free disk so swap has room "
                  "(20-30 GB), quit other apps,\n  and retry --nli-check. "
                  "Otherwise use Colab -- which is where the Feb-Apr\n  handoff "
                  "already assigned this verifier: \"the RELATIONAL verifier "
                  "(Sentence-BERT\n  + bart-large-mnli) is the one suited to "
                  "Colab/Kaggle GPU\".\n")
            print("    current/nonrouted_baseline_colab.ipynb")
        else:
            print("\n  RAM and disk look adequate, so memory pressure is "
                  "unlikely. Next suspicion is\n  the library stack: "
                  "transformers 5.x is a major version and phase3d was written\n"
                  "  against 4.x. Try --nli-check --safe-load to convert a "
                  "silent SIGBUS into a\n  real traceback, then Colab if it "
                  "still dies.")
    print("=" * 68)
    return 0


def safe_nli(threads: int = 1, device: int = -1):
    """Build the zero-shot pipeline with memory-mapping DISABLED.

    Same model -- `cross-encoder/nli-deberta-v3-large` -- so the experimental spec is
    untouched and the routed/non-routed comparison stays valid. Only *how* the
    weights reach memory changes, which is not part of the spec.

    `low_cpu_mem_usage=False` makes transformers materialise the full state dict
    in RAM rather than lazily mmap-ing it, so a bad page becomes a load-time
    error with a traceback instead of a SIGBUS mid-forward.

    `device` also matters on Colab: phase3d hardcodes `device=-1`, so without an
    override a GPU runtime would run BART on the CPU and waste the accelerator.
    Roughly 1000 NLI calls (356 claims x ~3 passages) is tens of minutes on CPU
    and a few minutes on a T4.
    """
    import torch
    from transformers import (AutoModelForSequenceClassification,
                              AutoTokenizer, pipeline)
    torch.set_num_threads(threads)

    name = "cross-encoder/nli-deberta-v3-large"
    print(f"loading {name} with low_cpu_mem_usage=False (no mmap), "
          f"device={device}...", flush=True)
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(
        name, low_cpu_mem_usage=False, dtype=torch.float32)
    model.eval()
    print("weights fully materialised in RAM.", flush=True)
    return pipeline("zero-shot-classification", model=model, tokenizer=tok,
                    device=device)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Non-routed baseline (RQ2): one generic Wikipedia+NLI "
                    "pipeline over every claim regardless of type.")
    ap.add_argument("--limit", type=int, default=None,
                    help="verify only N claims, stratified across types "
                         "(smoke test)")
    ap.add_argument("--claims-csv", default=None,
                    help="run over an arbitrary claims CSV (e.g. "
                         "current/synthetic_negatives.csv) instead of the "
                         "consolidated gold set. Maps corrupted_value -> value.")
    ap.add_argument("--out", default=None,
                    help="write results here instead of the default path, so a "
                         "negatives run does not overwrite the main results")
    ap.add_argument("--types", default=None,
                    help="comma-separated type filter, e.g. TEMPORAL,CITATION")
    ap.add_argument("--include-synthetic", action="store_true",
                    help="also include the 27 synthetic B3N negatives")
    ap.add_argument("--dry-run", action="store_true",
                    help="load and stratify claims, then stop; no network")
    ap.add_argument("--check", action="store_true",
                    help="verify phase3d imports and the key resolves, then stop")
    ap.add_argument("--nli-check", action="store_true",
                    help="isolate a native crash: load BART and run three "
                         "inferences of growing premise length, then stop")
    ap.add_argument("--threads", type=int, default=(1 if sys.platform == "darwin"
                                                    else 0),
                    help="pin all native thread pools to N. Default 1 on macOS "
                         "(the SIGBUS workaround) and 0 elsewhere, where 0 means "
                         "'let torch decide'. Pinning 1 on Colab's 2 vCPUs makes "
                         "a CPU run pathologically slow.")
    ap.add_argument("--max-passage-chars", type=int, default=MAX_PASSAGE_CHARS,
                    help=f"cap premise length before NLI (default "
                         f"{MAX_PASSAGE_CHARS}; 0 disables). bart-large-mnli "
                         f"cannot read past ~4000 chars regardless.")
    ap.add_argument("--doctor", action="store_true",
                    help="diagnose the SIGBUS without loading a model: check "
                         "versions, RAM, disk, and HF cache integrity")
    ap.add_argument("--safe-load", action="store_true",
                    help="load BART with low_cpu_mem_usage=False (no mmap). "
                         "Same model, so the ablation stays valid -- only how "
                         "the weights reach RAM changes.")
    ap.add_argument("--device", type=int, default=None,
                    help="NLI device: -1 CPU, 0 first GPU. Default AUTO -- 0 "
                         "when CUDA is present, else -1. phase3d hardcodes -1, "
                         "so without this a GPU runtime silently runs BART on "
                         "the CPU. Any value >= 0 implies --safe-load.")
    args = ap.parse_args()

    if args.device is None:
        # Auto-detect. Forgetting --device 0 on Colab is the single most
        # expensive mistake available here: it ran BART-large on one CPU thread
        # for over 30 minutes. Make the right thing the default.
        try:
            import torch
            args.device = 0 if torch.cuda.is_available() else -1
        except Exception:      # noqa: BLE001
            args.device = -1
        if args.device == 0:
            print("[auto] CUDA detected -> --device 0 (pass --device -1 to "
                  "force CPU)")

    if args.device >= 0:
        args.safe_load = True      # the override is how the device is applied

    if args.doctor:
        return doctor()

    if args.nli_check:
        return nli_check(args.threads, args.max_passage_chars, args.safe_load,
                         args.device)

    # Must happen before phase3d (and therefore torch) is imported.
    if not args.dry_run:
        harden_native(args.threads)

    if args.check:
        try:
            mod, key_src = load_phase3d()
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: could not import phase3d: "
                  f"{exc.__class__.__name__}: {exc}")
            return 1
        print("phase3d imported OK (Colab shim working)")
        print(f"  ENTAIL_THRESHOLD     = {getattr(mod, 'ENTAIL_THRESHOLD', '?')}")
        print(f"  CONTRADICT_THRESHOLD = {getattr(mod, 'CONTRADICT_THRESHOLD', '?')}")
        print(f"  TOP_K                = {getattr(mod, 'TOP_K', '?')}")
        print(f"  MIN_PASSAGE_SCORE    = {getattr(mod, 'MIN_PASSAGE_SCORE', '?')}")
        print(f"  cache file           = {getattr(mod, 'CACHE_FILE', '?')}")
        print(f"  gemini key source    = {key_src} -> {gemini_key.describe()}")
        rows, problems = CC.load_all()
        print(f"  claims available     = {len(rows)} "
              f"({len(problems)} loader warnings)")
        ok = gemini_key.get() is not None
        print(f"\n{'READY' if ok else 'READY (no Gemini key -- degraded)'}")
        return 0

    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
