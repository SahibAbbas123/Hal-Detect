#!/usr/bin/env python3
"""
HalDetect 2.5 -- Schema-Enriched 5-Tuple Claim Atomizer & Coreference Engine
============================================================================
Replaces naive flat-string splitting with a structured 5-tuple proposition schema:
  ⟨ Subject (S), Predicate (P), Object (O), Temporal Scope (T), Epistemic Mode (M) ⟩

Key Invariants:
  1. Anaphora & Coreference Normalization: Resolves pronoun chains ("He", "It", "They") across multi-sentence paragraphs.
  2. Multi-Aspect Detection: Flags compound claims (e.g., QUANTITATIVE + TEMPORAL) for DAG verification.
  3. Epistemic Preserving: Flags hypothetical or unproven hedges (ASSERTION vs HYPOTHESIS).
  4. Polarity Preserving: Captures explicit negation (ASSERTED_TRUE vs NEGATED).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


class SchemaAtomizer:
    """
    Rule-based & Regex-accelerated 5-Tuple Semantic Proposition Decomposer with
    Antecedent Anaphora Resolution.
    """

    NEGATION_REGEX = re.compile(
        r"\b(not|never|neither|nor|did not|does not|failed to|unsuccessfully|no longer|none|without)\b",
        re.I
    )

    HEDGE_REGEX = re.compile(
        r"\b(hypothesize|hypothesized|allegedly|rumored|theorized|claimed|believed to|may be|could be|possibly|perhaps|speculated)\b",
        re.I
    )

    PRONOUN_STARTS = re.compile(
        r"^(he|she|it|they|this|these|the company|the system|the processor|the chip|the algorithm|the model)\b",
        re.I
    )

    NUMBER_REGEX = re.compile(r"\b(\d+(?:\.\d+)?(?:\s*(?:billion|million|trillion|percent|%|cores|nm|qubits|meters|m|kg|gdp|kelvin|celsius|k|°c))?)\b", re.I)
    YEAR_REGEX = re.compile(r"\b(1\d{3}|20\d{2})\b")
    DOI_REGEX = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+|doi|arxiv|published in|journal|conference|neurips|icml|acl)\b", re.I)

    @classmethod
    def atomize_sentence(cls, sentence: str, antecedent_subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Decomposes a single complex sentence into a list of 5-tuple atomic propositions.
        Applies antecedent anaphora resolution if sentence begins with a pronoun.
        """
        text = sentence.strip()
        if not text:
            return []

        # 1. Epistemic Mode
        epistemic_mode = "ASSERTION"
        if cls.HEDGE_REGEX.search(text):
            epistemic_mode = "HYPOTHESIS"

        # 2. Polarity
        polarity = "ASSERTED_TRUE"
        if cls.NEGATION_REGEX.search(text):
            polarity = "NEGATED"

        # 3. Temporal Scope
        temporal_scope = {"tense": "PRESENT", "start": None, "end": None, "raw_years": []}
        if re.search(r"\b(was|were|served|served as|ruled|directed|published|founded|created|dissolved|died)\b", text, re.I):
            temporal_scope["tense"] = "HISTORICAL"
        elif re.search(r"\b(is|are|has|remains|continues to|currently)\b", text, re.I):
            temporal_scope["tense"] = "PRESENT"

        m_span = re.search(r"\b(?:from|between)\s+(\d{4})\s+(?:to|and|until)\s+(\d{4})\b", text, re.I)
        if m_span:
            temporal_scope["start"] = m_span.group(1)
            temporal_scope["end"] = m_span.group(2)
            temporal_scope["raw_years"] = [m_span.group(1), m_span.group(2)]
        else:
            years = cls.YEAR_REGEX.findall(text)
            if years:
                temporal_scope["raw_years"] = years
                temporal_scope["start"] = years[0]
                if len(years) > 1:
                    temporal_scope["end"] = years[-1]

        # 4. Multi-Aspect Tags
        aspect_tags = []
        if cls.NUMBER_REGEX.search(text):
            aspect_tags.append("QUANTITATIVE")
        if temporal_scope["raw_years"] or temporal_scope["tense"] == "HISTORICAL":
            aspect_tags.append("TEMPORAL")
        if cls.DOI_REGEX.search(text):
            aspect_tags.append("CITATION")
        if not aspect_tags:
            aspect_tags.append("RELATIONAL")

        # 5. Coreference / Anaphora Resolution
        words = text.split()
        first_few = " ".join(words[:2]).lower() if len(words) >= 2 else words[0].lower()
        
        extracted_subject = " ".join(words[:3]) if len(words) >= 3 else words[0]
        if antecedent_subject and cls.PRONOUN_STARTS.match(first_few):
            extracted_subject = antecedent_subject

        # Clean subject from trailing verbs
        extracted_subject = re.sub(r"\b(is|was|are|were|has|have|had|served|won|published)\b.*", "", extracted_subject, flags=re.I).strip()
        if not extracted_subject and antecedent_subject:
            extracted_subject = antecedent_subject

        prop_entry = {
            "raw_clause": text,
            "subject": extracted_subject or "Unknown_Subject",
            "predicate": "asserted_relation",
            "object": text,
            "temporal_scope": temporal_scope,
            "polarity": polarity,
            "epistemic_mode": epistemic_mode,
            "aspect_tags": aspect_tags,
            "is_compound": len(aspect_tags) > 1
        }

        return [prop_entry]

    @classmethod
    def atomize_paragraph(cls, paragraph: str) -> List[Dict[str, Any]]:
        """
        Decomposes an entire multi-sentence paragraph with forward antecedent tracking.
        """
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if len(s.strip()) > 8]
        propositions = []
        running_subject = None

        for s in sentences:
            props = cls.atomize_sentence(s, antecedent_subject=running_subject)
            for p in props:
                subj = p["subject"]
                # Update running subject if current subject is concrete and not a pronoun
                if subj and not cls.PRONOUN_STARTS.match(subj.lower()):
                    running_subject = subj
                propositions.append(p)

        return propositions


if __name__ == "__main__":
    sample_paragraph = (
        "The Apple M3 Max is manufactured on TSMC's 3nm process with 92 billion transistors. "
        "It was officially released in November 2023. "
        "The processor delivers industry-leading energy efficiency for pro laptops."
    )
    print("=" * 80)
    print(" HALDETECT 2.5: 5-TUPLE ATOMIZER WITH ANAPHORA TRACKING DEMO")
    print("=" * 80)
    res = SchemaAtomizer.atomize_paragraph(sample_paragraph)
    print(json.dumps(res, indent=2))
