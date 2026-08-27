#!/usr/bin/env python3
"""
HalDetect — Real-World Query Expansion Generator (EXP_* Dataset)
===============================================================

Generates a dense, realistic, multi-domain evaluation suite (EXP_* claims)
mirroring actual user queries to LLMs across 5 modalities:
  1. QUANTITATIVE     (tech specs, financial earnings, infrastructure, sports)
  2. TEMPORAL         (tech releases, treaties, space/history milestones, lifecycles)
  3. ENTITY_ATTRIBUTE (founders/CEOs, chemical formulas, architecture, literature)
  4. CITATION         (landmark AI papers, global reports, legal cases, phantoms)
  5. RELATIONAL       (drug mechanisms, macroeconomics, historical causality, A-E)
"""

from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "expansion_realworld_claims.csv")

# =============================================================================
# DATA DEFINITIONS
# =============================================================================

EXPANSION_CLAIMS = [
    # -------------------------------------------------------------------------
    # 1. QUANTITATIVE (Hardware, Finance, Infrastructure, Aviation, Physics)
    # -------------------------------------------------------------------------
    {
        "claim_id": "EXP_QUAN_001", "type": "QUANTITATIVE", "subject": "NVIDIA GeForce RTX 4090",
        "property": "vram_capacity", "value": "24 GB", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The NVIDIA GeForce RTX 4090 graphics card has 24 GB of GDDR6X VRAM.",
        "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Standard tech specification query"
    },
    {
        "claim_id": "EXP_QUAN_002", "type": "QUANTITATIVE", "subject": "NVIDIA GeForce RTX 4090",
        "property": "vram_capacity", "value": "32 GB", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The NVIDIA GeForce RTX 4090 graphics card has 32 GB of GDDR6X VRAM.",
        "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Plausible wrong spec hallucination (+33% scale)"
    },
    {
        "claim_id": "EXP_QUAN_003", "type": "QUANTITATIVE", "subject": "Apple M2 Ultra",
        "property": "transistor_count", "value": "134 billion", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Apple M2 Ultra system-on-chip contains 134 billion transistors.",
        "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Official Apple architecture specification"
    },
    {
        "claim_id": "EXP_QUAN_004", "type": "QUANTITATIVE", "subject": "Apple M2 Ultra",
        "property": "transistor_count", "value": "250 billion", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Apple M2 Ultra system-on-chip contains 250 billion transistors.",
        "domain": "tech_hardware", "sub_type": "NUMERICAL", "notes": "Hallucinated transistor scale error"
    },
    {
        "claim_id": "EXP_QUAN_005", "type": "QUANTITATIVE", "subject": "PlayStation 5",
        "property": "storage_capacity", "value": "825 GB", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The original PlayStation 5 console launched with a custom 825 GB internal SSD.",
        "domain": "consumer_tech", "sub_type": "NUMERICAL", "notes": "Non-standard custom storage size"
    },
    {
        "claim_id": "EXP_QUAN_006", "type": "QUANTITATIVE", "subject": "PlayStation 5",
        "property": "storage_capacity", "value": "1000 GB", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The original PlayStation 5 console launched with a standard 1000 GB internal SSD.",
        "domain": "consumer_tech", "sub_type": "NUMERICAL", "notes": "Common rounding assumption hallucination"
    },
    {
        "claim_id": "EXP_QUAN_007", "type": "QUANTITATIVE", "subject": "Apple Inc.",
        "property": "revenue_q4_2023", "value": "89.5 billion USD", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Apple reported revenue of $89.5 billion for its fiscal 2023 fourth quarter.",
        "domain": "corporate_finance", "sub_type": "COMPUTATIONAL", "notes": "SEC Form 10-K reported quarterly revenue"
    },
    {
        "claim_id": "EXP_QUAN_008", "type": "QUANTITATIVE", "subject": "Apple Inc.",
        "property": "revenue_q4_2023", "value": "105.2 billion USD", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Apple reported revenue of $105.2 billion for its fiscal 2023 fourth quarter.",
        "domain": "corporate_finance", "sub_type": "COMPUTATIONAL", "notes": "Confused Q4 with holiday Q1 revenue"
    },
    {
        "claim_id": "EXP_QUAN_009", "type": "QUANTITATIVE", "subject": "Tesla, Inc.",
        "property": "vehicle_deliveries_2023", "value": "1.81 million", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Tesla delivered 1.81 million electric vehicles globally in 2023.",
        "domain": "corporate_finance", "sub_type": "NUMERICAL", "notes": "Annual production and delivery disclosure"
    },
    {
        "claim_id": "EXP_QUAN_010", "type": "QUANTITATIVE", "subject": "Tesla, Inc.",
        "property": "vehicle_deliveries_2023", "value": "2.5 million", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Tesla delivered 2.5 million electric vehicles globally in 2023.",
        "domain": "corporate_finance", "sub_type": "NUMERICAL", "notes": "Overstated delivery target hallucination"
    },
    {
        "claim_id": "EXP_QUAN_011", "type": "QUANTITATIVE", "subject": "Burj Khalifa",
        "property": "height", "value": "828 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Burj Khalifa in Dubai stands at an architectural height of 828 meters.",
        "domain": "architecture", "sub_type": "NUMERICAL", "notes": "Official Council on Tall Buildings height"
    },
    {
        "claim_id": "EXP_QUAN_012", "type": "QUANTITATIVE", "subject": "Burj Khalifa",
        "property": "height", "value": "912 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Burj Khalifa in Dubai stands at an architectural height of 912 meters.",
        "domain": "architecture", "sub_type": "NUMERICAL", "notes": "Overstated architectural height"
    },
    {
        "claim_id": "EXP_QUAN_013", "type": "QUANTITATIVE", "subject": "Tokyo Skytree",
        "property": "height", "value": "634 meters", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Tokyo Skytree reaches a total height of 634 meters.",
        "domain": "architecture", "sub_type": "NUMERICAL", "notes": "Symbolic height (6-3-4 = Musashi)"
    },
    {
        "claim_id": "EXP_QUAN_014", "type": "QUANTITATIVE", "subject": "Tokyo Skytree",
        "property": "height", "value": "555 meters", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Tokyo Skytree reaches a total height of 555 meters.",
        "domain": "architecture", "sub_type": "NUMERICAL", "notes": "Confused with Lotte World Tower height"
    },
    {
        "claim_id": "EXP_QUAN_015", "type": "QUANTITATIVE", "subject": "Channel Tunnel",
        "property": "length", "value": "50.45 kilometers", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Channel Tunnel linking the UK and France has a total length of 50.45 kilometers.",
        "domain": "infrastructure", "sub_type": "NUMERICAL", "notes": "Exact undersea infrastructure length"
    },
    {
        "claim_id": "EXP_QUAN_016", "type": "QUANTITATIVE", "subject": "Channel Tunnel",
        "property": "length", "value": "32.5 kilometers", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Channel Tunnel linking the UK and France has a total length of 32.5 kilometers.",
        "domain": "infrastructure", "sub_type": "NUMERICAL", "notes": "Confused total length with undersea portion"
    },
    {
        "claim_id": "EXP_QUAN_017", "type": "QUANTITATIVE", "subject": "Wembley Stadium",
        "property": "seating_capacity", "value": "90000", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Wembley Stadium in London has an official seating capacity of 90,000.",
        "domain": "sports", "sub_type": "NUMERICAL", "notes": "Official stadium capacity"
    },
    {
        "claim_id": "EXP_QUAN_018", "type": "QUANTITATIVE", "subject": "Wembley Stadium",
        "property": "seating_capacity", "value": "115000", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Wembley Stadium in London has an official seating capacity of 115,000.",
        "domain": "sports", "sub_type": "NUMERICAL", "notes": "Exaggerated stadium capacity"
    },
    {
        "claim_id": "EXP_QUAN_019", "type": "QUANTITATIVE", "subject": "Boeing 787-9",
        "property": "maximum_range", "value": "14140 kilometers", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Boeing 787-9 Dreamliner has a maximum flight range of 14,140 kilometers.",
        "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Official Boeing commercial range spec"
    },
    {
        "claim_id": "EXP_QUAN_020", "type": "QUANTITATIVE", "subject": "Boeing 787-9",
        "property": "maximum_range", "value": "18500 kilometers", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Boeing 787-9 Dreamliner has a maximum flight range of 18,500 kilometers.",
        "domain": "aviation", "sub_type": "NUMERICAL", "notes": "Confused range spec"
    },
    {
        "claim_id": "EXP_QUAN_021", "type": "QUANTITATIVE", "subject": "Speed of light",
        "property": "vacuum_speed", "value": "299792458 m/s", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The speed of light in vacuum is exactly 299,792,458 meters per second.",
        "domain": "physics", "sub_type": "NUMERICAL", "notes": "SI standard physical constant"
    },
    {
        "claim_id": "EXP_QUAN_022", "type": "QUANTITATIVE", "subject": "Speed of light",
        "property": "vacuum_speed", "value": "340000000 m/s", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The speed of light in vacuum is exactly 340,000,000 meters per second.",
        "domain": "physics", "sub_type": "NUMERICAL", "notes": "Wrong magnitude hallucination"
    },
    {
        "claim_id": "EXP_QUAN_023", "type": "QUANTITATIVE", "subject": "Bitcoin",
        "property": "maximum_supply", "value": "21 million", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Bitcoin protocol mathematically caps the total supply at 21 million coins.",
        "domain": "crypto_tech", "sub_type": "NUMERICAL", "notes": "Protocol consensus rule"
    },
    {
        "claim_id": "EXP_QUAN_024", "type": "QUANTITATIVE", "subject": "Bitcoin",
        "property": "maximum_supply", "value": "100 million", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Bitcoin protocol mathematically caps the total supply at 100 million coins.",
        "domain": "crypto_tech", "sub_type": "NUMERICAL", "notes": "Confused cap error"
    },

    # -------------------------------------------------------------------------
    # 2. TEMPORAL (Releases, Treaties, Milestones, History)
    # -------------------------------------------------------------------------
    {
        "claim_id": "EXP_TEMP_001", "type": "TEMPORAL", "subject": "Python (programming language)",
        "property": "release_date", "value": "December 3, 2008", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Python 3.0 was officially released on December 3, 2008.",
        "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Major language release date"
    },
    {
        "claim_id": "EXP_TEMP_002", "type": "TEMPORAL", "subject": "Python (programming language)",
        "property": "release_date", "value": "December 3, 2012", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Python 3.0 was officially released on December 3, 2012.",
        "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Off-by-4-years release hallucination"
    },
    {
        "claim_id": "EXP_TEMP_003", "type": "TEMPORAL", "subject": "Linux kernel",
        "property": "inception_date", "value": "September 17, 1991", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Linus Torvalds released the initial Linux kernel version 0.01 on September 17, 1991.",
        "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Initial release date"
    },
    {
        "claim_id": "EXP_TEMP_004", "type": "TEMPORAL", "subject": "Linux kernel",
        "property": "inception_date", "value": "September 17, 1996", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Linus Torvalds released the initial Linux kernel version 0.01 on September 17, 1996.",
        "domain": "software_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted origin date error"
    },
    {
        "claim_id": "EXP_TEMP_005", "type": "TEMPORAL", "subject": "iPhone",
        "property": "announcement_date", "value": "January 9, 2007", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Steve Jobs announced the original iPhone during Macworld on January 9, 2007.",
        "domain": "consumer_tech", "sub_type": "POINT_IN_TIME", "notes": "Keynote date"
    },
    {
        "claim_id": "EXP_TEMP_006", "type": "TEMPORAL", "subject": "iPhone",
        "property": "announcement_date", "value": "January 9, 2009", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Steve Jobs announced the original iPhone during Macworld on January 9, 2009.",
        "domain": "consumer_tech", "sub_type": "POINT_IN_TIME", "notes": "Off-by-two-years hardware launch"
    },
    {
        "claim_id": "EXP_TEMP_007", "type": "TEMPORAL", "subject": "Kyoto Protocol",
        "property": "adoption_date", "value": "December 11, 1997", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Kyoto Protocol climate agreement was adopted on December 11, 1997 in Kyoto, Japan.",
        "domain": "geopolitics", "sub_type": "POINT_IN_TIME", "notes": "UNFCCC adoption date"
    },
    {
        "claim_id": "EXP_TEMP_008", "type": "TEMPORAL", "subject": "Kyoto Protocol",
        "property": "adoption_date", "value": "December 11, 2003", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Kyoto Protocol climate agreement was adopted on December 11, 2003 in Kyoto, Japan.",
        "domain": "geopolitics", "sub_type": "POINT_IN_TIME", "notes": "Shifted treaty adoption year"
    },
    {
        "claim_id": "EXP_TEMP_009", "type": "TEMPORAL", "subject": "Maastricht Treaty",
        "property": "signing_date", "value": "February 7, 1992", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Maastricht Treaty creating the European Union was signed on February 7, 1992.",
        "domain": "geopolitics", "sub_type": "POINT_IN_TIME", "notes": "Foundational EU treaty date"
    },
    {
        "claim_id": "EXP_TEMP_010", "type": "TEMPORAL", "subject": "Maastricht Treaty",
        "property": "signing_date", "value": "February 7, 1999", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Maastricht Treaty creating the European Union was signed on February 7, 1999.",
        "domain": "geopolitics", "sub_type": "POINT_IN_TIME", "notes": "Confused treaty signing with Euro introduction"
    },
    {
        "claim_id": "EXP_TEMP_011", "type": "TEMPORAL", "subject": "Apollo 11",
        "property": "landing_date", "value": "July 20, 1969", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Apollo 11 Lunar Module touched down on the Moon on July 20, 1969.",
        "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "NASA lunar landing date"
    },
    {
        "claim_id": "EXP_TEMP_012", "type": "TEMPORAL", "subject": "Apollo 11",
        "property": "landing_date", "value": "July 20, 1972", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Apollo 11 Lunar Module touched down on the Moon on July 20, 1972.",
        "domain": "space_history", "sub_type": "POINT_IN_TIME", "notes": "Confused Apollo 11 with Apollo 17"
    },
    {
        "claim_id": "EXP_TEMP_013", "type": "TEMPORAL", "subject": "Fall of the Berlin Wall",
        "property": "event_date", "value": "November 9, 1989", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Berlin Wall was opened and began to fall on November 9, 1989.",
        "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Cold war landmark date"
    },
    {
        "claim_id": "EXP_TEMP_014", "type": "TEMPORAL", "subject": "Fall of the Berlin Wall",
        "property": "event_date", "value": "November 9, 1991", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Berlin Wall was opened and began to fall on November 9, 1991.",
        "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Confused Wall fall with USSR dissolution"
    },
    {
        "claim_id": "EXP_TEMP_015", "type": "TEMPORAL", "subject": "Chernobyl disaster",
        "property": "event_date", "value": "April 26, 1986", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Chernobyl nuclear disaster occurred at Reactor No. 4 on April 26, 1986.",
        "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Nuclear accident date"
    },
    {
        "claim_id": "EXP_TEMP_016", "type": "TEMPORAL", "subject": "Chernobyl disaster",
        "property": "event_date", "value": "April 26, 1989", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Chernobyl nuclear disaster occurred at Reactor No. 4 on April 26, 1989.",
        "domain": "world_history", "sub_type": "POINT_IN_TIME", "notes": "Shifted accident year"
    },

    # -------------------------------------------------------------------------
    # 3. ENTITY_ATTRIBUTE (Tech, Science, Architecture, Culture)
    # -------------------------------------------------------------------------
    {
        "claim_id": "EXP_ENTI_001", "type": "ENTITY_ATTRIBUTE", "subject": "Stripe, Inc.",
        "property": "founder", "value": "Patrick Collison | John Collison", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Stripe was founded by brothers Patrick Collison and John Collison.",
        "domain": "tech_business", "sub_type": "FOUNDER", "notes": "Fintech company founders"
    },
    {
        "claim_id": "EXP_ENTI_002", "type": "ENTITY_ATTRIBUTE", "subject": "Stripe, Inc.",
        "property": "founder", "value": "Peter Thiel", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Stripe was founded by PayPal co-founder Peter Thiel.",
        "domain": "tech_business", "sub_type": "FOUNDER", "notes": "Thiel was an early investor, not founder"
    },
    {
        "claim_id": "EXP_ENTI_003", "type": "ENTITY_ATTRIBUTE", "subject": "Nvidia",
        "property": "chief_executive_officer", "value": "Jensen Huang", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Jensen Huang serves as the Chief Executive Officer of Nvidia.",
        "domain": "tech_business", "sub_type": "CEO", "notes": "Founder and current CEO"
    },
    {
        "claim_id": "EXP_ENTI_004", "type": "ENTITY_ATTRIBUTE", "subject": "Nvidia",
        "property": "chief_executive_officer", "value": "Lisa Su", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Lisa Su serves as the Chief Executive Officer of Nvidia.",
        "domain": "tech_business", "sub_type": "CEO", "notes": "Lisa Su is CEO of competitor AMD"
    },
    {
        "claim_id": "EXP_ENTI_005", "type": "ENTITY_ATTRIBUTE", "subject": "Glucose",
        "property": "chemical_formula", "value": "C6H12O6", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The molecular chemical formula for glucose is C6H12O6.",
        "domain": "chemistry", "sub_type": "FORMULA", "notes": "Standard biochemical formula"
    },
    {
        "claim_id": "EXP_ENTI_006", "type": "ENTITY_ATTRIBUTE", "subject": "Glucose",
        "property": "chemical_formula", "value": "C12H22O11", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The molecular chemical formula for glucose is C12H22O11.",
        "domain": "chemistry", "sub_type": "FORMULA", "notes": "C12H22O11 is sucrose, not glucose"
    },
    {
        "claim_id": "EXP_ENTI_007", "type": "ENTITY_ATTRIBUTE", "subject": "Gold",
        "property": "atomic_number", "value": "79", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Gold has an atomic number of 79 on the periodic table.",
        "domain": "chemistry", "sub_type": "ATOMIC_NUM", "notes": "Standard elemental property"
    },
    {
        "claim_id": "EXP_ENTI_008", "type": "ENTITY_ATTRIBUTE", "subject": "Gold",
        "property": "atomic_number", "value": "47", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Gold has an atomic number of 47 on the periodic table.",
        "domain": "chemistry", "sub_type": "ATOMIC_NUM", "notes": "47 is Silver, not Gold"
    },
    {
        "claim_id": "EXP_ENTI_009", "type": "ENTITY_ATTRIBUTE", "subject": "Sydney Opera House",
        "property": "architect", "value": "Jørn Utzon", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Sydney Opera House in Australia was designed by Danish architect Jørn Utzon.",
        "domain": "architecture", "sub_type": "ARCHITECT", "notes": "Pritzker Prize landmark architect"
    },
    {
        "claim_id": "EXP_ENTI_010", "type": "ENTITY_ATTRIBUTE", "subject": "Sydney Opera House",
        "property": "architect", "value": "Frank Gehry", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Sydney Opera House in Australia was designed by architect Frank Gehry.",
        "domain": "architecture", "sub_type": "ARCHITECT", "notes": "Gehry designed Bilbao Guggenheim"
    },
    {
        "claim_id": "EXP_ENTI_011", "type": "ENTITY_ATTRIBUTE", "subject": "Dune (novel)",
        "property": "author", "value": "Frank Herbert", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The science fiction epic Dune was written by American author Frank Herbert.",
        "domain": "literature", "sub_type": "AUTHOR", "notes": "Classic literature author"
    },
    {
        "claim_id": "EXP_ENTI_012", "type": "ENTITY_ATTRIBUTE", "subject": "Dune (novel)",
        "property": "author", "value": "Isaac Asimov", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The science fiction epic Dune was written by American author Isaac Asimov.",
        "domain": "literature", "sub_type": "AUTHOR", "notes": "Asimov wrote Foundation, not Dune"
    },

    # -------------------------------------------------------------------------
    # 4. CITATION (Landmark Papers, Reports, Phantoms)
    # -------------------------------------------------------------------------
    {
        "claim_id": "EXP_CITA_001", "type": "CITATION", "subject": "Attention Is All You Need",
        "property": "publication_year", "value": "2017", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The paper 'Attention Is All You Need' by Vaswani et al. was published in NeurIPS 2017.",
        "domain": "ai_research", "sub_type": "YEAR_CHECK", "notes": "Foundational Transformer paper citation"
    },
    {
        "claim_id": "EXP_CITA_002", "type": "CITATION", "subject": "Attention Is All You Need",
        "property": "publication_year", "value": "2021", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The paper 'Attention Is All You Need' by Vaswani et al. was published in NeurIPS 2021.",
        "domain": "ai_research", "sub_type": "YEAR_SHIFT", "notes": "Plausible +4 years shifted citation"
    },
    {
        "claim_id": "EXP_CITA_003", "type": "CITATION", "subject": "BERT: Pre-training of Deep Bidirectional Transformers",
        "property": "author", "value": "Jacob Devlin", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Jacob Devlin is the lead author of the BERT paper published at NAACL 2019.",
        "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "Lead author of BERT"
    },
    {
        "claim_id": "EXP_CITA_004", "type": "CITATION", "subject": "BERT: Pre-training of Deep Bidirectional Transformers",
        "property": "author", "value": "Yann LeCun", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Yann LeCun is the lead author of the BERT paper published at NAACL 2019.",
        "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "Author swap with another famous AI researcher"
    },
    {
        "claim_id": "EXP_CITA_005", "type": "CITATION", "subject": "Deep Residual Learning for Image Recognition",
        "property": "author", "value": "Kaiming He", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The ResNet paper 'Deep Residual Learning for Image Recognition' was authored by Kaiming He et al. (CVPR 2016).",
        "domain": "ai_research", "sub_type": "AUTHOR_CHECK", "notes": "ResNet landmark paper"
    },
    {
        "claim_id": "EXP_CITA_006", "type": "CITATION", "subject": "Deep Residual Learning for Image Recognition",
        "property": "author", "value": "Geoffrey Hinton", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The ResNet paper 'Deep Residual Learning for Image Recognition' was authored by Geoffrey Hinton et al. (CVPR 2016).",
        "domain": "ai_research", "sub_type": "AUTHOR_SWAP", "notes": "ResNet attributed to Hinton error"
    },
    {
        "claim_id": "EXP_CITA_007", "type": "CITATION", "subject": "Quantum Transformer Dynamics",
        "property": "publisher", "value": "Nature Machine Intelligence", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The landmark paper 'Quantum Transformer Dynamics' by A. Sterling was published in Nature Machine Intelligence in 2023.",
        "domain": "ai_research", "sub_type": "PHANTOM_CITATION", "notes": "100% fabricated paper title and author"
    },
    {
        "claim_id": "EXP_CITA_008", "type": "CITATION", "subject": "Autonomous Molecular Alignment Networks",
        "property": "publisher", "value": "Science", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The 2022 Science study 'Autonomous Molecular Alignment Networks' by Dr. Elena Rostova proved zero-shot folding.",
        "domain": "ai_research", "sub_type": "PHANTOM_CITATION", "notes": "Fabricated molecular biology paper"
    },
    {
        "claim_id": "EXP_CITA_009", "type": "CITATION", "subject": "IPCC Sixth Assessment Report",
        "property": "publisher", "value": "Intergovernmental Panel on Climate Change", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "The Sixth Assessment Report (AR6) was published by the Intergovernmental Panel on Climate Change (IPCC).",
        "domain": "climate_policy", "sub_type": "PUBLISHER", "notes": "Official institutional publisher"
    },
    {
        "claim_id": "EXP_CITA_010", "type": "CITATION", "subject": "IPCC Sixth Assessment Report",
        "property": "publisher", "value": "World Bank", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "The Sixth Assessment Report (AR6) on global warming was published by the World Bank.",
        "domain": "climate_policy", "sub_type": "PUBLISHER_SWAP", "notes": "Institutional attribution error"
    },

    # -------------------------------------------------------------------------
    # 5. RELATIONAL (Medical, Macroeconomics, Geochemistry, History A-E)
    # -------------------------------------------------------------------------
    {
        "claim_id": "EXP_RELA_001", "type": "RELATIONAL", "subject": "ACE inhibitors",
        "property": "mechanism_of_action", "value": "inhibits conversion of angiotensin I to angiotensin II", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "ACE inhibitors lower blood pressure by preventing the conversion of angiotensin I to angiotensin II, causing vasodilation.",
        "domain": "medicine", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Biochemical mechanism of action"
    },
    {
        "claim_id": "EXP_RELA_002", "type": "RELATIONAL", "subject": "ACE inhibitors",
        "property": "mechanism_of_action", "value": "stimulates angiotensin II receptors", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "ACE inhibitors lower blood pressure by directly stimulating angiotensin II receptors in smooth muscle.",
        "domain": "medicine", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Opposite mechanism hallucination"
    },
    {
        "claim_id": "EXP_RELA_003", "type": "RELATIONAL", "subject": "mRNA vaccines",
        "property": "mechanism_of_action", "value": "instructs cells to produce harmless viral spike protein", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "mRNA vaccines work by delivering genetic instructions to host cells to transiently produce the viral spike protein, triggering immune response.",
        "domain": "medicine", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Immunology mechanism"
    },
    {
        "claim_id": "EXP_RELA_004", "type": "RELATIONAL", "subject": "mRNA vaccines",
        "property": "mechanism_of_action", "value": "integrates directly into host nuclear DNA", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "mRNA vaccines function by permanently integrating foreign viral sequences into the patient's nuclear genomic DNA.",
        "domain": "medicine", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Common scientific misinformation hallucination"
    },
    {
        "claim_id": "EXP_RELA_005", "type": "RELATIONAL", "subject": "Central bank interest rate hikes",
        "property": "economic_effect", "value": "increases borrowing costs to cool aggregate demand and inflation", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Raising central bank policy rates increases the cost of borrowing, which reduces consumer spending and business investment to moderate inflation.",
        "domain": "macroeconomics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Monetary policy transmission mechanism"
    },
    {
        "claim_id": "EXP_RELA_006", "type": "RELATIONAL", "subject": "Central bank interest rate hikes",
        "property": "economic_effect", "value": "directly lowers treasury bond yields and expands money supply", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Raising central bank policy rates directly expands the broad money supply and pushes government bond yields downward.",
        "domain": "macroeconomics", "sub_type": "SUBTYPE_C_PROCESS", "notes": "Inverted monetary mechanism"
    },
    {
        "claim_id": "EXP_RELA_007", "type": "RELATIONAL", "subject": "Ocean acidification",
        "property": "causal_mechanism", "value": "dissolved atmospheric CO2 forms carbonic acid", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Ocean acidification occurs because absorbed atmospheric carbon dioxide reacts with seawater to form carbonic acid, lowering ocean pH.",
        "domain": "environmental_science", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Geochemical reaction mechanism"
    },
    {
        "claim_id": "EXP_RELA_008", "type": "RELATIONAL", "subject": "Ocean acidification",
        "property": "causal_mechanism", "value": "agricultural nitrogen runoff reacts directly with salt", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Ocean acidification is primarily driven by agricultural nitrogen runoff reacting with sodium chloride in surface waters.",
        "domain": "environmental_science", "sub_type": "SUBTYPE_D_MECHANISM", "notes": "Confused ocean acidification with eutrophication"
    },
    {
        "claim_id": "EXP_RELA_009", "type": "RELATIONAL", "subject": "Printing press",
        "property": "historical_impact", "value": "rapidly disseminated vernacular religious texts across Europe", "gold_verdict": "TRUE", "synthetic": "FALSE",
        "claim": "Johannes Gutenberg's moveable-type printing press enabled the rapid dissemination of vernacular Bibles, accelerating the Protestant Reformation.",
        "domain": "history", "sub_type": "SUBTYPE_A_CAUSAL", "notes": "Historical causal connection"
    },
    {
        "claim_id": "EXP_RELA_010", "type": "RELATIONAL", "subject": "Printing press",
        "property": "historical_impact", "value": "was banned completely by all European monarchies for two centuries", "gold_verdict": "FALSE", "synthetic": "TRUE",
        "claim": "Following its invention, the printing press was successfully banned across all European monarchies until the late 18th century.",
        "domain": "history", "sub_type": "SUBTYPE_A_CAUSAL", "notes": "Counterfactual historical claim"
    }
]


def generate_claims_csv(output_path: str = OUT_CSV) -> list[dict]:
    """Writes the curated realistic expansion dataset to disk."""
    fieldnames = [
        "claim_id", "type", "subject", "property", "value",
        "gold_verdict", "synthetic", "claim", "domain",
        "sub_type", "notes"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in EXPANSION_CLAIMS:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
    return EXPANSION_CLAIMS


def selftest() -> bool:
    """Verifies dataset constraints, disjoint IDs, and balance."""
    print("Running generate_master_expansion selftest...")
    ids = [r["claim_id"] for r in EXPANSION_CLAIMS]
    assert len(ids) == len(set(ids)), f"Duplicate claim_ids found: {len(ids)} vs {len(set(ids))}"
    
    types = set(r["type"] for r in EXPANSION_CLAIMS)
    expected_types = {"QUANTITATIVE", "TEMPORAL", "ENTITY_ATTRIBUTE", "CITATION", "RELATIONAL"}
    assert types == expected_types, f"Missing types: {expected_types - types}"
    
    golds = [r["gold_verdict"] for r in EXPANSION_CLAIMS]
    assert "TRUE" in golds and "FALSE" in golds, "Missing TRUE/FALSE distribution"
    
    for r in EXPANSION_CLAIMS:
        assert r["claim"].strip(), f"Empty claim text in {r['claim_id']}"
        assert r["subject"].strip(), f"Empty subject in {r['claim_id']}"
        assert r["property"].strip(), f"Empty property in {r['claim_id']}"
        assert r["value"].strip(), f"Empty value in {r['claim_id']}"
    
    print(f"Selftest PASSED: {len(EXPANSION_CLAIMS)} claims verified across {len(types)} types.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate real-world query expansion claims.")
    parser.add_argument("--out", default=OUT_CSV, help="Output CSV path")
    parser.add_argument("--selftest", action="store_true", help="Run validation checks")
    args = parser.parse_args()

    if args.selftest:
        ok = selftest()
        return 0 if ok else 1

    generate_claims_csv(args.out)
    print(f"Wrote {len(EXPANSION_CLAIMS)} real-world expansion claims to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
