"""
MAARS Lens: Statutory Rule Engine Exemptions & Applicability Guard
==================================================================
Evaluates statutory exemption conditions (e.g. package weight/volume thresholds,
surface area, export status, institutional consumers) under the Legal Metrology
(Packaged Commodities) Rules, 2011.

GROUND RULES:
- Legal thresholds live in DB/config, never hardcoded in evaluators.
- All exemption definitions specify rule_code, source_reference, description,
  and default legal_verified=False until official Gazette verification.
"""

from typing import Any, Dict, Optional, Tuple
import re
from app.models.enums import AuditResultType


def check_package_exemption(
    rule_code: str,
    check_definition: Dict[str, Any],
    facts: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Determines whether a statutory rule is exempted for a package based on:
    - Net weight / net volume threshold (e.g., packages <= 10g or <= 10ml).
    - Package surface area threshold (e.g., packages <= 10 cm^2 exempted from certain font rules).
    - Agricultural produce packages > 50kg.
    - Fast food items packed by restaurant/hotel.
    - Institutional / industrial consumer pack declarations.

    Returns:
        (is_exempt: bool, exemption_reason: Optional[str])
    """
    exemptions_config = check_definition.get("exemptions") or []
    if not exemptions_config:
        # Check rule-level exemption keys in check_definition
        min_net_qty_g = check_definition.get("exempt_if_net_qty_lte_g")
        min_net_qty_ml = check_definition.get("exempt_if_net_qty_lte_ml")
        max_net_qty_kg = check_definition.get("exempt_if_net_qty_gte_kg")
        exempt_surface_area = check_definition.get("exempt_if_surface_area_lte_cm2")
        exempt_commodity_types = check_definition.get("exempt_commodity_types") or []
    else:
        min_net_qty_g = None
        min_net_qty_ml = None
        max_net_qty_kg = None
        exempt_surface_area = None
        exempt_commodity_types = []
        for ex in exemptions_config:
            if ex.get("type") == "net_quantity_lte_g":
                min_net_qty_g = ex.get("threshold")
            elif ex.get("type") == "net_quantity_lte_ml":
                min_net_qty_ml = ex.get("threshold")
            elif ex.get("type") == "net_quantity_gte_kg":
                max_net_qty_kg = ex.get("threshold")
            elif ex.get("type") == "surface_area_lte_cm2":
                exempt_surface_area = ex.get("threshold")
            elif ex.get("type") == "commodity_type":
                exempt_commodity_types.extend(ex.get("values", []))

    # Parse numerical net quantity if available
    raw_qty = facts.get("net_quantity")
    qty_val, qty_unit = _parse_quantity_and_unit(raw_qty) if raw_qty else (None, None)

    # 1. Check small package exemption (weight <= threshold g)
    if min_net_qty_g is not None and qty_val is not None and qty_unit in ("g", "gm", "gram", "grams"):
        if qty_val <= float(min_net_qty_g):
            return True, f"Exempted under package weight threshold (net quantity {qty_val}{qty_unit} <= {min_net_qty_g}g)."

    # 2. Check small package exemption (volume <= threshold ml)
    if min_net_qty_ml is not None and qty_val is not None and qty_unit in ("ml", "milli", "millilitre", "milliliter"):
        if qty_val <= float(min_net_qty_ml):
            return True, f"Exempted under package volume threshold (net volume {qty_val}{qty_unit} <= {min_net_qty_ml}ml)."

    # 3. Check bulk package exemption (e.g. > 50 kg / 50 ltr)
    if max_net_qty_kg is not None and qty_val is not None:
        val_kg = qty_val if qty_unit in ("kg", "kilogram") else (qty_val / 1000.0 if qty_unit in ("g", "gm") else None)
        if val_kg is not None and val_kg >= float(max_net_qty_kg):
            return True, f"Exempted under bulk package threshold ({val_kg}kg >= {max_net_qty_kg}kg)."

    # 4. Check surface area exemption
    surface_area = facts.get("surface_area_cm2")
    if exempt_surface_area is not None and surface_area is not None:
        try:
            if float(surface_area) <= float(exempt_surface_area):
                return True, f"Exempted under small surface area threshold ({surface_area} cm2 <= {exempt_surface_area} cm2)."
        except (ValueError, TypeError):
            pass

    # 5. Check institutional consumer declaration
    if facts.get("is_institutional_consumer") or facts.get("not_for_retail_sale"):
        if check_definition.get("exempt_institutional_pack", False):
            return True, "Exempted as package is marked for institutional/industrial consumer (not for retail sale)."

    # 6. Check commodity type exemption
    commodity = (facts.get("commodity_type") or facts.get("product_category") or "").strip().lower()
    if commodity and exempt_commodity_types:
        for exc in exempt_commodity_types:
            if exc.lower() in commodity:
                return True, f"Exempted for commodity type '{commodity}' under statutory category exception."

    return False, None


def _parse_quantity_and_unit(qty_str: Any) -> Tuple[Optional[float], Optional[str]]:
    """Helper to extract numerical value and normalized unit from quantity string."""
    if isinstance(qty_str, (int, float)):
        return float(qty_str), "unit"
    if not isinstance(qty_str, str):
        return None, None

    match = re.search(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', qty_str)
    if match:
        try:
            val = float(match.group(1))
            unit = match.group(2).lower()
            return val, unit
        except (ValueError, TypeError):
            pass
    return None, None
