#!/usr/bin/env python3
"""
HalDetect -- 100 Adversarial "Stumper" Challenge Suite
=====================================================
A benchmark of 100 uniquely crafted adversarial claims across 9 failure taxonomies
specifically engineered to stress-test and expose edge cases, semantic traps,
homonym collisions, temporal state transitions, unit ambiguities, and NLI biases.

Taxonomies:
  1. Temporal State Transitions (Former vs Current)
  2. Entity Homonyms & Ambiguity (Name Collisions)
  3. Metric & Environmental Dependencies (Altitude, Boiling point, Refractive Index)
  4. Subtle Negation & Ordinal Mutations (First vs Second, Never vs Always)
  5. Chimeric Cross-Entity Swaps (Swapping directors, founders, authors)
  6. Scientific Misconceptions & Definitional Bounds (Herbs vs Trees, Glass states)
  7. Macroeconomic Revision & Denominator Clashes (Nominal vs PPP, Revisions)
  8. Citation & Venue Chimeras (Real authors + Real title + Fake journal)
  9. Polysemy & Hedged Bounds (Short tons vs Metric tonnes, Datum phrases)
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_CSV = HERE / "adversarial_stumpers_100.csv"

STUMPERS = [
    # ---------------------------------------------------------------------------
    # CATEGORY 1: Temporal State Transitions (Former vs Current) [12 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_001",
        "category": "Temporal State Transition",
        "claim": "Barack Obama is the President of the United States.",
        "subject": "Barack Obama",
        "property": "position held",
        "gold_verdict": "FALSE",
        "why_it_stumps": "P39 (position held) contains President of the US, but P582 (end time) was 2017. A present-tense predicate check sees Obama has Q11696 and falsely predicts TRUE if end-date is uninspected."
    },
    {
        "stumper_id": "STUMP_002",
        "category": "Temporal State Transition",
        "claim": "Queen Elizabeth II is the monarch of the United Kingdom.",
        "subject": "Queen Elizabeth II",
        "property": "position held",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Monarch until her death in Sept 2022. Verifier must check P570 (date of death) before verifying present-tense state."
    },
    {
        "stumper_id": "STUMP_003",
        "category": "Temporal State Transition",
        "claim": "Pluto is the ninth planet from the Sun.",
        "subject": "Pluto",
        "property": "instance of",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Historically classified as a planet (1930-2006); reclassified by IAU in 2006 as a dwarf planet (Q2199)."
    },
    {
        "stumper_id": "STUMP_004",
        "category": "Temporal State Transition",
        "claim": "Boris Johnson is the Prime Minister of the United Kingdom.",
        "subject": "Boris Johnson",
        "property": "position held",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Resigned in September 2022; succeeded by Liz Truss and Rishi Sunak."
    },
    {
        "stumper_id": "STUMP_005",
        "category": "Temporal State Transition",
        "claim": "Twitter headquarters is located at 1355 Market Street in San Francisco.",
        "subject": "Twitter",
        "property": "headquarters location",
        "gold_verdict": "FALSE",
        "why_it_stumps": "X Corp vacated the historic 1355 Market St San Francisco headquarters in 2024, relocating to Texas."
    },
    {
        "stumper_id": "STUMP_006",
        "category": "Temporal State Transition",
        "claim": "The United Kingdom is a member state of the European Union.",
        "subject": "United Kingdom",
        "property": "member of",
        "gold_verdict": "FALSE",
        "why_it_stumps": "UK was an EU member from 1973 until Brexit transition ended on Dec 31, 2020."
    },
    {
        "stumper_id": "STUMP_007",
        "category": "Temporal State Transition",
        "claim": "The Soviet Union has the largest nuclear arsenal in the world.",
        "subject": "Soviet Union",
        "property": "dissolved",
        "gold_verdict": "FALSE",
        "why_it_stumps": "USSR dissolved in December 1991; Russia is the successor state."
    },
    {
        "stumper_id": "STUMP_008",
        "category": "Temporal State Transition",
        "claim": "Angela Merkel is the Chancellor of Germany.",
        "subject": "Angela Merkel",
        "property": "position held",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Stepped down in December 2021; succeeded by Olaf Scholz."
    },
    {
        "stumper_id": "STUMP_009",
        "category": "Temporal State Transition",
        "claim": "Sundar Pichai was the CEO of Google in 2010.",
        "subject": "Sundar Pichai",
        "property": "chief executive officer",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Sundar Pichai became CEO of Google in 2015; Eric Schmidt was CEO in 2010."
    },
    {
        "stumper_id": "STUMP_010",
        "category": "Temporal State Transition",
        "claim": "The capital of Kazakhstan is Astana.",
        "subject": "Kazakhstan",
        "property": "capital",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Renamed to Nur-Sultan in 2019, then reverted back to Astana in September 2022. Triples change over time."
    },
    {
        "stumper_id": "STUMP_011",
        "category": "Temporal State Transition",
        "claim": "Croatia uses the Croatian kuna as its official currency.",
        "subject": "Croatia",
        "property": "currency",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Croatia adopted the Euro (EUR) on January 1, 2023, replacing the Kuna."
    },
    {
        "stumper_id": "STUMP_012",
        "category": "Temporal State Transition",
        "claim": "Sweden is a member state of NATO.",
        "subject": "Sweden",
        "property": "member of",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Sweden joined NATO on March 7, 2024 (Q32 entry). Static 2022 KGs mark this as unverified or false."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 2: Entity Homonyms & Ambiguity (Name Collisions) [12 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_013",
        "category": "Entity Ambiguity",
        "claim": "Michael Jordan is a professor of computer science at UC Berkeley.",
        "subject": "Michael Jordan",
        "property": "employer",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Entity linking collision with Michael Jordan the basketball player (Q41421). The scientist is Michael I. Jordan (Q3308285)."
    },
    {
        "stumper_id": "STUMP_014",
        "category": "Entity Ambiguity",
        "claim": "Paris has a population of fewer than 30,000 residents.",
        "subject": "Paris",
        "property": "population",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Paris, Texas (population ~25,000) vs Paris, France (population 2.1M). Entity resolution defaults to Paris, France."
    },
    {
        "stumper_id": "STUMP_015",
        "category": "Entity Ambiguity",
        "claim": "Apple was founded in London in 1968 by the Beatles.",
        "subject": "Apple",
        "property": "inception",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Apple Corps (Q210452) multimedia company vs Apple Inc. (Q312, Cupertino 1976). Linker almost always resolves to Apple Inc."
    },
    {
        "stumper_id": "STUMP_016",
        "category": "Entity Ambiguity",
        "claim": "Mercury has an atomic number of 80 and is a liquid metal.",
        "subject": "Mercury",
        "property": "atomic number",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Element Mercury (Q925) vs Planet Mercury (Q308) vs Freddie Mercury (Q15869)."
    },
    {
        "stumper_id": "STUMP_017",
        "category": "Entity Ambiguity",
        "claim": "Avatar was directed by M. Night Shyamalan in 2010.",
        "subject": "Avatar",
        "property": "director",
        "gold_verdict": "TRUE",
        "why_it_stumps": "The Last Airbender / Avatar film (2010) vs James Cameron's Avatar (2009). Linker will confuse Cameron and Shyamalan."
    },
    {
        "stumper_id": "STUMP_018",
        "category": "Entity Ambiguity",
        "claim": "Georgia is a member state of the European Union.",
        "subject": "Georgia",
        "property": "member of",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Georgia the country (Q230) vs Georgia the US state (Q1428). Neither is an EU member (candidate country only)."
    },
    {
        "stumper_id": "STUMP_019",
        "category": "Entity Ambiguity",
        "claim": "Columbia is an Ivy League research university located in New York City.",
        "subject": "Columbia",
        "property": "instance of",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Columbia University (Q49088) vs Republic of Colombia (country) vs Columbia Pictures (studio)."
    },
    {
        "stumper_id": "STUMP_020",
        "category": "Entity Ambiguity",
        "claim": "Washington has a population of over 7 million people.",
        "subject": "Washington",
        "property": "population",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Washington State (Q1223, ~7.8M) vs Washington D.C. (Q61, ~700k) vs George Washington."
    },
    {
        "stumper_id": "STUMP_021",
        "category": "Entity Ambiguity",
        "claim": "Genesis was written by Peter Gabriel and Phil Collins in the 1970s.",
        "subject": "Genesis",
        "property": "performer",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Genesis the rock band (Q151012) vs Book of Genesis (Bible, Q9184)."
    },
    {
        "stumper_id": "STUMP_022",
        "category": "Entity Ambiguity",
        "claim": "The Matrix is a rectangular array of numbers arranged in rows and columns.",
        "subject": "Matrix",
        "property": "subclass of",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Matrix (mathematics, Q44337) vs The Matrix (1999 film, Q83908)."
    },
    {
        "stumper_id": "STUMP_023",
        "category": "Entity Ambiguity",
        "claim": "Python is a non-venomous constrictor snake native to the tropics.",
        "subject": "Python",
        "property": "subclass of",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Python the snake family (Q184018) vs Python the programming language (Q28865)."
    },
    {
        "stumper_id": "STUMP_024",
        "category": "Entity Ambiguity",
        "claim": "Amazon is the longest river in the world.",
        "subject": "Amazon",
        "property": "instance of",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Nile is traditionally recognized as longest (6,650 km vs 6,400 km); also Amazon the river vs Amazon.com the tech giant."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 3: Metric, Environmental & Physical Constraints [12 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_025",
        "category": "Physical Nuance",
        "claim": "Water boils at 100 degrees Celsius on the summit of Mount Everest.",
        "subject": "water",
        "property": "boiling point",
        "gold_verdict": "FALSE",
        "why_it_stumps": "At 8,848m altitude (low atmospheric pressure ~33 kPa), water boils at approximately 71°C, not 100°C."
    },
    {
        "stumper_id": "STUMP_026",
        "category": "Physical Nuance",
        "claim": "Light travels at 300,000 km/s through a diamond.",
        "subject": "light",
        "property": "speed of light in diamond",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Speed of light in vacuum is ~300,000 km/s; in diamond (refractive index n=2.42), light slows to ~124,000 km/s."
    },
    {
        "stumper_id": "STUMP_027",
        "category": "Physical Nuance",
        "claim": "A metric ton is equal to exactly 2,000 pounds.",
        "subject": "tonne",
        "property": "conversion",
        "gold_verdict": "FALSE",
        "why_it_stumps": "A US short ton is 2,000 lbs (907 kg); a metric tonne is 1,000 kg (2,204.62 lbs)."
    },
    {
        "stumper_id": "STUMP_028",
        "category": "Physical Nuance",
        "claim": "Absolute zero corresponds to -273.15 degrees Celsius.",
        "subject": "absolute zero",
        "property": "temperature",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Exact thermodynamic definition: 0 Kelvin = -273.15°C."
    },
    {
        "stumper_id": "STUMP_029",
        "category": "Physical Nuance",
        "claim": "The speed of sound in dry air at 20 degrees Celsius is approximately 343 meters per second.",
        "subject": "speed of sound",
        "property": "speed",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Exact acoustic formula c = 331.3 * sqrt(1 + T/273.15) -> 343.2 m/s."
    },
    {
        "stumper_id": "STUMP_030",
        "category": "Physical Nuance",
        "claim": "One nautical mile is equal to exactly 1,852 meters.",
        "subject": "nautical mile",
        "property": "length",
        "gold_verdict": "TRUE",
        "why_it_stumps": "International standard SI definition: exactly 1,852 m (1.1508 statute miles)."
    },
    {
        "stumper_id": "STUMP_031",
        "category": "Physical Nuance",
        "claim": "The acceleration due to gravity on the surface of the Moon is approximately 1.62 m/s².",
        "subject": "Moon",
        "property": "surface gravity",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Moon surface gravity is 0.166g (~1.62 m/s²)."
    },
    {
        "stumper_id": "STUMP_032",
        "category": "Physical Nuance",
        "claim": "Sound travels faster in water than in air.",
        "subject": "sound",
        "property": "speed",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Sound in water is ~1,480 m/s vs ~343 m/s in air (over 4x faster due to bulk modulus)."
    },
    {
        "stumper_id": "STUMP_033",
        "category": "Physical Nuance",
        "claim": "The speed of light in vacuum is exactly 299,792,458 meters per second.",
        "subject": "speed of light",
        "property": "speed",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Exact SI constant defining the meter since 1983."
    },
    {
        "stumper_id": "STUMP_034",
        "category": "Physical Nuance",
        "claim": "Liquid nitrogen boils at 77 degrees Celsius.",
        "subject": "nitrogen",
        "property": "boiling point",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Boils at 77 Kelvin (-195.8°C), not 77° Celsius! Unit/scale confusion."
    },
    {
        "stumper_id": "STUMP_035",
        "category": "Physical Nuance",
        "claim": "The escape velocity of the Earth is approximately 11.2 kilometers per second.",
        "subject": "Earth",
        "property": "escape velocity",
        "gold_verdict": "TRUE",
        "why_it_stumps": "sqrt(2GM/R) = 11.186 km/s."
    },
    {
        "stumper_id": "STUMP_036",
        "category": "Physical Nuance",
        "claim": "A light-year is a unit of measurement for astronomical time.",
        "subject": "light-year",
        "property": "unit of",
        "gold_verdict": "FALSE",
        "why_it_stumps": "A light-year measures DISTANCE (~9.46 trillion km), not time."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 4: Subtle Negation & Inverted Quantifiers [11 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_037",
        "category": "Subtle Negation",
        "claim": "Marie Curie was never awarded a Nobel Prize in Chemistry.",
        "subject": "Marie Curie",
        "property": "award received",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Won Nobel in Physics (1903) AND Chemistry (1911). Cross-encoders see high token overlap and predict entailment."
    },
    {
        "stumper_id": "STUMP_038",
        "category": "Subtle Negation",
        "claim": "The Titanic did not sink on its maiden voyage.",
        "subject": "Titanic",
        "property": "event",
        "gold_verdict": "FALSE",
        "why_it_stumps": "The Titanic sank on April 15, 1912, on its maiden voyage from Southampton to NYC."
    },
    {
        "stumper_id": "STUMP_039",
        "category": "Subtle Negation",
        "claim": "Alexander Fleming failed to discover penicillin in 1928.",
        "subject": "Alexander Fleming",
        "property": "discoverer",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Fleming successfully discovered penicillin in September 1928."
    },
    {
        "stumper_id": "STUMP_040",
        "category": "Subtle Negation",
        "claim": "Neil Armstrong was the second human being to set foot on the Moon.",
        "subject": "Neil Armstrong",
        "property": "order",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Neil Armstrong was 1st; Buzz Aldrin was 2nd."
    },
    {
        "stumper_id": "STUMP_041",
        "category": "Subtle Negation",
        "claim": "George Washington was the second President of the United States.",
        "subject": "George Washington",
        "property": "position held",
        "gold_verdict": "FALSE",
        "why_it_stumps": "George Washington was 1st; John Adams was 2nd."
    },
    {
        "stumper_id": "STUMP_042",
        "category": "Subtle Negation",
        "claim": "No human being has ever walked on the surface of Mars.",
        "subject": "Mars",
        "property": "exploration",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Negation verification requires an Open-World closed check."
    },
    {
        "stumper_id": "STUMP_043",
        "category": "Subtle Negation",
        "claim": "Albert Einstein did not win the Nobel Prize for his theory of relativity.",
        "subject": "Albert Einstein",
        "property": "award received",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Won the 1921 Nobel Prize for the Photoelectric Effect, not relativity."
    },
    {
        "stumper_id": "STUMP_044",
        "category": "Subtle Negation",
        "claim": "The United States has never amended its Constitution.",
        "subject": "Constitution of the United States",
        "property": "amendments",
        "gold_verdict": "FALSE",
        "why_it_stumps": "The US Constitution has been amended 27 times."
    },
    {
        "stumper_id": "STUMP_045",
        "category": "Subtle Negation",
        "claim": "Jupiter is smaller in volume than Saturn.",
        "subject": "Jupiter",
        "property": "volume",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Jupiter is the largest planet (~1,300 Earths vs Saturn ~760 Earths)."
    },
    {
        "stumper_id": "STUMP_046",
        "category": "Subtle Negation",
        "claim": "The Pacific Ocean is smaller in surface area than the Atlantic Ocean.",
        "subject": "Pacific Ocean",
        "property": "area",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Pacific is ~165M km²; Atlantic is ~106M km²."
    },
    {
        "stumper_id": "STUMP_047",
        "category": "Subtle Negation",
        "claim": "Diamonds are not composed entirely of carbon atoms.",
        "subject": "diamond",
        "property": "material",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Diamond is pure elemental carbon in an sp3 tetrahedral crystal lattice."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 5: Chimeric Cross-Entity Swaps (Plausible Mergers) [11 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_048",
        "category": "Chimeric Swap",
        "claim": "Elon Musk founded Apple alongside Steve Wozniak in 1976.",
        "subject": "Apple",
        "property": "founder",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Steve Jobs + Steve Wozniak + Ronald Wayne founded Apple; Musk was 5 years old in 1976."
    },
    {
        "stumper_id": "STUMP_049",
        "category": "Chimeric Swap",
        "claim": "Christopher Nolan directed Inception, Oppenheimer, and Avatar.",
        "subject": "Christopher Nolan",
        "property": "director",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Directed Inception & Oppenheimer, but James Cameron directed Avatar."
    },
    {
        "stumper_id": "STUMP_050",
        "category": "Chimeric Swap",
        "claim": "The Mona Lisa was painted by Michelangelo Buonarroti in Florence.",
        "subject": "Mona Lisa",
        "property": "creator",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Painted by Leonardo da Vinci, not Michelangelo."
    },
    {
        "stumper_id": "STUMP_051",
        "category": "Chimeric Swap",
        "claim": "Apple iPhone 15 Pro uses the Qualcomm Snapdragon 8 Gen 3 chipset.",
        "subject": "iPhone 15 Pro",
        "property": "processor",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Uses Apple's proprietary A17 Pro Bionic chip, not Qualcomm."
    },
    {
        "stumper_id": "STUMP_052",
        "category": "Chimeric Swap",
        "claim": "The Origin of Species was written by Gregor Mendel in 1859.",
        "subject": "On the Origin of Species",
        "property": "author",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Written by Charles Darwin; Mendel founded pea plant genetics."
    },
    {
        "stumper_id": "STUMP_053",
        "category": "Chimeric Swap",
        "claim": "Satya Nadella was appointed CEO of Apple in 2014.",
        "subject": "Satya Nadella",
        "property": "employer",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Appointed CEO of Microsoft in 2014; Tim Cook is CEO of Apple."
    },
    {
        "stumper_id": "STUMP_054",
        "category": "Chimeric Swap",
        "claim": "The Lord of the Rings trilogy was written by C. S. Lewis.",
        "subject": "The Lord of the Rings",
        "property": "author",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Written by J. R. R. Tolkien; Lewis wrote Narnia."
    },
    {
        "stumper_id": "STUMP_055",
        "category": "Chimeric Swap",
        "claim": "The Eiffel Tower was designed by Gustave Eiffel for the 1889 Exposition Universelle in Paris.",
        "subject": "Eiffel Tower",
        "property": "architect",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Plausible true combination of architect, date, and venue."
    },
    {
        "stumper_id": "STUMP_056",
        "category": "Chimeric Swap",
        "claim": "Guido van Rossum created the Linux operating system kernel in 1991.",
        "subject": "Linux kernel",
        "property": "developer",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Linus Torvalds created Linux; Guido van Rossum created Python."
    },
    {
        "stumper_id": "STUMP_057",
        "category": "Chimeric Swap",
        "claim": "Jeff Bezos founded Amazon in Seattle in 1994.",
        "subject": "Amazon",
        "property": "founder",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Accurate composite of founder, location, and year."
    },
    {
        "stumper_id": "STUMP_058",
        "category": "Chimeric Swap",
        "claim": "Sony PlayStation 5 was designed and released by Nintendo in 2020.",
        "subject": "PlayStation 5",
        "property": "manufacturer",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Developed by Sony Interactive Entertainment, not Nintendo."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 6: Scientific Misconceptions & Definitional Bounds [11 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_059",
        "category": "Scientific Misconception",
        "claim": "The Great Wall of China is visible from the Moon with the naked eye.",
        "subject": "Great Wall of China",
        "property": "visibility",
        "gold_verdict": "FALSE",
        "why_it_stumps": "NASA and astronaut audits confirmed it is impossible to see without optical magnification."
    },
    {
        "stumper_id": "STUMP_060",
        "category": "Scientific Misconception",
        "claim": "Humans have 24 pairs of chromosomes in somatic cells.",
        "subject": "human genome",
        "property": "chromosome pairs",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Humans have 23 pairs (46 chromosomes total); chimpanzees have 24 pairs (48 total)."
    },
    {
        "stumper_id": "STUMP_061",
        "category": "Scientific Misconception",
        "claim": "Glass is an extremely slow-flowing liquid at room temperature.",
        "subject": "glass",
        "property": "state of matter",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Glass is an amorphous solid; medieval cathedral glass thickness variations are due to manufacturing methods, not liquid flow."
    },
    {
        "stumper_id": "STUMP_062",
        "category": "Scientific Misconception",
        "claim": "Bananas grow on large herbaceous perennial plants, not woody trees.",
        "subject": "banana",
        "property": "botanical classification",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Banana 'trunks' are pseudostems composed of tightly packed leaf sheaths, making them giant herbs."
    },
    {
        "stumper_id": "STUMP_063",
        "category": "Scientific Misconception",
        "claim": "Tomatoes and cucumbers are botanically classified as fruits.",
        "subject": "tomato",
        "property": "botany",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Botanically they develop from the ovary of a flower and contain seeds, making them berries/fruits."
    },
    {
        "stumper_id": "STUMP_064",
        "category": "Scientific Misconception",
        "claim": "Sharks are cartilaginous fish and do not possess bones.",
        "subject": "shark",
        "property": "anatomy",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Class Chondrichthyes have skeletons made entirely of cartilage, not calcified bone."
    },
    {
        "stumper_id": "STUMP_065",
        "category": "Scientific Misconception",
        "claim": "The Sahara is the largest desert on Earth by surface area.",
        "subject": "Sahara",
        "property": "desert rank",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Antarctica is the largest desert (~14.2M km²); Sahara is the largest HOT desert (~9.2M km²)."
    },
    {
        "stumper_id": "STUMP_066",
        "category": "Scientific Misconception",
        "claim": "Lightning never strikes the same place twice.",
        "subject": "lightning",
        "property": "physics",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Empire State Building is struck by lightning 20 to 25 times per year."
    },
    {
        "stumper_id": "STUMP_067",
        "category": "Scientific Misconception",
        "claim": "The tongue has specific discrete taste map zones for sweet, salty, sour, and bitter.",
        "subject": "tongue",
        "property": "gustation",
        "gold_verdict": "FALSE",
        "why_it_stumps": "The 'tongue map' was debunked; taste buds across all areas of the tongue perceive all basic tastes."
    },
    {
        "stumper_id": "STUMP_068",
        "category": "Scientific Misconception",
        "claim": "Bats are completely blind and rely solely on echolocation.",
        "subject": "bat",
        "property": "vision",
        "gold_verdict": "FALSE",
        "why_it_stumps": "All bat species have eyes and can see; many fruit bats have excellent night vision and do not echolocate."
    },
    {
        "stumper_id": "STUMP_069",
        "category": "Scientific Misconception",
        "claim": "Venus is the hottest planet in the Solar System despite Mercury being closer to the Sun.",
        "subject": "Venus",
        "property": "temperature",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Runaway greenhouse effect creates surface temperatures of ~465°C, hotter than Mercury (~430°C peak)."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 7: Macroeconomic Revisions, PPP vs Nominal [11 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_070",
        "category": "Macroeconomic Complexity",
        "claim": "The nominal GDP of China surpassed that of the United States in 2023.",
        "subject": "China",
        "property": "nominal GDP",
        "gold_verdict": "FALSE",
        "why_it_stumps": "In 2023, US Nominal GDP was $27.8T vs China $17.8T. (China is only larger on PPP GDP, not nominal)."
    },
    {
        "stumper_id": "STUMP_071",
        "category": "Macroeconomic Complexity",
        "claim": "The GDP per capita of Luxembourg exceeds 100,000 US dollars.",
        "subject": "Luxembourg",
        "property": "GDP per capita",
        "gold_verdict": "TRUE",
        "why_it_stumps": "World Bank confirms Luxembourg GDP per capita is ~$128,000."
    },
    {
        "stumper_id": "STUMP_072",
        "category": "Macroeconomic Complexity",
        "claim": "Japan is the largest economy in the world by nominal GDP.",
        "subject": "Japan",
        "property": "GDP rank",
        "gold_verdict": "FALSE",
        "why_it_stumps": "US is 1st, China is 2nd, Germany is 3rd, Japan slipped to 4th in 2023."
    },
    {
        "stumper_id": "STUMP_073",
        "category": "Macroeconomic Complexity",
        "claim": "The annual inflation rate in Zimbabwe exceeded 100 percent in 2020.",
        "subject": "Zimbabwe",
        "property": "inflation rate",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Extreme hyperinflation reached 557% in 2020."
    },
    {
        "stumper_id": "STUMP_074",
        "category": "Macroeconomic Complexity",
        "claim": "India had the largest total population in the world in 2024.",
        "subject": "India",
        "property": "population",
        "gold_verdict": "TRUE",
        "why_it_stumps": "UN confirmed India surpassed China in April 2023 (~1.43 billion)."
    },
    {
        "stumper_id": "STUMP_075",
        "category": "Macroeconomic Complexity",
        "claim": "The unemployment rate in South Africa was below 10 percent in 2023.",
        "subject": "South Africa",
        "property": "unemployment rate",
        "gold_verdict": "FALSE",
        "why_it_stumps": "World Bank / Stats SA reports South Africa unemployment rate at ~32%."
    },
    {
        "stumper_id": "STUMP_076",
        "category": "Macroeconomic Complexity",
        "claim": "The global human population reached 8 billion people in November 2022.",
        "subject": "world population",
        "property": "milestone",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Official UN milestone designated November 15, 2022 as Day of Eight Billion."
    },
    {
        "stumper_id": "STUMP_077",
        "category": "Macroeconomic Complexity",
        "claim": "The nominal GDP of Germany was approximately 4.5 trillion US dollars in 2023.",
        "subject": "Germany",
        "property": "nominal GDP",
        "gold_verdict": "TRUE",
        "why_it_stumps": "World Bank confirms German 2023 GDP was $4.46T (~4.5T)."
    },
    {
        "stumper_id": "STUMP_078",
        "category": "Macroeconomic Complexity",
        "claim": "Saudi Arabia has the highest GDP per capita in the world.",
        "subject": "Saudi Arabia",
        "property": "GDP per capita rank",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Luxembourg, Monaco, Singapore, and Ireland rank far higher than Saudi Arabia (~$32k)."
    },
    {
        "stumper_id": "STUMP_079",
        "category": "Macroeconomic Complexity",
        "claim": "The total population of Canada was approximately 40 million people in 2023.",
        "subject": "Canada",
        "property": "population",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Statistics Canada recorded official 40M milestone in June 2023."
    },
    {
        "stumper_id": "STUMP_080",
        "category": "Macroeconomic Complexity",
        "claim": "The official currency of Switzerland is the Euro.",
        "subject": "Switzerland",
        "property": "currency",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Switzerland uses the Swiss Franc (CHF), not the Euro."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 8: Citation, Venue & Chimeric Bibliographies [10 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_081",
        "category": "Bibliographic Chimera",
        "claim": "The paper Attention Is All You Need was published in Nature in 2017.",
        "subject": "Attention Is All You Need",
        "property": "venue",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Published in Advances in Neural Information Processing Systems (NeurIPS 2017), not Nature."
    },
    {
        "stumper_id": "STUMP_082",
        "category": "Bibliographic Chimera",
        "claim": "Yann LeCun, Yoshua Bengio, and Geoffrey Hinton published Deep Learning in Nature in 2015.",
        "subject": "Deep learning (review)",
        "property": "published in",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Nature Vol 521, pp. 436-444 (2015) DOI: 10.1038/nature14539."
    },
    {
        "stumper_id": "STUMP_083",
        "category": "Bibliographic Chimera",
        "claim": "BERT: Pre-training of Deep Bidirectional Transformers was authored by Ashish Vaswani and published at ICLR.",
        "subject": "BERT",
        "property": "author / venue",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Authored by Jacob Devlin et al. and published at NAACL 2019; Vaswani authored the Transformer."
    },
    {
        "stumper_id": "STUMP_084",
        "category": "Bibliographic Chimera",
        "claim": "Language Models are Few-Shot Learners introducing GPT-3 was published at NeurIPS in 2020.",
        "subject": "GPT-3 paper",
        "property": "venue",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Tom Brown et al. published the 75-author paper at NeurIPS 2020."
    },
    {
        "stumper_id": "STUMP_085",
        "category": "Bibliographic Chimera",
        "claim": "Deep Residual Learning for Image Recognition introducing ResNet was published by Kaiming He at CVPR 2016.",
        "subject": "ResNet paper",
        "property": "author / venue",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Won CVPR 2016 Best Paper (He, Zhang, Ren, Sun)."
    },
    {
        "stumper_id": "STUMP_086",
        "category": "Bibliographic Chimera",
        "claim": "The article on Shor's Algorithm was published in Physical Review Letters by Peter Shor in 1994.",
        "subject": "Shor's algorithm",
        "property": "venue",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Published in IEEE FOCS 1994 (Symposium on Foundations of Computer Science), not PRL."
    },
    {
        "stumper_id": "STUMP_087",
        "category": "Bibliographic Chimera",
        "claim": "Alan Turing published Computing Machinery and Intelligence in Mind in 1950.",
        "subject": "Turing test paper",
        "property": "journal",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Published in the philosophy journal Mind, 59(236), pp. 433-460."
    },
    {
        "stumper_id": "STUMP_088",
        "category": "Bibliographic Chimera",
        "claim": "Claude Shannon published A Mathematical Theory of Communication in the Bell System Technical Journal in 1948.",
        "subject": "Information Theory paper",
        "property": "journal",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Landmark 1948 paper in BSTJ establishing modern information theory."
    },
    {
        "stumper_id": "STUMP_089",
        "category": "Bibliographic Chimera",
        "claim": "The seminal paper on Generative Adversarial Nets was published by Ian Goodfellow in IEEE TPAMI.",
        "subject": "GAN paper",
        "property": "venue",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Goodfellow et al. published GANs at NeurIPS (NIPS 2014), not TPAMI."
    },
    {
        "stumper_id": "STUMP_090",
        "category": "Bibliographic Chimera",
        "claim": "Mastering the game of Go with deep neural networks and tree search was published by DeepMind in Nature in 2016.",
        "subject": "AlphaGo paper",
        "property": "journal",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Silver et al. AlphaGo cover article in Nature 529, 484-489 (Jan 2016)."
    },

    # ---------------------------------------------------------------------------
    # CATEGORY 9: Polysemy, Hedging & Pragmatic Boundary Edge Cases [10 claims]
    # ---------------------------------------------------------------------------
    {
        "stumper_id": "STUMP_091",
        "category": "Polysemy & Pragmatics",
        "claim": "Locks on the Panama Canal lift ships approximately 85 feet above sea level.",
        "subject": "Panama Canal",
        "property": "locks elevation",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Gatun Lake is 85 ft (26 m) above sea level; 'above sea level' is a datum, not an inequality operator."
    },
    {
        "stumper_id": "STUMP_092",
        "category": "Polysemy & Pragmatics",
        "claim": "Mount Kilimanjaro is the highest mountain peak in Africa.",
        "subject": "Mount Kilimanjaro",
        "property": "elevation rank",
        "gold_verdict": "TRUE",
        "why_it_stumps": "5,895 meters above sea level (highest in Africa)."
    },
    {
        "stumper_id": "STUMP_093",
        "category": "Polysemy & Pragmatics",
        "claim": "Mount Everest is taller when measured from base to peak underwater than Mauna Kea.",
        "subject": "Mount Everest",
        "property": "topographic height",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Mauna Kea is ~10,210 m base-to-peak (~4,207 m above sea level); Everest is only ~8,848 m above sea level."
    },
    {
        "stumper_id": "STUMP_094",
        "category": "Polysemy & Pragmatics",
        "claim": "The Mariana Trench is the deepest oceanic trench on Earth with a depth of over 10,000 meters.",
        "subject": "Mariana Trench",
        "property": "depth",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Challenger Deep is ~10,984 m; 'over 10,000 meters' lower bound is satisfied."
    },
    {
        "stumper_id": "STUMP_095",
        "category": "Polysemy & Pragmatics",
        "claim": "The human body consists of more than 500 distinct bones.",
        "subject": "human skeleton",
        "property": "bone count",
        "gold_verdict": "FALSE",
        "why_it_stumps": "Adult human skeleton has exactly 206 bones; infants have ~270."
    },
    {
        "stumper_id": "STUMP_096",
        "category": "Polysemy & Pragmatics",
        "claim": "An adult human brain consumes approximately 20 percent of the body's total energy.",
        "subject": "human brain",
        "property": "energy consumption",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Consumes ~20% of basal metabolic rate despite being only ~2% of body mass."
    },
    {
        "stumper_id": "STUMP_097",
        "category": "Polysemy & Pragmatics",
        "claim": "The Dead Sea is the lowest land-based elevation on Earth at over 400 meters below sea level.",
        "subject": "Dead Sea",
        "property": "elevation",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Surface is ~430 m below sea level."
    },
    {
        "stumper_id": "STUMP_098",
        "category": "Polysemy & Pragmatics",
        "claim": "The Nile River flows southward into the Mediterranean Sea.",
        "subject": "Nile",
        "property": "flow direction",
        "gold_verdict": "FALSE",
        "why_it_stumps": "The Nile flows NORTHWARD (from Lake Victoria north to the Mediterranean)."
    },
    {
        "stumper_id": "STUMP_099",
        "category": "Polysemy & Pragmatics",
        "claim": "Australia is both a sovereign country and a continent.",
        "subject": "Australia",
        "property": "classification",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Dual ontological instance: island continent and sovereign nation."
    },
    {
        "stumper_id": "STUMP_100",
        "category": "Polysemy & Pragmatics",
        "claim": "The International Space Station completes one full orbit around Earth in approximately 90 minutes.",
        "subject": "International Space Station",
        "property": "orbital period",
        "gold_verdict": "TRUE",
        "why_it_stumps": "Low Earth orbit period is ~92.9 minutes at ~27,600 km/h."
    },
]

def generate_csv():
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["stumper_id", "category", "claim", "subject", "property", "gold_verdict", "why_it_stumps"])
        writer.writeheader()
        writer.writerows(STUMPERS)
    print(f"Generated {len(STUMPERS)} adversarial stumpers at: {OUT_CSV}")

if __name__ == "__main__":
    generate_csv()
