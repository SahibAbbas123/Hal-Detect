#!/usr/bin/env python3
"""
Gemini API key rotation, with the verification step almost everyone skips.

WHY A SCRIPT AND NOT THREE SHELL COMMANDS
-----------------------------------------
Creating a new Gemini key does **not** revoke the old one. The old key keeps
working until it is explicitly deleted in the console. So "I made a new key and
saved it" is not a rotation -- it is two live keys, one of which has been sitting
in plaintext in three files and (until 2026-08-25) in notebook cached outputs.

This script therefore does four things in one pass, and the third is the point:

    1. live-check the NEW key                  -> must return HTTP 200
    2. install it atomically, mode 0600        -> only after (1) passes
    3. live-check the OLD key                  -> must now FAIL (403/400)
    4. remove the redundant duplicate copy     -> `.geminiAPI`, read by nothing

If step 3 still returns 200, the rotation is INCOMPLETE and the script says so
loudly: the old key is still valid and must be deleted at
https://aistudio.google.com/apikey

SECURITY
--------
* The new key is read from a FILE, never from argv. A key passed as a command-line
  argument leaks into shell history and into `ps` output for every user on the
  machine.
* Neither key is ever printed. Only masked fingerprints (`AQ.Ab8...ipHQ (len=53)`).
* The old key is held in memory only, never copied to a backup file -- a backup
  would recreate the exposure this rotation exists to end.
* `geminiAPI.txt` is written 0600 (it was found 0644, world-readable, on
  2026-08-25).

USAGE
    # 1. In the browser: https://aistudio.google.com/apikey
    #    -> create a new key, then DELETE the old one.
    # 2. Put the new key in a file (no echo, nothing in history):
    #        pbpaste > /tmp/newkey            # macOS, after copying the key
    # 3. Rotate:
    python current/rotate_gemini_key.py --new-key-file /tmp/newkey
    #    then delete that file:  rm -P /tmp/newkey

    python current/rotate_gemini_key.py --status     # inspect, change nothing
"""

from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import gemini_key  # noqa: E402

KEY_FILE = os.path.join(ROOT, gemini_key.DEFAULT_KEY_FILENAME)
REDUNDANT = os.path.join(ROOT, ".geminiAPI")


def mask(k: str | None) -> str:
    return gemini_key.describe(k)


def check_key(key: str, label: str) -> tuple[bool, str]:
    """Live-check an explicit key by temporarily placing it in the environment.

    `gemini_key.resolve()` reads env first, so this exercises the real code path
    without writing the key to disk.
    """
    saved = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = key
    try:
        ok, msg = gemini_key.check()
    finally:
        if saved is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = saved
    print(f"  {label:<12} {mask(key):<28} {'OK  ' if ok else 'FAIL'} -- {msg}")
    return ok, msg


def read_key_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    key = gemini_key._clean(raw)
    if not key:
        raise SystemExit(f"!! {path} holds no usable key after cleaning "
                         f"(len raw={len(raw)}). Aborting; nothing changed.")
    return key


def status() -> int:
    print("=" * 72)
    print("  GEMINI KEY STATUS")
    print("=" * 72)
    key, src = gemini_key.resolve()
    print(f"  resolved from : {src}")
    print(f"  fingerprint   : {mask(key)}")
    for p in (KEY_FILE, REDUNDANT):
        if os.path.exists(p):
            st = os.stat(p)
            perm = oct(st.st_mode & 0o777)
            warn = "  <-- should be 0o600" if (st.st_mode & 0o077) else ""
            print(f"  {os.path.relpath(p, ROOT):<16} {st.st_size:>4} B  "
                  f"mode {perm}{warn}")
    if os.path.exists(REDUNDANT):
        print(f"\n  NOTE: {os.path.relpath(REDUNDANT, ROOT)} is read by NO code in this")
        print("  repo (only geminiAPI.txt is in the resolution order). It is a second")
        print("  plaintext copy of the same secret with zero function -- this script")
        print("  removes it during rotation.")
    if not key:
        return 1
    print("\n  live check:")
    ok, _ = check_key(key, "current")
    return 0 if ok else 1


def rotate(new_key_file: str, keep_redundant: bool) -> int:
    print("=" * 72)
    print("  GEMINI KEY ROTATION")
    print("=" * 72)

    old_key, old_src = gemini_key.resolve()
    if not old_key:
        print(f"  no current key found ({old_src}) -- treating this as a fresh install")
    else:
        print(f"  old key       : {mask(old_key)}   (from {old_src})")

    new_key = read_key_file(new_key_file)
    print(f"  new key       : {mask(new_key)}   (from {new_key_file})")

    if old_key and new_key == old_key:
        raise SystemExit("!! The new key is IDENTICAL to the current one. That is not "
                         "a rotation. Create a new key first. Nothing changed.")

    # ---- 1. the new key must work BEFORE anything is overwritten ----------
    print("\n  [1/4] live-checking the NEW key before touching any file")
    ok, msg = check_key(new_key, "new")
    if not ok:
        raise SystemExit("\n!! The new key does not work. NOTHING HAS BEEN CHANGED.\n"
                         f"   {msg}\n"
                         "   Check you copied the whole key and that the Generative "
                         "Language API is enabled for its project.")

    # ---- 2. install atomically, 0600 -------------------------------------
    print("\n  [2/4] installing to geminiAPI.txt (atomic, mode 0600)")
    tmp = KEY_FILE + ".rotating"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, new_key.encode())
    finally:
        os.close(fd)
    os.replace(tmp, KEY_FILE)      # atomic; a crash leaves the old file intact
    os.chmod(KEY_FILE, 0o600)
    print(f"        wrote {os.path.relpath(KEY_FILE, ROOT)}  "
          f"({os.path.getsize(KEY_FILE)} B, mode 0o600)")

    # confirm the resolver now returns the new key
    got, src = gemini_key.resolve()
    if got != new_key:
        print(f"  !! resolver returned {mask(got)} from {src}, not the new key.")
        print("     An env var or $GEMINI_KEY_FILE is shadowing the file. Fix that "
              "before running anything that calls Gemini.")
    else:
        print(f"        resolver now returns {mask(got)} from {src}")

    # ---- 3. THE STEP EVERYONE SKIPS: is the old key dead? ----------------
    print("\n  [3/4] live-checking the OLD key -- it MUST now be rejected")
    if not old_key:
        print("        no old key to check")
        old_dead = True
    else:
        old_ok, old_msg = check_key(old_key, "old")
        old_dead = not old_ok
        if old_ok:
            print("\n  " + "!" * 66)
            print("  !! ROTATION INCOMPLETE -- THE OLD KEY STILL WORKS.")
            print("  !! Creating a new key does NOT revoke the old one.")
            print("  !! Go to https://aistudio.google.com/apikey and DELETE the key")
            print(f"  !! fingerprinted {mask(old_key)}.")
            print("  !! It has been in plaintext in 3 files and in notebook outputs.")
            print("  " + "!" * 66)

    # ---- 4. drop the redundant duplicate --------------------------------
    print("\n  [4/4] removing the redundant duplicate copy")
    if not os.path.exists(REDUNDANT):
        print("        .geminiAPI already absent")
    elif keep_redundant:
        print("        --keep-redundant given; leaving .geminiAPI in place")
        print("        (it is read by no code -- it is pure extra exposure)")
    else:
        os.remove(REDUNDANT)
        print("        removed .geminiAPI (read by no code; second copy of the secret)")

    print("\n" + "=" * 72)
    if old_dead:
        print("  ROTATION COMPLETE -- new key live, old key rejected.")
    else:
        print("  ROTATION HALF DONE -- new key live, OLD KEY STILL VALID. "
              "Delete it in the console.")
    print("=" * 72)
    print("\n  Reminder: shred the file you pasted the new key into:")
    print(f"      rm -P {new_key_file}")
    print("  Nothing needs re-running: rotating a key invalidates NO cache, so every")
    print("  recorded thesis number stays reproducible.")
    return 0 if old_dead else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true",
                    help="inspect the current key and file modes; change nothing")
    ap.add_argument("--new-key-file",
                    help="path to a file whose contents are the NEW key "
                         "(never pass the key itself as an argument)")
    ap.add_argument("--keep-redundant", action="store_true",
                    help="do not delete .geminiAPI")
    args = ap.parse_args()

    if args.status or not args.new_key_file:
        rc = status()
        if not args.new_key_file:
            print("\n  To rotate:")
            print("    1. https://aistudio.google.com/apikey -> create new, DELETE old")
            print("    2. pbpaste > /tmp/newkey")
            print("    3. python current/rotate_gemini_key.py --new-key-file /tmp/newkey")
            print("    4. rm -P /tmp/newkey")
        return rc
    return rotate(args.new_key_file, args.keep_redundant)


if __name__ == "__main__":
    raise SystemExit(main())
