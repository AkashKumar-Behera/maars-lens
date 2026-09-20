"""
MAARS Lens: Core Services Validation Suite
==========================================
Validates:
1. Import & syntax validation
2. Compliance aggregation tests (automated vs final, fail dominance, short-circuiting)
3. Finalization guard tests (assert_inspection_unfinalized, immutable state, manual review guards)
4. AES encrypt/decrypt round-trip (AES-256-GCM, Unicode, authentication tag tamper resistance)
5. SHA-256 determinism (canonical key sorting, formatting sha256:<64-hex>, collision resistance)
6. Rule engine demo tests (ComplianceRuleVersion.check_definition evaluation, confidence thresholds)
7. PDF generation sanity check (ReportLab generation, valid %PDF bytes, metadata rendering)
"""

import uuid
import datetime
import pytest
from cryptography.exceptions import InvalidTag

from app.models.enums import AuditResultType, ComplianceStatus, RuleType, SeverityLevel, RuleVerificationStatus
from app.models.inspection import Inspection
from app.models.rule import ComplianceRuleVersion
from app.services.compliance import (
    assert_inspection_unfinalized,
    InspectionAlreadyFinalizedError,
    InvalidManualReviewError,
    compute_effective_result,
    aggregate_compliance,
    compute_inspection_compliance,
)
from app.core.security import encrypt_data, decrypt_data, get_aesgcm
from app.services.pdf.generator import compute_report_hash, generate_report_pdf
from app.services.rule_engine.engine import evaluate_single_rule, evaluate_rules


# ==============================================================================
# 1. IMPORT & SYNTAX VALIDATION
# ==============================================================================

def test_imports_and_exports():
    import app.models as models
    import app.schemas as schemas
    import app.services as services

    assert hasattr(services, "assert_inspection_unfinalized")
    assert hasattr(services, "compute_effective_result")
    assert hasattr(services, "aggregate_compliance")
    assert hasattr(services, "compute_report_hash")
    assert hasattr(services, "generate_report_pdf")
    assert hasattr(services, "evaluate_single_rule")
    assert hasattr(services, "encrypt_data")
    assert hasattr(services, "decrypt_data")


# ==============================================================================
# 2. COMPLIANCE AGGREGATION TESTS
# ==============================================================================

def test_compliance_aggregation_all_pass():
    results = [AuditResultType.pass_, AuditResultType.pass_]
    assert aggregate_compliance(results) == ComplianceStatus.compliant


def test_compliance_aggregation_with_not_applicable():
    results = [AuditResultType.pass_, AuditResultType.not_applicable]
    assert aggregate_compliance(results) == ComplianceStatus.compliant


def test_compliance_aggregation_fail_dominates():
    # Even if needs_review is present, a statutory fail marks non_compliant
    results = [AuditResultType.pass_, AuditResultType.needs_review, AuditResultType.fail]
    assert aggregate_compliance(results) == ComplianceStatus.non_compliant


def test_compliance_aggregation_needs_review():
    results = [AuditResultType.pass_, AuditResultType.needs_review]
    assert aggregate_compliance(results) == ComplianceStatus.needs_review


def test_compliance_aggregation_no_applicable_rules():
    # Locked rule: zero applicable rules (empty list or all not_applicable) -> needs_review
    assert aggregate_compliance([]) == ComplianceStatus.needs_review
    assert aggregate_compliance([AuditResultType.not_applicable]) == ComplianceStatus.needs_review
    assert aggregate_compliance([AuditResultType.not_applicable, AuditResultType.not_applicable]) == ComplianceStatus.needs_review


def test_dual_layer_compliance_computation():
    # Case: Automated engine detected a fail, but Officer manual review resolved it with valid reason
    audit_items = [
        {
            "automated_result": AuditResultType.fail,
            "effective_result": AuditResultType.pass_,
        },
        {
            "automated_result": AuditResultType.pass_,
            "effective_result": AuditResultType.pass_,
        }
    ]
    auto_comp, final_comp = compute_inspection_compliance(audit_items)
    assert auto_comp == ComplianceStatus.non_compliant
    assert final_comp == ComplianceStatus.compliant


def test_dual_layer_compliance_officer_marks_fail():
    # Case: Automated was needs_review, Officer verified and marked fail
    audit_items = [
        {
            "automated_result": AuditResultType.needs_review,
            "effective_result": AuditResultType.fail,
        }
    ]
    auto_comp, final_comp = compute_inspection_compliance(audit_items)
    assert auto_comp == ComplianceStatus.needs_review
    assert final_comp == ComplianceStatus.non_compliant


# ==============================================================================
# 3. FINALIZATION GUARD TESTS
# ==============================================================================

def test_assert_inspection_unfinalized_on_unfinalized():
    # Inspection object with is_finalized=False
    insp = Inspection(
        id=uuid.uuid4(),
        client_submission_id=uuid.uuid4(),
        officer_id=uuid.uuid4(),
        area_id=uuid.uuid4(),
        image_storage_path="mock/path.jpg",
        is_finalized=False,
    )
    # Should not raise
    assert_inspection_unfinalized(insp)
    assert_inspection_unfinalized(False)
    assert_inspection_unfinalized({"is_finalized": False})


def test_assert_inspection_unfinalized_on_finalized():
    insp = Inspection(
        id=uuid.uuid4(),
        client_submission_id=uuid.uuid4(),
        officer_id=uuid.uuid4(),
        area_id=uuid.uuid4(),
        image_storage_path="mock/path.jpg",
        is_finalized=True,
    )
    with pytest.raises(InspectionAlreadyFinalizedError):
        assert_inspection_unfinalized(insp)

    with pytest.raises(InspectionAlreadyFinalizedError):
        assert_inspection_unfinalized(True)

    with pytest.raises(InspectionAlreadyFinalizedError):
        assert_inspection_unfinalized({"is_finalized": True})


def test_effective_result_no_manual_review():
    res = compute_effective_result(
        automated_result=AuditResultType.fail,
        manual_review_result=None,
        manual_review_reason=None,
    )
    assert res == AuditResultType.fail


def test_effective_result_valid_manual_override():
    res = compute_effective_result(
        automated_result=AuditResultType.fail,
        manual_review_result=AuditResultType.pass_,
        manual_review_reason="Declaration clearly visible under oblique lighting upon officer re-inspection.",
    )
    assert res == AuditResultType.pass_


def test_effective_result_missing_reason_rejected():
    with pytest.raises(InvalidManualReviewError):
        compute_effective_result(
            automated_result=AuditResultType.fail,
            manual_review_result=AuditResultType.pass_,
            manual_review_reason=None,
        )

    with pytest.raises(InvalidManualReviewError):
        compute_effective_result(
            automated_result=AuditResultType.fail,
            manual_review_result=AuditResultType.pass_,
            manual_review_reason="   ",  # Blank / whitespace only
        )


def test_effective_result_not_applicable_manual_rejected():
    with pytest.raises(InvalidManualReviewError):
        compute_effective_result(
            automated_result=AuditResultType.fail,
            manual_review_result=AuditResultType.not_applicable,
            manual_review_reason="Field not needed",
        )


# ==============================================================================
# 4. AES-256-GCM ENCRYPT/DECRYPT ROUND-TRIP
# ==============================================================================

def test_aes_encrypt_decrypt_round_trip():
    # Locked spec: AES-256-GCM is used exclusively for sensitive customer contact data
    customer_contact = "+919876543210"
    encrypted = encrypt_data(customer_contact)

    # Validate output structure: 12-byte nonce + ciphertext + 16-byte tag
    assert isinstance(encrypted, bytes)
    assert len(encrypted) >= 12 + 16 + len(customer_contact.encode("utf-8"))

    decrypted = decrypt_data(encrypted)
    assert decrypted == customer_contact


def test_aes_unicode_round_trip():
    customer_note = "उपभोक्ता शिकायत संपर्क: +919876543210"
    encrypted = encrypt_data(customer_note)
    decrypted = decrypt_data(encrypted)
    assert decrypted == customer_note


def test_aes_tamper_detection():
    customer_email = "consumer.alert@packaged-commodities.gov.in"
    encrypted = bytearray(encrypt_data(customer_email))

    # Tamper with the ciphertext/tag bytes
    encrypted[-1] ^= 0xFF

    with pytest.raises(InvalidTag):
        decrypt_data(bytes(encrypted))


# ==============================================================================
# 5. SHA-256 REPORT HASHING DETERMINISM
# ==============================================================================

def test_sha256_report_hash_determinism():
    test_uuid = uuid.UUID("11111111-2222-3333-4444-555555555555")
    dt = datetime.datetime(2026, 9, 18, 12, 0, 0)

    payload_a = {
        "id": test_uuid,
        "product_name": "Premium Tea 500g",
        "brand_name": "AssamGold",
        "final_compliance": "compliant",
        "evaluated_at": dt,
        "audit_results": [
            {"rule_code": "DEMO-MRP", "result": "pass"},
            {"rule_code": "DEMO-QTY", "result": "pass"},
        ]
    }

    # Same payload with re-ordered keys and reversed outer order
    payload_b = {
        "audit_results": [
            {"result": "pass", "rule_code": "DEMO-MRP"},
            {"rule_code": "DEMO-QTY", "result": "pass"},
        ],
        "evaluated_at": dt,
        "final_compliance": "compliant",
        "brand_name": "AssamGold",
        "product_name": "Premium Tea 500g",
        "id": test_uuid,
    }

    hash_a = compute_report_hash(payload_a)
    hash_b = compute_report_hash(payload_b)

    assert hash_a == hash_b
    assert hash_a.startswith("sha256:")
    assert len(hash_a) == 71  # "sha256:" (7) + 64 hex characters = 71 chars


def test_sha256_hash_distinct():
    payload_1 = {"product_name": "Product A", "mrp": 100}
    payload_2 = {"product_name": "Product B", "mrp": 100}

    assert compute_report_hash(payload_1) != compute_report_hash(payload_2)


# ==============================================================================
# 6. RULE ENGINE DEMO TESTS
# ==============================================================================

def test_rule_engine_presence_demo_rule():
    admin_id = uuid.uuid4()
    rule_id = uuid.uuid4()

    mrp_rule_v1 = ComplianceRuleVersion(
        id=uuid.uuid4(),
        rule_id=rule_id,
        version=1,
        statutory_reference="Rule 6(1)(e) Maximum Retail Price declaration",
        rule_type=RuleType.presence,
        target_field="mrp",
        check_definition={"operator": "exists", "confidence_threshold": 0.50},
        severity=SeverityLevel.critical,
        description_en="MRP must be declared on package.",
        failure_message_template="MRP declaration is missing from package facts.",
        requires_visual_measurement=False,
        verification_status=RuleVerificationStatus.demo,
        is_active=True,
        created_by=admin_id,
    )

    # 1. Passing case: MRP present and confidence high
    res_pass = evaluate_single_rule(
        rule_version=mrp_rule_v1,
        facts={"mrp": "Rs. 199.00 inclusive of all taxes"},
        ocr_confidences={"mrp": 0.94},
    )
    assert res_pass["automated_result"] == AuditResultType.pass_
    assert res_pass["effective_result"] == AuditResultType.pass_
    assert res_pass["severity"] == SeverityLevel.critical

    # 2. Failing case: MRP missing
    res_fail = evaluate_single_rule(
        rule_version=mrp_rule_v1,
        facts={"brand_name": "Test Brand"},
        ocr_confidences={},
    )
    assert res_fail["automated_result"] == AuditResultType.fail
    assert "missing" in res_fail["automated_reason"].lower()

    # 3. Low OCR confidence case: triggers needs_review
    res_review = evaluate_single_rule(
        rule_version=mrp_rule_v1,
        facts={"mrp": "Rs. 199"},
        ocr_confidences={"mrp": 0.35},  # Below 0.50 threshold
    )
    assert res_review["automated_result"] == AuditResultType.needs_review
    assert "Low OCR confidence" in res_review["automated_reason"]


def test_rule_engine_regex_and_numeric_checks():
    admin_id = uuid.uuid4()

    # Regex Rule: Manufacturing date in MM/YYYY format
    date_rule = ComplianceRuleVersion(
        id=uuid.uuid4(),
        rule_id=uuid.uuid4(),
        version=1,
        statutory_reference="Rule 6(1)(d) Month and Year of Manufacture",
        rule_type=RuleType.pattern,
        target_field="mfg_date",
        check_definition={"operator": "regex", "value": r"^(0[1-9]|1[0-2])\/\d{4}$"},
        severity=SeverityLevel.minor,
        description_en="Date in MM/YYYY format.",
        failure_message_template="Invalid manufacturing date format.",
        requires_visual_measurement=False,
        verification_status=RuleVerificationStatus.demo,
        is_active=True,
        created_by=admin_id,
    )

    valid_res = evaluate_single_rule(date_rule, facts={"mfg_date": "08/2026"})
    assert valid_res["automated_result"] == AuditResultType.pass_

    invalid_res = evaluate_single_rule(date_rule, facts={"mfg_date": "2026-08-15"})
    assert invalid_res["automated_result"] == AuditResultType.fail


# ==============================================================================
# 7. PDF GENERATION SANITY CHECK
# ==============================================================================

def test_pdf_generation_sanity():
    insp_id = uuid.uuid4()
    officer_id = uuid.uuid4()

    inspection_data = {
        "id": insp_id,
        "officer_id": officer_id,
        "product_name": "Organic Wheat Flour 5kg",
        "brand_name": "NatureFresh",
        "compliance_status": "compliant",
        "audit_results": [
            {
                "rule_code": "DEMO-TEST-MRP-PRESENCE",
                "statutory_reference": "Rule 6(1)(e)",
                "automated_result": AuditResultType.pass_,
                "manual_review_result": None,
                "effective_result": AuditResultType.pass_,
            },
            {
                "rule_code": "DEMO-TEST-NET-QTY",
                "statutory_reference": "Rule 6(1)(f)",
                "automated_result": AuditResultType.pass_,
                "manual_review_result": None,
                "effective_result": AuditResultType.pass_,
            }
        ]
    }

    pdf_bytes = generate_report_pdf(inspection_data)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500  # Non-trivial PDF size
    assert pdf_bytes.startswith(b"%PDF")  # Valid PDF signature
    assert b"%%EOF" in pdf_bytes[-1024:]  # Standard PDF EOF marker
