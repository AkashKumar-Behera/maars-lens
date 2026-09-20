"""
MAARS Lens: OCR Text Extraction Service
======================================
Provides OCR text extraction and fact parsing for packaged goods inspections
powered by PaddleOCR (English + Hindi / Devanagari multilingual pipeline)
with rapidfuzz-enhanced keyword parsing and normalization.
"""

import os
import re
import time
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
import numpy as np

# Rapidfuzz for robust typo/noise tolerant keyword matching
from rapidfuzz import fuzz

from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure MKLDNN flag is set before paddle runtime executes
if not settings.PADDLE_ENABLE_MKLDNN:
    os.environ["FLAGS_use_mkldnn"] = "0"


class OCRResultRegion:
    """Represents an individual detected text block with quadrilateral polygon, axis-aligned bbox, and confidence."""
    def __init__(
        self,
        bbox: List[Any],
        text: str,
        confidence: float,
        polygon: Optional[List[List[float]]] = None,
        language: str = "en",
        source_pass: str = "en",
        image_id: Optional[str] = None,
    ):
        # If bbox has 4 points [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], convert to polygon
        if bbox and isinstance(bbox[0], (list, tuple)) and len(bbox) == 4:
            self.polygon = [[float(pt[0]), float(pt[1])] for pt in bbox]
            xs = [pt[0] for pt in self.polygon]
            ys = [pt[1] for pt in self.polygon]
            self.bbox = [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]
        elif polygon is not None:
            self.polygon = polygon
            self.bbox = bbox if bbox else [0.0, 0.0, 0.0, 0.0]
        else:
            # Axis-aligned bbox [x1, y1, x2, y2]
            self.bbox = [float(c) for c in bbox] if bbox else [0.0, 0.0, 0.0, 0.0]
            x1, y1, x2, y2 = self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3]
            self.polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

        self.text = text
        self.confidence = float(confidence)
        self.language = language
        self.source_pass = source_pass
        self.image_id = image_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bbox": self.bbox,
            "polygon": self.polygon,
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "source_pass": self.source_pass,
            "image_id": self.image_id,
        }


# --- Normalization Utilities ---

DEVANAGARI_DIGITS_MAP = {
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
}


def normalize_devanagari_digits(text: str) -> str:
    """Translates Devanagari numerals (०-९) to standard Arabic digits (0-9)."""
    if not text:
        return ""
    result = []
    for char in text:
        result.append(DEVANAGARI_DIGITS_MAP.get(char, char))
    return "".join(result)


def normalize_ocr_confusions(text: str) -> str:
    """Normalizes frequent OCR character-digit confusions in numeric/price contexts."""
    if not text:
        return ""
    s = normalize_devanagari_digits(text)
    # Repeatedly normalize O/o adjacent to digits until stable (e.g. 5OO -> 500)
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'(\d)[oO]', r'\g<1>0', s)
        s = re.sub(r'[oO](\d)', r'0\g<1>', s)
    s = re.sub(r'(?<=\d)[lI](?=\d)', '1', s)
    s = re.sub(r'(?<=\d)[sS](?=\d)', '5', s)
    return s


def compute_iou(box1: List[float], box2: List[float]) -> float:
    """Computes Intersection over Union for two axis-aligned boxes [x1, y1, x2, y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter_area <= 0:
        return 0.0

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0

    return inter_area / union_area


def merge_ocr_passes(
    en_regions: List[OCRResultRegion],
    hi_regions: List[OCRResultRegion],
    iou_thresh: float = 0.40,
) -> List[OCRResultRegion]:
    """
    Merges English and Hindi OCR passes.
    For overlapping regions (IoU > iou_thresh):
      - If text contains digits, prefer the English pass.
      - Otherwise, keep the higher confidence result.
    """
    merged: List[OCRResultRegion] = list(en_regions)

    for hi_reg in hi_regions:
        matched = False
        for i, en_reg in enumerate(merged):
            iou = compute_iou(hi_reg.bbox, en_reg.bbox)
            if iou >= iou_thresh:
                matched = True
                has_en_digits = bool(re.search(r'\d', en_reg.text))
                has_hi_digits = bool(re.search(r'[\d०-९]', hi_reg.text))
                if has_en_digits and not has_hi_digits:
                    # Keep English
                    pass
                elif hi_reg.confidence > en_reg.confidence and not has_en_digits:
                    # Replace with higher confidence Hindi region
                    merged[i] = hi_reg
                break
        if not matched:
            merged.append(hi_reg)

    return merged


# --- Abstract Base & Implementations ---

class BaseOCRExtractor(ABC):
    """Abstract base interface for OCR extraction backends."""

    @abstractmethod
    def extract_regions(self, image: np.ndarray, image_id: Optional[str] = None) -> List[OCRResultRegion]:
        """Extracts text regions with bounding boxes, polygons, and confidence."""
        pass


class MockOCRExtractor(BaseOCRExtractor):
    """
    SIMULATED OCR Extractor.
    Used strictly for unit testing when real PaddleOCR execution is disabled.
    All outputs are explicitly tagged as 'mock (SIMULATED)'.
    """

    def __init__(self, default_confidence: float = 0.95):
        self.default_confidence = default_confidence

    def extract_regions(self, image: np.ndarray, image_id: Optional[str] = None) -> List[OCRResultRegion]:
        return [
            OCRResultRegion(
                bbox=[[10, 10], [200, 10], [200, 30], [10, 30]],
                text="MRP Rs. 150.00 incl. of all taxes",
                confidence=self.default_confidence,
                language="en",
                source_pass="mock (SIMULATED)",
                image_id=image_id,
            ),
            OCRResultRegion(
                bbox=[[10, 40], [150, 40], [150, 60], [10, 60]],
                text="Net Qty: 500g",
                confidence=0.92,
                language="en",
                source_pass="mock (SIMULATED)",
                image_id=image_id,
            ),
            OCRResultRegion(
                bbox=[[10, 70], [160, 70], [160, 90], [10, 90]],
                text="Mfg Date: 10/2023",
                confidence=0.88,
                language="en",
                source_pass="mock (SIMULATED)",
                image_id=image_id,
            ),
            OCRResultRegion(
                bbox=[[10, 100], [220, 100], [220, 120], [10, 120]],
                text="Consumer Care: 1800-111-222 / care@example.com",
                confidence=0.94,
                language="en",
                source_pass="mock (SIMULATED)",
                image_id=image_id,
            ),
            OCRResultRegion(
                bbox=[[10, 130], [180, 130], [180, 150], [10, 150]],
                text="Country of Origin: India",
                confidence=0.96,
                language="en",
                source_pass="mock (SIMULATED)",
                image_id=image_id,
            ),
        ]


class PaddleOCRExtractor(BaseOCRExtractor):
    """
    Real PaddleOCR production extractor supporting English + Hindi (Devanagari).
    Models are cached as thread-safe process-wide singletons.
    """

    _lock = threading.Lock()
    _ocr_en: Optional[Any] = None
    _ocr_hi: Optional[Any] = None
    _init_error: Optional[str] = None
    _init_time_sec: float = 0.0

    def __init__(self):
        self._ensure_models_initialized()

    @classmethod
    def _ensure_models_initialized(cls) -> None:
        if cls._ocr_en is not None and cls._ocr_hi is not None:
            return

        with cls._lock:
            if cls._ocr_en is not None and cls._ocr_hi is not None:
                return

            t0 = time.time()
            try:
                if not settings.PADDLE_ENABLE_MKLDNN:
                    os.environ["FLAGS_use_mkldnn"] = "0"

                from paddleocr import PaddleOCR

                kwargs_base = {
                    "use_angle_cls": False,
                    "use_gpu": settings.OCR_USE_GPU,
                    "enable_mkldnn": settings.PADDLE_ENABLE_MKLDNN,
                    "show_log": False,
                }
                if settings.PADDLE_MODEL_DIR:
                    kwargs_base["det_model_dir"] = os.path.join(settings.PADDLE_MODEL_DIR, "det")
                    kwargs_base["rec_model_dir"] = os.path.join(settings.PADDLE_MODEL_DIR, "rec")
                    kwargs_base["cls_model_dir"] = os.path.join(settings.PADDLE_MODEL_DIR, "cls")

                logger.info("Initializing PaddleOCR English model...")
                cls._ocr_en = PaddleOCR(lang="en", **kwargs_base)

                logger.info("Initializing PaddleOCR Hindi model...")
                cls._ocr_hi = PaddleOCR(lang="hi", **kwargs_base)

                cls._init_time_sec = time.time() - t0
                cls._init_error = None
                logger.info("PaddleOCR models loaded successfully in %.2fs", cls._init_time_sec)
            except Exception as exc:
                cls._init_error = str(exc)
                logger.error("Failed to initialize PaddleOCR: %s", exc, exc_info=True)
                raise RuntimeError(f"PaddleOCR failed to initialize: {exc}") from exc

    def _run_single_pass(self, ocr_engine: Any, image: np.ndarray, lang: str, image_id: Optional[str]) -> List[OCRResultRegion]:
        if ocr_engine is None or image is None or image.size == 0:
            return []

        # PaddleOCR expects 3-channel image (H, W, 3)
        img_input = image
        if len(img_input.shape) == 2:
            import cv2
            img_input = cv2.cvtColor(img_input, cv2.COLOR_GRAY2BGR)

        try:
            raw_res = ocr_engine.ocr(img_input, cls=False)
        except Exception as exc:
            logger.warning("PaddleOCR pass (%s) error: %s", lang, exc)
            return []

        # PaddleOCR 2.x returns [None] or empty list when no text is found
        if not raw_res or raw_res == [None] or raw_res[0] is None:
            return []

        regions: List[OCRResultRegion] = []
        for line in raw_res:
            if not line:
                continue
            for item in line:
                if not item or len(item) < 2:
                    continue
                pts, text_conf = item[0], item[1]
                text = str(text_conf[0]).strip()
                conf = float(text_conf[1])

                if not text:
                    continue

                # Translate Devanagari numerals
                text = normalize_devanagari_digits(text)

                region = OCRResultRegion(
                    bbox=pts,
                    text=text,
                    confidence=conf,
                    language=lang,
                    source_pass=f"paddle_{lang}",
                    image_id=image_id,
                )
                regions.append(region)

        return regions

    def extract_regions(self, image: np.ndarray, image_id: Optional[str] = None) -> List[OCRResultRegion]:
        """Runs English and Hindi OCR passes, merges with IoU de-duplication."""
        self._ensure_models_initialized()

        en_regions = self._run_single_pass(self._ocr_en, image, lang="en", image_id=image_id)
        hi_regions = self._run_single_pass(self._ocr_hi, image, lang="hi", image_id=image_id)

        merged = merge_ocr_passes(en_regions, hi_regions, iou_thresh=settings.OCR_IOU_THRESHOLD)
        return merged

    @classmethod
    def get_health_status(cls) -> Dict[str, Any]:
        """Diagnostic health status dictionary for /health/ocr."""
        if cls._init_error:
            return {
                "status": "error",
                "engine": "paddleocr",
                "error": cls._init_error,
            }
        try:
            cls._ensure_models_initialized()
            # Perform a tiny warm-up inference test
            dummy_img = np.full((60, 200, 3), 255, dtype=np.uint8)
            t0 = time.time()
            _ = cls._ocr_en.ocr(dummy_img, cls=False)
            latency = time.time() - t0

            import paddle
            import paddleocr

            return {
                "status": "ok",
                "engine": "paddleocr",
                "paddle_version": paddle.__version__,
                "paddleocr_version": paddleocr.__version__,
                "languages_loaded": ["en", "hi"],
                "model_dir": settings.PADDLE_MODEL_DIR or os.path.expanduser("~/.paddleocr/whl"),
                "mkldnn_enabled": settings.PADDLE_ENABLE_MKLDNN,
                "warmup_latency_sec": round(latency, 4),
            }
        except Exception as exc:
            return {
                "status": "error",
                "engine": "paddleocr",
                "error": str(exc),
            }


# --- Factory & Singleton Registry ---

_active_extractor: Optional[BaseOCRExtractor] = None


def get_ocr_extractor() -> BaseOCRExtractor:
    """Returns the configured active OCR extractor instance."""
    global _active_extractor
    if _active_extractor is None:
        engine_type = settings.OCR_ENGINE.lower().strip()
        if engine_type == "mock":
            logger.info("OCR_ENGINE=mock: Using MockOCRExtractor (SIMULATED).")
            _active_extractor = MockOCRExtractor()
        else:
            logger.info("OCR_ENGINE=paddleocr: Using PaddleOCRExtractor.")
            _active_extractor = PaddleOCRExtractor()
    return _active_extractor


def set_ocr_extractor(extractor: BaseOCRExtractor) -> None:
    """Allows test suites or dependency injection to register a specific extractor instance."""
    global _active_extractor
    _active_extractor = extractor


# --- Fact Extraction Pipeline ---

# Fuzzy keyword patterns (bilingual English + Hindi)
KEYWORD_PATTERNS = {
    "mrp": ["mrp", "m.r.p", "max retail price", "maximum retail price", "अधिकतम खुदरा मूल्य", "एम.आर.पी", "मूल्य", "rs.", "inr", "₹"],
    "tax_inclusive": ["incl. of all taxes", "inclusive of all taxes", "incl of taxes", "सभी कर सहित", "कर सहित"],
    "net_quantity": ["net qty", "net quantity", "net wt", "net weight", "शुद्ध मात्रा", "शुद्ध वजन", "मात्रा", "वजन"],
    "mfg_date": ["mfg date", "mfd date", "mfg.", "mfd.", "pkd date", "pkd.", "packed date", "date of packing", "date of manufacture", "निर्माण तिथि", "पैकिंग तिथि"],
    "expiry_date": ["best before", "use by", "expiry date", "exp date", "exp.", "समाप्ति तिथि", "उपयोग की अंतिम तिथि"],
    "manufacturer": ["manufactured by", "marketed by", "packed by", "imported by", "mfg by", "mfd by", "निर्माता", "द्वारा निर्मित"],
    "customer_care": ["consumer care", "customer care", "helpline", "toll free", "care@", "grievance officer", "उपभोक्ता संरक्षण", "ग्राहक सेवा"],
    "country_of_origin": ["country of origin", "origin:", "made in", "मूल देश", "उत्पत्ति देश"],
    "fssai": ["fssai", "एफएसएसएआई"],
}


def _matches_keyword(text: str, keywords: List[str], threshold: float = 75.0) -> bool:
    """Checks if text contains or fuzzy-matches any keyword with length guard."""
    text_clean = text.strip()
    if len(text_clean) < 3:
        return False
    text_lower = text_clean.lower()
    for kw in keywords:
        if kw in text_lower:
            return True
        # Guard against partial_ratio matching small substrings into short keywords
        if len(text_lower) >= 4 and len(kw) >= 5 and fuzz.partial_ratio(kw, text_lower) >= max(threshold, 82.0):
            return True
    return False



def extract_facts(
    image: np.ndarray,
    extractor: Optional[BaseOCRExtractor] = None,
    image_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], str, float, Dict[str, float]]:
    """
    Extracts structured package facts, raw text, overall confidence, and per-field confidences
    using PaddleOCR extraction and rapidfuzz-enhanced normalization.

    Returns:
        (facts_dict, raw_text, overall_confidence, per_field_confidences)
    """
    engine = extractor or get_ocr_extractor()
    try:
        regions = engine.extract_regions(image, image_id=image_id)
    except TypeError:
        regions = engine.extract_regions(image)

    raw_lines: List[str] = []
    confidences: List[float] = []
    per_field: Dict[str, float] = {}
    field_evidence: Dict[str, Any] = {}

    facts: Dict[str, Any] = {
        "mrp": None,
        "net_quantity": None,
        "mfg_date": None,
        "expiry_date": None,
        "manufacturer": None,
        "customer_care": None,
        "country_of_origin": None,
        "fssai": None,
        "ingredients": None,
        "mrp_tax_inclusive": False,
        "_evidence": field_evidence,
    }

    if not regions:
        return facts, "", 0.0, per_field

    for region in regions:
        raw_text = region.text
        conf = region.confidence
        norm_text = normalize_ocr_confusions(raw_text)
        raw_lines.append(norm_text)
        confidences.append(conf)

        # 1. MRP & Tax Inclusive Check
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["mrp"], threshold=78.0):
            if facts["mrp"] is None or conf > per_field.get("mrp", 0.0):
                facts["mrp"] = norm_text
                per_field["mrp"] = conf
                field_evidence["mrp"] = region.to_dict()

            if _matches_keyword(norm_text, KEYWORD_PATTERNS["tax_inclusive"], threshold=75.0):
                facts["mrp_tax_inclusive"] = True
                per_field["mrp_tax_inclusive"] = conf
                field_evidence["mrp_tax_inclusive"] = region.to_dict()

        # Check tax inclusive separately in case it appears on an adjacent line
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["tax_inclusive"], threshold=75.0):
            facts["mrp_tax_inclusive"] = True
            per_field["mrp_tax_inclusive"] = conf
            field_evidence["mrp_tax_inclusive"] = region.to_dict()

        # 2. Net Quantity
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["net_quantity"], threshold=75.0) or re.search(r'\b\d+\s*(?:g|kg|ml|l|ltr|nos|units|pieces|cm|m)\b', norm_text, re.IGNORECASE):
            if facts["net_quantity"] is None or conf > per_field.get("net_quantity", 0.0):
                facts["net_quantity"] = norm_text
                per_field["net_quantity"] = conf
                field_evidence["net_quantity"] = region.to_dict()

        # 3. Manufacturing / Packing Date
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["mfg_date"], threshold=75.0):
            if facts["mfg_date"] is None or conf > per_field.get("mfg_date", 0.0):
                facts["mfg_date"] = norm_text
                per_field["mfg_date"] = conf
                field_evidence["mfg_date"] = region.to_dict()

        # 4. Expiry / Best Before Date
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["expiry_date"], threshold=75.0):
            if facts["expiry_date"] is None or conf > per_field.get("expiry_date", 0.0):
                facts["expiry_date"] = norm_text
                per_field["expiry_date"] = conf
                field_evidence["expiry_date"] = region.to_dict()

        # 5. Manufacturer / Packer Details
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["manufacturer"], threshold=75.0):
            if facts["manufacturer"] is None or conf > per_field.get("manufacturer", 0.0):
                facts["manufacturer"] = norm_text
                per_field["manufacturer"] = conf
                field_evidence["manufacturer"] = region.to_dict()

        # 6. Customer Care Details
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["customer_care"], threshold=75.0) or re.search(r'\b\d{3,5}[-\s]?\d{6,8}\b|care@', norm_text):
            if facts["customer_care"] is None or conf > per_field.get("customer_care", 0.0):
                facts["customer_care"] = norm_text
                per_field["customer_care"] = conf
                field_evidence["customer_care"] = region.to_dict()

        # 7. Country of Origin
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["country_of_origin"], threshold=75.0):
            if facts["country_of_origin"] is None or conf > per_field.get("country_of_origin", 0.0):
                facts["country_of_origin"] = norm_text
                per_field["country_of_origin"] = conf
                field_evidence["country_of_origin"] = region.to_dict()

        # 8. FSSAI
        if _matches_keyword(norm_text, KEYWORD_PATTERNS["fssai"], threshold=80.0) or re.search(r'\b1\d{13}\b', norm_text):
            if facts["fssai"] is None or conf > per_field.get("fssai", 0.0):
                facts["fssai"] = norm_text
                per_field["fssai"] = conf
                field_evidence["fssai"] = region.to_dict()

    overall_conf = float(np.mean(confidences)) if confidences else 0.0
    full_text = "\n".join(raw_lines)

    return facts, full_text, overall_conf, per_field
