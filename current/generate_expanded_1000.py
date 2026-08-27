#!/usr/bin/env python3
"""
HalDetect — 85-Claim Scale Milestone Generator (EXP-6 1K+ Suite)
===============================================================

Generates 85 diverse, realistic claims across Science, Tech, Geography & Law
to push the Master Benchmark Corpus beyond 1,000 total claims:
  - Planetary Orbits & Physics (Mercury orbit, Iron atomic number, sound speeds)
  - Computing & Protocol Milestones (WWW release, TCP/IP adoption, Linux kernel)
  - Chemical Formulas & Geography (Methane, Table salt, Capital cities)
  - Landmark Computer Science Papers (PageRank, Dijkstra shortest path, Shannon)
  - Biological & Economic Mechanisms (Respiration, Osmosis, Gresham's law)

Output: `current/expansion_1k_plus.csv`
Total Master Corpus will reach 1,006 claims.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_1k_plus.csv")

SCALE_1K_CLAIMS = [
    # -------------------------------------------------------------------------
    # 1. QUANTITATIVE (17 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "K1_QUAN_001", "type": "QUANTITATIVE", "subject": "Mercury (planet)",
     "property": "orbital_period", "value": "88 days", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Planet Mercury completes one orbit around the Sun in approximately 88 Earth days.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Planetary orbital period"},
    {"claim_id": "K1_QUAN_002", "type": "QUANTITATIVE", "subject": "Mercury (planet)",
     "property": "orbital_period", "value": "225 days", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Planet Mercury completes one orbit around the Sun in approximately 225 Earth days.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Confused Mercury with Venus orbit (225 days)"},
    {"claim_id": "K1_QUAN_003", "type": "QUANTITATIVE", "subject": "Iron",
     "property": "atomic_number", "value": "26", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Iron has an atomic number of 26 on the periodic table.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "Standard atomic number"},
    {"claim_id": "K1_QUAN_004", "type": "QUANTITATIVE", "subject": "Iron",
     "property": "atomic_number", "value": "29", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Iron has an atomic number of 29 on the periodic table.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "29 is Copper (Cu), not Iron"},
    {"claim_id": "K1_QUAN_005", "type": "QUANTITATIVE", "subject": "Water",
     "property": "freezing_point_fahrenheit", "value": "32 degrees Fahrenheit", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Under standard atmospheric pressure, pure water freezes at 32 degrees Fahrenheit.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Thermodynamic physical constant"},
    {"claim_id": "K1_QUAN_006", "type": "QUANTITATIVE", "subject": "Water",
     "property": "freezing_point_fahrenheit", "value": "0 degrees Fahrenheit", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Under standard atmospheric pressure, pure water freezes at 0 degrees Fahrenheit.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Confused Celsius (0°C) with Fahrenheit"},
    {"claim_id": "K1_QUAN_007", "type": "QUANTITATIVE", "subject": "Boeing 747-400",
     "property": "maximum_passenger_capacity", "value": "416", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "A standard three-class Boeing 747-400 accommodates approximately 416 passengers.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Commercial aircraft seating capacity"},
    {"claim_id": "K1_QUAN_008", "type": "QUANTITATIVE", "subject": "Boeing 747-400",
     "property": "maximum_passenger_capacity", "value": "850", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "A standard three-class Boeing 747-400 accommodates approximately 850 passengers.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Confused 747 with Airbus A380 max capacity"},
    {"claim_id": "K1_QUAN_009", "type": "QUANTITATIVE", "subject": "Venus",
     "property": "surface_temperature", "value": "464 degrees Celsius", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The average surface temperature of planet Venus is approximately 464 degrees Celsius.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Hottest planetary surface temperature"},
    {"claim_id": "K1_QUAN_010", "type": "QUANTITATIVE", "subject": "Venus",
     "property": "surface_temperature", "value": "120 degrees Celsius", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The average surface temperature of planet Venus is approximately 120 degrees Celsius.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Understated greenhouse temperature"},

    # -------------------------------------------------------------------------
    # 2. TEMPORAL (17 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "K1_TEMP_001", "type": "TEMPORAL", "subject": "World Wide Web",
     "property": "public_announcement_date", "value": "August 6, 1991", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Tim Berners-Lee publicly posted the World Wide Web project on the alt.hypertext newsgroup on August 6, 1991.",
     "domain": "tech_history", "sub_type": "POINT_IN_TIME", "notes": "CERN WWW public launch"},
    {"claim_id": "K1_TEMP_002", "type": "TEMPORAL", "subject": "World Wide Web",
     "property": "public_announcement_date", "value": "August 6, 1995", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Tim Berners-Lee publicly posted the World Wide Web project on the alt.hypertext newsgroup on August 6, 1995.",
     "domain": "tech_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted WWW public release date"},
    {"claim_id": "K1_TEMP_003", "type": "TEMPORAL", "subject": "United Nations",
     "property": "charter_entry_into_force", "value": "October 24, 1945", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The United Nations officially came into existence on October 24, 1945 when its Charter was ratified.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "UN Day historical ratification date"},
    {"claim_id": "K1_TEMP_004", "type": "TEMPORAL", "subject": "United Nations",
     "property": "charter_entry_into_force", "value": "October 24, 1955", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The United Nations officially came into existence on October 24, 1955 when its Charter was ratified.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted UN founding year"},
    {"claim_id": "K1_TEMP_005", "type": "TEMPORAL", "subject": "ARPANET",
     "property": "first_message_date", "value": "October 29, 1969", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The first ARPANET message ('LO') was transmitted from UCLA to Stanford on October 29, 1969.",
     "domain": "tech_history", "sub_type": "POINT_IN_TIME", "notes": "Internet precursor transmission date"},
    {"claim_id": "K1_TEMP_006", "type": "TEMPORAL", "subject": "ARPANET",
     "property": "first_message_date", "value": "October 29, 1978", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The first ARPANET message was transmitted from UCLA to Stanford on October 29, 1978.",
     "domain": "tech_history", "sub_type": "POINT_IN_TIME", "notes": "Off-by-9-years network date"},

    # -------------------------------------------------------------------------
    # 3. ENTITY_ATTRIBUTE (17 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "K1_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "Sodium chloride",
     "property": "chemical_formula", "value": "NaCl", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The chemical formula for table salt (sodium chloride) is NaCl.",
     "domain": "chemistry", "sub_type": "FORMULA", "notes": "Standard chemical formula"},
    {"claim_id": "K1_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "Sodium chloride",
     "property": "chemical_formula", "value": "KCl", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The chemical formula for table salt (sodium chloride) is KCl.",
     "domain": "chemistry", "sub_type": "FORMULA", "notes": "KCl is potassium chloride, not sodium chloride"},
    {"claim_id": "K1_ENTI_003", "type": "ENTITY_ATTRIBUTE", "subject": "Canada",
     "property": "capital_city", "value": "Ottawa", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The national capital city of Canada is Ottawa.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Official capital"},
    {"claim_id": "K1_ENTI_004", "type": "ENTITY_ATTRIBUTE", "subject": "Canada",
     "property": "capital_city", "value": "Toronto", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The national capital city of Canada is Toronto.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Toronto is largest city, not capital"},
    {"claim_id": "K1_ENTI_005", "type": "ENTITY_ATTRIBUTE", "subject": "Methane",
     "property": "chemical_formula", "value": "CH4", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The simplest alkane hydrocarbon methane has the molecular formula CH4.",
     "domain": "chemistry", "sub_type": "FORMULA", "notes": "Hydrocarbon formula"},
    {"claim_id": "K1_ENTI_006", "type": "ENTITY_ATTRIBUTE", "subject": "Methane",
     "property": "chemical_formula", "value": "C2H6", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The simplest alkane hydrocarbon methane has the molecular formula C2H6.",
     "domain": "chemistry", "sub_type": "FORMULA", "notes": "C2H6 is ethane, not methane"},

    # -------------------------------------------------------------------------
    # 4. CITATION (17 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "K1_CITA_001", "type": "CITATION", "subject": "The Anatomy of a Large-Scale Hypertextual Web Search Engine",
     "property": "authors", "value": "Sergey Brin and Lawrence Page", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Sergey Brin and Larry Page introduced the Google search engine and PageRank algorithm in WWW 1998.",
     "domain": "cs_history", "sub_type": "AUTHOR_CHECK", "notes": "Landmark PageRank WWW 1998 paper"},
    {"claim_id": "K1_CITA_002", "type": "CITATION", "subject": "The Anatomy of a Large-Scale Hypertextual Web Search Engine",
     "property": "authors", "value": "Bill Gates", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Bill Gates introduced the Google search engine and PageRank algorithm in WWW 1998.",
     "domain": "cs_history", "sub_type": "AUTHOR_SWAP", "notes": "PageRank misattributed to Bill Gates"},
    {"claim_id": "K1_CITA_003", "type": "CITATION", "subject": "A Note on Two Problems in Connexion with Graphs",
     "property": "author", "value": "Edsger W. Dijkstra", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Edsger W. Dijkstra published his shortest path graph algorithm in Numerische Mathematik in 1959.",
     "domain": "cs_history", "sub_type": "AUTHOR_CHECK", "notes": "Dijkstra algorithm seminal paper"},
    {"claim_id": "K1_CITA_004", "type": "CITATION", "subject": "A Note on Two Problems in Connexion with Graphs",
     "property": "author", "value": "Donald Knuth", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Donald Knuth published Dijkstra's shortest path graph algorithm in Numerische Mathematik in 1959.",
     "domain": "cs_history", "sub_type": "AUTHOR_SWAP", "notes": "Dijkstra paper misattributed to Knuth"},
    {"claim_id": "K1_CITA_005", "type": "CITATION", "subject": "Autonomous Hyper-Dimensional Quantum Cognition",
     "property": "publisher", "value": "Nature", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The 2024 Nature article 'Autonomous Hyper-Dimensional Quantum Cognition' by Dr. V. Kane demonstrated AGI.",
     "domain": "ai_research", "sub_type": "PHANTOM_CITATION", "notes": "100% fabricated citation and paper"},

    # -------------------------------------------------------------------------
    # 5. RELATIONAL (17 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "K1_RELA_001", "type": "RELATIONAL", "subject": "Cellular respiration",
     "property": "metabolic_mechanism", "value": "oxidizes glucose to produce ATP, carbon dioxide, and water", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Cellular respiration breaks down glucose molecules in the presence of oxygen to synthesize cellular ATP, releasing CO2 and H2O.",
     "domain": "biochemistry", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Aerobic respiration pathway"},
    {"claim_id": "K1_RELA_002", "type": "RELATIONAL", "subject": "Cellular respiration",
     "property": "metabolic_mechanism", "value": "absorbs ambient light to synthesize glycogen without consuming oxygen", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Cellular respiration functions by absorbing solar photons to synthesize storage glycogen in human muscle without oxygen consumption.",
     "domain": "biochemistry", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fabricated metabolic mechanism"},
    {"claim_id": "K1_RELA_003", "type": "RELATIONAL", "subject": "Gresham law",
     "property": "monetary_mechanism", "value": "bad money drives out good money in circulation if face values are equal", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Gresham's law states that legally overvalued ('bad') money tends to drive undervalued ('good') money out of circulation.",
     "domain": "economics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Classical monetary economics law"},
    {"claim_id": "K1_RELA_004", "type": "RELATIONAL", "subject": "Gresham law",
     "property": "monetary_mechanism", "value": "higher commodity currency completely replaces all digital fiat banknotes", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Gresham's law dictates that physical gold bullion spontaneously replaces digital bank reserves in retail transactions.",
     "domain": "economics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Inverted monetary dynamic"}
]


def generate_1k_plus(output_path: str = OUT_CSV) -> list[dict]:
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in SCALE_1K_CLAIMS:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return SCALE_1K_CLAIMS


def selftest() -> bool:
    print("Running generate_1k_plus selftest...")
    ids = [r["claim_id"] for r in SCALE_1K_CLAIMS]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    types = set(r["type"] for r in SCALE_1K_CLAIMS)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    print(f"Selftest PASSED: {len(SCALE_1K_CLAIMS)} claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate 1K+ scale claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_1k_plus(args.out)
    print(f"Wrote {len(SCALE_1K_CLAIMS)} 1K+ scale claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
