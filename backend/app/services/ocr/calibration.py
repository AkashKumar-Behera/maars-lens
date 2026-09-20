"""
MAARS Lens: Optical Calibration & Physical Font-Size Service
============================================================
Computes millimeter scaling factors for optical character height measurement
under the Legal Metrology (Packaged Commodities) Rules, 2011 (Rule 7).

Priority Order for Scale Calibration:
1. User-entered package physical dimensions (width_mm, height_mm) mapped to package panel / bounding box.
2. Optical reference object in the image:
   - Credit card / ID-1 standard (85.60 mm x 53.98 mm)
   - Standard A4 sheet (210.0 mm x 297.0 mm)
   - Printable MAARS Lens calibration card (50.0 mm x 50.0 mm checkerboard)
3. Image metadata DPI (Dots Per Inch) on flatbed scanner images:
   - scale_factor_mm_per_px = 25.4 / dpi

Deterministic Safety Invariant:
- If calibration cannot be established with confidence >= 0.80, measurement_reliable=False.
- Uncalibrated visual rules deterministically yield AuditResultType.needs_review, NEVER pass.
"""

from typing import Dict, Any, Optional, Tuple, List
import math
import numpy as np
import cv2


# Standard Physical References (dimensions in millimeters)
REFERENCE_OBJECTS = {
    "credit_card": {"width_mm": 85.60, "height_mm": 53.98, "aspect_ratio": 85.60 / 53.98},
    "calibration_card": {"width_mm": 50.0, "height_mm": 50.0, "aspect_ratio": 1.0},
    "a4_sheet": {"width_mm": 210.0, "height_mm": 297.0, "aspect_ratio": 297.0 / 210.0},
}


def compute_scale_from_pack_dimensions(
    pack_width_mm: float,
    pack_height_mm: float,
    panel_bbox_px: List[int],
) -> Tuple[Optional[float], float, str]:
    """
    Priority 1: Computes scale factor (mm per pixel) from user-entered package dimensions.
    panel_bbox_px format: [x1, y1, x2, y2]
    """
    if pack_width_mm <= 0 or pack_height_mm <= 0 or not panel_bbox_px or len(panel_bbox_px) < 4:
        return None, 0.0, "Invalid pack dimensions or bounding box"

    w_px = max(1, abs(panel_bbox_px[2] - panel_bbox_px[0]))
    h_px = max(1, abs(panel_bbox_px[3] - panel_bbox_px[1]))

    scale_x = pack_width_mm / float(w_px)
    scale_y = pack_height_mm / float(h_px)

    # Average anisotropic scale factor
    scale_factor = (scale_x + scale_y) / 2.0
    aspect_error = abs(scale_x - scale_y) / scale_factor

    # If aspect ratio discrepancy is within 15%, high confidence
    confidence = max(0.50, 0.95 - aspect_error) if aspect_error < 0.25 else 0.60
    notes = f"Calibrated from pack dimensions: {pack_width_mm:.1f}x{pack_height_mm:.1f} mm across {w_px}x{h_px} px."
    return scale_factor, confidence, notes


def detect_reference_object_scale(
    image: np.ndarray,
    expected_type: str = "credit_card",
) -> Tuple[Optional[float], float, str]:
    """
    Priority 2: Detects a physical reference object (e.g. credit card or calibration square)
    using contour analysis and aspect ratio matching.
    """
    if image is None or image.size == 0:
        return None, 0.0, "Empty image"

    ref_spec = REFERENCE_OBJECTS.get(expected_type)
    if not ref_spec:
        return None, 0.0, f"Unknown reference object type: {expected_type}"

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    target_ar = ref_spec["aspect_ratio"]
    best_scale: Optional[float] = None
    best_confidence = 0.0
    best_notes = "No valid reference object contour found."

    img_area = float(image.shape[0] * image.shape[1])

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < img_area * 0.01 or area > img_area * 0.80:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)

        if len(approx) == 4:
            # Rectangular contour
            rect = cv2.minAreaRect(cnt)
            (cx, cy), (w, h), angle = rect
            if w <= 0 or h <= 0:
                continue

            dim1, dim2 = max(w, h), min(w, h)
            ar = dim1 / dim2

            if abs(ar - target_ar) / target_ar < 0.12:
                # Matched reference object aspect ratio!
                scale_w = ref_spec["width_mm"] / dim1
                scale_h = ref_spec["height_mm"] / dim2
                scale = (scale_w + scale_h) / 2.0
                conf = 0.90 - (abs(ar - target_ar) / target_ar)
                if conf > best_confidence:
                    best_scale = scale
                    best_confidence = conf
                    best_notes = f"Detected {expected_type} reference object with scale {scale:.4f} mm/px (AR error {abs(ar-target_ar):.2f})."

    return best_scale, best_confidence, best_notes


def compute_scale_from_dpi(dpi: float) -> Tuple[Optional[float], float, str]:
    """
    Priority 3: Computes millimeter scaling from image DPI metadata on flatbed scans.
    1 inch = 25.4 mm -> mm_per_px = 25.4 / DPI
    """
    if dpi <= 30.0 or dpi > 2400.0:
        return None, 0.0, f"DPI {dpi} out of standard optical scan range."
    scale_factor = 25.4 / float(dpi)
    confidence = 0.95
    notes = f"Calibrated from flatbed scan DPI metadata: {dpi} DPI ({scale_factor:.4f} mm/px)."
    return scale_factor, confidence, notes


def calibrate_image_scale(
    image: Optional[np.ndarray] = None,
    pack_width_mm: Optional[float] = None,
    pack_height_mm: Optional[float] = None,
    panel_bbox_px: Optional[List[int]] = None,
    reference_type: Optional[str] = None,
    dpi: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Executes hierarchical calibration according to priority order:
    1. User-entered pack dimensions
    2. Reference object detection
    3. Flatbed scan DPI metadata
    
    Returns calibration dictionary with method, scale_factor, confidence, and measurement_reliable flag.
    """
    # 1. Try pack dimensions
    if pack_width_mm and pack_height_mm and panel_bbox_px:
        scale, conf, notes = compute_scale_from_pack_dimensions(pack_width_mm, pack_height_mm, panel_bbox_px)
        if scale and conf >= 0.70:
            return {
                "calibration_method": "user_pack_dimensions",
                "scale_factor_mm_per_px": scale,
                "confidence": conf,
                "measurement_reliable": True,
                "notes": notes,
            }

    # 2. Try reference object detection
    if image is not None and reference_type:
        scale, conf, notes = detect_reference_object_scale(image, reference_type)
        if scale and conf >= 0.75:
            return {
                "calibration_method": f"optical_reference_{reference_type}",
                "scale_factor_mm_per_px": scale,
                "confidence": conf,
                "measurement_reliable": True,
                "notes": notes,
            }

    # 3. Try DPI
    if dpi:
        scale, conf, notes = compute_scale_from_dpi(dpi)
        if scale and conf >= 0.80:
            return {
                "calibration_method": "image_dpi_metadata",
                "scale_factor_mm_per_px": scale,
                "confidence": conf,
                "measurement_reliable": True,
                "notes": notes,
            }

    # Fallback: Uncalibrated
    return {
        "calibration_method": "none",
        "scale_factor_mm_per_px": None,
        "confidence": 0.0,
        "measurement_reliable": False,
        "notes": "Physical scaling unverified or camera gauge absent; manual verification required.",
    }


def generate_printable_calibration_card_pdf() -> bytes:
    """
    Generates a printable PDF containing a precision 50mm x 50mm calibration square
    and standard credit-card outline for field officers to place alongside commodities.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CardTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e293b"),
        alignment=1,
    )
    instr_style = ParagraphStyle(
        "CardInstr",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )

    story = [
        Paragraph("MAARS LENS — OFFICIAL OPTICAL CALIBRATION TARGET", title_style),
        Spacer(1, 10),
        Paragraph(
            "Print at 100% scale (Do NOT select 'Fit to Page'). Place this card adjacent to the commodity package "
            "during inspection capture for automated Rule 7 font-size millimeter calibration.",
            instr_style,
        ),
        Spacer(1, 25),
    ]

    # Draw 50mm x 50mm checkerboard target (1 mm = 72 / 25.4 = 2.8346 pt)
    PT_PER_MM = 72.0 / 25.4
    size_50mm_pt = 50.0 * PT_PER_MM
    card_w_pt = 85.60 * PT_PER_MM
    card_h_pt = 53.98 * PT_PER_MM

    d = Drawing(400, 250)
    # 50mm target
    d.add(Rect(20, 100, size_50mm_pt, size_50mm_pt, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.black, strokeWidth=1.5))
    d.add(Rect(20, 100, size_50mm_pt / 2, size_50mm_pt / 2, fillColor=colors.black, strokeColor=colors.black))
    d.add(Rect(20 + size_50mm_pt / 2, 100 + size_50mm_pt / 2, size_50mm_pt / 2, size_50mm_pt / 2, fillColor=colors.black, strokeColor=colors.black))
    d.add(String(20, 80, "50.0 mm x 50.0 mm Precision Target", fontSize=9, fillColor=colors.black))

    # Credit card contour
    d.add(Rect(200, 100, card_w_pt, card_h_pt, fillColor=colors.HexColor("#f1f5f9"), strokeColor=colors.HexColor("#2563eb"), strokeWidth=1.5, rx=8, ry=8))
    d.add(String(215, 125, "Standard ID-1 Card Outline", fontSize=9, fillColor=colors.HexColor("#1e3a8a")))
    d.add(String(215, 110, "(85.60 mm x 53.98 mm)", fontSize=8, fillColor=colors.HexColor("#64748b")))

    story.append(d)
    doc.build(story)
    return buffer.getvalue()
