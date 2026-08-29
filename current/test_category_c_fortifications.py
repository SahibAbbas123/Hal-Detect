#!/usr/bin/env python3
"""
HalDetect 2.0 -- Category C Integrated Fortification Verification Suite
========================================================================
Comprehensive test runner for:
  • C.1: Multi-Hop 2-Hop SPARQL Transitive Graph Verifier
  • C.2: Nickname, Alias & Acronym Lexicon Resolver
  • C.3: Nominal vs. PPP Multi-Currency Macroeconomic Normalizer
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from multihop_sparql_verifier import MultiHopSPARQLVerifier
from alias_lexicon_resolver import AliasLexiconResolver
from quantitative_tier2_verifier import verify_macro_claim, load_macro_cache

def run_suite():
    print("=" * 90)
    print(" 🚀 HALDETECT 2.0 -- CATEGORY C FORTIFICATION SUITE EXECUTION")
    print("=" * 90)
    
    passed_all = True

    # -----------------------------------------------------------------------
    # TEST 1: MULTI-HOP SPARQL (C.1)
    # -----------------------------------------------------------------------
    print("\n[1/3] 🌐 Testing Multi-Hop 2-Hop SPARQL Transitive Reasoning...")
    c1_tests = [
        ("The birthplace of the director of Inception is London.", "TRUE"),
        ("The birthplace of the director of Inception is Paris.", "FALSE"),
        ("The founder of the developer of ChatGPT is Sam Altman.", "TRUE"),
        ("The founder of the developer of ChatGPT is Sundar Pichai.", "FALSE"),
        ("The CEO of the parent company of Instagram is Mark Zuckerberg.", "TRUE"),
        ("The CEO of the parent company of Instagram is Satya Nadella.", "FALSE"),
    ]
    for claim, expected in c1_tests:
        res = MultiHopSPARQLVerifier.verify_multihop_claim(claim)
        verdict = res["verdict"] if res else "ABSTAIN"
        ok = (verdict == expected)
        if not ok: passed_all = False
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} | Verdict: {verdict:<5} (Expected: {expected}) | '{claim}'")

    # -----------------------------------------------------------------------
    # TEST 2: ALIAS & NICKNAME RESOLVER (C.2)
    # -----------------------------------------------------------------------
    print("\n[2/3] 🏷️ Testing Nickname, Alias & Acronym Lexicon Resolver...")
    c2_tests = [
        ("Joe Biden", "Joseph Biden", True),
        ("Bill Clinton", "William Clinton", True),
        ("Bob Dylan", "Robert Dylan", True),
        ("Dick Cheney", "Richard Cheney", True),
        ("Liz Truss", "Elizabeth Truss", True),
        ("Chuck Schumer", "Charles Schumer", True),
        ("Ted Kennedy", "Edward Kennedy", True),
        ("Jack Kennedy", "John Kennedy", True),
        ("MIT", "Massachusetts Institute of Technology", True),
        ("TSMC", "Taiwan Semiconductor Manufacturing Company", True),
        ("Albert Einstein", "Robert Einstein", False),
        ("John Adams", "John Quincy Adams", False),
    ]
    for p1, p2, expected in c2_tests:
        eq = AliasLexiconResolver.are_names_equivalent(p1, p2)
        ok = (eq == expected)
        if not ok: passed_all = False
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} | Match: {str(eq):<5} (Expected: {str(expected):<5}) | '{p1}' ⟷ '{p2}'")

    # -----------------------------------------------------------------------
    # TEST 3: NOMINAL VS PPP MACRO VERIFIER (C.3)
    # -----------------------------------------------------------------------
    print("\n[3/3] 📊 Testing Nominal vs. PPP World Bank Macroeconomic Verifier...")
    cache = load_macro_cache()
    c3_tests = [
        ({"claim": "The nominal GDP of the United States reached approximately 27.8 trillion dollars in 2023.", "subject": "United States"}, "TRUE"),
        ({"claim": "The nominal GDP of the United States in 2023 was only 12.5 trillion dollars.", "subject": "United States"}, "FALSE"),
        ({"claim": "India's GDP (PPP) in 2023 reached approximately 13.2 trillion dollars.", "subject": "India"}, "TRUE"),
        ({"claim": "India's GDP (PPP) in 2023 was only 4.5 trillion dollars.", "subject": "India"}, "FALSE"),
        ({"claim": "Life expectancy in Japan was approximately 84 years in 2022.", "subject": "Japan"}, "TRUE"),
        ({"claim": "Life expectancy in Japan dropped to 52 years in 2022.", "subject": "Japan"}, "FALSE"),
    ]
    for tc, expected in c3_tests:
        res = verify_macro_claim(tc, cache)
        verdict = res["verdict"]
        ok = (verdict == expected)
        if not ok: passed_all = False
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} | Verdict: {verdict:<5} (Expected: {expected}) | '{tc['claim']}'")

    print("\n" + "=" * 90)
    if passed_all:
        print(" 🎉 ALL CATEGORY C FORTIFICATION SUITES PASSED WITH 100% SUCCESS!")
    else:
        print(" ⚠️ SOME TESTS FAILED. PLEASE REVIEW LOGS.")
    print("=" * 90)

if __name__ == "__main__":
    run_suite()
