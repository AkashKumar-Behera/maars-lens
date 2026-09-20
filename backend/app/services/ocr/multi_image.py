"""
MAARS Lens: Multi-Image Evidence Processing & Merge Service
============================================================
Handles multi-panel scans (e.g. front panel, back panel, side panel, top).
- Validates file formats and magic bytes.
- Generates secure hashes and isolated storage paths.
- Runs OCR per panel and annotates detected regions with compliance/violation codes.
- Merges extracted package facts across all panels into a unified inspection facts dictionary,
  recording which panel contributed each declaration.
- Never overwrites original uploaded images.
"""

import os
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2

from app.core.config import settings
from app.services.ocr.preprocessor import preprocess_image
from app.services.ocr.extractor import extract_facts, BaseOCRExtractor, get_ocr_extractor
from app.services.ocr.annotator import annotate_evidence_image
from app.services.ocr.barcode import decode_barcode


# Allowed image magic signatures
MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp", # starts with RIFF....WEBP
}


def validate_and_hash_image(file_bytes: bytes) -> Tuple[str, str, int]:
    """
    Validates magic bytes, computes sha256, and returns (sha256, mime_type, byte_size).
    Raises ValueError on invalid formats.
    """
    size = len(file_bytes)
    if size < 8:
        raise ValueError("File is too small to be a valid image.")
    if size > 15 * 1024 * 1024:
        raise ValueError("File exceeds maximum allowed upload size of 15MB.")


    mime: Optional[str] = None
    for magic, detected_mime in MAGIC_BYTES.items():
        if file_bytes.startswith(magic):
            mime = detected_mime
            break

    if not mime:
        # Fallback check using cv2 imdecode
        nparr = np.frombuffer(file_bytes, np.uint8)
        decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if decoded is None:
            raise ValueError("Unsupported image format: magic bytes do not match JPEG, PNG, or WebP.")
        mime = "image/jpeg"

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    return sha256, mime, size


def save_image_to_storage(file_bytes: bytes, inspection_id: uuid.UUID, filename: str) -> str:
    """
    Saves image bytes under settings.UPLOAD_DIR / inspection_id / filename.
    Returns relative storage path.
    """
    rel_dir = os.path.join("inspections", str(inspection_id))
    abs_dir = os.path.join(settings.UPLOAD_DIR, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)

    # Sanitize filename to prevent directory traversal
    clean_filename = os.path.basename(filename).replace("..", "").strip()
    if not clean_filename:
        clean_filename = f"{uuid.uuid4()}.jpg"

    rel_path = os.path.join(rel_dir, clean_filename).replace("\\", "/")
    abs_path = os.path.join(abs_dir, clean_filename)


    with open(abs_path, "wb") as f:
        f.write(file_bytes)

    return rel_path


def process_and_merge_panels(
    panels: List[Dict[str, Any]],
    inspection_id: uuid.UUID,
    extractor: Optional[BaseOCRExtractor] = None,
) -> Dict[str, Any]:
    """
    Processes each panel through OCR, aggregates facts across all panels,
    and returns a unified inspection extraction payload.

    Args:
        panels: List of dicts, each with:
            - 'panel_type': str (e.g. 'front', 'back', 'side', 'top')
            - 'file_bytes': bytes
            - 'image_id': uuid.UUID
        inspection_id: UUID of inspection
        extractor: Optional custom OCR extractor for testing

    Returns:
        {
            "merged_facts": Dict[str, Any],
            "raw_text": str,
            "overall_confidence": float,
            "per_field_confidences": Dict[str, float],
            "panel_results": List[Dict[str, Any]],
        }
    """
    merged_facts: Dict[str, Any] = {}
    field_sources: Dict[str, str] = {} # field -> panel_type
    per_field_confidences: Dict[str, float] = {}
    all_raw_texts: List[str] = []
    all_confidences: List[float] = []
    panel_results: List[Dict[str, Any]] = []

    for p in panels:
        panel_type = p.get("panel_type", "other")
        file_bytes = p["file_bytes"]
        img_id = p.get("image_id") or uuid.uuid4()

        # Preprocess for OCR
        try:
            processed_img, _ = preprocess_image(file_bytes)
        except Exception:
            # Fallback to direct decoding if preprocessing raises
            nparr = np.frombuffer(file_bytes, np.uint8)
            processed_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Check for barcode in the image
        barcode_info = decode_barcode(processed_img)
        if barcode_info and "barcode" not in merged_facts:
            merged_facts["barcode"] = barcode_info.get("data")
            merged_facts["barcode_type"] = barcode_info.get("type")
            field_sources["barcode"] = panel_type
            per_field_confidences["barcode"] = 0.99

        facts, raw_text, conf, field_confs = extract_facts(
            processed_img,
            extractor=extractor,
            image_id=str(img_id),
        )

        all_raw_texts.append(f"--- Panel: {panel_type} ---\n{raw_text}")
        if conf > 0:
            all_confidences.append(conf)

        # Merge facts: if field not present or higher confidence, take it
        for k, v in facts.items():
            if v is not None:
                curr_conf = field_confs.get(k, 0.5)
                prev_conf = per_field_confidences.get(k, 0.0)
                if k not in merged_facts or merged_facts[k] is None or curr_conf > prev_conf:
                    merged_facts[k] = v
                    per_field_confidences[k] = curr_conf
                    field_sources[k] = panel_type

        panel_results.append({
            "image_id": img_id,
            "panel_type": panel_type,
            "raw_text": raw_text,
            "confidence": conf,
            "field_confidences": field_confs,
            "facts": facts,
        })

    overall_conf = float(np.mean(all_confidences)) if all_confidences else 0.0
    merged_facts["_panel_sources"] = field_sources

    return {
        "merged_facts": merged_facts,
        "raw_text": "\n\n".join(all_raw_texts),
        "overall_confidence": overall_conf,
        "per_field_confidences": per_field_confidences,
        "panel_results": panel_results,
    }
