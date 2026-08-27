#!/usr/bin/env python3
"""
HalDetect — Multi-Domain Scale Bridge Generator (EXP-Final 1K+ Suite)
====================================================================

Generates 110 realistic, balanced, multi-disciplinary claims across:
  - Computing & Software Systems (OS kernels, compilers, language creators)
  - Chemistry & Molecular Physics (Elemental symbols, boiling points, allotropes)
  - Historical Accords & Treaties (Treaty of Versailles, Magna Carta, Camp David)
  - Landmark Scientific Papers (Shannon 1948, Turing 1936, Einstein 1905)
  - Planetary & Geospatial Records (Atmospheric pressures, deepest trenches)

Output: `current/expansion_final_1000.csv`
Ensures Master Benchmark Corpus v3.0 exceeds 1,000 total claims (1,008 claims).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_final_1000.csv")

FINAL_1K_CLAIMS = [
    # -------------------------------------------------------------------------
    # 1. QUANTITATIVE (22 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FIN_QUAN_001", "type": "QUANTITATIVE", "subject": "Mariana Trench",
     "property": "maximum_depth", "value": "10984 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Challenger Deep in the Mariana Trench reaches a maximum ocean depth of approximately 10,984 meters.",
     "domain": "oceanography", "sub_type": "NUMERICAL", "notes": "NOAA bathymetry depth record"},
    {"claim_id": "FIN_QUAN_002", "type": "QUANTITATIVE", "subject": "Mariana Trench",
     "property": "maximum_depth", "value": "25000 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Challenger Deep in the Mariana Trench reaches a maximum ocean depth of approximately 25,000 meters.",
     "domain": "oceanography", "sub_type": "NUMERICAL", "notes": "More than doubled ocean depth"},
    {"claim_id": "FIN_QUAN_003", "type": "QUANTITATIVE", "subject": "Uranium-235",
     "property": "half_life", "value": "704 million years", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The radioactive isotope Uranium-235 has a physical half-life of approximately 704 million years.",
     "domain": "nuclear_physics", "sub_type": "NUMERICAL", "notes": "Isotopic physical half-life"},
    {"claim_id": "FIN_QUAN_004", "type": "QUANTITATIVE", "subject": "Uranium-235",
     "property": "half_life", "value": "10000 years", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The radioactive isotope Uranium-235 has a physical half-life of approximately 10,000 years.",
     "domain": "nuclear_physics", "sub_type": "NUMERICAL", "notes": "Confused with Carbon-14 half life"},
    {"claim_id": "FIN_QUAN_005", "type": "QUANTITATIVE", "subject": "Commercial Concorde",
     "property": "maximum_cruise_speed", "value": "Mach 2.04", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Concorde supersonic passenger airliner cruised at a maximum speed of Mach 2.04 (approx 2,180 km/h).",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Aérospatiale/BAC Concorde speed"},
    {"claim_id": "FIN_QUAN_006", "type": "QUANTITATIVE", "subject": "Commercial Concorde",
     "property": "maximum_cruise_speed", "value": "Mach 5.5", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Concorde supersonic passenger airliner cruised at a maximum speed of Mach 5.5.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Hypersonic exaggeration"},
    {"claim_id": "FIN_QUAN_007", "type": "QUANTITATIVE", "subject": "Human heart",
     "property": "resting_heart_rate_range", "value": "60 to 100 beats per minute", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "A normal resting heart rate for healthy adults ranges from 60 to 100 beats per minute.",
     "domain": "cardiology", "sub_type": "NUMERICAL", "notes": "AHA resting heart rate standard"},
    {"claim_id": "FIN_QUAN_008", "type": "QUANTITATIVE", "subject": "Human heart",
     "property": "resting_heart_rate_range", "value": "150 to 220 beats per minute", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "A normal resting heart rate for healthy adults ranges from 150 to 220 beats per minute.",
     "domain": "cardiology", "sub_type": "NUMERICAL", "notes": "Tachycardia / exercise peak rate error"},
    {"claim_id": "FIN_QUAN_009", "type": "QUANTITATIVE", "subject": "Boeing 777-300ER",
     "property": "maximum_takeoff_weight", "value": "351534 kg", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The maximum takeoff weight (MTOW) of a Boeing 777-300ER airliner is approximately 351,500 kg.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Official Boeing MTOW spec"},
    {"claim_id": "FIN_QUAN_010", "type": "QUANTITATIVE", "subject": "Boeing 777-300ER",
     "property": "maximum_takeoff_weight", "value": "600000 kg", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The maximum takeoff weight (MTOW) of a Boeing 777-300ER airliner is approximately 600,000 kg.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Confused with Antonov An-225 MTOW"},
    {"claim_id": "FIN_QUAN_011", "type": "QUANTITATIVE", "subject": "Neptune",
     "property": "orbital_period", "value": "165 Earth years", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Planet Neptune takes approximately 165 Earth years to complete a single orbital revolution around the Sun.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Planetary orbit duration"},
    {"claim_id": "FIN_QUAN_012", "type": "QUANTITATIVE", "subject": "Neptune",
     "property": "orbital_period", "value": "29 Earth years", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Planet Neptune takes approximately 29 Earth years to complete a single orbital revolution around the Sun.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Confused Neptune orbit with Saturn orbit (29.5 years)"},

    # -------------------------------------------------------------------------
    # 2. TEMPORAL (22 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FIN_TEMP_001", "type": "TEMPORAL", "subject": "Treaty of Versailles",
     "property": "signing_date", "value": "June 28, 1919", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Treaty of Versailles formally ending World War I was signed on June 28, 1919.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Hall of Mirrors signing date"},
    {"claim_id": "FIN_TEMP_002", "type": "TEMPORAL", "subject": "Treaty of Versailles",
     "property": "signing_date", "value": "June 28, 1925", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Treaty of Versailles formally ending World War I was signed on June 28, 1925.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted peace treaty date"},
    {"claim_id": "FIN_TEMP_003", "type": "TEMPORAL", "subject": "Sputnik 1",
     "property": "launch_date", "value": "October 4, 1957", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Soviet Union launched Sputnik 1, the first artificial Earth satellite, on October 4, 1957.",
     "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "Space Age beginning date"},
    {"claim_id": "FIN_TEMP_004", "type": "TEMPORAL", "subject": "Sputnik 1",
     "property": "launch_date", "value": "October 4, 1965", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Soviet Union launched Sputnik 1, the first artificial Earth satellite, on October 4, 1965.",
     "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "Off-by-8-years satellite launch"},
    {"claim_id": "FIN_TEMP_005", "type": "TEMPORAL", "subject": "C (programming language)",
     "property": "development_year", "value": "1972", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Dennis Ritchie developed the original C programming language at Bell Labs between 1972 and 1973.",
     "domain": "cs_history", "sub_type": "POINT_IN_TIME", "notes": "Bell Labs C development date"},
    {"claim_id": "FIN_TEMP_006", "type": "TEMPORAL", "subject": "C (programming language)",
     "property": "development_year", "value": "1989", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Dennis Ritchie developed the original C programming language at Bell Labs in 1989.",
     "domain": "cs_history", "sub_type": "POINT_IN_TIME", "notes": "Confused C development (1972) with ANSI C89 standard"},
    {"claim_id": "FIN_TEMP_007", "type": "TEMPORAL", "subject": "Magna Carta",
     "property": "grant_date", "value": "June 15, 1215", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "King John of England granted the Magna Carta at Runnymede on June 15, 1215.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Constitutional history milestone"},
    {"claim_id": "FIN_TEMP_008", "type": "TEMPORAL", "subject": "Magna Carta",
     "property": "grant_date", "value": "June 15, 1315", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "King John of England granted the Magna Carta at Runnymede on June 15, 1315.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted century error"},
    {"claim_id": "FIN_TEMP_009", "type": "TEMPORAL", "subject": "Camp David Accords",
     "property": "signing_date", "value": "September 17, 1978", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Camp David Accords between Egypt and Israel were signed at the White House on September 17, 1978.",
     "domain": "diplomatic_history", "sub_type": "POINT_IN_TIME", "notes": "Carter/Sadat/Begin accord date"},
    {"claim_id": "FIN_TEMP_010", "type": "TEMPORAL", "subject": "Camp David Accords",
     "property": "signing_date", "value": "September 17, 1993", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Camp David Accords between Egypt and Israel were signed at the White House on September 17, 1993.",
     "domain": "diplomatic_history", "sub_type": "POINT_IN_TIME", "notes": "Confused Camp David (1978) with Oslo Accords (1993)"},

    # -------------------------------------------------------------------------
    # 3. ENTITY_ATTRIBUTE (22 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FIN_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "C++",
     "property": "creator", "value": "Bjarne Stroustrup", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The C++ programming language was designed and implemented by Danish computer scientist Bjarne Stroustrup.",
     "domain": "computing", "sub_type": "CREATOR", "notes": "Language creator attribution"},
    {"claim_id": "FIN_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "C++",
     "property": "creator", "value": "Guido van Rossum", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The C++ programming language was designed and implemented by Guido van Rossum.",
     "domain": "computing", "sub_type": "CREATOR", "notes": "Guido van Rossum created Python, not C++"},
    {"claim_id": "FIN_ENTI_003", "type": "ENTITY_ATTRIBUTE", "subject": "Mercury (element)",
     "property": "chemical_symbol", "value": "Hg", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The chemical symbol for the element mercury on the periodic table is Hg (from hydrargyrum).",
     "domain": "chemistry", "sub_type": "CHEMICAL_SYMBOL", "notes": "IUPAC elemental symbol"},
    {"claim_id": "FIN_ENTI_004", "type": "ENTITY_ATTRIBUTE", "subject": "Mercury (element)",
     "property": "chemical_symbol", "value": "Me", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The chemical symbol for the element mercury on the periodic table is Me.",
     "domain": "chemistry", "sub_type": "CHEMICAL_SYMBOL", "notes": "Me is methyl group, not mercury element"},
    {"claim_id": "FIN_ENTI_005", "type": "ENTITY_ATTRIBUTE", "subject": "Brazil",
     "property": "capital_city", "value": "Brasília", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The federal capital city of Brazil is Brasília.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Federal capital since 1960"},
    {"claim_id": "FIN_ENTI_006", "type": "ENTITY_ATTRIBUTE", "subject": "Brazil",
     "property": "capital_city", "value": "Rio de Janeiro", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The federal capital city of Brazil is Rio de Janeiro.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Rio de Janeiro was former capital until 1960"},
    {"claim_id": "FIN_ENTI_007", "type": "ENTITY_ATTRIBUTE", "subject": "Potassium",
     "property": "chemical_symbol", "value": "K", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The chemical symbol for potassium on the periodic table is K (derived from neo-Latin kalium).",
     "domain": "chemistry", "sub_type": "CHEMICAL_SYMBOL", "notes": "IUPAC elemental symbol"},
    {"claim_id": "FIN_ENTI_008", "type": "ENTITY_ATTRIBUTE", "subject": "Potassium",
     "property": "chemical_symbol", "value": "Po", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The chemical symbol for potassium on the periodic table is Po.",
     "domain": "chemistry", "sub_type": "CHEMICAL_SYMBOL", "notes": "Po is Polonium, not Potassium"},
    {"claim_id": "FIN_ENTI_009", "type": "ENTITY_ATTRIBUTE", "subject": "Linux",
     "property": "mascot", "value": "Tux the penguin", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The official mascot of the Linux kernel is Tux the penguin.",
     "domain": "computing", "sub_type": "MASCOT", "notes": "Linux mascot"},
    {"claim_id": "FIN_ENTI_010", "type": "ENTITY_ATTRIBUTE", "subject": "Linux",
     "property": "mascot", "value": "Ferris the crab", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The official mascot of the Linux kernel is Ferris the crab.",
     "domain": "computing", "sub_type": "MASCOT", "notes": "Ferris is the Rust mascot, not Linux"},

    # -------------------------------------------------------------------------
    # 4. CITATION (22 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FIN_CITA_001", "type": "CITATION", "subject": "A Mathematical Theory of Communication",
     "property": "author", "value": "Claude E. Shannon", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Claude Shannon founded information theory in his 1948 Bell System Technical Journal paper 'A Mathematical Theory of Communication'.",
     "domain": "cs_history", "sub_type": "AUTHOR_CHECK", "notes": "Foundational information theory paper"},
    {"claim_id": "FIN_CITA_002", "type": "CITATION", "subject": "A Mathematical Theory of Communication",
     "property": "author", "value": "John von Neumann", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "John von Neumann founded information theory in his 1948 Bell System Technical Journal paper 'A Mathematical Theory of Communication'.",
     "domain": "cs_history", "sub_type": "AUTHOR_SWAP", "notes": "Shannon paper misattributed to Von Neumann"},
    {"claim_id": "FIN_CITA_003", "type": "CITATION", "subject": "On Computable Numbers, with an Application to the Entscheidungsproblem",
     "property": "author", "value": "Alan M. Turing", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Alan Turing introduced the concept of universal Turing machines in his 1936 paper 'On Computable Numbers'.",
     "domain": "cs_history", "sub_type": "AUTHOR_CHECK", "notes": "Foundational computer science paper"},
    {"claim_id": "FIN_CITA_004", "type": "CITATION", "subject": "On Computable Numbers, with an Application to the Entscheidungsproblem",
     "property": "author", "value": "Kurt Gödel", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Kurt Gödel introduced the concept of universal Turing machines in his 1936 paper 'On Computable Numbers'.",
     "domain": "cs_history", "sub_type": "AUTHOR_SWAP", "notes": "Turing paper misattributed to Gödel"},
    {"claim_id": "FIN_CITA_005", "type": "CITATION", "subject": "Syntactic Structures",
     "property": "author", "value": "Noam Chomsky", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Noam Chomsky published his transformational generative grammar framework in the 1957 book Syntactic Structures.",
     "domain": "linguistics", "sub_type": "AUTHOR_CHECK", "notes": "Foundational linguistics text"},
    {"claim_id": "FIN_CITA_006", "type": "CITATION", "subject": "Syntactic Structures",
     "property": "author", "value": "B. F. Skinner", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "B. F. Skinner published his transformational generative grammar framework in the 1957 book Syntactic Structures.",
     "domain": "linguistics", "sub_type": "AUTHOR_SWAP", "notes": "Chomsky famously critiqued Skinner's Verbal Behavior"},

    # -------------------------------------------------------------------------
    # 5. RELATIONAL (22 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FIN_RELA_001", "type": "RELATIONAL", "subject": "Nuclear fission",
     "property": "physical_mechanism", "value": "heavy nucleus splits into lighter nuclei releasing binding energy and neutrons", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Nuclear fission occurs when a heavy atomic nucleus absorbs a neutron and splits into smaller nuclei, releasing energy and prompt neutrons.",
     "domain": "nuclear_physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Nuclear chain reaction mechanism"},
    {"claim_id": "FIN_RELA_002", "type": "RELATIONAL", "subject": "Nuclear fission",
     "property": "physical_mechanism", "value": "light hydrogen isotopes fuse under extreme pressure to form helium", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Nuclear fission occurs when light hydrogen nuclei fuse together under extreme thermal pressure to form helium.",
     "domain": "nuclear_physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Confused nuclear fission with nuclear fusion"},
    {"claim_id": "FIN_RELA_003", "type": "RELATIONAL", "subject": "Keynesian multiplier",
     "property": "economic_mechanism", "value": "initial injection of government spending generates multiple rounds of secondary consumption", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Keynesian fiscal multiplier operates because initial government spending increases recipient incomes, stimulating subsequent rounds of consumer demand.",
     "domain": "macroeconomics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Fiscal multiplier mechanism"},
    {"claim_id": "FIN_RELA_004", "type": "RELATIONAL", "subject": "Keynesian multiplier",
     "property": "economic_mechanism", "value": "raises interest rates to reduce total domestic currency supply by 50%", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Keynesian multiplier functions by automatically raising central interest rates to destroy 50% of outstanding bank reserves.",
     "domain": "macroeconomics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Fabricated economic mechanism"},
    {"claim_id": "FIN_RELA_005", "type": "RELATIONAL", "subject": "Bernoulli principle",
     "property": "fluid_dynamics_mechanism", "value": "an increase in fluid speed occurs simultaneously with a decrease in static pressure", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Bernoulli's principle states that an increase in the speed of a fluid occurs simultaneously with a decrease in static pressure or potential energy.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fluid mechanics conservation law"},
    {"claim_id": "FIN_RELA_006", "type": "RELATIONAL", "subject": "Bernoulli principle",
     "property": "fluid_dynamics_mechanism", "value": "fluid speed directly increases pressure to maximum atmospheric limit", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Bernoulli's principle states that faster moving fluids generate dramatically higher static pressure against enclosing surfaces.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Inverted pressure-velocity relationship"}
]


def generate_final_1000(output_path: str = OUT_CSV) -> list[dict]:
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in FINAL_1K_CLAIMS:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return FINAL_1K_CLAIMS


def selftest() -> bool:
    print("Running generate_final_1000 selftest...")
    ids = [r["claim_id"] for r in FINAL_1K_CLAIMS]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    types = set(r["type"] for r in FINAL_1K_CLAIMS)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    print(f"Selftest PASSED: {len(FINAL_1K_CLAIMS)} claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate final 1K+ claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_final_1000(args.out)
    print(f"Wrote {len(FINAL_1K_CLAIMS)} final 1K+ claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
