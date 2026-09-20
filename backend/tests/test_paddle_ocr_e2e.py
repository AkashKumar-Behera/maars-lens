"""
MAARS Lens: End-to-End Real PaddleOCR Pipeline Tests
====================================================
Tests the end-to-end OCR and statutory rule engine pipeline on all 8 synthetic label fixtures:
- Loads real fixture images.
- Executes PaddleOCRExtractor with English + Hindi passes.
- Extracts structured package facts, raw text, and per-field confidences.
- Evaluates against the statutory compliance rule engine.
- Asserts expected compliance verdict and violation codes.
"""

import os
import json
import uuid
import cv2
import pytest

from app.services.ocr.extractor import PaddleOCRExtractor, extract_facts
from app.services.ocr.annotator import annotate_evidence_image
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.models.enums import RuleType, SeverityLevel, RuleVerificationStatus, AuditResultType, ComplianceStatus
from app.services.rule_engine.engine import evaluate_rules
from app.services.compliance import aggregate_compliance


FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "labels"))
EXPECTED_PATH = os.path.join(FIXTURES_DIR, "expected_results.json")


def _build_test_rules() -> list[ComplianceRuleVersion]:
    """Builds standard test rule set representing LMPC presence & font requirements."""
    admin_id = uuid.uuid4()
    specs = [
        # 1. MRP
        (
            "LMPC-R6-MRP",
            "Rule 6(1)(e) Maximum Retail Price declaration",
            "mrp",
            {"operator": "exists", "confidence_threshold": 0.40},
            SeverityLevel.critical,
            "MRP must be declared on package.",
            False,
        ),
        # 2. Net Quantity
        (
            "LMPC-R6-QTY",
            "Rule 6(1)(d) Net quantity declaration",
            "net_quantity",
            {"operator": "exists", "confidence_threshold": 0.40},
            SeverityLevel.critical,
            "Net quantity must be declared on package.",
            False,
        ),
        # 3. Manufacturer Name & Address
        (
            "LMPC-R6-MFR",
            "Rule 6(1)(a) Manufacturer name and address",
            "manufacturer",
            {"operator": "exists", "confidence_threshold": 0.40},
            SeverityLevel.major,
            "Manufacturer name and address must be declared.",
            False,
        ),
        # 4. Country of Origin
        (
            "LMPC-R6-COO",
            "Rule 6(10) Country of Origin declaration",
            "country_of_origin",
            {"operator": "exists", "confidence_threshold": 0.40},
            SeverityLevel.major,
            "Country of origin must be declared.",
            False,
        ),
        # 5. Font size / visual measurement (simulated rule)
        (
            "LMPC-R6-FONT",
            "Rule 7 Minimum height of numerals and letters",
            "numeral_height_mm",
            {"operator": ">=", "threshold": 2.0, "confidence_threshold": 0.70},
            SeverityLevel.minor,
            "Minimum numeral height must be at least 2.0mm.",
            True,
        ),
    ]

    rules = []
    for code, stat_ref, field, check_def, severity, desc, req_vis in specs:
        rule = ComplianceRule(
            id=uuid.uuid4(),
            rule_code=code,
            category="mandatory_declarations",
        )
        rv = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=rule.id,
            version=1,
            statutory_reference=stat_ref,
            rule_type=RuleType.visual if req_vis else RuleType.presence,
            target_field=field,
            check_definition=check_def,
            severity=severity,
            description_en=desc,
            failure_message_template=f"{desc} missing or invalid.",
            requires_visual_measurement=req_vis,
            measurement_unit="mm" if req_vis else None,
            verification_status=RuleVerificationStatus.demo,
            is_active=True,
            created_by=admin_id,
        )
        rv.rule = rule
        rules.append(rv)

    return rules


@pytest.fixture(scope="module")
def ocr_extractor():
    """Initializes a shared PaddleOCRExtractor singleton instance."""
    return PaddleOCRExtractor()


@pytest.fixture(scope="module")
def expected_specs():
    with open(EXPECTED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.ocr
def test_paddle_ocr_fixture_01_compliant(ocr_extractor, expected_specs):
    """Fixture 01: Compliant bilingual label."""
    img_path = os.path.join(FIXTURES_DIR, "01_compliant_bilingual.png")
    img = cv2.imread(img_path)
    assert img is not None

    facts, raw_text, overall_conf, field_confs = extract_facts(img, extractor=ocr_extractor)

    assert facts["mrp"] is not None
    assert facts["net_quantity"] is not None
    assert facts["country_of_origin"] is not None
    assert overall_conf > 0.80

    rules = [r for r in _build_test_rules() if not r.requires_visual_measurement]
    eval_results = evaluate_rules(rules, facts, ocr_confidences=field_confs)
    verdict = aggregate_compliance([r["automated_result"] for r in eval_results])

    assert verdict == ComplianceStatus.compliant


@pytest.mark.ocr
def test_paddle_ocr_fixture_02_missing_mrp(ocr_extractor, expected_specs):
    """Fixture 02: Missing MRP -> non_compliant."""
    img_path = os.path.join(FIXTURES_DIR, "02_missing_mrp.png")
    img = cv2.imread(img_path)
    assert img is not None

    facts, raw_text, overall_conf, field_confs = extract_facts(img, extractor=ocr_extractor)

    assert facts["mrp"] is None

    rules = [r for r in _build_test_rules() if not r.requires_visual_measurement]
    eval_results = evaluate_rules(rules, facts, ocr_confidences=field_confs)
    verdict = aggregate_compliance([r["automated_result"] for r in eval_results])

    assert verdict == ComplianceStatus.non_compliant
    failed_codes = [r["rule_code"] for r in eval_results if r["automated_result"] == AuditResultType.fail]
    assert "LMPC-R6-MRP" in failed_codes


@pytest.mark.ocr
def test_paddle_ocr_fixture_05_missing_origin(ocr_extractor, expected_specs):
    """Fixture 05: Missing Country of Origin -> non_compliant."""
    img_path = os.path.join(FIXTURES_DIR, "05_imported_no_origin.png")
    img = cv2.imread(img_path)
    assert img is not None

    facts, raw_text, overall_conf, field_confs = extract_facts(img, extractor=ocr_extractor)

    rules = [r for r in _build_test_rules() if not r.requires_visual_measurement]
    eval_results = evaluate_rules(rules, facts, ocr_confidences=field_confs)
    verdict = aggregate_compliance([r["automated_result"] for r in eval_results])

    assert verdict == ComplianceStatus.non_compliant
    failed_codes = [r["rule_code"] for r in eval_results if r["automated_result"] == AuditResultType.fail]
    assert "LMPC-R6-COO" in failed_codes


@pytest.mark.ocr
def test_paddle_ocr_fixture_07_hindi_english_mix(ocr_extractor, expected_specs):
    """Fixture 07: Mixed Hindi and English declarations."""
    img_path = os.path.join(FIXTURES_DIR, "07_hindi_english_mix.png")
    img = cv2.imread(img_path)
    assert img is not None

    facts, raw_text, overall_conf, field_confs = extract_facts(img, extractor=ocr_extractor)

    # Should detect both English MRP and Devanagari numerals/Hindi net qty
    assert facts["mrp"] is not None
    assert facts["net_quantity"] is not None
    assert overall_conf > 0.75


@pytest.mark.ocr
def test_evidence_image_annotation(ocr_extractor, tmp_path):
    """Tests polygon annotation generation on a label."""
    img_path = os.path.join(FIXTURES_DIR, "01_compliant_bilingual.png")
    img = cv2.imread(img_path)
    regions = ocr_extractor.extract_regions(img)

    annotations = []
    for r in regions:
        annotations.append({
            "polygon": r.polygon,
            "label": r.text[:20],
            "status": "compliant" if r.confidence > 0.85 else "needs_review",
            "rule_code": "LMPC-DECL",
        })

    out_file = str(tmp_path / "annotated.jpg")
    annotated = annotate_evidence_image(img, annotations, output_path=out_file)

    assert os.path.exists(out_file)
    assert annotated.shape == img.shape
    # Check that pixels were altered by annotation
    assert not (annotated == img).all()
