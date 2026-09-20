import re
from typing import Dict, Any, Optional

def parse_listing_text(text: str) -> Dict[str, Any]:
    """
    Parses unstructured pasted e-commerce product listing text into structured facts.
    Supports English and bilingual Hindi lines.
    """
    facts: Dict[str, Any] = {
        "mrp": None,
        "mrp_tax_inclusive": False,
        "net_quantity": None,
        "mfg_date": None,
        "expiry_date": None,
        "manufacturer": None,
        "customer_care": None,
        "country_of_origin": None,
        "fssai": None,
        "unit_sale_price": None,
    }

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines:
        line_lower = line.lower()

        # MRP & Tax Inclusive
        if any(kw in line_lower for kw in ["mrp", "price:", "m.r.p", "₹", "rs."]):
            if not facts["mrp"]:
                facts["mrp"] = line
            if any(t in line_lower for t in ["inclusive", "incl", "कर सहित"]):
                facts["mrp_tax_inclusive"] = True

        if any(t in line_lower for t in ["inclusive of all taxes", "incl. of all taxes", "incl of taxes", "सभी कर सहित"]):
            facts["mrp_tax_inclusive"] = True

        # Net Quantity
        if any(kw in line_lower for kw in ["net qty", "net quantity", "net weight", "weight:", "volume:", "शुद्ध मात्रा", "मात्रा"]):
            if not facts["net_quantity"]:
                facts["net_quantity"] = line
        elif re.search(r'\b\d+\s*(?:g|kg|ml|l|ltr|gm|grams|pieces|units)\b', line, re.IGNORECASE):
            if not facts["net_quantity"]:
                facts["net_quantity"] = line

        # Unit Sale Price
        if any(kw in line_lower for kw in ["usp", "unit price", "unit sale price", "/g", "/kg", "/ml", "/l"]):
            if not facts["unit_sale_price"]:
                facts["unit_sale_price"] = line

        # Mfg / Pkd Date
        if any(kw in line_lower for kw in ["mfg", "manufacture date", "pkd", "packed", "date of pack", "निर्माण तिथि"]):
            if not facts["mfg_date"]:
                facts["mfg_date"] = line

        # Expiry Date
        if any(kw in line_lower for kw in ["expiry", "exp date", "use by", "best before", "समाप्ति तिथि"]):
            if not facts["expiry_date"]:
                facts["expiry_date"] = line

        # Manufacturer / Packer / Importer
        if any(kw in line_lower for kw in ["manufacturer", "manufactured by", "marketed by", "packer", "imported by", "निर्माता"]):
            if not facts["manufacturer"]:
                facts["manufacturer"] = line

        # Customer Care
        if any(kw in line_lower for kw in ["customer care", "consumer care", "toll free", "care@", "helpline", "grievance", "ग्राहक सेवा"]):
            if not facts["customer_care"]:
                facts["customer_care"] = line
        elif re.search(r'\b1800[-\s]?\d{3}[-\s]?\d{3,4}\b|@.*\.(?:com|in)', line):
            if not facts["customer_care"]:
                facts["customer_care"] = line

        # Country of origin
        if any(kw in line_lower for kw in ["country of origin", "origin:", "made in", "उत्पत्ति देश", "मूल देश"]):
            if not facts["country_of_origin"]:
                facts["country_of_origin"] = line

        # FSSAI
        if "fssai" in line_lower or re.search(r'\b1\d{13}\b', line):
            if not facts["fssai"]:
                facts["fssai"] = line

    return facts
