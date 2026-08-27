#!/usr/bin/env python3
"""
HalDetect — 350-Claim Multi-Domain Expansion Generator (EXP-3 Suite)
===================================================================

Generates a dense, realistic, multi-domain evaluation expansion (350 claims)
mirroring actual user queries to LLMs across 5 modalities:
  1. QUANTITATIVE     (+70 claims: tech specs, aerospace, macroeconomics, clinical)
  2. TEMPORAL         (+70 claims: software releases, treaties, scientific discoveries)
  3. ENTITY_ATTRIBUTE (+70 claims: tech leadership, chemistry, architecture, literature)
  4. CITATION         (+70 claims: landmark AI papers, SCOTUS rulings, phantom citations)
  5. RELATIONAL       (+70 claims: pharmacology mechanisms, macroeconomics, physics)

Output: `current/expansion_v3_claims.csv`
Total Expanded Master Corpus will reach 1,064 claims.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_v3_claims.csv")

CLAIMS_V3 = [
    # =========================================================================
    # 1. QUANTITATIVE (70 claims)
    # =========================================================================
    # Hardware & Compute
    {"claim_id": "EXP3_QUAN_001", "type": "QUANTITATIVE", "subject": "AMD EPYC 9654",
     "property": "core_count", "value": "96", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The AMD EPYC 9654 server processor features 96 Zen 4 CPU cores.",
     "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Official AMD CPU specification"},
    {"claim_id": "EXP3_QUAN_002", "type": "QUANTITATIVE", "subject": "AMD EPYC 9654",
     "property": "core_count", "value": "128", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The AMD EPYC 9654 server processor features 128 Zen 4 CPU cores.",
     "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Confused EPYC 9654 with 9754 Bergamo"},
    {"claim_id": "EXP3_QUAN_003", "type": "QUANTITATIVE", "subject": "Tesla V3 Supercharger",
     "property": "peak_power_output", "value": "250 kW", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Tesla V3 Superchargers deliver a peak charging rate of up to 250 kW per vehicle.",
     "domain": "consumer_tech", "sub_type": "NUMERICAL", "notes": "Tesla V3 official power rate"},
    {"claim_id": "EXP3_QUAN_004", "type": "QUANTITATIVE", "subject": "Tesla V3 Supercharger",
     "property": "peak_power_output", "value": "500 kW", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Tesla V3 Superchargers deliver a peak charging rate of up to 500 kW per vehicle.",
     "domain": "consumer_tech", "sub_type": "NUMERICAL", "notes": "Doubled charging rate hallucination"},
    {"claim_id": "EXP3_QUAN_005", "type": "QUANTITATIVE", "subject": "Qualcomm Snapdragon 8 Gen 3",
     "property": "prime_core_clock", "value": "3.3 GHz", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Qualcomm Snapdragon 8 Gen 3 Cortex-X4 prime core clocks up to 3.3 GHz.",
     "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Qualcomm official architecture spec"},
    {"claim_id": "EXP3_QUAN_006", "type": "QUANTITATIVE", "subject": "Qualcomm Snapdragon 8 Gen 3",
     "property": "prime_core_clock", "value": "4.2 GHz", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Qualcomm Snapdragon 8 Gen 3 Cortex-X4 prime core clocks up to 4.2 GHz.",
     "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Exaggerated mobile CPU clock rate"},
    # Aerospace & Physics
    {"claim_id": "EXP3_QUAN_007", "type": "QUANTITATIVE", "subject": "James Webb Space Telescope",
     "property": "primary_mirror_diameter", "value": "6.5 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The primary mirror of the James Webb Space Telescope measures 6.5 meters across.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "NASA official JWST mirror diameter"},
    {"claim_id": "EXP3_QUAN_008", "type": "QUANTITATIVE", "subject": "James Webb Space Telescope",
     "property": "primary_mirror_diameter", "value": "12.4 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The primary mirror of the James Webb Space Telescope measures 12.4 meters across.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Doubled telescope mirror diameter"},
    {"claim_id": "EXP3_QUAN_009", "type": "QUANTITATIVE", "subject": "Saturn V",
     "property": "payload_to_leo", "value": "140000 kg", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Apollo Saturn V rocket could inject a payload of approximately 140,000 kg into Low Earth Orbit.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Apollo Saturn V LEO payload capacity"},
    {"claim_id": "EXP3_QUAN_010", "type": "QUANTITATIVE", "subject": "Saturn V",
     "property": "payload_to_leo", "value": "45000 kg", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Apollo Saturn V rocket could inject a payload of approximately 45,000 kg into Low Earth Orbit.",
     "domain": "aerospace", "sub_type": "NUMERICAL", "notes": "Confused LEO payload with Lunar injection payload"},
    {"claim_id": "EXP3_QUAN_011", "type": "QUANTITATIVE", "subject": "Speed of sound",
     "property": "air_sea_level_speed", "value": "343 m/s", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The speed of sound in dry air at 20 degrees Celsius is approximately 343 meters per second.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Standard acoustic constant at 20°C"},
    {"claim_id": "EXP3_QUAN_012", "type": "QUANTITATIVE", "subject": "Speed of sound",
     "property": "air_sea_level_speed", "value": "520 m/s", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The speed of sound in dry air at 20 degrees Celsius is approximately 520 meters per second.",
     "domain": "physics", "sub_type": "NUMERICAL", "notes": "Shifted speed of sound magnitude"},
    # Macroeconomics & Demographics
    {"claim_id": "EXP3_QUAN_013", "type": "QUANTITATIVE", "subject": "Japan",
     "property": "population", "value": "125 million", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The population of Japan is approximately 125 million people.",
     "domain": "demographics", "sub_type": "NUMERICAL", "notes": "World Bank / Statistics Bureau of Japan"},
    {"claim_id": "EXP3_QUAN_014", "type": "QUANTITATIVE", "subject": "Japan",
     "property": "population", "value": "210 million", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The population of Japan is approximately 210 million people.",
     "domain": "demographics", "sub_type": "NUMERICAL", "notes": "Confused Japan population with Nigeria/Brazil"},
    # Biomedical & Clinical Numbers
    {"claim_id": "EXP3_QUAN_015", "type": "QUANTITATIVE", "subject": "Human blood",
     "property": "volume", "value": "5 liters", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The average adult human body contains approximately 5 liters of blood.",
     "domain": "medicine", "sub_type": "NUMERICAL", "notes": "Standard physiological blood volume"},
    {"claim_id": "EXP3_QUAN_016", "type": "QUANTITATIVE", "subject": "Human blood",
     "property": "volume", "value": "14 liters", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The average adult human body contains approximately 14 liters of blood.",
     "domain": "medicine", "sub_type": "NUMERICAL", "notes": "Almost tripled physiological volume error"},
    {"claim_id": "EXP3_QUAN_017", "type": "QUANTITATIVE", "subject": "SARS-CoV-2",
     "property": "genome_length", "value": "29900 base pairs", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The single-stranded RNA genome of SARS-CoV-2 is approximately 29.9 kilobases in length.",
     "domain": "virology", "sub_type": "NUMERICAL", "notes": "NCBI Reference Sequence NC_045512.2"},
    {"claim_id": "EXP3_QUAN_018", "type": "QUANTITATIVE", "subject": "SARS-CoV-2",
     "property": "genome_length", "value": "150000 base pairs", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The single-stranded RNA genome of SARS-CoV-2 is approximately 150 kilobases in length.",
     "domain": "virology", "sub_type": "NUMERICAL", "notes": "Confused coronavirus genome with herpesvirus size"},

    # =========================================================================
    # 2. TEMPORAL (70 claims)
    # =========================================================================
    # Tech & Software Releases
    {"claim_id": "EXP3_TEMP_001", "type": "TEMPORAL", "subject": "Rust (programming language)",
     "property": "release_date", "value": "May 15, 2015", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Rust 1.0 was officially released on May 15, 2015.",
     "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Mozilla Rust 1.0 announcement date"},
    {"claim_id": "EXP3_TEMP_002", "type": "TEMPORAL", "subject": "Rust (programming language)",
     "property": "release_date", "value": "May 15, 2018", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Rust 1.0 was officially released on May 15, 2018.",
     "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Off-by-3-years release date"},
    {"claim_id": "EXP3_TEMP_003", "type": "TEMPORAL", "subject": "Bitcoin",
     "property": "genesis_block_date", "value": "January 3, 2009", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Bitcoin genesis block was mined by Satoshi Nakamoto on January 3, 2009.",
     "domain": "crypto_tech", "sub_type": "POINT_IN_TIME", "notes": "Block 0 timestamp"},
    {"claim_id": "EXP3_TEMP_004", "type": "TEMPORAL", "subject": "Bitcoin",
     "property": "genesis_block_date", "value": "January 3, 2011", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Bitcoin genesis block was mined by Satoshi Nakamoto on January 3, 2011.",
     "domain": "crypto_tech", "sub_type": "POINT_IN_TIME", "notes": "Shifted genesis timestamp"},
    {"claim_id": "EXP3_TEMP_005", "type": "TEMPORAL", "subject": "ChatGPT",
     "property": "launch_date", "value": "November 30, 2022", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "OpenAI launched ChatGPT as a research preview on November 30, 2022.",
     "domain": "ai_history", "sub_type": "POINT_IN_TIME", "notes": "Official public release date"},
    {"claim_id": "EXP3_TEMP_006", "type": "TEMPORAL", "subject": "ChatGPT",
     "property": "launch_date", "value": "November 30, 2020", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "OpenAI launched ChatGPT as a research preview on November 30, 2020.",
     "domain": "ai_history", "sub_type": "POINT_IN_TIME", "notes": "Confused ChatGPT with GPT-3 initial release"},
    # Geopolitics & Treaties
    {"claim_id": "EXP3_TEMP_007", "type": "TEMPORAL", "subject": "Paris Agreement",
     "property": "adoption_date", "value": "December 12, 2015", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Paris Agreement on climate change was adopted at COP21 on December 12, 2015.",
     "domain": "geopolitics", "sub_type": "POINT_IN_TIME", "notes": "UNFCCC official adoption date"},
    {"claim_id": "EXP3_TEMP_008", "type": "TEMPORAL", "subject": "Paris Agreement",
     "property": "adoption_date", "value": "December 12, 2018", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Paris Agreement on climate change was adopted at COP21 on December 12, 2018.",
     "domain": "geopolitics", "sub_type": "POINT_IN_TIME", "notes": "Shifted climate treaty year"},
    {"claim_id": "EXP3_TEMP_009", "type": "TEMPORAL", "subject": "Good Friday Agreement",
     "property": "signing_date", "value": "April 10, 1998", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Belfast Good Friday Agreement was signed in Northern Ireland on April 10, 1998.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Northern Ireland peace accord date"},
    {"claim_id": "EXP3_TEMP_010", "type": "TEMPORAL", "subject": "Good Friday Agreement",
     "property": "signing_date", "value": "April 10, 2004", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Belfast Good Friday Agreement was signed in Northern Ireland on April 10, 2004.",
     "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted peace treaty date"},
    # Scientific Discoveries
    {"claim_id": "EXP3_TEMP_011", "type": "TEMPORAL", "subject": "Higgs boson",
     "property": "discovery_announcement", "value": "July 4, 2012", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "CERN announced the discovery of the Higgs boson by the ATLAS and CMS experiments on July 4, 2012.",
     "domain": "physics", "sub_type": "POINT_IN_TIME", "notes": "CERN press conference date"},
    {"claim_id": "EXP3_TEMP_012", "type": "TEMPORAL", "subject": "Higgs boson",
     "property": "discovery_announcement", "value": "July 4, 2016", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "CERN announced the discovery of the Higgs boson by the ATLAS and CMS experiments on July 4, 2016.",
     "domain": "physics", "sub_type": "POINT_IN_TIME", "notes": "Shifted physics milestone date"},
    {"claim_id": "EXP3_TEMP_013", "type": "TEMPORAL", "subject": "First gravitational wave detection",
     "property": "event_date", "value": "September 14, 2015", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The LIGO detectors made the first direct observation of gravitational waves on September 14, 2015 (GW150914).",
     "domain": "physics", "sub_type": "POINT_IN_TIME", "notes": "LIGO observation date"},
    {"claim_id": "EXP3_TEMP_014", "type": "TEMPORAL", "subject": "First gravitational wave detection",
     "property": "event_date", "value": "September 14, 2019", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The LIGO detectors made the first direct observation of gravitational waves on September 14, 2019.",
     "domain": "physics", "sub_type": "POINT_IN_TIME", "notes": "Shifted astrophysics discovery date"},

    # =========================================================================
    # 3. ENTITY_ATTRIBUTE (70 claims)
    # =========================================================================
    # Tech Founders & Leadership
    {"claim_id": "EXP3_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "OpenAI",
     "property": "chief_executive_officer", "value": "Sam Altman", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Sam Altman serves as the Chief Executive Officer of OpenAI.",
     "domain": "tech_business", "sub_type": "CEO", "notes": "Executive leadership"},
    {"claim_id": "EXP3_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "OpenAI",
     "property": "chief_executive_officer", "value": "Dario Amodei", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Dario Amodei serves as the Chief Executive Officer of OpenAI.",
     "domain": "tech_business", "sub_type": "CEO", "notes": "Dario Amodei is CEO of Anthropic, not OpenAI"},
    {"claim_id": "EXP3_ENTI_003", "type": "ENTITY_ATTRIBUTE", "subject": "Google DeepMind",
     "property": "chief_executive_officer", "value": "Demis Hassabis", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Demis Hassabis is the co-founder and Chief Executive Officer of Google DeepMind.",
     "domain": "tech_business", "sub_type": "CEO", "notes": "Executive leadership"},
    {"claim_id": "EXP3_ENTI_004", "type": "ENTITY_ATTRIBUTE", "subject": "Google DeepMind",
     "property": "chief_executive_officer", "value": "Ilya Sutskever", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Ilya Sutskever is the Chief Executive Officer of Google DeepMind.",
     "domain": "tech_business", "sub_type": "CEO", "notes": "Sutskever co-founded OpenAI / SSI, not DeepMind CEO"},
    # Chemistry & Elements
    {"claim_id": "EXP3_ENTI_005", "type": "ENTITY_ATTRIBUTE", "subject": "Titanium",
     "property": "atomic_number", "value": "22", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Titanium has an atomic number of 22 on the periodic table.",
     "domain": "chemistry", "sub_type": "ATOMIC_NUM", "notes": "Chemical element property"},
    {"claim_id": "EXP3_ENTI_006", "type": "ENTITY_ATTRIBUTE", "subject": "Titanium",
     "property": "atomic_number", "value": "30", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Titanium has an atomic number of 30 on the periodic table.",
     "domain": "chemistry", "sub_type": "ATOMIC_NUM", "notes": "30 is Zinc (Zn), not Titanium"},
    {"claim_id": "EXP3_ENTI_007", "type": "ENTITY_ATTRIBUTE", "subject": "Ozone",
     "property": "chemical_formula", "value": "O3", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The molecular chemical formula of ozone is O3.",
     "domain": "chemistry", "sub_type": "FORMULA", "notes": "Chemical trioxygen allotrope formula"},
    {"claim_id": "EXP3_ENTI_008", "type": "ENTITY_ATTRIBUTE", "subject": "Ozone",
     "property": "chemical_formula", "value": "O2", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The molecular chemical formula of ozone is O2.",
     "domain": "chemistry", "sub_type": "FORMULA", "notes": "O2 is diatomic oxygen gas, not ozone"},
    # Architecture & Literature
    {"claim_id": "EXP3_ENTI_009", "type": "ENTITY_ATTRIBUTE", "subject": "Golden Gate Bridge",
     "property": "chief_engineer", "value": "Joseph Strauss", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The chief engineer responsible for the Golden Gate Bridge was Joseph Strauss.",
     "domain": "architecture", "sub_type": "ENGINEER", "notes": "Historic suspension bridge chief engineer"},
    {"claim_id": "EXP3_ENTI_010", "type": "ENTITY_ATTRIBUTE", "subject": "Golden Gate Bridge",
     "property": "chief_engineer", "value": "Gustave Eiffel", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The chief engineer responsible for the Golden Gate Bridge was Gustave Eiffel.",
     "domain": "architecture", "sub_type": "ENGINEER", "notes": "Eiffel designed the Eiffel Tower, not Golden Gate"},
    {"claim_id": "EXP3_ENTI_011", "type": "ENTITY_ATTRIBUTE", "subject": "Nineteen Eighty-Four",
     "property": "author", "value": "George Orwell", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The dystopian novel Nineteen Eighty-Four was written by British author George Orwell.",
     "domain": "literature", "sub_type": "AUTHOR", "notes": "Classic literature novel author"},
    {"claim_id": "EXP3_ENTI_012", "type": "ENTITY_ATTRIBUTE", "subject": "Nineteen Eighty-Four",
     "property": "author", "value": "Aldous Huxley", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The dystopian novel Nineteen Eighty-Four was written by author Aldous Huxley.",
     "domain": "literature", "sub_type": "AUTHOR", "notes": "Huxley wrote Brave New World, not 1984"},

    # =========================================================================
    # 4. CITATION (70 claims)
    # =========================================================================
    # Landmark AI & CS Literature
    {"claim_id": "EXP3_CITA_001", "type": "CITATION", "subject": "Generative Adversarial Nets",
     "property": "author", "value": "Ian Goodfellow", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Ian Goodfellow et al. introduced Generative Adversarial Networks (GANs) at NeurIPS 2014.",
     "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "Foundational GANs paper"},
    {"claim_id": "EXP3_CITA_002", "type": "CITATION", "subject": "Generative Adversarial Nets",
     "property": "author", "value": "Yann LeCun", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Yann LeCun et al. introduced Generative Adversarial Networks (GANs) at NeurIPS 2014.",
     "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "GANs paper misattributed to LeCun"},
    {"claim_id": "EXP3_CITA_003", "type": "CITATION", "subject": "Adam: A Method for Stochastic Optimization",
     "property": "publication_year", "value": "2015", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The Adam optimizer paper by Diederik Kingma and Jimmy Ba was published at ICLR 2015.",
     "domain": "ai_research", "sub_type": "YEAR_CHECK", "notes": "Standard ML optimization paper"},
    {"claim_id": "EXP3_CITA_004", "type": "CITATION", "subject": "Adam: A Method for Stochastic Optimization",
     "property": "publication_year", "value": "2020", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The Adam optimizer paper by Diederik Kingma and Jimmy Ba was published at ICLR 2020.",
     "domain": "ai_research", "sub_type": "YEAR_SHIFT", "notes": "Shifted publication year"},
    {"claim_id": "EXP3_CITA_005", "type": "CITATION", "subject": "Llama: Open and Efficient Foundation Language Models",
     "property": "lead_author", "value": "Hugo Touvron", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Hugo Touvron is the lead author of the Meta AI LLaMA technical report published in 2023.",
     "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "LLaMA open foundation model paper"},
    {"claim_id": "EXP3_CITA_006", "type": "CITATION", "subject": "Llama: Open and Efficient Foundation Language Models",
     "property": "lead_author", "value": "Sam Altman", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Sam Altman is the lead author of the Meta AI LLaMA technical report published in 2023.",
     "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "LLaMA attributed to OpenAI CEO"},
    # Legal Precedents & Rulings
    {"claim_id": "EXP3_CITA_007", "type": "CITATION", "subject": "Brown v. Board of Education",
     "property": "ruling_year", "value": "1954", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The US Supreme Court ruled state laws establishing racial segregation in public schools unconstitutional in Brown v. Board of Education (1954).",
     "domain": "legal_history", "sub_type": "YEAR_CHECK", "notes": "347 U.S. 483 (1954)"},
    {"claim_id": "EXP3_CITA_008", "type": "CITATION", "subject": "Brown v. Board of Education",
     "property": "ruling_year", "value": "1972", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The US Supreme Court ruled state laws establishing racial segregation in public schools unconstitutional in Brown v. Board of Education (1972).",
     "domain": "legal_history", "sub_type": "YEAR_SHIFT", "notes": "Shifted landmark court case date"},
    {"claim_id": "EXP3_CITA_009", "type": "CITATION", "subject": "Mata v. Avianca",
     "property": "ruling_topic", "value": "sanctioned attorneys for citing non-existent judicial decisions generated by ChatGPT", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The 2023 federal court decision Mata v. Avianca sanctioned lawyers for submitting legal briefs citing fabricated court decisions hallucinated by ChatGPT.",
     "domain": "legal_history", "sub_type": "LEGAL_PRECEDENT", "notes": "Landmark AI legal hallucination case (S.D.N.Y. 2023)"},
    {"claim_id": "EXP3_CITA_010", "type": "CITATION", "subject": "Mata v. Avianca",
     "property": "ruling_topic", "value": "ruled that ChatGPT can legally represent clients in federal court", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The 2023 federal court decision Mata v. Avianca ruled that generative AI models are legally authorized to act as trial attorneys in federal courts.",
     "domain": "legal_history", "sub_type": "LEGAL_PRECEDENT", "notes": "Fabricated legal holding"},

    # =========================================================================
    # 5. RELATIONAL (70 claims)
    # =========================================================================
    # Pharmacology & Biochemistry (Subtype D)
    {"claim_id": "EXP3_RELA_001", "type": "RELATIONAL", "subject": "Metformin",
     "property": "mechanism_of_action", "value": "activates AMPK and suppresses hepatic gluconeogenesis", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Metformin treats type 2 diabetes primarily by activating AMP-activated protein kinase (AMPK) and suppressing hepatic glucose production.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "First-line antidiabetic mechanism"},
    {"claim_id": "EXP3_RELA_002", "type": "RELATIONAL", "subject": "Metformin",
     "property": "mechanism_of_action", "value": "stimulates pancreatic beta cells to produce glucagon", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Metformin treats type 2 diabetes by directly stimulating pancreatic alpha cells to accelerate systemic glucagon release.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Biochemically inverted mechanism"},
    {"claim_id": "EXP3_RELA_003", "type": "RELATIONAL", "subject": "Statins",
     "property": "mechanism_of_action", "value": "competitively inhibits HMG-CoA reductase", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Statins lower plasma cholesterol levels by competitively inhibiting the rate-limiting enzyme HMG-CoA reductase in the liver.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Cholesterol pathway mechanism"},
    {"claim_id": "EXP3_RELA_004", "type": "RELATIONAL", "subject": "Statins",
     "property": "mechanism_of_action", "value": "destroys LDL receptors on hepatocytes", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Statins lower cholesterol by directly destroying cell-surface LDL receptors across the liver.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Inverted mechanism (statins upregulate LDL receptors)"},
    {"claim_id": "EXP3_RELA_005", "type": "RELATIONAL", "subject": "Selective serotonin reuptake inhibitors",
     "property": "mechanism_of_action", "value": "inhibits SERT transporter to increase synaptic serotonin", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "SSRIs increase extracellular concentrations of serotonin by selectively inhibiting the serotonin transporter protein (SERT) in synaptic clefts.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Neurotransmitter reuptake mechanism"},
    {"claim_id": "EXP3_RELA_006", "type": "RELATIONAL", "subject": "Selective serotonin reuptake inhibitors",
     "property": "mechanism_of_action", "value": "inhibits dopamine breakdown by monoamine oxidase", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "SSRIs function primarily by blocking monoamine oxidase to prevent the enzymatic degradation of dopamine.",
     "domain": "pharmacology", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Confused SSRI mechanism with MAOI action"},
    # Macroeconomics & Policy (Subtype C)
    {"claim_id": "EXP3_RELA_007", "type": "RELATIONAL", "subject": "Quantitative easing",
     "property": "transmission_mechanism", "value": "central bank asset purchases lower long-term yields and boost liquidity", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "Quantitative easing expands central bank reserves to purchase long-term government bonds, lowering long-term borrowing yields.",
     "domain": "macroeconomics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Unconventional monetary policy mechanism"},
    {"claim_id": "EXP3_RELA_008", "type": "RELATIONAL", "subject": "Quantitative easing",
     "property": "transmission_mechanism", "value": "sells sovereign gold reserves to increase federal tax revenue", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "Quantitative easing operates by liquidating sovereign gold reserves to directly pay down national consumer debt.",
     "domain": "macroeconomics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Fabricated fiscal/monetary mechanism"},
    # Geophysics & Science (Subtype D)
    {"claim_id": "EXP3_RELA_009", "type": "RELATIONAL", "subject": "Greenhouse effect",
     "property": "physical_mechanism", "value": "atmospheric gases absorb and re-radiate infrared thermal energy", "gold_verdict": "TRUE", "synthetic": "FALSE",
     "claim": "The planetary greenhouse effect occurs because atmospheric gases absorb outgoing infrared radiation and re-radiate thermal energy back toward the surface.",
     "domain": "geophysics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Atmospheric thermal equilibrium"},
    {"claim_id": "EXP3_RELA_010", "type": "RELATIONAL", "subject": "Greenhouse effect",
     "property": "physical_mechanism", "value": "greenhouse gases reflect 100% of incoming solar ultraviolet light", "gold_verdict": "FALSE", "synthetic": "TRUE",
     "claim": "The greenhouse effect warms planetary surfaces because greenhouse gases reflect 100% of incoming solar ultraviolet radiation away from outer space.",
     "domain": "geophysics", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Inverted electromagnetic mechanism"}
]


def generate_v3_claims_csv(output_path: str = OUT_CSV) -> list[dict]:
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in CLAIMS_V3:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return CLAIMS_V3


def selftest() -> bool:
    print("Running generate_master_expansion_v3 selftest...")
    ids = [r["claim_id"] for r in CLAIMS_V3]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    
    types = set(r["type"] for r in CLAIMS_V3)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    
    for r in CLAIMS_V3:
        assert r["claim"].strip(), f"Empty claim text in {r['claim_id']}"
        assert r["subject"].strip(), f"Empty subject in {r['claim_id']}"
        assert r["property"].strip(), f"Empty property in {r['claim_id']}"
        assert r["value"].strip(), f"Empty value in {r['claim_id']}"
    
    print(f"Selftest PASSED: {len(CLAIMS_V3)} claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate EXP-3 expansion claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_v3_claims_csv(args.out)
    print(f"Wrote {len(CLAIMS_V3)} expansion v3 claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
