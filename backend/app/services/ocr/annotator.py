"""
MAARS Lens: Evidence Image Annotator
====================================
Draws bounding polygons and overlays on package label images:
- Green boxes for recognized compliant declarations.
- Amber/Yellow boxes for declarations requiring review or borderline confidence.
- Red boxes for detected violations with associated rule codes.

Original images are NEVER overwritten. Annotated versions are stored as separate
derived artifacts linked to the parent image.
"""

import os
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# Color definitions (BGR for OpenCV)
COLOR_COMPLIANT = (34, 197, 94)      # Green #22c55e -> BGR: (94, 197, 34)
COLOR_NEEDS_REVIEW = (234, 179, 8)   # Yellow/Amber #eab308 -> BGR: (8, 179, 234)
COLOR_VIOLATION = (239, 68, 68)      # Red #ef4444 -> BGR: (68, 68, 239)


def annotate_evidence_image(
    image_input: Any, # np.ndarray or file path string
    annotations: List[Dict[str, Any]],
    output_path: Optional[str] = None,
) -> np.ndarray:
    """
    Overlays detected text regions and audit outcomes onto a package label image.

    Args:
        image_input: Either a numpy array (BGR or grayscale) or path to an image file.
        annotations: List of annotation dicts, each with:
            - 'polygon': List of 4 [x, y] coordinates [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            - 'label': Short text label to draw (e.g. 'MRP: Rs. 150', 'NET_QTY', 'VIOLATION: R6_MRP')
            - 'status': 'compliant' (green) | 'needs_review' (amber) | 'violation' (red)
            - 'rule_code': Optional string like 'LMPC_R6_MRP'
        output_path: If provided, saves the annotated image to this path.

    Returns:
        Annotated image as a uint8 BGR numpy array.
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            raise FileNotFoundError(f"Could not load image from path: {image_input}")
    elif isinstance(image_input, np.ndarray):
        img = image_input.copy()
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        raise TypeError(f"Unsupported image_input type: {type(image_input)}")

    overlay = img.copy()
    alpha = 0.25  # semi-transparent fill

    for ann in annotations:
        status = ann.get("status", "compliant").lower()
        if status == "violation":
            color = (68, 68, 239)      # Red in BGR
            text_color = (255, 255, 255)
            bg_color = (68, 68, 239)
        elif status in ("needs_review", "warning"):
            color = (8, 179, 234)      # Amber in BGR
            text_color = (0, 0, 0)
            bg_color = (8, 179, 234)
        else:
            color = (94, 197, 34)      # Green in BGR
            text_color = (255, 255, 255)
            bg_color = (94, 197, 34)

        polygon = ann.get("polygon")
        if not polygon or len(polygon) < 3:
            # Fall back to bbox [x1, y1, x2, y2]
            bbox = ann.get("bbox")
            if bbox and len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                pts = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32)
            else:
                continue
        else:
            pts = np.array(polygon, dtype=np.int32)

        # Draw semi-transparent filled polygon on overlay
        cv2.fillPoly(overlay, [pts], color)

        # Draw crisp outline on primary image
        cv2.polylines(img, [pts], isClosed=True, color=color, thickness=2, lineType=cv2.LINE_AA)

        # Determine label position (top-left of polygon)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        min_x = max(0, int(min(xs)))
        min_y = max(0, int(min(ys)))

        label_text = ann.get("label") or ""
        rule_code = ann.get("rule_code")
        if rule_code:
            label_text = f"[{rule_code}] {label_text}".strip()

        if label_text:
            # Calculate text size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.45
            thickness = 1
            (w, h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)

            # Draw background tag
            tag_top = max(0, min_y - h - 6)
            tag_bottom = min_y
            tag_right = min_x + w + 6
            cv2.rectangle(img, (min_x, tag_top), (tag_right, tag_bottom), bg_color, -1)
            cv2.putText(
                img,
                label_text,
                (min_x + 3, min_y - 3),
                font,
                font_scale,
                text_color,
                thickness,
                lineType=cv2.LINE_AA,
            )

    # Blend overlay with original for translucent highlights
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cv2.imwrite(output_path, img)

    return img
