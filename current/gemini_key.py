#!/usr/bin/env python3
"""
Portable GEMINI_API_KEY resolution + endpoint construction.

WHY THIS EXISTS
---------------
Every piece of Gemini-calling code in this project was written for Colab and
starts with:

    from google.colab import userdata
    GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')

That import raises `ModuleNotFoundError` outside Colab, so
`archive/scripts/relational_verifier_phase3d.py` -- which the RAG-for-fact-
verification handoff calls "the authoritative code for thesis results" -- cannot
even be *imported* on this machine, let alone run. Since the non-routed baseline
(RQ2) is built by running that same pipeline over every claim regardless of type,
the Colab coupling is directly in the way of the thesis's core experiment.

This module removes it. Import it instead of touching `userdata` directly.

RESOLUTION ORDER
----------------
1. `GEMINI_API_KEY` environment variable          (CI / shell-exported)
2. a key file                                     (this repo's actual setup)
       - `$GEMINI_KEY_FILE` if set
       - else `geminiAPI.txt` beside the repo root
3. Colab `userdata.get('GEMINI_API_KEY')`         (so the notebook keeps working)

Returns `None` when nothing is found -- it never raises. That is deliberate: the
RELATIONAL verifier has a documented fallback (bare-subject query) for exactly
this case, and turning a missing key into an exception would convert a graceful
coverage degradation into a crashed run.

SECURITY
--------
The key is never printed, logged, or written anywhere by this module.
`describe()` returns a masked fingerprint (`AQ.Ab8...4f21`, length only) so a
diagnostic can prove *which* key is loaded without disclosing it. `--check`
prints the masked form and the HTTP status, never the key.

If this repo is ever put under git, the key file MUST be gitignored. A
`.gitignore` covering `geminiAPI.txt` ships alongside this module.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DEFAULT_KEY_FILENAME = "geminiAPI.txt"
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Where a key file may live. Checked in order.
_CANDIDATE_DIRS = (ROOT, HERE, os.getcwd())


class GeminiKeyMissing(RuntimeError):
    """Raised only by `require()`, never by `resolve()`."""


def _clean(raw: str | None) -> str | None:
    """Strip whitespace/newlines and reject obvious non-keys.

    A key file saved from a browser or editor routinely carries a trailing
    newline; passing that straight into a URL yields a confusing 400 rather
    than an auth error, so it is stripped here once and for all.
    """
    if not raw:
        return None
    key = raw.strip().strip('"').strip("'").strip()
    if not key:
        return None
    # Guard against someone saving the whole `KEY=value` line, or a placeholder.
    if key.lower().startswith(("gemini_api_key=", "key=")):
        key = key.split("=", 1)[1].strip()
    if key.lower() in {"none", "null", "your-key-here", "changeme"}:
        return None
    return key


def key_file_path() -> str | None:
    """Locate the key file without reading it."""
    explicit = os.environ.get("GEMINI_KEY_FILE")
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for d in _CANDIDATE_DIRS:
        p = os.path.join(d, DEFAULT_KEY_FILENAME)
        if os.path.isfile(p):
            return p
    return None


def resolve() -> tuple[str | None, str]:
    """Return `(key_or_None, source_label)`. Never raises, never logs the key."""
    env = _clean(os.environ.get("GEMINI_API_KEY"))
    if env:
        return env, "env:GEMINI_API_KEY"

    path = key_file_path()
    if path:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                k = _clean(fh.read())
            if k:
                return k, f"file:{os.path.relpath(path, ROOT)}"
        except OSError as exc:
            # Report the failure shape, not the contents.
            return None, f"file:{path} unreadable ({exc.__class__.__name__})"

    try:  # pragma: no cover - only reachable inside Colab
        from google.colab import userdata  # type: ignore
        k = _clean(userdata.get("GEMINI_API_KEY"))
        if k:
            return k, "colab:userdata"
    except Exception:
        pass

    return None, "not found"


def get() -> str | None:
    """Just the key, or None. The common case."""
    return resolve()[0]


def require() -> str:
    """The key, or raise with actionable instructions."""
    key, src = resolve()
    if key:
        return key
    raise GeminiKeyMissing(
        "No Gemini API key found. Tried, in order: $GEMINI_API_KEY, "
        f"$GEMINI_KEY_FILE, {DEFAULT_KEY_FILENAME} in {ROOT}, Colab userdata. "
        f"(last status: {src})\n"
        f"Fix with either:\n"
        f"  export GEMINI_API_KEY=...\n"
        f"  printf %s '<key>' > {os.path.join(ROOT, DEFAULT_KEY_FILENAME)}"
    )


def describe(key: str | None = None) -> str:
    """Masked fingerprint, safe to print and safe to paste into a log."""
    if key is None:
        key = get()
    if not key:
        return "<no key>"
    n = len(key)
    if n <= 12:
        return f"<key len={n}>"
    return f"{key[:6]}...{key[-4:]} (len={n})"


def endpoint(model: str = DEFAULT_MODEL, key: str | None = None) -> str:
    """Full generateContent URL. Contains the key -- never print the result."""
    k = key or require()
    return f"{API_BASE}/{model}:generateContent?key={k}"


def _scrub(msg: str, key: str | None) -> str:
    """Replace any occurrence of `key` in `msg` with its masked fingerprint.

    Google's API takes the key as a URL query parameter, so the key is inside
    every request URL -- and several exception types embed the URL they failed
    on. `http.client.InvalidURL` is the one that bit us on 2026-08-25: it is an
    `HTTPException`, so neither the `HTTPError` nor the `URLError` handler in
    `check()` caught it, and it reached stdout carrying the whole key.

    Scrubbing the message is the durable fix rather than adding one more
    `except` clause, because the next exception type to embed a URL would leak
    again. Anything that returns a message derived from a request must pass it
    through here first.

    Two subtleties, both found by the regression test rather than by reasoning:

    * Exceptions often render the URL with `repr()`, so a key containing a
      newline appears as the two characters `\\n` and the literal key string
      does not match. So we scrub the whitespace-separated FRAGMENTS too.
    * A malformed key file can hold several keys (that is exactly how the leak
      was discovered -- `old:`/`new:` labelled lines). Every fragment long
      enough to be a secret is scrubbed, not just the first.
    """
    if not key or not msg:
        return msg
    out = msg.replace(key, describe(key))
    # Longest first, so a fragment can never partially clobber a longer one.
    for frag in sorted(key.split(), key=len, reverse=True):
        if len(frag) > 12:
            out = out.replace(frag, describe(frag))
    return out


# ---------------------------------------------------------------------------
# Live check
# ---------------------------------------------------------------------------

def check(model: str = DEFAULT_MODEL, timeout: int = 30) -> tuple[bool, str]:
    """One minimal generateContent call. Returns `(ok, human_message)`.

    Distinguishes the three failure modes that matter, because they need
    different fixes: no key at all, a key the API rejects (400/403), and a key
    that is fine but the model name is wrong (404).
    """
    key, src = resolve()
    if not key:
        return False, f"no key ({src})"

    body = json.dumps({
        "contents": [{"parts": [{"text": "Reply with the single word: OK"}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 8},
    }).encode()

    req = urllib.request.Request(
        endpoint(model, key), data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
        text = ""
        for cand in payload.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")
        return True, f"HTTP 200 from {model}; replied {text.strip()[:40]!r}"
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            err = json.loads(exc.read().decode())
            detail = err.get("error", {}).get("message", "")[:200]
        except Exception:
            pass
        hint = {
            400: "malformed request or invalid key",
            401: "not a valid API key (this is what a revoked or mistyped key returns)",
            403: "key rejected / API not enabled for this project",
            404: f"model {model!r} not found for this key",
            429: "rate limited (key works)",
        }.get(exc.code, "")
        return exc.code == 429, _scrub(f"HTTP {exc.code} ({hint}) {detail}", key)
    except urllib.error.URLError as exc:
        return False, _scrub(f"network error: {exc.reason}", key)
    except Exception as exc:
        # Catch-all on purpose. `http.client.InvalidURL` is neither HTTPError
        # nor URLError, so before 2026-08-25 it escaped both handlers above and
        # printed the request URL -- key included. Never let a request-derived
        # message reach a caller unscrubbed, whatever its type.
        return False, _scrub(f"{type(exc).__name__}: {exc}", key)
    except Exception as exc:  # noqa: BLE001
        return False, f"{exc.__class__.__name__}: {exc}"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Gemini key resolution + live check")
    ap.add_argument("--check", action="store_true", help="make one live API call")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    key, src = resolve()
    print(f"source : {src}")
    print(f"key    : {describe(key)}")
    print(f"model  : {args.model}")
    kf = key_file_path()
    print(f"keyfile: {kf or '<none found>'}")

    if not args.check:
        print("\n(pass --check to make one live API call)")
        return 0 if key else 1

    ok, msg = check(args.model)
    print(f"\nlive   : {'OK' if ok else 'FAIL'} -- {msg}")
    if ok:
        print("\nGemini is usable from this machine. The Colab `userdata` "
              "coupling is no longer a blocker for the non-routed baseline.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
