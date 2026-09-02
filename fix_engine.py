import os

path = "current/dimensional_quantity_engine.py"
with open(path, "r") as f:
    text = f.read()

# Fix Dimensionality in Case 2
old_case2 = """        # Case 2: Distance / Elevation comparison
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
            }"""

new_case2 = """        # Case 2: Distance / Elevation comparison
        claimed_m = cls.normalize_distance_to_meters(claimed_text)
        if claimed_m is not None:
            # Bug 12 fix: Strictly enforce unit dimensionality check
            valid_length_units = {"m", "meter", "meters", "metres", "km", "kilometer", "kilometers", "kilometres", "ft", "foot", "feet", "mi", "mile", "miles", "ly", "light-years"}
            if ground_truth_unit and ground_truth_unit.lower() not in valid_length_units:
                return {
                    "is_match": False,
                    "dimension": "DIMENSION_MISMATCH",
                    "detail": f"Claimed length but ground truth unit is '{ground_truth_unit}'"
                }
                
            gt_m = ground_truth_val
            if ground_truth_unit in {"km", "kilometers", "kilometres"}:
                gt_m *= 1000.0
            elif ground_truth_unit in {"ft", "feet", "foot"}:
                gt_m *= 0.3048
            elif ground_truth_unit in {"mi", "mile", "miles"}:
                gt_m *= 1609.34

            rel_err = abs(claimed_m - gt_m) / max(gt_m, 1e-5)
            is_match = (rel_err <= rel_tolerance) or (abs(claimed_m - gt_m) <= 5.0)
            return {
                "is_match": is_match,
                "claimed_norm": f"{round(claimed_m, 2)} m",
                "ground_truth_norm": f"{round(gt_m, 2)} m",
                "rel_error": round(rel_err, 4),
                "dimension": "DISTANCE"
            }"""

text = text.replace(old_case2, new_case2)
with open(path, "w") as f:
    f.write(text)

# Also fix quantitative_verifier.py where "m": 1_000_000 exists
qv_path = "current/quantitative_verifier.py"
with open(qv_path, "r") as f:
    qv_text = f.read()

qv_text = qv_text.replace('"m": 1_000_000, "million": 1_000_000, "mn": 1_000_000,', '"M": 1_000_000, "million": 1_000_000, "mn": 1_000_000,')

# And fix the exact issue: comparing 10 to 10kg
# Around line 757: elif cu and not au and cu not in _DIMENSIONLESS:
# We should also handle `not cu and au and au not in _DIMENSIONLESS`
old_check = """    elif cu and not au and cu not in _DIMENSIONLESS:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": (f"claim has unit '{claimed.get('unit')}' but Wikidata "
                           f"value is dimensionless — cannot align")}"""
                           
new_check = """    elif cu and not au and cu not in _DIMENSIONLESS:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": (f"claim has unit '{claimed.get('unit')}' but Wikidata "
                           f"value is dimensionless — cannot align")}
    elif not cu and au and au not in _DIMENSIONLESS:
        return {"verdict": "UNVERIFIABLE", "confidence": 0.0, "rel_error": None,
                "detail": (f"claim is dimensionless but Wikidata "
                           f"value has unit '{actual.get('unit')}' ({au}) — cannot align")}"""
                           
qv_text = qv_text.replace(old_check, new_check)

with open(qv_path, "w") as f:
    f.write(qv_text)

