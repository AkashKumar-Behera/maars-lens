"""
MAARS Lens: OCR Robustness Tests
================================
Tests for Devanagari digit normalization and empty text handling in PaddleOCR extractor.
"""

import pytest
import numpy as np
from app.services.ocr.extractor import (
    normalize_devanagari_digits,
    normalize_ocr_confusions,
    PaddleOCRExtractor,
)


def test_devanagari_digit_normalizer():
    """Test Devanagari numerals (०-९) conversion to standard Arabic digits (0-9)."""
    # 500 in English vs 50० in Devanagari mix vs ५०० in pure Devanagari
    assert normalize_devanagari_digits("50०") == "500"
    assert normalize_devanagari_digits("५००") == "500"
    assert normalize_devanagari_digits("रु. ५००/-") == "रु. 500/-"
    assert normalize_devanagari_digits("०१२३४५६७८९") == "0123456789"
    assert normalize_devanagari_digits("Net Wt 100g") == "Net Wt 100g"


def test_ocr_confusions_with_devanagari():
    """Test confusion corrections when combined with Devanagari numerals."""
    raw = "MRP Rs. ५OO/-"
    normalized = normalize_ocr_confusions(raw)
    assert "500" in normalized


def test_paddleocr_empty_or_none_result_handling():
    """Verify extractor safely handles empty image or None detection result without crash."""
    extractor = PaddleOCRExtractor()
    
    # Empty blank image (e.g. 100x100 white pixels)
    blank_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    results = extractor.extract_regions(blank_img, image_id="blank_test")
    
    # Should safely return an empty list, not throw NoneType AttributeError
    assert isinstance(results, list)
    assert len(results) == 0
