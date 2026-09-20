import cv2
import numpy as np
from dataclasses import dataclass
from typing import List

@dataclass
class QualityIssue:
    type: str
    severity: str
    score: float
    threshold: float
    message: str
    actionable_advice: str

def assess_image_quality(image_bytes: bytes) -> dict:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    issues = []
    
    # Blur detection
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
    if laplacian_var < 100:
        issues.append({
            "type": "blur", "severity": "high", "score": laplacian_var, "threshold": 100,
            "message": "The image is too blurry to reliably read the package text.",
            "actionable_advice": "Hold the camera steady and wait for autofocus."
        })
    elif laplacian_var < 200:
        issues.append({
            "type": "blur", "severity": "medium", "score": laplacian_var, "threshold": 200,
            "message": "The image is slightly blurry.",
            "actionable_advice": "Try to stabilize the camera."
        })
        
    # Glare (Overexposed regions > 250)
    glare_mask = cv2.threshold(img, 250, 255, cv2.THRESH_BINARY)[1]
    glare_ratio = cv2.countNonZero(glare_mask) / (img.shape[0] * img.shape[1])
    if glare_ratio > 0.15:
        issues.append({
            "type": "glare", "severity": "high", "score": glare_ratio, "threshold": 0.15,
            "message": "Bright reflection is covering important package information.",
            "actionable_advice": "Change angle to reduce reflection."
        })
        
    # Brightness
    mean_brightness = np.mean(img)
    if mean_brightness < 50:
        issues.append({
            "type": "low_brightness", "severity": "high", "score": mean_brightness, "threshold": 50,
            "message": "The package text may not be readable due to dark image.",
            "actionable_advice": "Ensure adequate lighting."
        })
    elif mean_brightness > 220:
        issues.append({
            "type": "overexposure", "severity": "high", "score": mean_brightness, "threshold": 220,
            "message": "The image is overexposed and text may be washed out.",
            "actionable_advice": "Avoid direct intense light."
        })
        
    # Contrast
    std_dev = np.std(img)
    if std_dev < 30:
        issues.append({
            "type": "low_contrast", "severity": "medium", "score": std_dev, "threshold": 30,
            "message": "Image contrast is low; some text may be hard to read.",
            "actionable_advice": "Improve lighting conditions."
        })
        
    # Resolution
    h, w = img.shape
    if h < 640 or w < 640:
        issues.append({
            "type": "low_resolution", "severity": "high", "score": min(h, w), "threshold": 640,
            "message": "Image resolution is too low for reliable text extraction.",
            "actionable_advice": "Move closer to the package."
        })

    is_acceptable = not any(iss['severity'] == 'high' for iss in issues)
    is_borderline = is_acceptable and any(iss['severity'] == 'medium' for iss in issues)
    
    # Mock score
    score = 100.0 - (len(issues) * 10)
    
    return {
        "is_acceptable": is_acceptable,
        "is_borderline": is_borderline,
        "overall_quality_score": max(0.0, score),
        "issues": issues
    }
