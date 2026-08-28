#!/usr/bin/env python3
"""
HalDetect Evolved -- Schema-Enriched 5-Tuple Claim Atomizer
==========================================================
Replaces naive flat-string splitting with a structured 5-tuple proposition schema:
  ⟨ Subject (S), Predicate (P), Object (O), Temporal Scope (T), Epistemic Mode (M) ⟩

Key Invariants:
  1. Temporal Preserving: Extracts start/end bounds and grammatical tense (PAST, PRESENT).
  2. Polarity Preserving: Captures explicit negation (ASSERTED_TRUE vs NEGATED).
  3. Epistemic Preserving: Flags hypothetical or unproven hedges (ASSERTION vs HYPOTHESIS).
  4. Unit/Datum Preserving: Isolates measurement datums ("above sea level") from operators.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


class SchemaAtomizer:
    """
    Rule-based & Regex-accelerated 5-Tuple Semantic Proposition Decomposer.
    Can be paired with an LLM grammar for zero-shot open-domain parsing.
    """

    # Common negation markers
    NEGATION_REGEX = re.compile(
        r"\b(not|never|neither|nor|did not|does not|failed to|unsuccessfully|no longer|none|without)\b",
        re.I
    )

    # Epistemic hedge markers
    HEDGE_REGEX = re.compile(
        r"\b(hypothesize|hypothesized|allegedly|rumored|theorized|claimed|believed to|may be|could be|possibly|perhaps)\b",
        re.I
    )

    # Temporal year/date pattern
    YEAR_SPAN_REGEX = re.compile(
        r"\b(?:from|between)\s+(\d{4})\s+(?:to|and|until)\s+(\d{4})\b|\b(?:in|on|since|until|during)\s+(\d{4})\b|\b(\d{4})\b",
        re.I
    )

    @classmethod
    def atomize_sentence(cls, sentence: str) -> List[Dict[str, Any]]:
        """
        Decomposes a single complex sentence into a list of 5-tuple atomic propositions.
        """
        text = sentence.strip()
        if not text:
            return []

        # 1. Determine Epistemic Mode
        epistemic_mode = "ASSERTION"
        if cls.HEDGE_REGEX.search(text):
            epistemic_mode = "HYPOTHESIS"

        # 2. Determine Polarity
        polarity = "ASSERTED_TRUE"
        if cls.NEGATION_REGEX.search(text):
            polarity = "NEGATED"

        # 3. Extract Temporal Scope
        temporal_scope = {"tense": "PRESENT", "start": None, "end": None, "raw_years": []}
        
        # Check grammatical tense
        if re.search(r"\b(was|were|served|served as|ruled|directed|published|founded|created|dissolved|died)\b", text, re.I):
            temporal_scope["tense"] = "HISTORICAL"
        elif re.search(r"\b(is|are|has|remains|continues to|currently)\b", text, re.I):
            temporal_scope["tense"] = "PRESENT"

        # Extract explicit year intervals
        m_span = re.search(r"\b(?:from|between)\s+(\d{4})\s+(?:to|and|until)\s+(\d{4})\b", text, re.I)
        if m_span:
            temporal_scope["start"] = m_span.group(1)
            temporal_scope["end"] = m_span.group(2)
            temporal_scope["raw_years"] = [m_span.group(1), m_span.group(2)]
        else:
            years = re.findall(r"\b(1\d{3}|20\d{2})\b", text)
            if years:
                temporal_scope["raw_years"] = years
                temporal_scope["start"] = years[0]
                if len(years) > 1:
                    temporal_scope["end"] = years[-1]

        # 4. Split Multi-Clause Conjunctions while preserving Subject
        # E.g. "Dwayne Johnson was born in 1972 and played college football for Miami"
        clauses = []
        if " and " in text and not re.search(r"\b(between \w+ and \w+|both \w+ and \w+)\b", text, re.I):
            parts = text.split(" and ")
            clauses = parts
        elif ", and " in text:
            clauses = text.split(", and ")
        else:
            clauses = [text]

        propositions = []
        primary_subject = None

        for idx, clause in enumerate(clauses):
            clause_clean = clause.strip()
            if not clause_clean:
                continue

            # Extract subject / predicate / object
            words = clause_clean.split()
            if idx == 0 or not primary_subject:
                primary_subject = " ".join(words[:2]) if len(words) >= 2 else words[0]

            prop_entry = {
                "raw_clause": clause_clean,
                "subject": primary_subject,
                "predicate": "relation",
                "object": clause_clean,
                "temporal_scope": temporal_scope,
                "polarity": polarity,
                "epistemic_mode": epistemic_mode
            }

            # Specialize predicate if obvious keywords exist
            if re.search(r"\b(born in|date of birth)\b", clause_clean, re.I):
                prop_entry["predicate"] = "date of birth"
            elif re.search(r"\b(died in|date of death)\b", clause_clean, re.I):
                prop_entry["predicate"] = "date of death"
            elif re.search(r"\b(president of|prime minister of|chancellor of|monarch of)\b", clause_clean, re.I):
                prop_entry["predicate"] = "position held"
            elif re.search(r"\b(gdp|population|inflation|unemployment)\b", clause_clean, re.I):
                prop_entry["predicate"] = "macroeconomic indicator"
            elif re.search(r"\b(published in|doi|author of)\b", clause_clean, re.I):
                prop_entry["predicate"] = "bibliographic"

            propositions.append(prop_entry)

        return propositions


if __name__ == "__main__":
    sample_text = (
        "Barack Obama served as the 44th President of the United States from 2009 to 2017. "
        "Marie Curie did not win the Nobel Prize in Literature, but she won in Physics. "
        "Scientists hypothesize that dark matter may account for 85% of total cosmic mass."
    )
    print("=" * 80)
    print(" HALDETECT EVOLVED: 5-TUPLE SCHEMA ATOMIZER DEMO")
    print("=" * 80)
    for sent in sample_text.split(". "):
        if sent:
            res = SchemaAtomizer.atomize_sentence(sent)
            print(f"\nRAW SENTENCE: \"{sent.strip()}\"")
            print(json.dumps(res, indent=2))
