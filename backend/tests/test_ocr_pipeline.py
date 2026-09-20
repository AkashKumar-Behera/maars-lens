"""
MAARS Lens: OCR & Preprocessing Pipeline Tests
==============================================
Validates Step 4 requirements:
(a) Preprocessing output properties:
    - Grayscale conversion (ensures 1 channel / 2D numpy array)
    - Denoising, CLAHE enhancement, and error handling for invalid/empty buffers.
(b) Extraction returns text + confidence score per region on a known sample.
(c) Low-confidence OCR result triggers 'needs_review' via the existing rule engine gating.
"""

import uuid
import cv2
import numpy as np
import pytest

from app.services.ocr.preprocessor import preprocess_image, PreprocessingError
from app.services.ocr.extractor import (
    BaseOCRExtractor,
    MockOCRExtractor,
    OCRResultRegion,
    extract_facts,
    set_ocr_extractor,
)
from app.models.rule import ComplianceRuleVersion
from app.models.enums import AuditResultType, RuleType, SeverityLevel
from app.services.rule_engine.engine import evaluate_single_rule


def _create_synthetic_test_image(text: str = "MRP Rs. 150") -> bytes:
    """Generates a synthetic test image containing text rendered onto a white background."""
    img = np.ones((200, 500, 3), dtype=np.uint8) * 255
    # Draw simple dark text
    cv2.putText(
        img,
        text,
        (30, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 0, 0),
        2,
        cv2.LINE_AA,
    )
    success, buffer = cv2.imencode(".jpg", img)
    assert success, "Failed to encode test image"
    return buffer.tobytes()


# ------------------------------------------------------------------------------
# Requirement (a): Preprocessing output properties
# ------------------------------------------------------------------------------
def test_preprocessing_valid_image_produces_single_channel_and_valid_shape():
    """Verifies that preprocessing converts a 3-channel image to a 1-channel grayscale ndarray with metadata."""
    image_bytes = _create_synthetic_test_image("MRP Rs. 250 Net Qty 500g")
    processed_img, metadata = preprocess_image(image_bytes)

    # 1. Output must be a numpy ndarray of uint8
    assert isinstance(processed_img, np.ndarray)
    assert processed_img.dtype == np.uint8

    # 2. Channel count must be exactly 1 (2D shape)
    assert processed_img.ndim == 2, f"Expected 2D array (1 channel), got shape {processed_img.shape}"
    assert metadata.get("channels") == 1
    assert metadata.get("grayscale") is True
    assert metadata.get("clahe") is True
    assert metadata.get("denoised") is True

    # 3. Dimensions must match the original width and height
    orig_h, orig_w = metadata["original_shape"][:2]
    assert processed_img.shape[0] == orig_h
    assert processed_img.shape[1] == orig_w


def test_preprocessing_rejects_empty_and_corrupt_bytes():
    """Verifies that empty or non-image payloads raise PreprocessingError cleanly."""
    with pytest.raises(PreprocessingError, match="Empty image bytes"):
        preprocess_image(b"")

    with pytest.raises(PreprocessingError, match="Failed to decode image"):
        preprocess_image(b"not_a_valid_image_payload_bytes_12345")


# ------------------------------------------------------------------------------
# Requirement (b): Extraction returns text + confidence score per region
# ------------------------------------------------------------------------------
def test_ocr_extraction_returns_text_and_confidence_scores():
    """Verifies that the extractor interface extracts text and confidence score per detected region."""
    image_bytes = _create_synthetic_test_image("MRP Rs. 150.00 incl. of all taxes")
    processed_img, _ = preprocess_image(image_bytes)

    extractor = MockOCRExtractor(default_confidence=0.95)
    regions = extractor.extract_regions(processed_img)

    assert len(regions) > 0
    for r in regions:
        assert isinstance(r, OCRResultRegion)
        assert len(r.text.strip()) > 0
        assert 0.0 <= r.confidence <= 1.0
        assert len(r.bbox) == 4, "Expected 4 corner coordinates in bbox"

    # Extract facts and per-field confidences
    facts, raw_text, overall_conf, per_field = extract_facts(processed_img, extractor=extractor)

    assert facts["mrp"] is not None
    assert "MRP" in facts["mrp"]
    assert facts["mrp_tax_inclusive"] is True
    assert "mrp" in per_field
    assert per_field["mrp"] == 0.95
    assert facts["net_quantity"] is not None
    assert per_field["net_quantity"] == 0.92
    assert 0.0 < overall_conf <= 1.0


# ------------------------------------------------------------------------------
# Requirement (c): Low-confidence OCR result triggers 'needs_review'
# ------------------------------------------------------------------------------
class ConfigurableOCRExtractor(BaseOCRExtractor):
    """Test extractor returning configurable confidence for specified text fields."""
    def __init__(self, mrp_confidence: float):
        self.mrp_confidence = mrp_confidence

    def extract_regions(self, image: np.ndarray):
        return [
            OCRResultRegion(
                bbox=[[0, 0], [100, 0], [100, 20], [0, 20]],
                text="MRP Rs. 150.00 incl. of all taxes",
                confidence=self.mrp_confidence,
            ),
        ]


def test_low_confidence_ocr_triggers_needs_review_via_rule_engine():
    """
    Validates that when OCR confidence for a declared field falls below the rule's
    confidence_threshold (e.g. 0.80), evaluate_single_rule() produces AuditResultType.needs_review.
    """
    # 1. Simulate low confidence extraction (0.42 confidence, below threshold 0.80)
    low_conf_extractor = ConfigurableOCRExtractor(mrp_confidence=0.42)
    dummy_img = np.zeros((100, 200), dtype=np.uint8)
    facts, _, _, per_field_conf = extract_facts(dummy_img, extractor=low_conf_extractor)

    assert facts["mrp"] is not None
    assert per_field_conf["mrp"] == 0.42

    # 2. Define rule with confidence_threshold of 0.80
    admin_id = uuid.uuid4()
    rule_version = ComplianceRuleVersion(
        id=uuid.uuid4(),
        rule_id=uuid.uuid4(),
        version=1,
        statutory_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e)",
        rule_type=RuleType.presence,
        target_field="mrp",
        severity=SeverityLevel.major,
        description_en="MRP must be declared on package.",
        failure_message_template="MRP declaration fails statutory requirement.",
        requires_visual_measurement=False,
        check_definition={
            "operator": "regex",
            "value": r"(?:MRP|M\.R\.P\.|Rs\.?|₹)\s*\d+(?:\.\d{1,2})?",
            "confidence_threshold": 0.80,
        },
        is_active=True,
        created_by=admin_id,
    )

    # 3. Evaluate rule with low confidence
    result = evaluate_single_rule(
        rule_version=rule_version,
        facts=facts,
        visual_measurements=None,
        ocr_confidences=per_field_conf,
    )

    # 4. Result must be needs_review due to low confidence gating
    assert result["automated_result"] == AuditResultType.needs_review
    assert result["effective_result"] == AuditResultType.needs_review
    assert "Low OCR confidence (0.42) for field 'mrp' below threshold (0.80)" in result["automated_reason"]
    assert result["fact_confidence"] == 0.42


def test_high_confidence_ocr_passes_rule_engine_gating():
    """Validates that when OCR confidence meets or exceeds threshold (0.95 >= 0.80), the rule evaluates to pass_."""
    high_conf_extractor = ConfigurableOCRExtractor(mrp_confidence=0.95)
    dummy_img = np.zeros((100, 200), dtype=np.uint8)
    facts, _, _, per_field_conf = extract_facts(dummy_img, extractor=high_conf_extractor)

    admin_id = uuid.uuid4()
    rule_version = ComplianceRuleVersion(
        id=uuid.uuid4(),
        rule_id=uuid.uuid4(),
        version=1,
        statutory_reference="Legal Metrology (Packaged Commodities) Rules, 2011 - Rule 6(1)(e)",
        rule_type=RuleType.presence,
        target_field="mrp",
        severity=SeverityLevel.major,
        description_en="MRP must be declared on package.",
        failure_message_template="MRP declaration fails statutory requirement.",
        requires_visual_measurement=False,
        check_definition={
            "operator": "regex",
            "value": r"(?:MRP|M\.R\.P\.|Rs\.?|₹)\s*\d+(?:\.\d{1,2})?",
            "confidence_threshold": 0.80,
        },
        is_active=True,
        created_by=admin_id,
    )

    result = evaluate_single_rule(
        rule_version=rule_version,
        facts=facts,
        visual_measurements=None,
        ocr_confidences=per_field_conf,
    )

    assert result["automated_result"] == AuditResultType.pass_
    assert result["effective_result"] == AuditResultType.pass_
    assert result["fact_confidence"] == 0.95


