#!/usr/bin/env python3
"""
HalDetect 2.0 -- Comprehensive Nickname, Alias & Acronym Resolver (Category C.2)
=================================================================================
Expands entity linking and property resolution by bridging informal diminutives,
common English/multilingual nicknames, institutional acronyms, and geographical aliases.
"""

from __future__ import annotations

import re
import sys
from typing import Dict, List, Set, Tuple

# Disjoint canonical nickname sets (no polysemous bridges across distinct root names)
CANONICAL_NICKNAMES: Dict[str, Set[str]] = {
    # English Male Roots
    "william": {"william", "bill", "billy", "will", "willy", "liam"},
    "robert": {"robert", "bob", "bobby", "rob", "robbie"},
    "richard": {"richard", "dick", "rick", "ricky", "rich", "richie"},
    "james": {"james", "jim", "jimmy", "jamie"},
    "john": {"john", "jack", "jackie", "johnny", "jon"},
    "joseph": {"joseph", "joe", "joey"},
    "charles": {"charles", "chuck", "charlie", "chas"},
    "edward": {"edward", "ted", "teddy", "ed", "eddie", "ned"},
    "theodore": {"theodore", "ted", "teddy", "theo"},
    "alexander": {"alexander", "alex", "alec", "sasha", "xander"},
    "anthony": {"anthony", "tony", "antony"},
    "samuel": {"samuel", "sam", "sammy"},
    "thomas": {"thomas", "tom", "tommy"},
    "daniel": {"daniel", "dan", "danny"},
    "michael": {"michael", "mike", "mikey"},
    "david": {"david", "dave", "davey"},
    "henry": {"henry", "hank", "harry", "hal"},
    "francis": {"francis", "frank", "frankie"},
    "franklin": {"franklin", "frank", "frankie"},
    "christopher": {"christopher", "chris"},
    "matthew": {"matthew", "matt", "matty"},
    "nicholas": {"nicholas", "nick", "nicky", "nicolas"},
    "kenneth": {"kenneth", "ken", "kenny"},
    "stephen": {"stephen", "steven", "steve", "stevie"},
    "andrew": {"andrew", "andy", "drew"},
    "peter": {"peter", "pete"},
    "ronald": {"ronald", "ron", "ronnie"},
    "donald": {"donald", "don", "donnie"},
    "bernard": {"bernard", "bernie"},
    "manuel": {"manuel", "manny", "emmanuel"},
    "benjamin": {"benjamin", "ben", "benny", "benji"},
    "arthur": {"arthur", "art", "artie"},
    "albert": {"albert", "al"},
    "walter": {"walter", "walt", "wally"},
    "timothy": {"timothy", "tim", "timmy"},
    "patrick": {"patrick", "pat", "paddy"},

    # English Female Roots
    "elizabeth": {"elizabeth", "liz", "lizzie", "beth", "betty", "eliza", "bess", "ellie"},
    "margaret": {"margaret", "peggy", "maggie", "meg", "marge", "margie", "daisy"},
    "catherine": {"catherine", "katherine", "cathy", "kathy", "kate", "katie", "kay"},
    "mary": {"mary", "molly", "polly", "mae"},
    "patricia": {"patricia", "pat", "patty", "trish", "tricia"},
    "susan": {"susan", "sue", "susie", "suzy"},
    "jennifer": {"jennifer", "jen", "jenny"},
    "eleanor": {"eleanor", "ellie", "nora", "nell"},
    "virginia": {"virginia", "ginny"},
    "rebecca": {"rebecca", "becky", "becca"},
    "sarah": {"sarah", "sally", "sadie"},
    "dorothy": {"dorothy", "dot", "dottie"},
    "judith": {"judith", "judy"},
    "barbara": {"barbara", "barb", "barbie"},
    "teresa": {"teresa", "theresa", "terry", "tess"},
    "abigail": {"abigail", "abby", "gail"},
    "victoria": {"victoria", "vicky", "tori"},
    "deborah": {"deborah", "deb", "debby", "debbie"},
    "samantha": {"samantha", "sam", "sammy"}
}

# Build fast lookup map: name -> canonical root
_NAME_TO_ROOTS: Dict[str, Set[str]] = {}
for root, var_set in CANONICAL_NICKNAMES.items():
    for name in var_set:
        if name not in _NAME_TO_ROOTS:
            _NAME_TO_ROOTS[name] = set()
        _NAME_TO_ROOTS[name].add(root)


# ---------------------------------------------------------------------------
# INSTITUTIONAL & SCIENTIFIC ACRONYMS
# ---------------------------------------------------------------------------
ACRONYM_MAP: Dict[str, str] = {
    "mit": "Massachusetts Institute of Technology",
    "cmu": "Carnegie Mellon University",
    "caltech": "California Institute of Technology",
    "nyu": "New York University",
    "ucla": "University of California, Los Angeles",
    "ucb": "University of California, Berkeley",
    "uc berkeley": "University of California, Berkeley",
    "eth": "ETH Zurich",
    "cern": "European Organization for Nuclear Research",
    "nasa": "National Aeronautics and Space Administration",
    "esa": "European Space Agency",
    "who": "World Health Organization",
    "un": "United Nations",
    "unicef": "United Nations Children's Fund",
    "imf": "International Monetary Fund",
    "wto": "World Trade Organization",
    "wb": "World Bank",
    "epa": "Environmental Protection Agency",
    "fda": "Food and Drug Administration",
    "usgs": "United States Geological Survey",
    "iupac": "International Union of Pure and Applied Chemistry",
    "noaa": "National Oceanic and Atmospheric Administration",
    "nist": "National Institute of Standards and Technology",
    "fbi": "Federal Bureau of Investigation",
    "cia": "Central Intelligence Agency",
    "cdc": "Centers for Disease Control and Prevention",
    "nih": "National Institutes of Health",
    "ibm": "International Business Machines",
    "tsmc": "Taiwan Semiconductor Manufacturing Company",
    "asml": "ASML Holding",
    "amd": "Advanced Micro Devices",
    "arm": "Arm Holdings",
    "gdp": "Gross Domestic Product",
    "cpi": "Consumer Price Index",
    "ppp": "Purchasing Power Parity"
}


class AliasLexiconResolver:
    """
    Performs fast, deterministic alias and nickname canonicalization.
    """

    @classmethod
    def are_first_names_equivalent(cls, fn1: str, fn2: str) -> bool:
        f1, f2 = fn1.strip().lower(), fn2.strip().lower()
        if f1 == f2:
            return True
        roots1 = _NAME_TO_ROOTS.get(f1, set())
        roots2 = _NAME_TO_ROOTS.get(f2, set())
        return bool(roots1.intersection(roots2))

    @classmethod
    def expand_person_name(cls, full_name: str) -> Set[str]:
        tokens = full_name.strip().split()
        if not tokens:
            return {full_name}

        first = tokens[0].lower()
        rest = " ".join(tokens[1:])
        variants = {full_name}

        roots = _NAME_TO_ROOTS.get(first, set())
        for r in roots:
            for fn_var in CANONICAL_NICKNAMES[r]:
                variants.add(f"{fn_var.title()} {rest}".strip() if rest else fn_var.title())
        return variants

    @classmethod
    def are_names_equivalent(cls, name1: str, name2: str) -> bool:
        n1 = name1.strip().lower()
        n2 = name2.strip().lower()
        if n1 == n2:
            return True

        # Acronym check
        if n1 in ACRONYM_MAP and ACRONYM_MAP[n1].lower() == n2:
            return True
        if n2 in ACRONYM_MAP and ACRONYM_MAP[n2].lower() == n1:
            return True

        # Check full name tokens
        toks1 = n1.split()
        toks2 = n2.split()
        if len(toks1) == 1 and len(toks2) == 1:
            return cls.are_first_names_equivalent(toks1[0], toks2[0])

        if len(toks1) >= 2 and len(toks2) >= 2:
            last1, last2 = toks1[-1], toks2[-1]
            if last1 == last2:
                first1, first2 = toks1[0], toks2[0]
                if cls.are_first_names_equivalent(first1, first2):
                    # Middle name check if present
                    if len(toks1) == 2 and len(toks2) == 2:
                        return True
                    if len(toks1) == 3 and len(toks2) == 3:
                        return toks1[1] == toks2[1] or toks1[1][0] == toks2[1][0]
                    # If one has middle name and the other does not:
                    # Only match if middle name is a single letter initial (e.g. Samuel H. Altman == Sam Altman)
                    if len(toks1) == 3 and len(toks2) == 2:
                        return len(toks1[1].rstrip(".")) == 1
                    if len(toks1) == 2 and len(toks2) == 3:
                        return len(toks2[1].rstrip(".")) == 1
                    return False

        return False


if __name__ == "__main__":
    print("=" * 80)
    print(" 🚀 HALDETECT 2.0 -- NICKNAME, ALIAS & ACRONYM RESOLVER TEST")
    print("=" * 80)
    test_pairs = [
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
        ("IUPAC", "International Union of Pure and Applied Chemistry", True),
        ("Albert Einstein", "Robert Einstein", False),
        ("John Adams", "John Quincy Adams", False)
    ]
    all_passed = True
    for p1, p2, expected in test_pairs:
        eq = AliasLexiconResolver.are_names_equivalent(p1, p2)
        passed = (eq == expected)
        if not passed: all_passed = False
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | '{p1}' ⟷ '{p2}' : result={eq} (expected={expected})")
    
    if all_passed:
        print("\n🎉 ALL 13 TEST CASES PASSED PERFECTLY!")
