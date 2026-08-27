#!/usr/bin/env python3
"""Build the offline work-list for the #16 `nli__` cache-key rescore.

WHAT #16 IS
-----------
`relational_verifier_phase3d.py:194` keys every NLI score on

    nli__{claim[:60]}__{passage[:40]}          (spaces -> underscores)

The synthetic-negatives harness perturbs a single number or year, and in the
worst cases `claim[:60]` cuts *mid-number*:

    'The Emergency Economic Stabilization Act of 2008 provided $7' | '00 billion...'
    'The Emergency Economic Stabilization Act of 2008 provided $7' | '07 billion...'

so the original and its perturbations share one cache entry. Whoever ran first
wrote the score; everyone after silently inherited it. The recorded artifacts
show this to four decimal places -- six claims with values 1.1 / 1.2 / 1.4 /
1.7 / 2.2 / 11.0 all carry entail 0.6139, contradict 0.1117.

WHY A WORK-LIST INSTEAD OF A RE-RUN
-----------------------------------
Only BART needs a GPU-class machine (it SIGBUSes on this Mac). Everything else
in phase3d's chain -- Gemini query lookup, Wikipedia title/text lookup,
`chunk_passages`, SBERT `rank_passages`, the MIN_PASSAGE_SCORE filter and the
baseline's 3000-char cap -- is either a cache hit or pure local compute. So this
script reproduces the full pipeline offline and emits only the
(claim, passage) pairs that need scoring. The Colab side then does BART and
nothing else, which keeps retrieval fixed and makes the cache key the only
variable that changes.

THE REPRODUCTION GATE (the important part)
------------------------------------------
An offline reconstruction of someone else's recorded run is a claim, not a
fact. So before writing anything, this script re-derives each row's
(entail, contradict) from the *legacy* keys in the shipped cache and requires
them to equal the values recorded in the results CSV. A row that does not
reproduce is not exported -- its passage list is wrong, and scoring the wrong
passages would produce a number that looks like a fix and is not one.

That gate is also what makes the experiment's headline defensible: if the old
scores are reproducible from the old keys, then any movement after the rescore
is attributable to the key change alone.

CONTAMINATED `subject` IS DELIBERATE HERE -- DO NOT "FIX" IT
-----------------------------------------------------------
R12 says the corpus `subject` column is contaminated: for a perturbed row it
holds the *original* un-perturbed value. phase3d L294-296 falls back to
`return subject` when Gemini errors, *without caching*, which is why 14 of the
16 negatives have no `llmquery__` entry -- the recorded run retrieved off that
contaminated subject. Replaying it is therefore the only faithful
reconstruction. Using a corrected subject would change which Wikipedia page is
fetched and conflate a retrieval change with the key fix. R12 forbids
*resolving* from that column in a verifier; it does not forbid replaying what
the recorded run did.

USAGE
-----
    python3 current/nli_rescore_prep.py --set negatives      # experiment 1
    python3 current/nli_rescore_prep.py --set natural        # experiment 2
    python3 current/nli_rescore_prep.py --set both           # recommended
    python3 current/nli_rescore_prep.py --selftest

Offline. No API key, no network, no model. Runs in a few seconds.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import inspect
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

NAT_RESULTS = "current/nonrouted_baseline_results.csv"
NEG_RESULTS = "current/nonrouted_negatives_results.csv"
NEG_SOURCE = "current/synthetic_negatives.csv"
PHASE3D = "archive/scripts/relational_verifier_phase3d.py"

# The caches are gitignored, so they exist only in the main checkout. Resolution
# order is printed at run time -- a silently-chosen cache is a silently-chosen
# result.
MAIN_CHECKOUT = "/Users/sahibabc/8th Semester Materials/ThesisCode_copy"
CACHE_CANDIDATES = (
    os.path.join(HERE, "nonrouted_cache.json"),
    os.path.join(MAIN_CHECKOUT, "current", "nonrouted_cache.json"),
)

# R14: bump the prefix, never reuse it. Reusing `nli__` would preserve the bug
# while making the fix appear to work.
FIXED_PREFIX = "nli2__"
HASH_CHARS = 16          # 64 bits each side; uniqueness is asserted, not assumed

# SYN_CITA_083 was dropped (task #23) but its scored row remains on disk by
# design (R19). NEG_SOURCE is the authority on membership, exactly as
# negatives_cache_audit.py has it.
DROPPED = {"SYN_CITA_083": "WHO co-published SOFI 2023; the source_swap injects no falsity"}


# --------------------------------------------------------------------------
# keys
# --------------------------------------------------------------------------
def legacy_key(claim: str, passage: str) -> str:
    """Exactly phase3d:194. Must reproduce the BUG, not a corrected version."""
    return f"nli__{claim[:60].replace(' ', '_')}__{passage[:40].replace(' ', '_')}"


def legacy_claim_part(claim: str) -> str:
    """The claim half of the legacy key -- the collision surface on its own."""
    return claim[:60].replace(" ", "_")


def fixed_key(claim: str, passage: str) -> str:
    """Collision-free replacement: full text hashed, so no truncation exists."""
    ch = hashlib.sha1(claim.encode("utf-8")).hexdigest()[:HASH_CHARS]
    ph = hashlib.sha1(passage.encode("utf-8")).hexdigest()[:HASH_CHARS]
    return f"{FIXED_PREFIX}{ch}__{ph}"


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
def _load(rel: str) -> list[dict]:
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def resolve_cache_path(explicit: str | None) -> str:
    if explicit:
        if not os.path.exists(explicit):
            raise SystemExit(f"--cache {explicit!r} does not exist")
        return explicit
    for p in CACHE_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit(
        "No retrieval/NLI cache found. The caches are gitignored, so they live "
        "only in the main checkout. Looked in:\n  "
        + "\n  ".join(CACHE_CANDIDATES)
        + "\nPass --cache <path> explicitly.")


def import_phase3d():
    """Import phase3d through the baseline's Colab shim, as the baseline does.

    phase3d does `from google.colab import userdata` at module scope;
    `nonrouted_baseline._install_colab_shim()` is the supported way to import it
    off Colab. Going around the shim would be a second import path, which is the
    class of drift this project has been bitten by four times.
    """
    sys.path.insert(0, os.path.join(ROOT, "current"))
    sys.path.insert(0, os.path.join(ROOT, "archive", "scripts"))
    import nonrouted_baseline as nb
    nb._install_colab_shim()
    import relational_verifier_phase3d as p3
    return nb, p3


def harvest_nli_spec() -> dict:
    """Read the NLI call spec out of phase3d's SOURCE, never retyped.

    `candidate_labels` and `hypothesis_template` are inline arguments inside
    `run_nli_on_passages`, not module constants, so they cannot be imported.
    Regexing them out of the source means the notebook either picks up a change
    to phase3d or this script aborts -- it can never quietly diverge.
    """
    src = open(os.path.join(ROOT, PHASE3D), encoding="utf-8").read()

    m = re.search(r"candidate_labels\s*=\s*\[([^\]]*)\]", src)
    if not m:
        raise SystemExit("could not find candidate_labels in phase3d source")
    labels = [s.strip().strip("\"'") for s in m.group(1).split(",") if s.strip()]

    m = re.search(r'hypothesis_template\s*=\s*"([^"]*)"\s*\+\s*claim', src)
    if not m:
        raise SystemExit(
            "could not find the `hypothesis_template=\"...\" + claim` pattern in "
            "phase3d source -- the template shape changed, so the notebook's "
            "prompt would be wrong. Fix this regex against the new source.")
    prefix = m.group(1)

    m = re.search(r'cache_key\s*=\s*f"(nli__\{[^"]*)"', src)
    if not m:
        raise SystemExit("could not find the nli__ cache_key f-string in phase3d source")
    return {
        "candidate_labels": labels,
        "hypothesis_template_prefix": prefix,
        "hypothesis_template_note":
            'phase3d builds it per claim as: hypothesis_template = prefix + claim',
        "legacy_key_fstring_in_source": m.group(1),
    }


# --------------------------------------------------------------------------
# the pipeline, offline
# --------------------------------------------------------------------------
class Resolver:
    """phase3d's retrieval + ranking chain, replayed from the shipped cache."""

    def __init__(self, cache: dict, p3, cap: int) -> None:
        self.cache = cache
        self.p3 = p3
        self.cap = cap

    def query_for(self, claim: str, subject: str) -> tuple[str, str]:
        """phase3d:243-296. The except branch returns `subject` UNCACHED."""
        k = "llmquery__" + claim[:80].replace(" ", "_")
        if k in self.cache:
            return self.cache[k], "GEMINI"
        return subject, "FALLBACK"

    def passages_for(self, claim: str, subject: str) -> dict:
        query, qsrc = self.query_for(claim, subject)
        title = self.cache.get("title__" + str(query).lower().replace(" ", "_"))
        if not isinstance(title, str) or not title:
            return {"ok": False, "reason": "title_uncached", "query": query,
                    "query_source": qsrc, "title": None, "passages": []}
        text = self.cache.get("text__" + title.lower().replace(" ", "_"))
        if not isinstance(text, str) or not text:
            return {"ok": False, "reason": "text_uncached", "query": query,
                    "query_source": qsrc, "title": title, "passages": []}

        chunks = self.p3.chunk_passages(text)
        ranked = self.p3.rank_passages(claim, chunks, self.p3.TOP_K)
        surviving = [(p, s) for p, s in ranked if s >= self.p3.MIN_PASSAGE_SCORE]
        # The baseline caps premise length AFTER the filter. The cap cannot move a
        # passage to a different legacy key, because the key uses passage[:40].
        capped = [(p[:self.cap] if self.cap and len(p) > self.cap else p, s)
                  for p, s in surviving]
        return {"ok": True, "reason": "", "query": query, "query_source": qsrc,
                "title": title, "passages": capped}


def rederive_recorded(claim: str, passages: list, cache: dict) -> tuple[float, float, int]:
    """MAX entail / MAX contradict over the LEGACY keys -- phase3d's aggregate.

    This is the reproduction gate. It reads the same keys the recorded run read,
    so it must return the recorded numbers.
    """
    best_e, best_c, found = 0.0, 0.0, 0
    for passage, _sim in passages:
        got = cache.get(legacy_key(claim, passage))
        if isinstance(got, dict) and "entail" in got:
            found += 1
            best_e = max(best_e, float(got["entail"]))
            best_c = max(best_c, float(got["contradict"]))
    return best_e, best_c, found


def _fmt(x: float) -> str:
    """Match how the baseline wrote floats into the CSV (repr of a rounded float)."""
    return repr(round(x, 4))


def _same(recorded: str, derived: float) -> bool:
    """Compare recorded CSV text against a derived float, tolerantly.

    The CSV holds whatever `str()` produced; comparing floats with a small
    tolerance avoids a false failure on formatting while still catching a real
    mismatch (which is always far larger than 5e-5).
    """
    recorded = (recorded or "").strip()
    if recorded == "":
        return derived == 0.0
    try:
        return abs(float(recorded) - derived) < 5e-5
    except ValueError:
        return False


# --------------------------------------------------------------------------
# candidate selection
# --------------------------------------------------------------------------
def collision_groups(rows: list[dict]) -> dict[str, list[dict]]:
    """Group rows by the legacy CLAIM key, keeping groups with >1 distinct claim.

    Grouping spans both populations on purpose. Each single-population audit can
    only see half the problem: the documented failure is a perturbed claim
    colliding with *its original*, and the original lives in the natural set
    while the perturbation lives in the negatives set.
    """
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        groups[legacy_claim_part(r["claim"])].append(r)
    return {k: v for k, v in groups.items()
            if len({r["claim"] for r in v}) > 1}


def build(cache_path: str, want: str, verbose: bool = True) -> dict:
    nb, p3 = import_phase3d()
    p3.CACHE_FILE = cache_path
    cache = p3.load_cache()

    nat = _load(NAT_RESULTS)
    src = {r["claim_id"]: r for r in _load(NEG_SOURCE)}
    scored = _load(NEG_RESULTS)
    orphans = {r["claim_id"] for r in scored} - set(src)
    if orphans != set(DROPPED):
        raise SystemExit(
            "NEG_RESULTS / NEG_SOURCE membership mismatch.\n"
            f"  recorded drops: {sorted(DROPPED)}\n"
            f"  actual orphans: {sorted(orphans)}\n"
            "Record the drop in DROPPED with its reason -- never widen this "
            "check to make the run pass.")
    neg = [r for r in scored if r["claim_id"] in src]

    for r in nat:
        r["_pop"] = "natural"
    for r in neg:
        r["_pop"] = "negative"

    if verbose:
        print(f"cache        : {cache_path}")
        print(f"               {len(cache)} entries, "
              f"{os.path.getsize(cache_path) / 1e6:.1f} MB")
        print(f"populations  : natural {len(nat)}, negatives {len(neg)} "
              f"(of {len(scored)} scored; {len(DROPPED)} dropped by #23)")
        print(f"constants    : TOP_K={p3.TOP_K} MIN_PASSAGE_SCORE={p3.MIN_PASSAGE_SCORE} "
              f"ENTAIL={p3.ENTAIL_THRESHOLD} CONTRADICT={p3.CONTRADICT_THRESHOLD} "
              f"MAX_PASSAGE_CHARS={nb.MAX_PASSAGE_CHARS} MIN_MARGIN={nb.MIN_MARGIN}")

    groups = collision_groups(nat + neg)
    candidates = [r for v in groups.values() for r in v]
    if verbose:
        print(f"\nlegacy claim-key groups holding >1 distinct claim: {len(groups)}"
              f"  ({len(candidates)} rows)")

    res = Resolver(cache, p3, nb.MAX_PASSAGE_CHARS)

    # Resolve every candidate first: a row can only be judged contaminated once
    # its own passage list is known, because the legacy key is
    # (claim[:60], passage[:40]) -- a shared claim prefix alone is not enough.
    resolved: dict[str, dict] = {}
    for r in candidates:
        info = res.passages_for(r["claim"], r.get("subject", ""))
        info["row"] = r
        resolved[r["claim_id"]] = info

    # Which legacy keys are shared by more than one distinct claim text?
    owners: dict[str, set[str]] = collections.defaultdict(set)
    for cid, info in resolved.items():
        for passage, _s in info["passages"]:
            owners[legacy_key(info["row"]["claim"], passage)].add(info["row"]["claim"])
    shared_keys = {k for k, v in owners.items() if len(v) > 1}

    items, gate_failures, no_passages, uncontaminated = [], [], [], []
    for cid, info in sorted(resolved.items()):
        r = info["row"]
        if not info["ok"] or not info["passages"]:
            no_passages.append((cid, info["reason"] or "no_surviving_passages"))
            continue

        keys = [legacy_key(r["claim"], p) for p, _ in info["passages"]]
        contaminated = [k for k in keys if k in shared_keys]
        if not contaminated:
            uncontaminated.append(cid)
            continue

        e, c, found = rederive_recorded(r["claim"], info["passages"], cache)
        ok_e = _same(r.get("entail", ""), e)
        ok_c = _same(r.get("contradict", ""), c)
        if found != len(info["passages"]) or not (ok_e and ok_c):
            gate_failures.append({
                "claim_id": cid, "scored_found": found,
                "passages": len(info["passages"]),
                "recorded": (r.get("entail"), r.get("contradict")),
                "derived": (_fmt(e), _fmt(c)),
            })
            continue

        items.append({
            "claim_id": cid,
            "population": r["_pop"],
            "type": r.get("type", ""),
            "gold_type": r.get("gold_type", ""),
            "gold_verdict": r.get("gold_verdict", ""),
            "base_claim_id": src.get(cid, {}).get("base_claim_id", ""),
            "injection_type": src.get(cid, {}).get("injection_type", ""),
            "claim": r["claim"],
            "query": info["query"],
            "query_source": info["query_source"],
            "title": info["title"],
            "collision_group": legacy_claim_part(r["claim"]),
            "shared_legacy_keys": len(contaminated),
            "recorded": {
                "entail": r.get("entail", ""),
                "contradict": r.get("contradict", ""),
                "verdict": r.get("verdict", ""),
                "verdict_confidence": r.get("verdict_confidence", ""),
                "verdict_margin": r.get("verdict_margin", ""),
                "verdict_margin_confidence": r.get("verdict_margin_confidence", ""),
            },
            "passages": [
                {"idx": i, "sbert": round(float(s), 6),
                 "legacy_key": legacy_key(r["claim"], p),
                 "legacy_key_shared": legacy_key(r["claim"], p) in shared_keys,
                 "fixed_key": fixed_key(r["claim"], p),
                 "text": p}
                for i, (p, s) in enumerate(info["passages"])
            ],
        })

    if gate_failures:
        print("\n!! REPRODUCTION GATE FAILURES -- these rows are NOT exported:")
        for g in gate_failures:
            print(f"   {g['claim_id']:<14} scored {g['scored_found']}/{g['passages']} "
                  f"recorded={g['recorded']} derived={g['derived']}")
        print("   The offline passage reconstruction disagrees with the recorded run "
              "for these rows,\n   so their passage list is wrong and scoring it "
              "would produce a fake fix.")

    if want != "both":
        keep = "negative" if want == "negatives" else "natural"
        items = [it for it in items if it["population"] == keep]

    # A computed uniqueness check, not a probability argument.
    seen: dict[str, str] = {}
    for it in items:
        for p in it["passages"]:
            prev = seen.get(p["fixed_key"])
            if prev is not None and prev != p["text"]:
                raise SystemExit(
                    f"fixed_key collision on {p['fixed_key']} -- two different "
                    "passages hash alike. Raise HASH_CHARS.")
            seen[p["fixed_key"]] = p["text"]

    pairs = sum(len(it["passages"]) for it in items)
    doc = {
        "meta": {
            "set": want,
            "task": "#16 nli__ cache-key collision rescore",
            "phase3d_source": PHASE3D,
            "cache_used": cache_path,
            "cache_entries": len(cache),
            "constants": {
                "TOP_K": p3.TOP_K,
                "MIN_PASSAGE_SCORE": p3.MIN_PASSAGE_SCORE,
                "ENTAIL_THRESHOLD": p3.ENTAIL_THRESHOLD,
                "CONTRADICT_THRESHOLD": p3.CONTRADICT_THRESHOLD,
                "MAX_PASSAGE_CHARS": nb.MAX_PASSAGE_CHARS,
                "MIN_MARGIN": nb.MIN_MARGIN,
            },
            "nli": harvest_nli_spec(),
            "key_format": {
                "legacy": "nli__{claim[:60]}__{passage[:40]}, spaces -> underscores",
                "fixed": f"{FIXED_PREFIX}{{sha1(claim)[:{HASH_CHARS}]}}"
                         f"__{{sha1(passage)[:{HASH_CHARS}]}}",
            },
            "counts": {
                "collision_groups": len(groups),
                "candidate_rows": len(candidates),
                "exported_rows": len(items),
                "nli_pairs": pairs,
                "rows_without_passages": len(no_passages),
                "rows_prefix_collides_but_keys_do_not": len(uncontaminated),
                "reproduction_gate_failures": len(gate_failures),
            },
            "reproduction_gate": "PASS" if not gate_failures else "PARTIAL",
            "excluded": {
                "no_passages": no_passages,
                "prefix_only": sorted(uncontaminated),
                "gate_failed": gate_failures,
            },
        },
        "items": items,
    }
    return doc


def report(doc: dict) -> None:
    m = doc["meta"]
    c = m["counts"]
    print(f"\nrows whose legacy keys are genuinely SHARED with another claim: "
          f"{c['exported_rows']}")
    print(f"  excluded, no surviving passages (verdict cannot move) : "
          f"{c['rows_without_passages']}")
    print(f"  excluded, claim prefix collides but no key does       : "
          f"{c['rows_prefix_collides_but_keys_do_not']}")
    print(f"  excluded, reproduction gate failed                    : "
          f"{c['reproduction_gate_failures']}")
    print(f"\nreproduction gate: {m['reproduction_gate']}"
          "   (recorded entail/contradict re-derived from the legacy keys)")

    by_pop = collections.Counter(it["population"] for it in doc["items"])
    print(f"\nexported: {c['exported_rows']} rows / {c['nli_pairs']} NLI pairs"
          f"   natural={by_pop['natural']} negatives={by_pop['negative']}")

    groups: dict[str, list[str]] = collections.defaultdict(list)
    for it in doc["items"]:
        groups[it["collision_group"]].append(it["claim_id"])
    print("\ncollision groups being rescored:")
    for k, ids in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  n={len(ids)}  {ids}")
        print(f"        shared claim prefix: {k[:72]!r}")

    fb = sum(1 for it in doc["items"] if it["query_source"] == "FALLBACK")
    print(f"\nretrieval provenance: {fb} of {c['exported_rows']} rows used phase3d's "
          f"UNCACHED `return subject` fallback.")
    print("  -> Colab must run WITHOUT a Gemini key. With a key those rows would get "
          "freshly\n     generated queries, different pages, and the rescore would "
          "conflate the key fix\n     with a retrieval change.")


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------
def selftest() -> int:
    ok = True

    def check(label: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        if not cond:
            ok = False
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}"
              + (f"   {detail}" if detail and not cond else ""))

    print("nli_rescore_prep selftest")
    print("-" * 74)

    # 1. legacy_key must be byte-identical to phase3d's inline f-string.
    src = open(os.path.join(ROOT, PHASE3D), encoding="utf-8").read()
    want = ('cache_key = f"nli__{claim[:60].replace(\' \', \'_\')}'
            '__{passage[:40].replace(\' \', \'_\')}"')
    check("legacy_key matches phase3d's f-string verbatim", want in src,
          "phase3d's key expression changed; update legacy_key()")

    c1 = "The Emergency Economic Stabilization Act of 2008 provided $700 billion for bank bailouts."
    c2 = "The Emergency Economic Stabilization Act of 2008 provided $707 billion for bank bailouts."
    c3 = "The Emergency Economic Stabilization Act of 2008 provided $875 billion for bank bailouts."
    p = "The Act authorized the Treasury to purchase troubled assets." * 3

    # 2. the bug reproduces
    check("legacy key COLLIDES for $700 vs $707 (the real bug)",
          legacy_key(c1, p) == legacy_key(c2, p))
    # 3. non-vacuity: it does not flag everything
    check("legacy key does NOT collide for $700 vs $875 (non-vacuity)",
          legacy_key(c1, p) != legacy_key(c3, p))
    # 4. the fix
    check("fixed key separates $700 / $707 / $875",
          len({fixed_key(c1, p), fixed_key(c2, p), fixed_key(c3, p)}) == 3)
    # 5. the cap cannot move a passage to a different key
    long_p = "x" * 5000
    check("3000-char cap cannot change a legacy key (passage[:40])",
          legacy_key(c1, long_p) == legacy_key(c1, long_p[:3000]))
    check("3000-char cap DOES change a fixed key (full text is hashed)",
          fixed_key(c1, long_p) != fixed_key(c1, long_p[:3000]),
          "so the work-list must ship the already-capped text, which it does")

    # 6. the NLI spec is harvestable from source
    try:
        spec = harvest_nli_spec()
        check("candidate_labels harvested from phase3d source",
              spec["candidate_labels"] == ["entailment", "contradiction", "neutral"],
              str(spec["candidate_labels"]))
        check("hypothesis_template prefix harvested",
              spec["hypothesis_template_prefix"] == "This passage {}s that ",
              repr(spec["hypothesis_template_prefix"]))
    except SystemExit as exc:
        check("NLI spec harvestable from phase3d source", False, str(exc))

    # 7. the real corpus reproduces the documented collision families
    nat = _load(NAT_RESULTS)
    src_neg = {r["claim_id"]: r for r in _load(NEG_SOURCE)}
    neg = [r for r in _load(NEG_RESULTS) if r["claim_id"] in src_neg]
    groups = collision_groups(nat + neg)
    fams = {frozenset(r["claim_id"] for r in v) for v in groups.values()}

    for expect in (
        {"Q2_C11", "SYN_QUAN_027", "SYN_QUAN_028", "SYN_QUAN_032"},
        {"SYN_QUAN_030", "SYN_QUAN_031"},
        {"Q5_C04", "SYN_QUAN_033", "SYN_QUAN_034", "SYN_QUAN_035",
         "SYN_QUAN_036", "SYN_QUAN_037"},
        {"Q1_C02", "SYN_TEMP_056", "SYN_TEMP_057", "SYN_TEMP_058",
         "SYN_TEMP_059", "SYN_TEMP_060"},
    ):
        check(f"corpus reproduces collision family {sorted(expect)[0]}+{len(expect) - 1}",
              frozenset(expect) in fams)

    check("SYN_QUAN_029 ($8 prefix) is in NO collision group -- non-vacuity on real data",
          not any("SYN_QUAN_029" in f for f in fams))

    # 8. cross-population reach: the whole point of grouping the union
    cross = [v for v in groups.values()
             if len({("SYN_" in r["claim_id"]) for r in v}) > 1]
    check("grouping the UNION finds cross-population collisions "
          "(neither single-population audit can)", len(cross) >= 4,
          f"found {len(cross)}")

    print("-" * 74)
    print("ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", dest="which", choices=("negatives", "natural", "both"),
                    default="both")
    ap.add_argument("--cache", default=None,
                    help="path to nonrouted_cache.json (default: search)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="report only, write nothing")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    doc = build(resolve_cache_path(args.cache), args.which)
    report(doc)

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    out = args.out or os.path.join(HERE, f"nli_rescore_worklist_{args.which}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print(f"\nwork-list -> {out}   ({os.path.getsize(out) / 1024:.1f} KB)")
    print("Upload that one file to Colab. Nothing else is needed there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
