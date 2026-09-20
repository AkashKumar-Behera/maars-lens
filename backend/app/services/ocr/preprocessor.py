"""
MAARS Lens: Image Preprocessing Utility
======================================
OpenCV-based image preprocessing for packaged goods label inspection.
Provides:
- Grayscale conversion (1 channel)
- Basic denoising and CLAHE contrast enhancement suitable for label text
- Dimension and channel validation
- Rotation / deskew estimation

This module is strictly prototype-focused and contains no custom ML models or heavy pipelines.
"""

from typing import Tuple, Dict, Any
import cv2
import numpy as np


class PreprocessingError(Exception):
    """Raised when an image cannot be decoded or processed."""
    pass


def preprocess_image(image_bytes: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Decodes raw image bytes and applies standardized label preprocessing:
    1. Decode image into BGR format
    2. Convert to Grayscale (single channel)
    3. Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
    4. Apply Fast Non-Local Means Denoising
    5. Check orientation / deskew
    
    Returns:
        (preprocessed_image, metadata_dict)
        where preprocessed_image is a 2D single-channel uint8 numpy ndarray.
    """
    if not image_bytes:
        raise PreprocessingError("Empty image bytes provided.")

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None or img.size == 0:
        raise PreprocessingError("Failed to decode image: invalid or corrupt image format.")

    steps_applied: Dict[str, Any] = {
        "original_shape": img.shape,
    }

    # 1. Grayscale conversion (ensures 1 channel)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    steps_applied["grayscale"] = True

    # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    steps_applied["clahe"] = True

    # 3. Denoising
    denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21)
    steps_applied["denoised"] = True

    # 4. Basic Deskew / Hough lines orientation check
    edges = cv2.Canny(denoised, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    deskew_angle = 0.0
    if lines is not None:
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta)
            if angle < 45:
                angles.append(angle)
            elif angle > 135:
                angles.append(angle - 180)

        if angles:
            median_angle = float(np.median(angles))
            if abs(median_angle) > 0.5:
                (h, w) = denoised.shape[:2]
                center = (w // 2, h // 2)
                rot_mat = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                denoised = cv2.warpAffine(
                    denoised, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                )
                deskew_angle = median_angle

    steps_applied["deskew_angle_deg"] = deskew_angle
    steps_applied["final_shape"] = denoised.shape
    steps_applied["channels"] = 1 if len(denoised.shape) == 2 else denoised.shape[2]

    return denoised, steps_applied

