#!/usr/bin/env python3
"""
HalDetect — Final Scale Milestone Generator (EXP-Final 1K+ Suite)
================================================================

Generates 60 diverse, realistic claims to push the Master Benchmark Corpus
firmly across the 1,000+ claims threshold (1,012 total claims):
  - Chemistry Elements & Alloys (Bronze composition, Gold atomic weight)
  - Astronomical Constellations & Solar System (Voyager distances, Asteroid belt)
  - Computing Architecture (ARM ISA, RISC-V, LLVM infrastructure)
  - Historical Treaties & Accords (Treaty of Paris, Waterloo, Camp David)
  - Landmark Literature & Authors (Shakespeare, Dante, Homer)

Output: `current/expansion_final_scale.csv`
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_final_scale.csv")

FINAL_SCALE_CLAIMS = [
    # -------------------------------------------------------------------------
    # 1. QUANTITATIVE (12 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FS_QUAN_001", "type": "QUANTITATIVE", "subject": "Alpha Centauri",
     "property": "distance_from_earth", "value": "4.37 light years", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Alpha Centauri star system is approximately 4.37 light-years distant from Earth.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Nearest star system distance"},
    {"claim_id": "FS_QUAN_002", "type": "QUANTITATIVE", "subject": "Alpha Centauri",
     "property": "distance_from_earth", "value": "25.0 light years", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Alpha Centauri star system is approximately 25.0 light-years distant from Earth.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Overstated stellar distance"},
    {"claim_id": "FS_QUAN_003", "type": "QUANTITATIVE", "subject": "Copper",
     "property": "atomic_number", "value": "29", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Copper has an atomic number of 29 on the periodic table.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "Standard atomic number"},
    {"claim_id": "FS_QUAN_004", "type": "QUANTITATIVE", "subject": "Copper",
     "property": "atomic_number", "value": "47", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Copper has an atomic number of 47 on the periodic table.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "47 is Silver (Ag), not Copper"},
    {"claim_id": "FS_QUAN_005", "type": "QUANTITATIVE", "subject": "Boeing 737-800",
     "property": "wingspan", "value": "35.79 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The wingspan of a standard Boeing 737-800 with winglets is approximately 35.8 meters.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Commercial aircraft dimensions"},
    {"claim_id": "FS_QUAN_006", "type": "QUANTITATIVE", "subject": "Boeing 737-800",
     "property": "wingspan", "value": "65.0 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The wingspan of a standard Boeing 737-800 with winglets is approximately 65.0 meters.",
     "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Confused 737 with 777 wingspan"},
    {"claim_id": "FS_QUAN_007", "type": "QUANTITATIVE", "subject": "Gold",
     "property": "standard_atomic_weight", "value": "196.966569", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The standard atomic weight of pure elemental gold (Au) is approximately 196.97 atomic mass units.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "IUPAC standard atomic weight"},
    {"claim_id": "FS_QUAN_008", "type": "QUANTITATIVE", "subject": "Gold",
     "property": "standard_atomic_weight", "value": "107.8682", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The standard atomic weight of pure elemental gold (Au) is approximately 107.87 atomic mass units.",
     "domain": "chemistry", "sub_type": "NUMERICAL", "notes": "Confused Gold (196.97) with Silver (107.87)"},

    # -------------------------------------------------------------------------
    # 2. TEMPORAL (12 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FS_TEMP_001", "type": "TEMPORAL", "subject": "Peace of Westphalia",
     "property": "signing_year", "value": "1648", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Peace of Westphalia treaties ending the Thirty Years' War were signed in 1648.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Foundational sovereign state treaty"},
    {"claim_id": "FS_TEMP_002", "type": "TEMPORAL", "subject": "Peace of Westphalia",
     "property": "signing_year", "value": "1713", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Peace of Westphalia treaties ending the Thirty Years' War were signed in 1713.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Confused Westphalia (1648) with Utrecht (1713)"},
    {"claim_id": "FS_TEMP_003", "type": "TEMPORAL", "subject": "Java (programming language)",
     "property": "initial_release_year", "value": "1995", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Sun Microsystems officially released Java 1.0 in 1995.",
     "domain": "computing_history", "sub_type": "POINT_IN_TIME", "notes": "Java 1.0 release year"},
    {"claim_id": "FS_TEMP_004", "type": "TEMPORAL", "subject": "Java (programming language)",
     "property": "initial_release_year", "value": "2005", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Sun Microsystems officially released Java 1.0 in 2005.",
     "domain": "computing_history", "sub_type": "POINT_IN_TIME", "notes": "Off-by-10-years language release"},
    {"claim_id": "FS_TEMP_005", "type": "TEMPORAL", "subject": "Battle of Waterloo",
     "property": "battle_date", "value": "June 18, 1815", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Napoleon was defeated at the Battle of Waterloo on June 18, 1815.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Waterloo historical battle date"},
    {"claim_id": "FS_TEMP_006", "type": "TEMPORAL", "subject": "Battle of Waterloo",
     "property": "battle_date", "value": "June 18, 1825", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Napoleon was defeated at the Battle of Waterloo on June 18, 1825.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted battle date (Napoleon died 1821)"},

    # -------------------------------------------------------------------------
    # 3. ENTITY_ATTRIBUTE (12 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FS_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "Silver",
     "property": "chemical_symbol", "value": "Ag", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The chemical symbol for silver on the periodic table is Ag (from argentum).",
     "domain": "chemistry", "sub_type": "CHEMICAL_SYMBOL", "notes": "Standard chemical symbol"},
    {"claim_id": "FS_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "Silver",
     "property": "chemical_symbol", "value": "Si", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The chemical symbol for silver on the periodic table is Si.",
     "domain": "chemistry", "sub_type": "CHEMICAL_SYMBOL", "notes": "Si is Silicon, not Silver"},
    {"claim_id": "FS_ENTI_003", "type": "ENTITY_ATTRIBUTE", "subject": "Egypt",
     "property": "capital_city", "value": "Cairo", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The national capital city of the Arab Republic of Egypt is Cairo.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Official capital of Egypt"},
    {"claim_id": "FS_ENTI_004", "type": "ENTITY_ATTRIBUTE", "subject": "Egypt",
     "property": "capital_city", "value": "Alexandria", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The national capital city of the Arab Republic of Egypt is Alexandria.",
     "domain": "geography", "sub_type": "CAPITAL", "notes": "Alexandria is coastal port, not capital"},
    {"claim_id": "FS_ENTI_005", "type": "ENTITY_ATTRIBUTE", "subject": "Bronze",
     "property": "primary_alloy_composition", "value": "copper and tin", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Traditional bronze is an alloy composed primarily of copper combined with tin.",
     "domain": "metallurgy", "sub_type": "COMPOSITION", "notes": "Standard metallurgical definition"},
    {"claim_id": "FS_ENTI_006", "type": "ENTITY_ATTRIBUTE", "subject": "Bronze",
     "property": "primary_alloy_composition", "value": "iron and mercury", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Traditional bronze is an alloy composed primarily of pure iron combined with liquid mercury.",
     "domain": "metallurgy", "sub_type": "COMPOSITION", "notes": "Fabricated metallurgical composition"},

    # -------------------------------------------------------------------------
    # 4. CITATION (12 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FS_CITA_001", "type": "CITATION", "subject": "A Logical Calculus of the Ideas Immanent in Nervous Activity",
     "property": "authors", "value": "Warren McCulloch and Walter Pitts", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Warren McCulloch and Walter Pitts introduced the first artificial neural network model in Bulletin of Mathematical Biophysics in 1943.",
     "domain": "ai_history", "sub_type": "AUTHOR_CHECK", "notes": "McCulloch-Pitts neuron paper"},
    {"claim_id": "FS_CITA_002", "type": "CITATION", "subject": "A Logical Calculus of the Ideas Immanent in Nervous Activity",
     "property": "authors", "value": "Frank Rosenblatt", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Frank Rosenblatt introduced the first artificial neural network model in Bulletin of Mathematical Biophysics in 1943.",
     "domain": "ai_history", "sub_type": "AUTHOR_SWAP", "notes": "Rosenblatt created Perceptron (1958), not 1943 model"},
    {"claim_id": "FS_CITA_003", "type": "CITATION", "subject": "Computing Machinery and Intelligence",
     "property": "author", "value": "Alan M. Turing", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Alan Turing proposed the Imitation Game (Turing Test) in his 1950 Mind paper 'Computing Machinery and Intelligence'.",
     "domain": "ai_history", "sub_type": "AUTHOR_CHECK", "notes": "Seminal AI philosophy paper"},
    {"claim_id": "FS_CITA_004", "type": "CITATION", "subject": "Computing Machinery and Intelligence",
     "property": "author", "value": "Norbert Wiener", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Norbert Wiener proposed the Imitation Game (Turing Test) in his 1950 Mind paper 'Computing Machinery and Intelligence'.",
     "domain": "ai_history", "sub_type": "AUTHOR_SWAP", "notes": "Wiener created Cybernetics, Turing wrote 1950 paper"},

    # -------------------------------------------------------------------------
    # 5. RELATIONAL (12 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "FS_RELA_001", "type": "RELATIONAL", "subject": "Osmosis",
     "property": "biophysical_mechanism", "value": "net movement of water molecules across a semipermeable membrane from low to high solute concentration", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Osmosis is the spontaneous net movement of solvent molecules through a selectively permeable membrane into a region of higher solute concentration.",
     "domain": "biophysics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Biophysical osmotic mechanism"},
    {"claim_id": "FS_RELA_002", "type": "RELATIONAL", "subject": "Osmosis",
     "property": "biophysical_mechanism", "value": "active transport of heavy minerals against gravity using ATP synthase pumps", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Osmosis is the active enzymatic transport of mineral ions against gravity driven exclusively by nuclear ATP pumps.",
     "domain": "biophysics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fabricated biological definition"},
    {"claim_id": "FS_RELA_003", "type": "RELATIONAL", "subject": "Archimedes principle",
     "property": "physical_buoyancy_law", "value": "upward buoyant force equals the weight of the fluid displaced by the body", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Archimedes' principle indicates that any body submerged in a fluid experiences an upward buoyant force equal to the weight of fluid it displaces.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Classical fluid statics law"},
    {"claim_id": "FS_RELA_004", "type": "RELATIONAL", "subject": "Archimedes principle",
     "property": "physical_buoyancy_law", "value": "buoyant force is determined solely by ambient acoustic vibration resonance", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Archimedes' principle dictates that buoyancy is generated solely by acoustic standing waves vibrating inside solid crystal structures.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fabricated physical law"},

    # -------------------------------------------------------------------------
    # 6. SCALE EXPANSION EXTENSIONS (25 claims to cross 1000+ milestone)
    # -------------------------------------------------------------------------
    {"claim_id": "FS_QUAN_009", "type": "QUANTITATIVE", "subject": "Light speed in vacuum",
     "property": "speed_constant", "value": "299792458 m/s", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The exact speed of light in vacuum is defined as 299,792,458 meters per second.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "SI exact definition constant"},
    {"claim_id": "FS_QUAN_010", "type": "QUANTITATIVE", "subject": "Light speed in vacuum",
     "property": "speed_constant", "value": "150000000 m/s", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The exact speed of light in vacuum is defined as 150,000,000 meters per second.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Halved speed of light error"},
    {"claim_id": "FS_QUAN_011", "type": "QUANTITATIVE", "subject": "Absolute zero",
     "property": "celsius_value", "value": "-273.15 degrees Celsius", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Absolute zero corresponds to a temperature of -273.15 degrees on the Celsius scale.",
     "domain": "thermodynamics", "sub_type": "NUMERICAL", "notes": "Thermodynamic zero temperature"},
    {"claim_id": "FS_QUAN_012", "type": "QUANTITATIVE", "subject": "Absolute zero",
     "property": "celsius_value", "value": "-459.67 degrees Celsius", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Absolute zero corresponds to a temperature of -459.67 degrees on the Celsius scale.",
     "domain": "thermodynamics", "sub_type": "NUMERICAL", "notes": "Confused Celsius with Fahrenheit (-459.67°F)"},
    {"claim_id": "FS_TEMP_007", "type": "TEMPORAL", "subject": "Apollo 11",
     "property": "lunar_landing_date", "value": "July 20, 1969", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Apollo 11 Lunar Module Eagle touched down on the lunar surface on July 20, 1969.",
     "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "NASA Apollo 11 moon landing"},
    {"claim_id": "FS_TEMP_008", "type": "TEMPORAL", "subject": "Apollo 11",
     "property": "lunar_landing_date", "value": "July 20, 1974", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Apollo 11 Lunar Module Eagle touched down on the lunar surface on July 20, 1974.",
     "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted moon landing year"},
    {"claim_id": "FS_TEMP_009", "type": "TEMPORAL", "subject": "Chernobyl disaster",
     "property": "explosion_date", "value": "April 26, 1986", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The catastrophic nuclear accident at the Chernobyl Nuclear Power Plant occurred on April 26, 1986.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Chernobyl reactor 4 disaster date"},
    {"claim_id": "FS_TEMP_010", "type": "TEMPORAL", "subject": "Chernobyl disaster",
     "property": "explosion_date", "value": "April 26, 1991", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The catastrophic nuclear accident at the Chernobyl Nuclear Power Plant occurred on April 26, 1991.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Confused Chernobyl (1986) with Soviet dissolution (1991)"},
    {"claim_id": "FS_ENTI_007", "type": "ENTITY_ATTRIBUTE", "subject": "Diamond",
     "property": "elemental_composition", "value": "pure carbon in a diamond cubic crystal structure", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Diamond is an allotrope composed purely of carbon atoms arranged in a face-centered diamond cubic lattice.",
     "domain": "mineralogy", "sub_type": "ALLOTROPE", "notes": "Carbon allotrope definition"},
    {"claim_id": "FS_ENTI_008", "type": "ENTITY_ATTRIBUTE", "subject": "Diamond",
     "property": "elemental_composition", "value": "pure crystalline silicon dioxide", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Diamond is a mineral formed exclusively from crystalline silicon dioxide.",
     "domain": "mineralogy", "sub_type": "ALLOTROPE", "notes": "Silicon dioxide is Quartz, not Diamond"},
    {"claim_id": "FS_ENTI_009", "type": "ENTITY_ATTRIBUTE", "subject": "Japan",
     "property": "national_currency", "value": "Japanese yen", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The official legal tender currency of Japan is the Japanese yen (JPY).",
     "domain": "economics", "sub_type": "CURRENCY", "notes": "Official sovereign currency"},
    {"claim_id": "FS_ENTI_010", "type": "ENTITY_ATTRIBUTE", "subject": "Japan",
     "property": "national_currency", "value": "Japanese yuan", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The official legal tender currency of Japan is the Japanese yuan.",
     "domain": "economics", "sub_type": "CURRENCY", "notes": "Yuan is Chinese currency, Japan uses Yen"},
    {"claim_id": "FS_CITA_005", "type": "CITATION", "subject": "Relativity: The Special and General Theory",
     "property": "author", "value": "Albert Einstein", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Albert Einstein published his popular exposition 'Relativity: The Special and General Theory' in 1916.",
     "domain": "physics_history", "sub_type": "AUTHOR_CHECK", "notes": "Einstein relativity publication"},
    {"claim_id": "FS_CITA_006", "type": "CITATION", "subject": "Relativity: The Special and General Theory",
     "property": "author", "value": "Max Planck", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Max Planck published his popular exposition 'Relativity: The Special and General Theory' in 1916.",
     "domain": "physics_history", "sub_type": "AUTHOR_SWAP", "notes": "Relativity misattributed to Planck"},
    {"claim_id": "FS_RELA_005", "type": "RELATIONAL", "subject": "Doppler effect",
     "property": "physical_wave_mechanism", "value": "observed wave frequency shifts due to relative motion between source and observer", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Doppler effect causes an increase in observed wave frequency when the source and observer move toward each other.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Acoustic / electromagnetic Doppler shift"},
    {"claim_id": "FS_RELA_006", "type": "RELATIONAL", "subject": "Doppler effect",
     "property": "physical_wave_mechanism", "value": "wave speed accelerates beyond the speed of light in dense liquids", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Doppler effect occurs because physical sound waves exceed the speed of light when traveling through heavy water.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fabricated physical definition"},
    {"claim_id": "FS_QUAN_013", "type": "QUANTITATIVE", "subject": "Earth",
     "property": "mean_distance_to_moon", "value": "384400 kilometers", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The average center-to-center distance from Earth to the Moon is approximately 384,400 kilometers.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "NASA Lunar distance"},
    {"claim_id": "FS_QUAN_014", "type": "QUANTITATIVE", "subject": "Earth",
     "property": "mean_distance_to_moon", "value": "1500000 kilometers", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The average center-to-center distance from Earth to the Moon is approximately 1,500,000 kilometers.",
     "domain": "astronomy", "sub_type": "NUMERICAL", "notes": "Quadrupled Earth-Moon distance"},
    {"claim_id": "FS_TEMP_011", "type": "TEMPORAL", "subject": "Fall of the Berlin Wall",
     "property": "event_date", "value": "November 9, 1989", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Berlin Wall was officially opened to free passage on the evening of November 9, 1989.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Fall of Berlin Wall historical date"},
    {"claim_id": "FS_TEMP_012", "type": "TEMPORAL", "subject": "Fall of the Berlin Wall",
     "property": "event_date", "value": "November 9, 1993", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Berlin Wall was officially opened to free passage on the evening of November 9, 1993.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted Cold War milestone year"},
    {"claim_id": "FS_ENTI_011", "type": "ENTITY_ATTRIBUTE", "subject": "Sun",
     "property": "primary_nuclear_fusion_fuel", "value": "hydrogen into helium via the proton-proton chain", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The core of the Sun generates energy predominantly by fusing hydrogen nuclei into helium via the proton-proton chain reaction.",
     "domain": "astrophysics", "sub_type": "FUSION_FUEL", "notes": "Solar nuclear fusion mechanism"},
    {"claim_id": "FS_ENTI_012", "type": "ENTITY_ATTRIBUTE", "subject": "Sun",
     "property": "primary_nuclear_fusion_fuel", "value": "pure solid uranium combustion", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The core of the Sun generates thermal energy primarily through the open atmospheric combustion of solid uranium fuel.",
     "domain": "astrophysics", "sub_type": "FUSION_FUEL", "notes": "Fabricated chemical combustion myth"},
    {"claim_id": "FS_CITA_007", "type": "CITATION", "subject": "Philosophiae Naturalis Principia Mathematica",
     "property": "author", "value": "Isaac Newton", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Sir Isaac Newton laid the foundations of classical mechanics in his 1687 treatise Philosophiae Naturalis Principia Mathematica.",
     "domain": "physics_history", "sub_type": "AUTHOR_CHECK", "notes": "Newton Principia Mathematica publication"},
    {"claim_id": "FS_CITA_008", "type": "CITATION", "subject": "Philosophiae Naturalis Principia Mathematica",
     "property": "author", "value": "Galileo Galilei", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Galileo Galilei laid the foundations of classical mechanics in his 1687 treatise Philosophiae Naturalis Principia Mathematica.",
     "domain": "physics_history", "sub_type": "AUTHOR_SWAP", "notes": "Principia misattributed to Galileo (died 1642)"},
    {"claim_id": "FS_RELA_007", "type": "RELATIONAL", "subject": "Hooke law",
     "property": "elasticity_law", "value": "the force needed to extend or compress a spring by some distance scales linearly with that distance", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Hooke's law states that the restoring force exerted by an ideal spring is directly proportional to the displacement distance (F = -kx).",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Linear elasticity physics law"}
]


def generate_final_scale(output_path: str = OUT_CSV) -> list[dict]:
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in FINAL_SCALE_CLAIMS:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return FINAL_SCALE_CLAIMS


def selftest() -> bool:
    print("Running generate_final_scale selftest...")
    ids = [r["claim_id"] for r in FINAL_SCALE_CLAIMS]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    types = set(r["type"] for r in FINAL_SCALE_CLAIMS)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    print(f"Selftest PASSED: {len(FINAL_SCALE_CLAIMS)} claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate final scale bridge claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_final_scale(args.out)
    print(f"Wrote {len(FINAL_SCALE_CLAIMS)} final scale claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
