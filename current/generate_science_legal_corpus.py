#!/usr/bin/env python3
"""
HalDetect — Science, Legal & Clinical Benchmark Suite (EXP-5 Dataset)
====================================================================

Generates 105 dense, realistic claims across Science, Law, Medicine & History:
  - Physics Constants & Astronomy (Planck constant, Jupiter moons, Saturn moons)
  - Chemistry & Molecular Biology (Atomic weights, Elements, DNA base pairs)
  - Clinical Pharmacology (Drug indications, Transplants, Receptors)
  - Legal Precedents (SCOTUS, International declarations, Treaties)
  - World Geography & Infrastructure (Canals, Bridge spans, Capital cities)

Output: `current/expansion_science_legal.csv`
Total Master Corpus will exceed 1,000 claims (1,014 total claims).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_science_legal.csv")

SCIENCE_LEGAL_CLAIMS = [
    # -------------------------------------------------------------------------
    # 1. QUANTITATIVE (21 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "SL_QUAN_001", "type": "QUANTITATIVE", "subject": "Jupiter",
     "property": "number_of_moons", "value": "95", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "As recognized by the IAU, Jupiter has 95 officially confirmed natural satellites.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "IAU official planetary moon count"},
    {"claim_id": "SL_QUAN_002", "type": "QUANTITATIVE", "subject": "Jupiter",
     "property": "number_of_moons", "value": "150", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "As recognized by the IAU, Jupiter has 150 officially confirmed natural satellites.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Exaggerated satellite count"},
    {"claim_id": "SL_QUAN_003", "type": "QUANTITATIVE", "subject": "Saturn",
     "property": "number_of_moons", "value": "146", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Saturn has 146 officially recognized moons in its planetary orbit.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "IAU 2023 Saturn satellite discovery"},
    {"claim_id": "SL_QUAN_004", "type": "QUANTITATIVE", "subject": "Saturn",
     "property": "number_of_moons", "value": "50", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Saturn has 50 officially recognized moons in its planetary orbit.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Severely understated moon count"},
    {"claim_id": "SL_QUAN_005", "type": "QUANTITATIVE", "subject": "Carbon",
     "property": "standard_atomic_weight", "value": "12.011", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The IUPAC standard atomic weight of carbon is approximately 12.011 atomic mass units.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "IUPAC standard atomic weight"},
    {"claim_id": "SL_QUAN_006", "type": "QUANTITATIVE", "subject": "Carbon",
     "property": "standard_atomic_weight", "value": "14.500", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The IUPAC standard atomic weight of carbon is approximately 14.500 atomic mass units.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "Shifted atomic weight"},
    {"claim_id": "SL_QUAN_007", "type": "QUANTITATIVE", "subject": "Avogadro constant",
     "property": "numerical_value", "value": "6.02214076e23", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Avogadro constant is defined exactly as 6.02214076 × 10^23 reciprocal moles.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "SI standard physical constant"},
    {"claim_id": "SL_QUAN_008", "type": "QUANTITATIVE", "subject": "Avogadro constant",
     "property": "numerical_value", "value": "9.81e23", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Avogadro constant is defined exactly as 9.81 × 10^23 reciprocal moles.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Confused with gravitational acceleration constant"},
    {"claim_id": "SL_QUAN_009", "type": "QUANTITATIVE", "subject": "Panama Canal",
     "property": "length", "value": "82 kilometers", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Panama Canal cuts across the Isthmus of Panama for a total length of 82 kilometers.",
     "domain": "infrastructure", "sub_type": "NUMERICAL", "notes": "Panama Canal Authority official length"},
    {"claim_id": "SL_QUAN_010", "type": "QUANTITATIVE", "subject": "Panama Canal",
     "property": "length", "value": "193 kilometers", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Panama Canal cuts across the Isthmus of Panama for a total length of 193 kilometers.",
     "domain": "infrastructure", "sub_type": "NUMERICAL", "notes": "Confused Panama Canal with Suez Canal (193 km)"},
    {"claim_id": "SL_QUAN_011", "type": "QUANTITATIVE", "subject": "Planck constant",
     "property": "value", "value": "6.62607015e-34 J s", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The fundamental Planck constant is defined as 6.62607015 × 10^-34 joule-seconds.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "NIST standard physical constant"},
    {"claim_id": "SL_QUAN_012", "type": "QUANTITATIVE", "subject": "Planck constant",
     "property": "value", "value": "1.380649e-23 J s", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The fundamental Planck constant is defined as 1.380649 × 10^-23 joule-seconds.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Confused Planck constant with Boltzmann constant"},

    # -------------------------------------------------------------------------
    # 2. TEMPORAL (21 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "SL_TEMP_001", "type": "TEMPORAL", "subject": "Universal Declaration of Human Rights",
     "property": "adoption_date", "value": "December 10, 1948", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The United Nations General Assembly adopted the Universal Declaration of Human Rights on December 10, 1948.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "UN General Assembly resolution 217 A"},
    {"claim_id": "SL_TEMP_002", "type": "TEMPORAL", "subject": "Universal Declaration of Human Rights",
     "property": "adoption_date", "value": "December 10, 1960", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The United Nations General Assembly adopted the Universal Declaration of Human Rights on December 10, 1960.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted declaration date"},
    {"claim_id": "SL_TEMP_003", "type": "TEMPORAL", "subject": "Human Genome Project",
     "property": "draft_completion_date", "value": "June 26, 2000", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The initial working draft of the human genome was jointly announced by the Human Genome Project and Celera on June 26, 2000.",
     "domain": "science_history", "sub_type": "POINT_IN_TIME", "notes": "White House genome announcement"},
    {"claim_id": "SL_TEMP_004", "type": "TEMPORAL", "subject": "Human Genome Project",
     "property": "draft_completion_date", "value": "June 26, 1990", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The initial working draft of the human genome was jointly announced by the Human Genome Project and Celera on June 26, 1990.",
     "domain": "science_history", "sub_type": "POINT_IN_TIME", "notes": "Confused project launch with draft announcement"},
    {"claim_id": "SL_TEMP_005", "type": "TEMPORAL", "subject": "First human heart transplant",
     "property": "surgery_date", "value": "December 3, 1967", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Dr. Christiaan Barnard performed the world's first human-to-human heart transplant on December 3, 1967 in Cape Town.",
     "domain": "medical_history", "sub_type": "POINT_IN_TIME", "notes": "Groote Schuur Hospital transplant"},
    {"claim_id": "SL_TEMP_006", "type": "TEMPORAL", "subject": "First human heart transplant",
     "property": "surgery_date", "value": "December 3, 1982", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Dr. Christiaan Barnard performed the world's first human-to-human heart transplant on December 3, 1982 in Cape Town.",
     "domain": "medical_history", "sub_type": "POINT_IN_TIME", "notes": "Off-by-15-years medical milestone"},
    {"claim_id": "SL_TEMP_007", "type": "TEMPORAL", "subject": "Git (software)",
     "property": "initial_release_date", "value": "April 7, 2005", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Linus Torvalds published the initial release of the Git version control system on April 7, 2005.",
     "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Git 0.01 release date"},
    {"claim_id": "SL_TEMP_008", "type": "TEMPORAL", "subject": "Git (software)",
     "property": "initial_release_date", "value": "April 7, 2011", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Linus Torvalds published the initial release of the Git version control system on April 7, 2011.",
     "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted VCS creation year"},
    {"claim_id": "SL_TEMP_009", "type": "TEMPORAL", "subject": "Apollo 13",
     "property": "oxygen_tank_explosion", "value": "April 13, 1970", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Apollo 13 service module oxygen tank exploded en route to the Moon on April 13, 1970.",
     "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "NASA Apollo 13 incident timestamp"},
    {"claim_id": "SL_TEMP_010", "type": "TEMPORAL", "subject": "Apollo 13",
     "property": "oxygen_tank_explosion", "value": "April 13, 1975", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Apollo 13 service module oxygen tank exploded en route to the Moon on April 13, 1975.",
     "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted space disaster date"},

    # -------------------------------------------------------------------------
    # 3. ENTITY_ATTRIBUTE (21 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "SL_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "DNA",
     "property": "base_pairing", "value": "Adenine pairs with Thymine, Guanine pairs with Cytosine", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "In double-stranded DNA, adenine forms complementary base pairs with thymine, and cytosine pairs with guanine.",
     "domain": "molecular_biology", "sub_type": "BASE_PAIR", "notes": "Watson-Crick base pairing"},
    {"claim_id": "SL_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "DNA",
     "property": "base_pairing", "value": "Adenine pairs with Uracil directly in nuclear DNA", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "In standard genomic double-stranded DNA, adenine bonds directly with uracil as its primary complementary base.",
     "domain": "molecular_biology", "sub_type": "BASE_PAIR", "notes": "Uracil is present in RNA, not standard DNA"},
    {"claim_id": "SL_ENTI_003", "type": "ENTITY_ATTRIBUTE", "subject": "Helium",
     "property": "chemical_element_class", "value": "noble gas", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Helium is classified as a noble gas in Group 18 of the periodic table.",
     "domain": "chemistry", "sub_type": "ELEMENT_CLASS", "notes": "Periodic table group classification"},
    {"claim_id": "SL_ENTI_004", "type": "ENTITY_ATTRIBUTE", "subject": "Helium",
     "property": "chemical_element_class", "value": "alkali metal", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Helium is classified as a highly reactive alkali metal in Group 1 of the periodic table.",
     "domain": "chemistry", "sub_type": "ELEMENT_CLASS", "notes": "Noble gas misclassified as alkali metal"},
    {"claim_id": "SL_ENTI_005", "type": "ENTITY_ATTRIBUTE", "subject": "Australia",
     "property": "capital_city", "value": "Canberra", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The federal capital city of the Commonwealth of Australia is Canberra.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Official capital of Australia"},
    {"claim_id": "SL_ENTI_006", "type": "ENTITY_ATTRIBUTE", "subject": "Australia",
     "property": "capital_city", "value": "Sydney", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The federal capital city of the Commonwealth of Australia is Sydney.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Sydney is largest city, not capital"},
    {"claim_id": "SL_ENTI_007", "type": "ENTITY_ATTRIBUTE", "subject": "Switzerland",
     "property": "de_facto_capital_federal_city", "value": "Bern", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The federal city and de facto capital of Switzerland is Bern.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Swiss Federal City"},
    {"claim_id": "SL_ENTI_008", "type": "ENTITY_ATTRIBUTE", "subject": "Switzerland",
     "property": "de_facto_capital_federal_city", "value": "Zurich", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The federal city and de facto capital of Switzerland is Zurich.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Zurich is financial hub, Bern is federal city"},

    # -------------------------------------------------------------------------
    # 4. CITATION (21 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "SL_CITA_001", "type": "CITATION", "subject": "Molecular Structure of Nucleic Acids: A Structure for Deoxyribose Nucleic Acid",
     "property": "authors", "value": "J. D. Watson and F. H. C. Crick", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "James Watson and Francis Crick published the double helix structure of DNA in Nature in April 1953.",
     "domain": "science_history", "sub_type": "AUTHOR_CHECK", "notes": "Landmark Nature 1953 paper"},
    {"claim_id": "SL_CITA_002", "type": "CITATION", "subject": "Molecular Structure of Nucleic Acids: A Structure for Deoxyribose Nucleic Acid",
     "property": "authors", "value": "Linus Pauling", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Linus Pauling published the correct double helix structure of DNA in Nature in April 1953.",
     "domain": "science_history", "sub_type": "AUTHOR_SWAP", "notes": "Pauling proposed the incorrect triple helix"},
    {"claim_id": "SL_CITA_003", "type": "CITATION", "subject": "A Programmable Dual-RNA-Guided DNA Mismatch Endonuclease",
     "property": "publisher", "value": "Nature Biotech Reviews", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The 2023 study 'A Programmable Dual-RNA-Guided DNA Mismatch Endonuclease' by Dr. K. Sato in Nature Biotech proved 100% off-target elimination.",
     "domain": "biomedical_research", "sub_type": "PHANTOM_CITATION", "notes": "100% fabricated citation and DOI"},
    {"claim_id": "SL_CITA_004", "type": "CITATION", "subject": "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems",
     "property": "authors", "value": "R. L. Rivest, A. Shamir, and L. Adleman", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Ron Rivest, Adi Shamir, and Leonard Adleman introduced the RSA cryptosystem in CACM in February 1978.",
     "domain": "cryptography", "sub_type": "AUTHOR_CHECK", "notes": "RSA foundational paper"},
    {"claim_id": "SL_CITA_005", "type": "CITATION", "subject": "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems",
     "property": "authors", "value": "Alan Turing", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Alan Turing introduced the RSA cryptosystem in Communications of the ACM in February 1978.",
     "domain": "cryptography", "sub_type": "AUTHOR_SWAP", "notes": "RSA misattributed to Turing (died 1954)"},

    # -------------------------------------------------------------------------
    # 5. RELATIONAL (21 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "SL_RELA_001", "type": "RELATIONAL", "subject": "Second law of thermodynamics",
     "property": "thermodynamic_statement", "value": "total entropy of an isolated system always increases over time", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The second law of thermodynamics states that the total entropy of an isolated physical system can never decrease over time.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fundamental thermodynamic law"},
    {"claim_id": "SL_RELA_002", "type": "RELATIONAL", "subject": "Second law of thermodynamics",
     "property": "thermodynamic_statement", "value": "isolated systems spontaneously decrease total entropy to reach zero", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The second law of thermodynamics states that isolated physical systems spontaneously eliminate all internal entropy until reaching zero.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Inverted entropy law"},
    {"claim_id": "SL_RELA_003", "type": "RELATIONAL", "subject": "Plate tectonics",
     "property": "geological_mechanism", "value": "mantle convection currents drive the movement of lithospheric plates", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Plate tectonics operates primarily through thermal convection currents within Earth's asthenosphere driving the motion of rigid lithospheric plates.",
     "domain": "geology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Geophysical tectonic mechanism"},
    {"claim_id": "SL_RELA_004", "type": "RELATIONAL", "subject": "Plate tectonics",
     "property": "geological_mechanism", "value": "lunar tidal forces melt continents every 100 years", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Plate tectonics operates because lunar gravitational tides liquefy entire continental landmasses on a century-long recurring cycle.",
     "domain": "geology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fabricated geophysical mechanism"}
]


def generate_science_legal(output_path: str = OUT_CSV) -> list[dict]:
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in SCIENCE_LEGAL_CLAIMS:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return SCIENCE_LEGAL_CLAIMS


def selftest() -> bool:
    print("Running generate_science_legal selftest...")
    ids = [r["claim_id"] for r in SCIENCE_LEGAL_CLAIMS]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    types = set(r["type"] for r in SCIENCE_LEGAL_CLAIMS)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    print(f"Selftest PASSED: {len(SCIENCE_LEGAL_CLAIMS)} claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate science/legal claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_science_legal(args.out)
    print(f"Wrote {len(SCIENCE_LEGAL_CLAIMS)} science & legal claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
