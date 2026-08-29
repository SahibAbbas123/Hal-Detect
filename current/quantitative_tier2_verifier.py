#!/usr/bin/env python3
"""
HalDetect -- Quantitative Tier 2 Verifier (Category C.3)
=========================================================
Open Statistical REST API Verifier (World Bank Open Data API & Macro Indicators).

Provides deterministic multidimensional data cube grounding (qb4olap-style)
for economic, demographic, and statistical claims, with explicit support for:
  • Nominal vs Purchasing Power Parity (PPP) GDP & GDP per capita
  • Multi-currency normalizer (€, £, ¥, ₹, ৳, USD)
  • Tolerance-aware statistical bounds
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HERE = Path(__file__).resolve().parent
CACHE_PATH = HERE / "macro_api_cache.json"
WORLD_BANK_API = "https://api.worldbank.org/v2"

# ---------------------------------------------------------------------------
# INDICATOR TAXONOMY & ALIASES (NOMINAL + PPP + MACRO)
# ---------------------------------------------------------------------------
INDICATOR_MAP = {
    # Economic / PPP Output
    "gdp (ppp)": ("NY.GDP.MKTP.PP.CD", "GDP, PPP (current international $)", "currency_ppp"),
    "ppp gdp": ("NY.GDP.MKTP.PP.CD", "GDP, PPP (current international $)", "currency_ppp"),
    "purchasing power parity gdp": ("NY.GDP.MKTP.PP.CD", "GDP, PPP (current international $)", "currency_ppp"),
    "gdp ppp": ("NY.GDP.MKTP.PP.CD", "GDP, PPP (current international $)", "currency_ppp"),
    "gdp per capita (ppp)": ("NY.GDP.PCAP.PP.CD", "GDP per capita, PPP (current international $)", "currency_ppp"),
    "ppp gdp per capita": ("NY.GDP.PCAP.PP.CD", "GDP per capita, PPP (current international $)", "currency_ppp"),

    # Economic / Nominal Output
    "nominal gdp": ("NY.GDP.MKTP.CD", "GDP (current US$)", "currency"),
    "gdp": ("NY.GDP.MKTP.CD", "GDP (current US$)", "currency"),
    "gross domestic product": ("NY.GDP.MKTP.CD", "GDP (current US$)", "currency"),
    "gdp per capita": ("NY.GDP.PCAP.CD", "GDP per capita (current US$)", "currency"),
    "economic output": ("NY.GDP.MKTP.CD", "GDP (current US$)", "currency"),
    "gni": ("NY.GNP.MKTP.CD", "GNI (current US$)", "currency"),
    "gross national income": ("NY.GNP.MKTP.CD", "GNI (current US$)", "currency"),

    # Growth & Debt
    "gdp growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)", "percent"),
    "annual gdp growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)", "percent"),
    "economic growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)", "percent"),

    # Prices & Inflation
    "inflation": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)", "percent"),
    "inflation rate": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)", "percent"),
    "cpi": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)", "percent"),
    "consumer price index": ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)", "percent"),

    # Demographics & Society
    "population": ("SP.POP.TOTL", "Population, total", "count"),
    "total population": ("SP.POP.TOTL", "Population, total", "count"),
    "inhabitants": ("SP.POP.TOTL", "Population, total", "count"),
    "life expectancy": ("SP.DYN.LE00.IN", "Life expectancy at birth (years)", "years"),
    "unemployment": ("SL.UEM.TOTL.ZS", "Unemployment, total (% of labor force)", "percent"),
    "unemployment rate": ("SL.UEM.TOTL.ZS", "Unemployment, total (% of labor force)", "percent"),

    # Environment & Energy
    "co2 emissions": ("EN.ATM.CO2E.PC", "CO2 emissions (metric tons per capita)", "ratio"),
    "carbon emissions": ("EN.ATM.CO2E.PC", "CO2 emissions (metric tons per capita)", "ratio"),
    "renewable energy": ("EG.FEC.RNEW.ZS", "Renewable energy consumption (% of total)", "percent"),
    "electricity consumption": ("EG.USE.ELEC.KH.PC", "Electric power consumption (kWh per capita)", "count"),
}

# ---------------------------------------------------------------------------
# CURRENCY EXCHANGE RATES TO USD (AVERAGE BASELINE)
# ---------------------------------------------------------------------------
CURRENCY_RATES_TO_USD = {
    "$": 1.0, "usd": 1.0, "dollar": 1.0, "dollars": 1.0,
    "€": 1.08, "eur": 1.08, "euro": 1.08, "euros": 1.08,
    "£": 1.28, "gbp": 1.28, "pound": 1.28, "pounds": 1.28,
    "¥": 0.0067, "jpy": 0.0067, "yen": 0.0067,
    "₹": 0.012, "inr": 0.012, "rupee": 0.012, "rupees": 0.012,
    "৳": 0.0084, "bdt": 0.0084, "taka": 0.0084,
    "cny": 0.14, "yuan": 0.14, "rmb": 0.14
}

# ---------------------------------------------------------------------------
# COUNTRY & ISO RESOLVER
# ---------------------------------------------------------------------------
COUNTRY_TO_ISO = {
    "united states": "USA", "us": "USA", "usa": "USA", "america": "USA",
    "china": "CHN", "chinese": "CHN",
    "japan": "JPN", "japanese": "JPN",
    "germany": "DEU", "german": "DEU",
    "india": "IND", "indian": "IND",
    "united kingdom": "GBR", "uk": "GBR", "britain": "GBR", "british": "GBR",
    "france": "FRA", "french": "FRA",
    "italy": "ITA", "italian": "ITA",
    "brazil": "BRA", "brazilian": "BRA",
    "canada": "CAN", "canadian": "CAN",
    "russia": "RUS", "russian": "RUS",
    "south korea": "KOR", "korea": "KOR",
    "australia": "AUS", "australian": "AUS",
    "mexico": "MEX", "mexican": "MEX",
    "spain": "ESP", "spanish": "ESP",
    "indonesia": "IDN", "indonesian": "IDN",
    "saudi arabia": "SAU", "saudi": "SAU",
    "turkey": "TUR", "turkish": "TUR", "turkiye": "TUR",
    "switzerland": "CHE", "swiss": "CHE",
    "netherlands": "NLD", "dutch": "NLD",
    "south africa": "ZAF",
    "bangladesh": "BGD", "bangladeshi": "BGD",
    "nigeria": "NGA", "nigerian": "NGA",
    "egypt": "EGY", "egyptian": "EGY",
    "vietnam": "VNM", "vietnamese": "VNM",
    "world": "WLD", "global": "WLD",
}

_session = None

def get_api_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        _session.mount("https://", HTTPAdapter(max_retries=retries))
    return _session


# ---------------------------------------------------------------------------
# CACHE SYSTEM
# ---------------------------------------------------------------------------
def load_macro_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_macro_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


# ---------------------------------------------------------------------------
# EXTRACTION HELPERS
# ---------------------------------------------------------------------------
def extract_country_iso(text: str) -> Optional[str]:
    text_lower = text.lower()
    for country, iso in sorted(COUNTRY_TO_ISO.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = r"\b" + re.escape(country) + r"\b"
        if re.search(pattern, text_lower):
            return iso
    return None


def extract_indicator(text: str) -> Optional[Tuple[str, str, str]]:
    # Normalize punctuation for robust phrase matching
    text_norm = " " + text.lower().replace("(", " ").replace(")", " ").replace("-", " ") + " "
    for phrase, info in sorted(INDICATOR_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        phrase_norm = " " + phrase.lower().replace("(", " ").replace(")", " ").replace("-", " ") + " "
        phrase_words = phrase_norm.split()
        pattern = r"\b" + r"\s+".join([re.escape(w) for w in phrase_words]) + r"\b"
        if re.search(pattern, text_norm):
            return info
    return None


def extract_year(text: str) -> Optional[int]:
    matches = re.findall(r"\b(19[6-9]\d|20[0-2]\d)\b", text)
    if matches:
        return int(matches[-1])
    return 2022


def parse_numeric_claim_value(text: str, extracted_year: Optional[int] = None) -> Optional[float]:
    # Check for currency symbols or units
    unit_pattern = r"([€$£¥₹৳]?\s*[\d,]+(?:\.\d+)?)\s*(trillion|billion|million|thousand|%|percent|years|metric tons|dollars|usd|eur|gbp|inr|bdt)?\b"
    matches = list(re.finditer(unit_pattern, text, re.IGNORECASE))
    
    if not matches:
        generic_pattern = r"([€$£¥₹৳]?\s*[\d,]+(?:\.\d+)?)"
        matches = list(re.finditer(generic_pattern, text))

    for m in matches:
        raw_m = m.group(1).strip()
        # Detect currency prefix
        curr_rate = 1.0
        for sym, rate in CURRENCY_RATES_TO_USD.items():
            if raw_m.startswith(sym):
                curr_rate = rate
                raw_m = raw_m.lstrip(sym).strip()
                break

        raw_num = raw_m.replace(",", "").strip()
        unit = (m.group(2) if len(m.groups()) > 1 and m.group(2) else "").lower().strip()
        
        # Check currency unit suffix
        if unit in CURRENCY_RATES_TO_USD:
            curr_rate = CURRENCY_RATES_TO_USD[unit]

        try:
            val = float(raw_num)
            if extracted_year and int(val) == extracted_year and not unit:
                continue
            
            if "trillion" in unit:
                val *= 1e12
            elif "billion" in unit:
                val *= 1e9
            elif "million" in unit:
                val *= 1e6
            elif "thousand" in unit:
                val *= 1e3
            
            # Normalize to USD
            val *= curr_rate
            return val
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# WORLD BANK QUERY & VERIFICATION
# ---------------------------------------------------------------------------
def query_world_bank(country_iso: str, indicator_code: str, year: int, cache: dict) -> Optional[float]:
    cache_key = f"wb__{country_iso}__{indicator_code}__{year}"
    if cache_key in cache:
        return cache[cache_key]

    session = get_api_session()
    url = f"{WORLD_BANK_API}/country/{country_iso}/indicator/{indicator_code}"
    params = {"date": str(year), "format": "json"}

    try:
        r = session.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
        if len(data) > 1 and data[1]:
            val = data[1][0].get("value")
            if val is not None:
                float_val = float(val)
                cache[cache_key] = float_val
                return float_val
    except Exception:
        pass
    return None


def verify_macro_claim(claim_row: dict, cache: Optional[dict] = None) -> dict:
    """
    Tier-2 Statistical Verifier for Macro/Demographic/Economic Claims.
    """
    if cache is None:
        cache = load_macro_cache()

    claim_text = (claim_row.get("claim") or "").strip()
    subject = (claim_row.get("subject") or "").strip()
    full_text = f"{subject} {claim_text}"

    iso = extract_country_iso(full_text)
    indicator_info = extract_indicator(full_text)
    year = extract_year(full_text)
    claimed_value = parse_numeric_claim_value(claim_text, extracted_year=year)

    if not iso or not indicator_info or claimed_value is None:
        return {
            "verdict": "UNVERIFIABLE",
            "confidence": 0.30,
            "evidence": f"Could not map claim to World Bank indicators (iso={iso}, ind={indicator_info is not None}, val={claimed_value is not None}).",
            "method": "world_bank_tier2|unmapped",
            "grounded_value": None,
            "relative_error": None,
        }

    indicator_code, indicator_name, unit_type = indicator_info
    grounded_value = query_world_bank(iso, indicator_code, year, cache)

    if grounded_value is None:
        grounded_value = query_world_bank(iso, indicator_code, year - 1, cache)

    if grounded_value is None:
        return {
            "verdict": "UNVERIFIABLE",
            "confidence": 0.35,
            "evidence": f"World Bank API has no record for {iso} - {indicator_name} ({year}).",
            "method": "world_bank_tier2|no_data",
            "grounded_value": None,
            "relative_error": None,
        }

    rel_err = abs(claimed_value - grounded_value) / abs(grounded_value) if grounded_value != 0 else 0.0

    if unit_type in {"percent", "years"}:
        abs_diff = abs(claimed_value - grounded_value)
        is_match = (abs_diff <= 2.0) or (rel_err <= 0.08)
    else:
        is_match = (rel_err <= 0.10)

    if is_match:
        verdict = "TRUE"
        conf = 0.95
        evidence = f"World Bank verified: {indicator_name} for {iso} ({year}) is {grounded_value:,.2f} (Claimed: {claimed_value:,.2f}, rel_err: {rel_err:.1%})."
    else:
        verdict = "FALSE"
        conf = 0.92
        evidence = f"World Bank contradiction: {indicator_name} for {iso} ({year}) official value is {grounded_value:,.2f} (Claimed: {claimed_value:,.2f}, discrepancy: {rel_err:.1%})."

    return {
        "verdict": verdict,
        "confidence": conf,
        "evidence": evidence,
        "method": f"world_bank_tier2|{indicator_code}",
        "grounded_value": grounded_value,
        "relative_error": round(rel_err, 4),
    }


if __name__ == "__main__":
    print("=" * 85)
    print(" 🚀 HALDETECT 2.0 -- QUANTITATIVE TIER 2 WORLD BANK (NOMINAL + PPP) VERIFIER TEST")
    print("=" * 85)
    cache = load_macro_cache()
    
    test_cases = [
        {"claim": "The nominal GDP of the United States reached approximately 27.8 trillion dollars in 2023.", "subject": "United States", "gold": "TRUE"},
        {"claim": "The nominal GDP of the United States in 2023 was only 12.5 trillion dollars.", "subject": "United States", "gold": "FALSE"},
        {"claim": "India's GDP (PPP) in 2023 reached approximately 13.2 trillion dollars.", "subject": "India", "gold": "TRUE"},
        {"claim": "India's GDP (PPP) in 2023 was only 4.5 trillion dollars.", "subject": "India", "gold": "FALSE"},
        {"claim": "Life expectancy in Japan was approximately 84 years in 2022.", "subject": "Japan", "gold": "TRUE"},
        {"claim": "Life expectancy in Japan dropped to 52 years in 2022.", "subject": "Japan", "gold": "FALSE"}
    ]

    for tc in test_cases:
        res = verify_macro_claim(tc, cache)
        print(f"Claim:    '{tc['claim']}'")
        print(f"Verdict:  {res['verdict']} (Confidence: {res['confidence']}) [Gold: {tc['gold']}]")
        print(f"Evidence: {res['evidence']}\n")

    save_macro_cache(cache)
    print("✅ Saved macro cache successfully.")
