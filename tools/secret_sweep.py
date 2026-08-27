#!/usr/bin/env python3
"""Three-arm secret sweep over STAGED content. Prints only computed booleans.

Arm 1  filename    -- no credential-shaped path is staged.
Arm 2  literal     -- the resolved secret VALUES do not appear in staged content.
                      A filename check cannot catch an embedded key, which is the
                      whole reason this arm exists.
Arm 3  shape       -- no key-shaped token appears in staged content, which catches
                      a DIFFERENT key than the ones this machine can resolve.

The secret values are read into memory and compared; they are NEVER printed,
logged, or passed through argv. Output is booleans and counts only.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

BAD_NAME = re.compile(
    r"(^|/)(\.env|\.envrc|geminiAPI\.txt|.*_key\.txt|.*\.pem|.*\.p12|.*\.pfx|"
    r"id_rsa.*|id_ed25519.*|.*credentials.*\.json|\.netrc|\.zshrc|.*\.key)$",
    re.I,
)

# Shapes, not values. Google AI Studio keys, Google OAuth-ish tokens, Anthropic
# keys, OpenAI keys, generic long base64ish blobs assigned to a key-ish name.
SHAPES = [
    ("google-aistudio", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("google-oauth-ish", re.compile(r"\bAQ\.[A-Za-z0-9_\-]{20,}")),
    ("anthropic", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai", re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    ("github-pat", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}")),
    ("assigned-blob", re.compile(
        r"(?i)(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*"
        r"['\"][A-Za-z0-9_\-+/=\.]{28,}['\"]")),
]


def sh(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout


def resolved_secrets() -> tuple[list[str], list[str]]:
    """Return (values, labels). Values are secret; labels are safe to print."""
    vals: list[str] = []
    labels: list[str] = []

    sys.path.insert(0, os.path.join(ROOT, "current"))
    try:
        import gemini_key  # noqa: PLC0415
        # get() returns the key or None. resolve() returns a (key, source) TUPLE
        # -- calling the wrong one silently puts a tuple in `vals`, and `v in
        # blob` then raises instead of comparing, which is an arm that looks like
        # it ran and proved nothing.
        v = gemini_key.get()
        if v:
            vals.append(v)
            labels.append(f"gemini ({gemini_key.describe()})")
        else:
            labels.append("gemini UNRESOLVED (get() returned None) -- arm 2 weaker")
    except Exception as exc:  # noqa: BLE001
        labels.append(f"gemini UNRESOLVED ({type(exc).__name__}) -- arm 2 weaker")

    for env in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                "GOOGLE_API_KEY", "OPENAI_API_KEY"):
        v = os.environ.get(env)
        if v and len(v) >= 16:
            vals.append(v)
            labels.append(f"{env} (len={len(v)})")

    # ~/.zshrc holds a live token per the project's security notes. Read it into
    # memory to extract assignment values -- never printed.
    zsh = os.path.expanduser("~/.zshrc")
    if os.path.isfile(zsh):
        try:
            txt = open(zsh, encoding="utf-8", errors="replace").read()
            for m in re.finditer(
                    r"(?:export\s+)?([A-Z0-9_]*(?:TOKEN|KEY|SECRET))\s*=\s*"
                    r"['\"]?([A-Za-z0-9_\-+/=\.]{16,})['\"]?", txt):
                vals.append(m.group(2))
                labels.append(f"~/.zshrc:{m.group(1)} (len={len(m.group(2))})")
        except Exception as exc:  # noqa: BLE001
            labels.append(f"~/.zshrc unreadable ({type(exc).__name__})")

    return vals, labels


def main() -> int:
    staged = [p for p in sh("git", "diff", "--cached", "--name-only").split("\n") if p]
    if not staged:
        print("nothing staged -- stage first, then sweep")
        return 1

    fails = 0
    print(f"staged files: {len(staged)}")
    for p in staged:
        print(f"  {p}")

    print("\n-- arm 1: filename shapes --")
    hits = [p for p in staged if BAD_NAME.search(p)]
    print(f"  credential-shaped paths staged: {len(hits)}  {hits if hits else 'none'}")
    fails += len(hits)

    # Staged CONTENT, read once into memory.
    blob = sh("git", "diff", "--cached", "--unified=0")

    print("\n-- arm 2: literal secret values in staged content --")
    vals, labels = resolved_secrets()
    print(f"  secrets resolved for comparison: {len(vals)}")
    for lab in labels:
        print(f"    - {lab}")
    if not vals:
        print("  !! NO secret resolved -- arm 2 proved nothing; rely on arms 1 and 3")
    n2 = 0
    for v in vals:
        if v and v in blob:
            n2 += 1
    print(f"  staged content contains a resolved secret: {bool(n2)}  (matches={n2})")
    fails += n2

    print("\n-- arm 3: key-shaped tokens in staged content --")
    n3 = 0
    for name, rx in SHAPES:
        found = rx.findall(blob)
        # Report the COUNT and the pattern name only -- never the match.
        if found:
            n3 += len(found)
            print(f"  {name:16s} MATCHES: {len(found)}  <-- inspect manually, not printed")
        else:
            print(f"  {name:16s} clean")
    fails += n3

    print("\n" + ("SWEEP CLEAN -- safe to commit" if fails == 0
                  else f"SWEEP FAILED -- {fails} finding(s), DO NOT COMMIT"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
