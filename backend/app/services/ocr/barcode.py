"""
Barcode detection helper.
Uses pyzbar if installed/available, with graceful fallback to None if not installed.
"""
from typing import Optional, Tuple, Dict, Any
import numpy as np

def decode_barcode(image: np.ndarray) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract barcode/QR code data and format from an image.
    Returns dict with {"data": str, "type": str} or None.
    Gracefully handles missing pyzbar or underlying zbar C-library.
    """
    try:
        from pyzbar import pyzbar
        decoded = pyzbar.decode(image)
        if decoded:
            first = decoded[0]
            data_str = first.data.decode("utf-8", errors="ignore").strip()
            barcode_type = first.type
            return {"data": data_str, "type": barcode_type}
    except Exception:
        # Fallback if pyzbar or libzbar not available or image decode error
        pass
    return None
