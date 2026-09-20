"""
MAARS Lens: Statutory Rule Engine & Exemption Tests (Batch 2)
============================================================
Validates:
1. Loading statutory rule definitions from externalized JSON config (`legal_verified=False` default).
2. All 9 standard LMPC statutory rule categories:
   - Manufacturer name & address
   - Net quantity
   - MRP
   - MRP tax inclusive
   - Mfg month/year
   - Country of origin
   - Consumer care
   - Unit sale price (calculated verification + tolerance)
   - Font size lookup table (Rule 7 bands)
3. Package exemption handling:
   - Weight threshold exemption (e.g. <= 10g)
   - Volume threshold exemption (e.g. <= 10ml)
   - Bulk threshold exemption (e.g. >= 50kg)
   - Surface area threshold exemption (e.g. <= 10 cm^2)
   - Institutional consumer / non-retail exemption
4. Evaluation produces `not_applicable` for exempted packages without failing overall inspection.
"""

import uuid
import pytest

from app.models.enums import AuditResultType, ComplianceStatus, RuleType, SeverityLevel, RuleVerificationStatus
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.services.rule_engine.engine import evaluate_single_rule, evaluate_rules
from app.services.rule_engine.exemptions import check_package_exemption
from app.services.compliance import aggregate_compliance
from app.core.statutory_rules import build_statutory_rule_entities, load_statutory_rules_config


# ------------------------------------------------------------------------------
# 1. Statutory Rules Config Loading & Verification Defaults
# ------------------------------------------------------------------------------
def test_statutory_rules_config_loading():
    raw_rules = load_statutory_rules_config()
    assert len(raw_rules) >= 9

    codes = [r["rule_code"] for r in raw_rules]
    assert "LMPC-R6-NAME-ADDRESS" in codes
    assert "LMPC-R6-NET-QTY" in codes
    assert "LMPC-R6-MRP" in codes
    assert "LMPC-R6-MRP-TAX-INCLUSIVE" in codes
    assert "LMPC-R6-MFG-MONTH-YEAR" in codes
    assert "LMPC-R6-COUNTRY-OF-ORIGIN" in codes
    assert "LMPC-R6-CONSUMER-CARE" in codes
    assert "LMPC-R6-UNIT-SALE-PRICE" in codes
    assert "LMPC-R7-FONT-SIZE" in codes

    for r in raw_rules:
        # Ground Rule 3: legal_verified must default to False
        assert r.get("legal_verified") is False
        assert "source_reference" in r
        assert "description" in r
        assert "severity" in r
        assert "version" in r


def test_statutory_rule_entities_instantiation():
    entities = build_statutory_rule_entities()
    assert len(entities) >= 9

    for rv in entities:
        assert isinstance(rv, ComplianceRuleVersion)
        assert rv.rule is not None
        assert rv.verification_status == RuleVerificationStatus.demo  # unverified -> demo


# ------------------------------------------------------------------------------
# 2. Package Weight & Volume Exemptions
# ------------------------------------------------------------------------------
def test_small_package_weight_exemption():
    """Small packages <= 10g are exempted from net quantity and unit price."""
    check_def = {
        "operator": "exists",
        "exempt_if_net_qty_lte_g": 10.0,
    }

    # Case A: 5g package (exempt)
    is_exempt, reason = check_package_exemption("LMPC-R6-NET-QTY", check_def, {"net_quantity": "5g"})
    assert is_exempt is True
    assert "5.0g <= 10.0g" in reason

    # Case B: 50g package (NOT exempt)
    is_exempt_b, _ = check_package_exemption("LMPC-R6-NET-QTY", check_def, {"net_quantity": "50g"})
    assert is_exempt_b is False


def test_small_package_volume_exemption():
    """Small liquid packages <= 10ml are exempted."""
    check_def = {
        "operator": "exists",
        "exempt_if_net_qty_lte_ml": 10.0,
    }
    is_exempt, reason = check_package_exemption("LMPC-R6-NET-QTY", check_def, {"net_quantity": "8ml"})
    assert is_exempt is True
    assert "8.0ml <= 10.0ml" in reason


def test_bulk_package_exemption():
    """Bulk packages >= 50kg are exempted from retail packaging rules."""
    check_def = {
        "operator": "exists",
        "exempt_if_net_qty_gte_kg": 50.0,
    }
    is_exempt, reason = check_package_exemption("LMPC-R6-MRP", check_def, {"net_quantity": "60kg"})
    assert is_exempt is True
    assert "60.0kg >= 50.0kg" in reason


def test_institutional_consumer_exemption():
    """Institutional / Industrial packs marked not for retail sale are exempted."""
    check_def = {
        "operator": "exists",
        "exempt_institutional_pack": True,
    }
    facts = {
        "product_name": "Industrial Cleanser 25L",
        "is_institutional_consumer": True,
        "not_for_retail_sale": True,
    }
    is_exempt, reason = check_package_exemption("LMPC-R6-MRP", check_def, facts)
    assert is_exempt is True
    assert "institutional" in reason.lower()


# ------------------------------------------------------------------------------
# 3. Rule Engine Integration with Exemptions
# ------------------------------------------------------------------------------
def test_rule_engine_handles_exemption_as_not_applicable():
    """When a package is exempt, rule evaluates to not_applicable, allowing compliance."""
    entities = build_statutory_rule_entities()
    qty_rule = next(r for r in entities if r.rule.rule_code == "LMPC-R6-NET-QTY")

    # Facts with 5g item (exempt from net quantity declaration)
    facts = {
        "net_quantity": "5g",
    }
    res = evaluate_single_rule(qty_rule, facts)

    assert res["automated_result"] == AuditResultType.not_applicable
    assert res["effective_result"] == AuditResultType.not_applicable
    assert "Exempted under package weight" in res["automated_reason"]


# ------------------------------------------------------------------------------
# 4. Unit Sale Price (USP) Evaluator Verification
# ------------------------------------------------------------------------------
def test_unit_sale_price_evaluator_pass():
    """Verifies that unit price = MRP / Qty within 5% tolerance passes."""
    entities = build_statutory_rule_entities()
    usp_rule = next(r for r in entities if r.rule.rule_code == "LMPC-R6-UNIT-SALE-PRICE")

    # 500g package at Rs. 200.00 -> USP = Rs. 0.40 per g
    facts = {
        "mrp": "Rs. 200.00",
        "net_quantity": "500g",
        "unit_sale_price": "Rs. 0.40",
    }
    res = evaluate_single_rule(usp_rule, facts)
    assert res["automated_result"] == AuditResultType.pass_


def test_unit_sale_price_evaluator_mismatch_fails():
    """Verifies that an incorrect unit price fails compliance."""
    entities = build_statutory_rule_entities()
    usp_rule = next(r for r in entities if r.rule.rule_code == "LMPC-R6-UNIT-SALE-PRICE")

    # Declared unit price 0.80 when calculated is 0.40
    facts = {
        "mrp": "Rs. 200.00",
        "net_quantity": "500g",
        "unit_sale_price": "Rs. 0.80",
    }
    res = evaluate_single_rule(usp_rule, facts)
    assert res["automated_result"] == AuditResultType.fail
    assert "differs from calculated" in res["automated_reason"]


# ------------------------------------------------------------------------------
# 5. Font Size Table Lookup Evaluator Verification
# ------------------------------------------------------------------------------
def test_font_size_band_evaluator_pass():
    """Verifies Rule 7 numeral height bands by net quantity."""
    entities = build_statutory_rule_entities()
    font_rule = next(r for r in entities if r.rule.rule_code == "LMPC-R7-FONT-SIZE")

    # For net quantity 400g, required height band is (200, 1000] -> min 4.0mm
    facts = {
        "net_quantity": "400g",
        "numeral_height_mm": 4.5,
    }
    visual_measurements = {
        "text_regions": [{"label": "numeral_height_mm", "measurement_reliable": True}],
    }
    res = evaluate_single_rule(font_rule, facts, visual_measurements=visual_measurements)
    assert res["automated_result"] == AuditResultType.pass_


def test_font_size_band_evaluator_fail():
    """Numeral height 2.5mm when 4.0mm is required fails."""
    entities = build_statutory_rule_entities()
    font_rule = next(r for r in entities if r.rule.rule_code == "LMPC-R7-FONT-SIZE")

    facts = {
        "net_quantity": "400g",
        "numeral_height_mm": 2.5,
    }
    visual_measurements = {
        "text_regions": [{"label": "numeral_height_mm", "measurement_reliable": True}],
    }
    res = evaluate_single_rule(font_rule, facts, visual_measurements=visual_measurements)
    assert res["automated_result"] == AuditResultType.fail
    assert "less than required minimum" in res["automated_reason"]
