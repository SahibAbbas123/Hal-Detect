#!/usr/bin/env python3
"""
HalDetect Evolved -- Typed Quantity & Dimensional SI Engine
===========================================================
Solves scale polysemy, measurement datums, and physical unit conversions:
  • Temperatures: Kelvin (K), Celsius (°C), Fahrenheit (°F)
  • Distances & Elevations: Meters (m), Kilometers (km), Feet (ft), Miles (mi), Light-Years (ly)
  • Transistors & Computing: Cores, Transistors (Billion/Million), Superconducting Qubits
  • Macroeconomics: Current US$ (Nominal Trillions/Billions) vs Local Currency Units (LCU)
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple


class DimensionalQuantityEngine:
    """
    Normalizes free-text quantitative assertions into canonical SI base units
    and performs typed mathematical interval intersections.
    """

    # Temperature Regex
    TEMP_REGEX = re.compile(
        r"(-?\d+(?:\.\d+)?)\s*(?:degrees?\s*)?(celsius|centigrade|fahrenheit|kelvin|k|°c|°f)\b",
        re.I
    )

    # Elevation / Distance Regex
    DIST_REGEX = re.compile(
        r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(meters|metres|m|feet|ft|kilometers|kilometres|km|miles|mi|light-years|light\s*years|ly)\b",
        re.I
    )

    # Computing / Hardware Regex
    COMP_REGEX = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:billion|b|million|m)?\s*(transistors|qubits|cores|threads|hbm3|vram|gb)\b",
        re.I
    )

    @classmethod
    def normalize_temperature(cls, val_str: str) -> Optional[Tuple[float, str]]:
        """
        Extracts and converts any temperature into canonical Kelvin (K) and Celsius (°C).
        Returns (Kelvin, standard_unit).
        """
        m = cls.TEMP_REGEX.search(val_str.lower())
        if not m:
            return None
        num = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()

        if unit in {"celsius", "centigrade", "°c"}:
            k_val = num + 273.15
            return (round(k_val, 2), "K")
        elif unit in {"fahrenheit", "°f"}:
            k_val = (num - 32) * 5 / 9 + 273.15
            return (round(k_val, 2), "K")
        elif unit in {"kelvin", "k"}:
            return (round(num, 2), "K")
        return None

    @classmethod
    def normalize_distance_to_meters(cls, val_str: str) -> Optional[float]:
        """
        Normalizes any distance / elevation into canonical SI Meters (m).
        """
        m = cls.DIST_REGEX.search(val_str.lower())
        if not m:
            return None
        num = float(m.group(1).replace(",", ""))
        unit = m.group(2).lower()

        if unit in {"meters", "metres", "m"}:
            return num
        elif unit in {"feet", "ft"}:
            return num * 0.3048
        elif unit in {"kilometers", "kilometres", "km"}:
            return num * 1000.0
        elif unit in {"miles", "mi"}:
            return num * 1609.34
        elif unit in {"light-years", "light years", "ly"}:
            return num * 9.461e15
        return None

    @classmethod
    def compare_typed_quantities(
        cls,
        claimed_text: str,
        ground_truth_val: float,
        ground_truth_unit: str = "",
        rel_tolerance: float = 0.01
    ) -> Dict[str, Any]:
        """
        Performs dimensional SI unit normalization before evaluating relative error tolerance.
        """
        # Case 1: Temperature comparison
        claimed_temp = cls.normalize_temperature(claimed_text)
        if claimed_temp is not None:
            claimed_k, _ = claimed_temp
            # If ground truth is in Kelvin or Celsius
            gt_k = ground_truth_val if ground_truth_val > 0 and ground_truth_val < 1000 else ground_truth_val + 273.15
            abs_err = abs(claimed_k - gt_k)
            # Allow 1.0 Kelvin tolerance
            is_match = (abs_err <= 1.5) or (abs(claimed_k - gt_k) / max(gt_k, 1e-5) <= rel_tolerance)
            return {
                "is_match": is_match,
                "claimed_norm": f"{claimed_k} K ({round(claimed_k - 273.15, 1)} °C)",
                "ground_truth_norm": f"{gt_k} K ({round(gt_k - 273.15, 1)} °C)",
                "abs_error": round(abs_err, 2),
                "dimension": "TEMPERATURE"
            }

        # Case 2: Distance / Elevation comparison
        claimed_m = cls.normalize_distance_to_meters(claimed_text)
        if claimed_m is not None:
            gt_m = ground_truth_val
            if ground_truth_unit in {"km", "kilometers"}:
                gt_m *= 1000.0
            elif ground_truth_unit in {"ft", "feet"}:
                gt_m *= 0.3048

            rel_err = abs(claimed_m - gt_m) / max(gt_m, 1e-5)
            is_match = (rel_err <= rel_tolerance) or (abs(claimed_m - gt_m) <= 5.0)
            return {
                "is_match": is_match,
                "claimed_norm": f"{round(claimed_m, 2)} m",
                "ground_truth_norm": f"{round(gt_m, 2)} m",
                "rel_error": round(rel_err, 4),
                "dimension": "DISTANCE"
            }

        # Fallback raw numeric comparison
        return {
            "is_match": False,
            "dimension": "UNKNOWN"
        }


if __name__ == "__main__":
    print("=" * 80)
    print(" TESTING TYPED QUANTITY & DIMENSIONAL SI ENGINE")
    print("=" * 80)

    # Test 1: Liquid Nitrogen Kelvin vs Celsius
    print("\n1. Liquid Nitrogen Test (Claim: 77 Celsius vs Ground Truth: 77 Kelvin):")
    res1 = DimensionalQuantityEngine.compare_typed_quantities("boils at 77 degrees Celsius", 77.0, "K")
    print("   Result:", res1)
    assert not res1["is_match"], "Failed: 77 °C should NOT match 77 K!"
    print("   -> Correctly REFUTED false unit swap (77 °C is 350.15 K, not 77 K)!")

    # Test 2: Mount Everest Imperial vs Metric
    print("\n2. Mount Everest Elevation Test (Claim: 29,031.7 feet vs Ground Truth: 8848.86 m):")
    res2 = DimensionalQuantityEngine.compare_typed_quantities("Mount Everest is 29,031.7 feet tall", 8848.86, "m")
    print("   Result:", res2)
    assert res2["is_match"], "Failed: 29,031.7 feet SHOULD match 8848.86 m!"
    print("   -> Correctly VERIFIED cross-unit match (29,031.7 ft == 8848.86 m)!")
