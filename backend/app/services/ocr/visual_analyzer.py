"""
MAARS Lens: Visual Analyzer Service
===================================
Analyzes package geometry, text bounding box dimensions, polygon perspective skew,
and prepares measurements for Legal Metrology font height evaluation.
"""

from typing import List, Dict, Any, Union
import numpy as np


def analyze_visual_layout(image: np.ndarray, ocr_results: List[Any]) -> Dict[str, Any]:
    """
    Analyzes visual layout from either OCRResultRegion instances or legacy (bbox, text_info) tuples.
    Computes polygon edge lengths, character height estimates, and perspective skew.
    """
    measurements = []
    h_img, w_img = (image.shape[0], image.shape[1]) if image is not None and len(image.shape) >= 2 else (0, 0)

    for item in ocr_results:
        if hasattr(item, "polygon") and hasattr(item, "text") and hasattr(item, "confidence"):
            # OCRResultRegion instance
            text = str(item.text)
            conf = float(item.confidence)
            pts = np.array(item.polygon, dtype=np.float32)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            bbox, text_info = item[0], item[1]
            text = str(text_info[0]) if isinstance(text_info, (list, tuple)) else str(text_info)
            conf = float(text_info[1]) if isinstance(text_info, (list, tuple)) and len(text_info) > 1 else 0.90
            pts = np.array(bbox, dtype=np.float32)
        else:
            continue

        if len(pts) != 4:
            continue

        # Paddle quadrilateral polygon: p0=top-left, p1=top-right, p2=bottom-right, p3=bottom-left
        # Width: average of top and bottom edges
        w_top = np.linalg.norm(pts[0] - pts[1])
        w_bot = np.linalg.norm(pts[3] - pts[2])
        width = float((w_top + w_bot) / 2.0)

        # Height: average of left and right side edges
        h_left = np.linalg.norm(pts[0] - pts[3])
        h_right = np.linalg.norm(pts[1] - pts[2])
        height = float((h_left + h_right) / 2.0)

        # Skew: ratio between left and right side edge heights (1.0 = perfectly parallel / no perspective tilt)
        skew_ratio = float(min(h_left, h_right) / max(h_left, h_right)) if max(h_left, h_right) > 0 else 1.0

        # Angle tilt in degrees
        dx = float(pts[1][0] - pts[0][0])
        dy = float(pts[1][1] - pts[0][1])
        angle_deg = float(np.degrees(np.arctan2(dy, dx))) if dx != 0 else 0.0

        text_lower = text.lower()
        declaration_type = "unknown"
        if "mrp" in text_lower or "rs" in text_lower or "₹" in text_lower:
            declaration_type = "mrp"
        elif "qty" in text_lower or "net" in text_lower or "ग्राम" in text_lower or "मात्रा" in text_lower:
            declaration_type = "net_quantity"
        elif "mfg" in text_lower or "pkd" in text_lower or "तिथि" in text_lower:
            declaration_type = "mfg_date"
        elif "care" in text_lower or "help" in text_lower:
            declaration_type = "customer_care"
        elif "origin" in text_lower or "made in" in text_lower or "देश" in text_lower:
            declaration_type = "country_of_origin"

        measurements.append({
            "declaration_type": declaration_type,
            "text": text,
            "polygon": pts.tolist(),
            "bounding_box_px": {"width": width, "height": height},
            "side_edge_lengths": {"left": float(h_left), "right": float(h_right)},
            "skew_ratio": skew_ratio,
            "angle_tilt_deg": angle_deg,
            "estimated_text_height_mm": None,
            "measurement_reliable": False,
            "measurement_confidence": conf,
        })

    return {
        "image_resolution": {"width": w_img, "height": h_img},
        "scale_reference_available": False,
        "detected_package_area": None,
        "measurements": measurements,
    }
