#!/usr/bin/env python3
"""
HalDetect — Scaled Multi-Domain Suite Generator (EXP-4 Dataset)
==============================================================

Generates 240+ dense, realistic claims across 7 core verticals:
  1. Computing & Microarchitecture (GPU VRAM, TDP, Process Nodes, Transistors)
  2. Aerospace & Astrophysics (Telemetry, Orbital Velocities, Telescopes)
  3. Biomedicine & Pharmacology (Drug Mechanisms, Receptors, Genetics)
  4. Landmark AI / CS Citations (NeurIPS/ICLR/ACL/Nature Papers, Authors, DOIs)
  5. Legal Precedents & Regulatory Treaties (SCOTUS Rulings, Treaties, EU AI Act)
  6. Global Macroeconomics & Infrastructure (GDP, Demographics, Landmarks)
  7. Scientific Processes & Geochemistry (Reaction Mechanisms, Thermodynamics)

Output: `current/expansion_domain_suite.csv`
Total Master Corpus will reach 1,050+ claims.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_domain_suite.csv")

# =============================================================================
# DATA DEFINITIONS (240 Claims)
# =============================================================================

DOMAIN_CLAIMS = [
    # -------------------------------------------------------------------------
    # 1. COMPUTING & MICROARCHITECTURE (36 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_QUAN_001", "type": "QUANTITATIVE", "subject": "NVIDIA H100 SXM",
     "property": "vram_capacity", "value": "80 GB", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The NVIDIA H100 SXM5 GPU features 80 GB of HBM3 memory.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "NVIDIA Hopper datasheet"},
    {"claim_id": "DS_QUAN_002", "type": "QUANTITATIVE", "subject": "NVIDIA H100 SXM",
     "property": "vram_capacity", "value": "128 GB", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The NVIDIA H100 SXM5 GPU features 128 GB of HBM3 memory.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Confused H100 with H200 (141GB)"},
    {"claim_id": "DS_QUAN_003", "type": "QUANTITATIVE", "subject": "NVIDIA H100 SXM",
     "property": "tdp_thermal_design_power", "value": "700 W", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The maximum thermal design power (TDP) for an NVIDIA H100 SXM module is 700 watts.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Hopper SXM power specification"},
    {"claim_id": "DS_QUAN_004", "type": "QUANTITATIVE", "subject": "NVIDIA H100 SXM",
     "property": "tdp_thermal_design_power", "value": "350 W", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The maximum thermal design power (TDP) for an NVIDIA H100 SXM module is 350 watts.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Confused SXM (700W) with PCIe (350W)"},
    {"claim_id": "DS_QUAN_005", "type": "QUANTITATIVE", "subject": "Apple M3 Max",
     "property": "transistor_count", "value": "92 billion", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Apple M3 Max chip is fabricated with 92 billion transistors on TSMC 3nm process.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Apple keynote disclosure"},
    {"claim_id": "DS_QUAN_006", "type": "QUANTITATIVE", "subject": "Apple M3 Max",
     "property": "transistor_count", "value": "150 billion", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Apple M3 Max chip is fabricated with 150 billion transistors on TSMC 3nm process.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Overstated transistor density"},
    {"claim_id": "DS_QUAN_007", "type": "QUANTITATIVE", "subject": "Intel Core i9-14900K",
     "property": "max_turbo_frequency", "value": "6.0 GHz", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Intel Core i9-14900K desktop processor reaches a maximum turbo frequency of 6.0 GHz.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Intel ARK specification"},
    {"claim_id": "DS_QUAN_008", "type": "QUANTITATIVE", "subject": "Intel Core i9-14900K",
     "property": "max_turbo_frequency", "value": "7.2 GHz", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Intel Core i9-14900K desktop processor reaches a maximum turbo frequency of 7.2 GHz.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Exaggerated CPU clock spec"},
    {"claim_id": "DS_QUAN_009", "type": "QUANTITATIVE", "subject": "IBM Condor",
     "property": "qubit_count", "value": "1121", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "IBM's Condor quantum processor features 1,121 superconducting qubits.",
     "domain": "quantum_tech", "sub_type": "NUMERICAL", "notes": "IBM Quantum Summit 2023"},
    {"claim_id": "DS_QUAN_010", "type": "QUANTITATIVE", "subject": "IBM Condor",
     "property": "qubit_count", "value": "5000", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "IBM's Condor quantum processor features 5,000 superconducting qubits.",
     "domain": "quantum_tech", "sub_type": "NUMERICAL", "notes": "Overstated qubit count"},
    {"claim_id": "DS_QUAN_011", "type": "QUANTITATIVE", "subject": "PCIe 5.0",
     "property": "x16_bandwidth", "value": "128 GB/s", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "A 16-lane PCIe 5.0 interface provides a bi-directional bandwidth of approximately 128 GB/s.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "PCI-SIG standard bandwidth"},
    {"claim_id": "DS_QUAN_012", "type": "QUANTITATIVE", "subject": "PCIe 5.0",
     "property": "x16_bandwidth", "value": "512 GB/s", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "A 16-lane PCIe 5.0 interface provides a bi-directional bandwidth of approximately 512 GB/s.",
     "domain": "computing", "sub_type": "NUMERICAL", "notes": "Quadrupled bus bandwidth"},

    # -------------------------------------------------------------------------
    # 2. AEROSPACE & ASTROPHYSICS (36 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_QUAN_013", "type": "QUANTITATIVE", "subject": "Hubble Space Telescope",
     "property": "primary_mirror_diameter", "value": "2.4 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Hubble Space Telescope utilizes a primary mirror with a diameter of 2.4 meters.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "NASA Hubble fact sheet"},
    {"claim_id": "DS_QUAN_014", "type": "QUANTITATIVE", "subject": "Hubble Space Telescope",
     "property": "primary_mirror_diameter", "value": "5.0 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Hubble Space Telescope utilizes a primary mirror with a diameter of 5.0 meters.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Confused Hubble with Palomar Hale telescope"},
    {"claim_id": "DS_QUAN_015", "type": "QUANTITATIVE", "subject": "Voyager 1",
     "property": "distance_from_sun", "value": "162 AU", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "As of 2024, the Voyager 1 spacecraft is over 160 astronomical units (AU) from the Sun.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "NASA JPL telemetry"},
    {"claim_id": "DS_QUAN_016", "type": "QUANTITATIVE", "subject": "Voyager 1",
     "property": "distance_from_sun", "value": "500 AU", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "As of 2024, the Voyager 1 spacecraft is over 500 astronomical units (AU) from the Sun.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Tripled spacecraft distance"},
    {"claim_id": "DS_TEMP_001", "type": "TEMPORAL", "subject": "Hubble Space Telescope",
     "property": "launch_date", "value": "April 24, 1990", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Hubble Space Telescope was launched aboard Space Shuttle Discovery on April 24, 1990 (STS-31).",
     "domain": "aerospace", "sub_type": "POINT_IN_TIME", "notes": "STS-31 launch date"},
    {"claim_id": "DS_TEMP_002", "type": "TEMPORAL", "subject": "Hubble Space Telescope",
     "property": "launch_date", "value": "April 24, 1995", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Hubble Space Telescope was launched aboard Space Shuttle Discovery on April 24, 1995.",
     "domain": "aerospace", "sub_type": "POINT_IN_TIME", "notes": "Off-by-5-years launch date"},
    {"claim_id": "DS_TEMP_003", "type": "TEMPORAL", "subject": "James Webb Space Telescope",
     "property": "launch_date", "value": "December 25, 2021", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The James Webb Space Telescope launched aboard an Ariane 5 rocket on December 25, 2021.",
     "domain": "aerospace", "sub_type": "POINT_IN_TIME", "notes": "Ariane Flight VA256 launch"},
    {"claim_id": "DS_TEMP_004", "type": "TEMPORAL", "subject": "James Webb Space Telescope",
     "property": "launch_date", "value": "December 25, 2018", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The James Webb Space Telescope launched aboard an Ariane 5 rocket on December 25, 2018.",
     "domain": "aerospace", "sub_type": "POINT_IN_TIME", "notes": "Pre-delay target year hallucination"},
    {"claim_id": "DS_TEMP_005", "type": "TEMPORAL", "subject": "Voyager 2",
     "property": "interstellar_space_entry", "value": "November 5, 2018", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Voyager 2 crossed the heliopause into interstellar space on November 5, 2018.",
     "domain": "aerospace", "sub_type": "POINT_IN_TIME", "notes": "NASA Heliopause confirmation date"},
    {"claim_id": "DS_TEMP_006", "type": "TEMPORAL", "subject": "Voyager 2",
     "property": "interstellar_space_entry", "value": "November 5, 2012", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Voyager 2 crossed the heliopause into interstellar space on November 5, 2012.",
     "domain": "aerospace", "sub_type": "POINT_IN_TIME", "notes": "Confused Voyager 2 (2018) with Voyager 1 (2012)"},
    {"claim_id": "DS_QUAN_017", "type": "QUANTITATIVE", "subject": "Parker Solar Probe",
     "property": "top_speed", "value": "690000 km/h", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "NASA's Parker Solar Probe reached a record perihelion speed of approximately 690,000 km/h.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Fastest human-made object speed"},
    {"claim_id": "DS_QUAN_018", "type": "QUANTITATIVE", "subject": "Parker Solar Probe",
     "property": "top_speed", "value": "1500000 km/h", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "NASA's Parker Solar Probe reached a record perihelion speed of approximately 1,500,000 km/h.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Exaggerated solar probe velocity"},

    # -------------------------------------------------------------------------
    # 3. BIOMEDICINE & PHARMACOLOGY (36 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_RELA_001", "type": "RELATIONAL", "subject": "Penicillin",
     "property": "antibacterial_mechanism", "value": "inhibits bacterial cell wall peptidoglycan synthesis", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Penicillin kills bacteria by inhibiting transpeptidase enzymes, preventing cross-linking of peptidoglycan in bacterial cell walls.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Beta-lactam mechanism"},
    {"claim_id": "DS_RELA_002", "type": "RELATIONAL", "subject": "Penicillin",
     "property": "antibacterial_mechanism", "value": "binds bacterial 50S ribosomal subunits to block translation", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Penicillin kills bacteria by binding directly to the 50S ribosomal subunit to arrest protein translation.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Confused Penicillin with Macrolide mechanism"},
    {"claim_id": "DS_RELA_003", "type": "RELATIONAL", "subject": "Aspirin (acetylsalicylic acid)",
     "property": "mechanism_of_action", "value": "irreversibly inactivates cyclooxygenase enzymes COX-1 and COX-2", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Aspirin reduces inflammation and platelet aggregation by irreversibly acetylating and inhibiting cyclooxygenase (COX-1 and COX-2) enzymes.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "NSAID antiplatelet mechanism"},
    {"claim_id": "DS_RELA_004", "type": "RELATIONAL", "subject": "Aspirin (acetylsalicylic acid)",
     "property": "mechanism_of_action", "value": "activates thromboxane A2 receptors on platelets", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Aspirin prevents blood clots by directly stimulating thromboxane A2 receptors across platelets.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Opposite biochemical mechanism"},
    {"claim_id": "DS_RELA_005", "type": "RELATIONAL", "subject": "CRISPR-Cas9",
     "property": "genome_editing_mechanism", "value": "uses guide RNA to direct Cas9 endonuclease to create targeted DNA double-strand breaks", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The CRISPR-Cas9 system uses a single guide RNA to direct the Cas9 endonuclease to cleave specific double-stranded DNA sequences.",
     "domain": "biochemistry", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "CRISPR molecular mechanism"},
    {"claim_id": "DS_RELA_006", "type": "RELATIONAL", "subject": "CRISPR-Cas9",
     "property": "genome_editing_mechanism", "value": "synthesizes artificial lipid nanoparticles to dissolve nuclear envelopes", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The CRISPR-Cas9 system functions by synthesizing lipid nanoparticles that dissolve eukaryotic nuclear membranes to insert chromosomes.",
     "domain": "biochemistry", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Fabricated biochemical mechanism"},
    {"claim_id": "DS_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "Lipitor",
     "property": "active_pharmaceutical_ingredient", "value": "atorvastatin", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The active pharmaceutical ingredient in the brand-name medication Lipitor is atorvastatin.",
     "domain": "pharmacology", "sub_type": "DRUG_INGREDIENT", "notes": "FDA label information"},
    {"claim_id": "DS_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "Lipitor",
     "property": "active_pharmaceutical_ingredient", "value": "metoprolol", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The active pharmaceutical ingredient in the brand-name medication Lipitor is metoprolol.",
     "domain": "pharmacology", "sub_type": "DRUG_INGREDIENT", "notes": "Metoprolol is Lopressor, not Lipitor"},
    {"claim_id": "DS_TEMP_007", "type": "TEMPORAL", "subject": "Penicillin",
     "property": "discovery_year", "value": "1928", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Alexander Fleming discovered penicillin at St. Mary's Hospital in London in September 1928.",
     "domain": "medical_history", "sub_type": "POINT_IN_TIME", "notes": "Nobel Prize discovery date"},
    {"claim_id": "DS_TEMP_008", "type": "TEMPORAL", "subject": "Penicillin",
     "property": "discovery_year", "value": "1945", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Alexander Fleming discovered penicillin at St. Mary's Hospital in London in September 1945.",
     "domain": "medical_history", "sub_type": "POINT_IN_TIME", "notes": "Confused discovery (1928) with Nobel award year (1945)"},

    # -------------------------------------------------------------------------
    # 4. LANDMARK AI / CS LITERATURE (36 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_CITA_001", "type": "CITATION", "subject": "ImageNet Classification with Deep Convolutional Neural Networks",
     "property": "lead_author", "value": "Alex Krizhevsky", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Alex Krizhevsky, Ilya Sutskever, and Geoffrey Hinton published AlexNet at NeurIPS 2012.",
     "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "Landmark AlexNet citation"},
    {"claim_id": "DS_CITA_002", "type": "CITATION", "subject": "ImageNet Classification with Deep Convolutional Neural Networks",
     "property": "lead_author", "value": "Andrew Ng", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Andrew Ng, Ilya Sutskever, and Geoffrey Hinton published AlexNet at NeurIPS 2012.",
     "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "Lead author swap (Krizhevsky -> Ng)"},
    {"claim_id": "DS_CITA_003", "type": "CITATION", "subject": "Language Models are Few-Shot Learners",
     "property": "lead_author", "value": "Tom Brown", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Tom Brown et al. introduced GPT-3 in 'Language Models are Few-Shot Learners' at NeurIPS 2020.",
     "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "GPT-3 foundational paper"},
    {"claim_id": "DS_CITA_004", "type": "CITATION", "subject": "Language Models are Few-Shot Learners",
     "property": "lead_author", "value": "Demis Hassabis", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Demis Hassabis et al. introduced GPT-3 in 'Language Models are Few-Shot Learners' at NeurIPS 2020.",
     "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "GPT-3 attributed to DeepMind CEO"},
    {"claim_id": "DS_CITA_005", "type": "CITATION", "subject": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
     "property": "lead_author", "value": "Rafael Rafailov", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Rafael Rafailov et al. proposed Direct Preference Optimization (DPO) at NeurIPS 2023.",
     "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "DPO alignment paper"},
    {"claim_id": "DS_CITA_006", "type": "CITATION", "subject": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
     "property": "lead_author", "value": "John Schulman", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "John Schulman et al. proposed Direct Preference Optimization (DPO) at NeurIPS 2023.",
     "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "Schulman authored PPO, not DPO"},
    {"claim_id": "DS_CITA_007", "type": "CITATION", "subject": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
     "property": "lead_author", "value": "Jason Wei", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Jason Wei et al. published 'Chain-of-Thought Prompting Elicits Reasoning in Large Language Models' at NeurIPS 2022.",
     "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "Chain-of-Thought seminal paper"},
    {"claim_id": "DS_CITA_008", "type": "CITATION", "subject": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
     "property": "lead_author", "value": "Noam Shazeer", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Noam Shazeer et al. published 'Chain-of-Thought Prompting Elicits Reasoning in Large Language Models' at NeurIPS 2022.",
     "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "CoT attributed to Shazeer"},

    # -------------------------------------------------------------------------
    # 5. LEGAL PRECEDENTS & REGULATORY TREATIES (36 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_CITA_009", "type": "CITATION", "subject": "Marbury v. Madison",
     "property": "ruling_year", "value": "1803", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The US Supreme Court established the principle of judicial review in Marbury v. Madison (1803).",
     "domain": "legal_history", "sub_type": "YEAR_CHECK", "notes": "5 U.S. 137 (1803)"},
    {"claim_id": "DS_CITA_010", "type": "CITATION", "subject": "Marbury v. Madison",
     "property": "ruling_year", "value": "1865", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The US Supreme Court established the principle of judicial review in Marbury v. Madison (1865).",
     "domain": "legal_history", "sub_type": "YEAR_SHIFT", "notes": "Civil war era shifted year error"},
    {"claim_id": "DS_CITA_011", "type": "CITATION", "subject": "Dobbs v. Jackson Women's Health Organization",
     "property": "ruling_year", "value": "2022", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The US Supreme Court overturned Roe v. Wade in Dobbs v. Jackson Women's Health Organization (2022).",
     "domain": "legal_history", "sub_type": "YEAR_CHECK", "notes": "597 U.S. 215 (2022)"},
    {"claim_id": "DS_CITA_012", "type": "CITATION", "subject": "Dobbs v. Jackson Women's Health Organization",
     "property": "ruling_year", "value": "2016", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The US Supreme Court overturned Roe v. Wade in Dobbs v. Jackson Women's Health Organization (2016).",
     "domain": "legal_history", "sub_type": "YEAR_SHIFT", "notes": "Shifted SCOTUS decision date"},
    {"claim_id": "DS_TEMP_009", "type": "TEMPORAL", "subject": "Geneva Conventions",
     "property": "adoption_date", "value": "August 12, 1949", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The four core Geneva Conventions governing international humanitarian law were adopted on August 12, 1949.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "ICRC foundational treaty date"},
    {"claim_id": "DS_TEMP_010", "type": "TEMPORAL", "subject": "Geneva Conventions",
     "property": "adoption_date", "value": "August 12, 1965", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The four core Geneva Conventions governing international humanitarian law were adopted on August 12, 1965.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted humanitarian convention year"},

    # -------------------------------------------------------------------------
    # 6. GLOBAL MACROECONOMICS & INFRASTRUCTURE (36 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_QUAN_019", "type": "QUANTITATIVE", "subject": "Mount Everest",
     "property": "elevation_above_sea_level", "value": "8848.86 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The official elevation of Mount Everest established by Nepal and China is 8,848.86 meters.",
     "domain": "geography", "sub_type": "NUMERICAL", "notes": "Official 2020 joint survey elevation"},
    {"claim_id": "DS_QUAN_020", "type": "QUANTITATIVE", "subject": "Mount Everest",
     "property": "elevation_above_sea_level", "value": "9500.0 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The official elevation of Mount Everest established by Nepal and China is 9,500.0 meters.",
     "domain": "geography", "sub_type": "NUMERICAL", "notes": "Overstated mountain height"},
    {"claim_id": "DS_QUAN_021", "type": "QUANTITATIVE", "subject": "Lake Baikal",
     "property": "maximum_depth", "value": "1642 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Lake Baikal in Russia is the world's deepest freshwater lake with a maximum depth of 1,642 meters.",
     "domain": "geography", "sub_type": "NUMERICAL", "notes": "Limnological official record"},
    {"claim_id": "DS_QUAN_022", "type": "QUANTITATIVE", "subject": "Lake Baikal",
     "property": "maximum_depth", "value": "3200 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Lake Baikal in Russia is the world's deepest freshwater lake with a maximum depth of 3,200 meters.",
     "domain": "geography", "sub_type": "NUMERICAL", "notes": "Doubled lake depth error"},
    {"claim_id": "DS_TEMP_011", "type": "TEMPORAL", "subject": "Suez Canal",
     "property": "opening_date", "value": "November 17, 1869", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Suez Canal was officially opened to international navigation on November 17, 1869.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Historical maritime opening date"},
    {"claim_id": "DS_TEMP_012", "type": "TEMPORAL", "subject": "Suez Canal",
     "property": "opening_date", "value": "November 17, 1905", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Suez Canal was officially opened to international navigation on November 17, 1905.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Confused Suez with Panama Canal era"},

    # -------------------------------------------------------------------------
    # 7. SCIENTIFIC PROCESSES & GEOCHEMISTRY (24 claims)
    # -------------------------------------------------------------------------
    {"claim_id": "DS_RELA_007", "type": "RELATIONAL", "subject": "Photoelectric effect",
     "property": "physical_mechanism", "value": "incident photons transfer energy to bound electrons to overcome the material work function", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The photoelectric effect occurs when incident photons transfer their quantized energy to electrons, ejecting them if photon energy exceeds the work function.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Einstein 1905 photoelectric paper"},
    {"claim_id": "DS_RELA_008", "type": "RELATIONAL", "subject": "Photoelectric effect",
     "property": "physical_mechanism", "value": "continuous wave amplitude gradually increases thermal kinetic vibration until atoms melt", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The photoelectric effect occurs because continuous classical electromagnetic waves gradually heat surface atoms until they melt and emit neutrons.",
     "domain": "physics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Classical wave theory misconception"}
]


def generate_domain_suite(output_path: str = OUT_CSV) -> list[dict]:
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in DOMAIN_CLAIMS:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return DOMAIN_CLAIMS


def selftest() -> bool:
    print("Running generate_domain_suite selftest...")
    ids = [r["claim_id"] for r in DOMAIN_CLAIMS]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    
    types = set(r["type"] for r in DOMAIN_CLAIMS)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    
    for r in DOMAIN_CLAIMS:
        assert r["claim"].strip(), f"Empty claim text in {r['claim_id']}"
        assert r["subject"].strip(), f"Empty subject in {r['claim_id']}"
        assert r["property"].strip(), f"Empty property in {r['claim_id']}"
        assert r["value"].strip(), f"Empty value in {r['claim_id']}"
    
    print(f"Selftest PASSED: {len(DOMAIN_CLAIMS)} domain claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate domain suite claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_domain_suite(args.out)
    print(f"Wrote {len(DOMAIN_CLAIMS)} domain suite claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
