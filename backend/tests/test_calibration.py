"""
Unit and Integration Tests for Optical Scale Calibration and Rule 7 Font Size Verification
========================================================================================
Verifies:
1. Pack dimensions scale computation (Priority 1).
2. Reference object detection scale computation (Priority 2).
3. Image flatbed scan DPI scale computation (Priority 3).
4. Printable calibration card PDF generation.
5. Integration with Rule 7 font size evaluator:
   - Synthetic label with known pixel height and calibration scale factor.
   - Converted mm height evaluated deterministically against Rule 7 bands.
   - Uncalibrated image yields needs_review (deterministic safety invariant).
   - Insufficient font height yields fail with exact mm deficit detail.
   - Compliant font height yields pass.
"""

import numpy as np
import cv2
import pytest

from app.models.enums import AuditResultType, RuleType, SeverityLevel
from app.models.rule import ComplianceRuleVersion
from app.services.rule_engine.engine import evaluate_single_rule
from app.services.ocr.calibration import (
    compute_scale_from_pack_dimensions,
    compute_scale_from_dpi,
    detect_reference_object_scale,
    calibrate_image_scale,
    generate_printable_calibration_card_pdf,
)


def test_pack_dimensions_calibration():
    # Pack: 100mm wide x 200mm high, rendered into 500px wide x 1000px high bbox
    bbox = [0, 0, 500, 1000]
    scale, conf, notes = compute_scale_from_pack_dimensions(100.0, 200.0, bbox)
    assert scale is not None
    assert pytest.approx(scale, rel=1e-3) == 0.20  # 0.20 mm per pixel
    assert conf >= 0.80
    assert "100.0x200.0 mm" in notes


def test_dpi_calibration():
    # 300 DPI flatbed scan: 25.4 / 300 = 0.084666 mm per px
    scale, conf, notes = compute_scale_from_dpi(300.0)
    assert scale is not None
    assert pytest.approx(scale, rel=1e-3) == 25.4 / 300.0
    assert conf >= 0.90
    assert "300.0 DPI" in notes


def test_reference_object_scale_credit_card():
    # Create synthetic image with a credit card outline (85.60 x 53.98 mm)
    # At 0.2 mm/px, width = 428 px, height = 270 px (AR = 1.5857)
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    cv2.rectangle(img, (100, 100), (528, 370), (255, 255, 255), -1)

    scale, conf, notes = detect_reference_object_scale(img, "credit_card")
    assert scale is not None
    # Expected scale close to 85.60 / 428 = 0.20 mm/px
    assert pytest.approx(scale, rel=0.05) == 0.20
    assert conf >= 0.75
    assert "credit_card" in notes


def test_printable_calibration_card_pdf():
    pdf_bytes = generate_printable_calibration_card_pdf()
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_rule7_font_size_uncalibrated_invariance():
    # Invariant: Uncalibrated visual measurement deterministically yields needs_review
    rule_ver = ComplianceRuleVersion(
        id="00000000-0000-0000-0000-000000000007",
        rule_id="00000000-0000-0000-0000-000000000007",
        version=1,
        statutory_reference="Rule 7(1) - Minimum Font Size of Net Quantity",
        rule_type=RuleType.visual,
        requires_visual_measurement=True,
        target_field="numeral_height_mm",
        check_definition={
            "operator": "font_size_band",
            "bands": [
                {"max_qty": 50, "min_height_mm": 1.0},
                {"min_qty": 50, "max_qty": 200, "min_height_mm": 2.0},
                {"min_qty": 200, "max_qty": 1000, "min_height_mm": 4.0},
                {"min_qty": 1000, "min_height_mm": 6.0},
            ],
            "default_min_height_mm": 2.0,
        },
        severity=SeverityLevel.minor,
    )

    facts = {"net_quantity": "500 g", "numeral_height_mm": 15.0}  # 15px uncalibrated
    visual_measurements = {
        "calibration": {"measurement_reliable": False},
        "text_regions": [
            {
                "label": "numeral_height_mm",
                "estimated_text_height_px": 15,
                "measurement_reliable": False,
            }
        ],
    }

    res = evaluate_single_rule(rule_ver, facts, visual_measurements=visual_measurements)
    assert res["automated_result"] == AuditResultType.needs_review
    assert res["measurement_reliable"] is False


def test_rule7_font_size_calibrated_pass_and_fail():
    rule_ver = ComplianceRuleVersion(
        id="00000000-0000-0000-0000-000000000007",
        rule_id="00000000-0000-0000-0000-000000000007",
        version=1,
        statutory_reference="Rule 7(1) - Minimum Font Size of Net Quantity",
        rule_type=RuleType.visual,
        requires_visual_measurement=True,
        target_field="numeral_height_mm",
        check_definition={
            "operator": "font_size_band",
            "bands": [
                {"max_qty": 50, "min_height_mm": 1.0},
                {"min_qty": 50, "max_qty": 200, "min_height_mm": 2.0},
                {"min_qty": 200, "max_qty": 1000, "min_height_mm": 4.0},
                {"min_qty": 1000, "min_height_mm": 6.0},
            ],
            "default_min_height_mm": 2.0,
        },
        severity=SeverityLevel.minor,
    )

    # 1. 500g package requires min 4.0 mm
    # Case A: Measured 5.0 mm (Pass)
    facts_pass = {"net_quantity": "500 g", "numeral_height_mm": 5.0}
    vm_pass = {
        "calibration": {"measurement_reliable": True, "scale_factor_mm_per_px": 0.20},
        "text_regions": [
            {
                "label": "numeral_height_mm",
                "estimated_text_height_px": 25,
                "estimated_text_height_mm": 5.0,
                "measurement_reliable": True,
            }
        ],
    }
    res_pass = evaluate_single_rule(rule_ver, facts_pass, visual_measurements=vm_pass)
    assert res_pass["automated_result"] == AuditResultType.pass_
    assert res_pass["measurement_reliable"] is True

    # Case B: Measured 2.5 mm on a 500g package (Fail - required is 4.0mm)
    facts_fail = {"net_quantity": "500 g", "numeral_height_mm": 2.5}
    vm_fail = {
        "calibration": {"measurement_reliable": True, "scale_factor_mm_per_px": 0.20},
        "text_regions": [
            {
                "label": "numeral_height_mm",
                "estimated_text_height_px": 12,
                "estimated_text_height_mm": 2.5,
                "measurement_reliable": True,
            }
        ],
    }
    res_fail = evaluate_single_rule(rule_ver, facts_fail, visual_measurements=vm_fail)
    assert res_fail["automated_result"] == AuditResultType.fail
    assert res_fail["measurement_reliable"] is True
    assert "Measured numeral height (2.50 mm) is less than required minimum (4.00 mm)" in res_fail["automated_reason"]
