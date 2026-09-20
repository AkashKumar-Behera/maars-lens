"""
MAARS Lens: Rule Evaluators
===========================
Evaluates individual rule definitions against extracted package facts,
OCR confidences, and visual measurements based on ComplianceRuleVersion.check_definition.
"""

import re
from typing import Any, Dict, Optional, Tuple
from app.models.enums import AuditResultType


def evaluate_rule_check(
    operator: str,
    check_definition: Dict[str, Any],
    actual_value: Any,
    facts: Dict[str, Any],
    visual_measurements: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates a specific check definition operator.
    
    Returns:
        (passed: bool, expected_repr: str, error_detail: Optional[str])
    """
    op = (operator or "").strip().lower()
    expected_val = check_definition.get("value")
    case_sensitive = check_definition.get("case_sensitive", False)

    # 1. Presence check
    if op in ("exists", "not_empty", "not_null", "present"):
        expected_repr = "Must be declared on package"
        if actual_value is None:
            return False, expected_repr, "Field is missing from extracted package declarations."
        if isinstance(actual_value, str) and not actual_value.strip():
            return False, expected_repr, "Field is declared as blank or empty string."
        return True, expected_repr, None

    # For subsequent checks, missing field fails unless explicit fallback
    if actual_value is None:
        return False, str(expected_val), f"Target field is missing; cannot evaluate {op}."

    actual_str = str(actual_value).strip()

    # 2. Regex matching
    if op in ("regex", "pattern", "matches"):
        expected_repr = str(expected_val)
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            matched = bool(re.search(expected_val, actual_str, flags=flags))
            detail = None if matched else f"Value '{actual_str}' does not match statutory pattern '{expected_val}'."
            return matched, expected_repr, detail
        except re.error as e:
            return False, expected_repr, f"Invalid rule regular expression: {e}"

    # 3. Substring contains
    if op == "contains":
        expected_repr = f"Contains '{expected_val}'"
        exp_str = str(expected_val)
        if not case_sensitive:
            matched = exp_str.lower() in actual_str.lower()
        else:
            matched = exp_str in actual_str
        detail = None if matched else f"Value '{actual_str}' does not contain required substring '{exp_str}'."
        return matched, expected_repr, detail

    # 4. Equality
    if op in ("eq", "equals", "=="):
        expected_repr = str(expected_val)
        if not case_sensitive and isinstance(expected_val, str):
            matched = actual_str.lower() == expected_val.lower()
        else:
            matched = str(actual_value) == str(expected_val)
        detail = None if matched else f"Value '{actual_str}' does not equal expected '{expected_val}'."
        return matched, expected_repr, detail

    # 5. Numeric comparisons: gte, lte, gt, lt
    if op in ("gte", "lte", "gt", "lt"):
        try:
            num_actual = float(actual_value)
            num_expected = float(expected_val)
            expected_repr = f"{op} {num_expected}"

            if op == "gte":
                matched = num_actual >= num_expected
            elif op == "lte":
                matched = num_actual <= num_expected
            elif op == "gt":
                matched = num_actual > num_expected
            elif op == "lt":
                matched = num_actual < num_expected
            else:
                matched = False

            detail = None if matched else f"Actual numerical value ({num_actual}) violates condition {op} {num_expected}."
            return matched, expected_repr, detail
        except (ValueError, TypeError) as e:
            return False, str(expected_val), f"Non-numeric value encountered for {op} comparison: {e}"

    # 6. Range check: between
    if op in ("between", "range"):
        try:
            num_actual = float(actual_value)
            if isinstance(expected_val, (list, tuple)) and len(expected_val) >= 2:
                low, high = float(expected_val[0]), float(expected_val[1])
            else:
                return False, str(expected_val), "Rule definition error: 'between' expects [low, high]."

            expected_repr = f"[{low} - {high}]"
            matched = low <= num_actual <= high
            detail = None if matched else f"Actual value ({num_actual}) outside permissible range [{low} - {high}]."
            return matched, expected_repr, detail
        except (ValueError, TypeError) as e:
            return False, str(expected_val), f"Non-numeric value encountered for between comparison: {e}"

    # 7. Compare Field with Tolerance (e.g. net quantity vs unit price)
    if op == "compare_field":
        compare_field = check_definition.get("compare_field")
        tolerance_pct = float(check_definition.get("tolerance_pct", 0.0))
        comp_val = facts.get(compare_field) if compare_field else None
        expected_repr = f"Equal to '{compare_field}' within {tolerance_pct}%"

        if comp_val is None:
            return False, expected_repr, f"Comparison target field '{compare_field}' missing from facts."

        try:
            num_act = float(actual_value)
            num_cmp = float(comp_val)
            diff_pct = abs(num_act - num_cmp) / (num_cmp if num_cmp != 0 else 1.0) * 100.0
            matched = diff_pct <= tolerance_pct
            detail = None if matched else f"Value difference ({diff_pct:.2f}%) exceeds allowed tolerance ({tolerance_pct}%)."
            return matched, expected_repr, detail
        except (ValueError, TypeError):
            matched = str(actual_value).strip().lower() == str(comp_val).strip().lower()
            detail = None if matched else f"Field values do not match: '{actual_value}' != '{comp_val}'."
            return matched, expected_repr, detail

    # 8. Unit Sale Price Verification (Calculated comparison: price per g/kg/ml/l)
    if op in ("unit_sale_price", "unit_price"):
        # Expects facts to contain mrp and net_quantity
        mrp_raw = facts.get("mrp")
        qty_raw = facts.get("net_quantity")
        tolerance_pct = float(check_definition.get("tolerance_pct", 5.0)) # 5% rounding tolerance

        if not mrp_raw or not qty_raw:
            return False, "Unit sale price matching MRP / Net Quantity", "Cannot verify unit price: MRP or Net Quantity missing."

        # Parse numerical values
        mrp_match = re.search(r'(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)', str(mrp_raw), re.IGNORECASE)
        qty_match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', str(qty_raw))
        actual_usp_match = re.search(r'(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)', str(actual_value), re.IGNORECASE)

        if not mrp_match or not qty_match or not actual_usp_match:
            return False, "Numerical unit sale price", f"Unable to parse numeric values from MRP ('{mrp_raw}'), Qty ('{qty_raw}'), or Unit Price ('{actual_value}')."

        mrp_num = float(mrp_match.group(1))
        qty_num = float(qty_match.group(1))
        declared_usp = float(actual_usp_match.group(1))

        if qty_num <= 0:
            return False, "Positive net quantity", f"Net quantity ({qty_num}) is non-positive."

        # Compute theoretical unit price
        expected_usp = mrp_num / qty_num
        expected_repr = f"Rs. {expected_usp:.2f} per unit (+/- {tolerance_pct}%)"

        diff_pct = abs(declared_usp - expected_usp) / (expected_usp if expected_usp != 0 else 1.0) * 100.0
        matched = diff_pct <= tolerance_pct
        detail = None if matched else f"Declared unit sale price (Rs. {declared_usp:.2f}) differs from calculated MRP/Qty (Rs. {expected_usp:.2f}) by {diff_pct:.1f}% (max allowed: {tolerance_pct}%)."
        return matched, expected_repr, detail

    # 9. Font Size Lookup Table (Rule 7 font height bands by net quantity)
    if op in ("font_size_band", "table_lookup"):
        # Bands: net weight/vol ranges map to minimum numeral height in mm
        # Format in check_definition:
        # "bands": [
        #   {"max_qty": 50, "min_height_mm": 1.0},
        #   {"min_qty": 50, "max_qty": 200, "min_height_mm": 2.0},
        #   {"min_qty": 200, "max_qty": 1000, "min_height_mm": 4.0},
        #   {"min_qty": 1000, "min_height_mm": 6.0}
        # ]
        bands = check_definition.get("bands") or []
        qty_raw = facts.get("net_quantity")
        qty_match = re.search(r'(\d+(?:\.\d+)?)', str(qty_raw)) if qty_raw else None
        qty_val = float(qty_match.group(1)) if qty_match else None

        # Find required minimum height
        required_min_mm = float(check_definition.get("default_min_height_mm", 2.0))
        if qty_val is not None:
            for b in bands:
                low = b.get("min_qty")
                high = b.get("max_qty")
                if low is not None and high is not None and low < qty_val <= high:
                    required_min_mm = float(b.get("min_height_mm", required_min_mm))
                    break
                elif low is None and high is not None and qty_val <= high:
                    required_min_mm = float(b.get("min_height_mm", required_min_mm))
                    break
                elif high is None and low is not None and qty_val > low:
                    required_min_mm = float(b.get("min_height_mm", required_min_mm))
                    break

        expected_repr = f">= {required_min_mm} mm"
        try:
            actual_height = float(actual_value)
            matched = actual_height >= required_min_mm
            detail = None if matched else f"Measured numeral height ({actual_height:.2f} mm) is less than required minimum ({required_min_mm:.2f} mm)."
            return matched, expected_repr, detail
        except (ValueError, TypeError) as e:
            return False, expected_repr, f"Invalid measured numeral height '{actual_value}': {e}"

    # Default fallback: unsupported operator
    return False, str(expected_val), f"Unsupported check definition operator: '{operator}'"

