#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# HalDetect environment + fix verification.
#
# Run:  ./verify_env.sh          (from the repo root)
#
# Checks, in dependency order:
#   1. every module in current/ parses            (offline)
#   2. the two bugs found on 2026-08-22 are fixed (offline)
#   3. Gemini key resolves and the API answers    (network)
#   4. ollama / gemma4:31b-cloud is reachable     (network)
#
# Never prints the Gemini API key -- only a masked fingerprint.
# ---------------------------------------------------------------------------
set -uo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
[ -x "$PY" ] || { echo "FATAL: $PY not found. Wrong directory?"; exit 1; }

hr() { printf '\n%s\n' "------------------------------------------------------------"; }

hr; echo "1. SYNTAX -- every module in current/ must parse"
"$PY" - <<'PYEOF'
import ast, pathlib, sys
bad = []
for p in sorted(pathlib.Path("current").glob("*.py")):
    try:
        ast.parse(p.read_text())
        print(f"   OK    {p.name}")
    except SyntaxError as e:
        bad.append(p.name)
        print(f"   FAIL  {p.name}: line {e.lineno}: {e.msg}")
print()
print("   => all modules parse" if not bad else f"   => STILL BROKEN: {bad}")
sys.exit(1 if bad else 0)
PYEOF

hr; echo "2a. BUG FIX -- quantitative_verifier.py --selftest"
echo "    (was: SyntaxError line 489, two statements on one line)"
"$PY" current/quantitative_verifier.py --selftest 2>&1 | tail -25

hr; echo "2b. BUG FIX -- consolidate_claims.py --verify"
echo "    (was: 'b1: expected 126 rows, got 125' -- the expectation was wrong,"
echo "     125 is correct; wc -l counted 2 embedded newlines as rows)"
"$PY" current/consolidate_claims.py --verify 2>&1 | tail -14

hr; echo "3. GEMINI -- key resolution + one live API call"
echo "   (removes the Colab 'from google.colab import userdata' coupling)"
"$PY" current/gemini_key.py --check 2>&1 | tail -12

hr; echo "4. OLLAMA / gemma4:31b-cloud"
if curl -s -m 12 http://localhost:11434/api/tags -o /tmp/haldetect_ollama.json \
     -w "   HTTP %{http_code}\n" 2>/dev/null; then
  "$PY" - <<'PYEOF'
import json
try:
    d = json.load(open("/tmp/haldetect_ollama.json"))
    names = [m.get("name", "?") for m in d.get("models", [])]
    print("   installed models:", names or "(none)")
    hit = [n for n in names if "gemma" in n.lower()]
    print("   gemma found     :", hit or "NO -- run: ollama pull gemma4:31b-cloud")
except Exception as e:
    print("   could not parse ollama response:", e.__class__.__name__)
PYEOF
else
  echo "   ollama NOT reachable at localhost:11434 -- start it with: ollama serve"
fi

hr; echo "5. LLM baseline connectivity (uses the model above)"
"$PY" current/llm_baseline.py --check 2>&1 | tail -12

hr; echo "6. NON-ROUTED BASELINE (RQ2) -- plumbing only, no network"
echo "   Loads all 356 claims and stratifies them. Should print the type mix."
"$PY" current/nonrouted_baseline.py --dry-run 2>&1 | tail -18

hr; echo "7. NON-ROUTED BASELINE -- can it import the authoritative verifier?"
echo "   This is the real test of the Colab shim: archive/scripts/"
echo "   relational_verifier_phase3d.py could not be imported off Colab before."
"$PY" current/nonrouted_baseline.py --check 2>&1 | tail -18

hr
cat <<'EOF'
Done.

If steps 1-7 are clean, the next command is the actual experiment. Start with a
stratified smoke test (10 claims, ~2 per type) before the full run:

    .venv/bin/python current/nonrouted_baseline.py --limit 10

Then the full pass over all 356 labeled claims (slow -- Wikipedia fetches plus
BART-MNLI per passage; it checkpoints to CSV every 10 claims so a crash does not
lose work):

    .venv/bin/python current/nonrouted_baseline.py

Anything marked FAIL above is a real blocker; report it verbatim.
EOF

