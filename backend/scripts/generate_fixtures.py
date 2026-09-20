"""
Synthetic Label Generator for MAARS Lens E2E Fixtures
======================================================
Generates 8 labeled synthetic packaging labels using Pillow with Nirmala/Devanagari font support.
Labels are explicitly marked as "SYNTHETIC TEST FIXTURE - NOT A REAL PRODUCT".
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def get_font(size: int):
    # Try Windows Nirmala font for English + Hindi
    font_paths = [
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/NirmalaB.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def create_label(
    lines: list,
    output_path: str,
    font_size: int = 24,
    blur: bool = False,
    width: int = 700,
    height: int = 450,
):
    img = Image.new("RGB", (width, height), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    font = get_font(font_size)
    small_font = get_font(14)

    # Watermark synthetic banner
    draw.rectangle([(0, 0), (width, 24)], fill=(220, 220, 220))
    draw.text((10, 4), "[SYNTHETIC TEST FIXTURE - FOR QA/TESTING ONLY]", fill=(80, 80, 80), font=small_font)

    # Outer border
    draw.rectangle([(8, 30), (width - 8, height - 8)], outline=(180, 180, 180), width=2)

    y = 45
    for line in lines:
        draw.text((30, y), line, fill=(10, 10, 10), font=font)
        y += font_size + 14

    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=7))

    img.save(output_path, "PNG")
    print(f"Generated fixture: {output_path}")


def main():
    target_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "labels")
    os.makedirs(target_dir, exist_ok=True)

    fixtures_meta = {}

    # 1. Compliant Bilingual
    f1 = os.path.join(target_dir, "01_compliant_bilingual.png")
    create_label([
        "PURE ORGANIC BASMATI RICE",
        "MRP Rs. 250.00 incl. of all taxes",
        "अधिकतम खुदरा मूल्य: ₹ 250.00 सभी कर सहित",
        "Net Qty: 500g (शुद्ध मात्रा: 500 ग्राम)",
        "Mfg Date: 08/2024",
        "Manufactured by: Pure Foods India Pvt Ltd, Okhla, New Delhi 110020",
        "Consumer Care: 1800-111-2222 / care@purefoods.com",
        "Country of Origin: India",
    ], f1, font_size=20, height=420)
    fixtures_meta["01_compliant_bilingual.png"] = {
        "is_synthetic": True,
        "scenario": "compliant_bilingual",
        "expected_verdict": "compliant",
        "expected_violations": [],
        "mandatory_fields_present": ["mrp", "net_quantity", "mfg_date", "manufacturer", "customer_care", "country_of_origin"],
    }

    # 2. Missing MRP
    f2 = os.path.join(target_dir, "02_missing_mrp.png")
    create_label([
        "HIMALAYAN HERBAL TEA",
        "Net Qty: 250g",
        "Mfg Date: 07/2024",
        "Manufactured by: Himalaya Herbs Ltd, Dehradun, UK 248001",
        "Consumer Care: 1800-222-3333 / help@himalaya.org",
        "Country of Origin: India",
    ], f2, font_size=22, height=360)
    fixtures_meta["02_missing_mrp.png"] = {
        "is_synthetic": True,
        "scenario": "missing_mrp",
        "expected_verdict": "non_compliant",
        "expected_violations": ["LMPC-R6-MRP"],
        "mandatory_fields_present": ["net_quantity", "mfg_date", "manufacturer", "customer_care", "country_of_origin"],
    }

    # 3. Tiny Font
    f3 = os.path.join(target_dir, "03_tiny_font.png")
    create_label([
        "MINI ENERGY DROPS",
        "MRP Rs. 50.00 incl. of all taxes",
        "Net Qty: 50ml",
        "Mfg Date: 09/2024",
        "Manufactured by: Tiny Drops Co, Solan, HP 173212",
        "Consumer Care: 1800-333-4444 / info@tinydrops.com",
        "Country of Origin: India",
    ], f3, font_size=10, height=200, width=400)
    fixtures_meta["03_tiny_font.png"] = {
        "is_synthetic": True,
        "scenario": "tiny_font",
        "expected_verdict": "needs_review",
        "expected_violations": ["LMPC-R6-FONT"],
        "mandatory_fields_present": ["mrp", "net_quantity", "mfg_date", "manufacturer", "customer_care", "country_of_origin"],
    }

    # 4. Missing Address
    f4 = os.path.join(target_dir, "04_missing_address.png")
    create_label([
        "CRUNCHY CORN FLAKES",
        "MRP Rs. 180.00 incl. of all taxes",
        "Net Qty: 400g",
        "Mfg Date: 06/2024",
        "Manufactured by: Sunshine Brands",  # Missing address & PIN!
        "Consumer Care: 1800-444-5555 / support@sunshine.com",
        "Country of Origin: India",
    ], f4, font_size=22, height=360)
    fixtures_meta["04_missing_address.png"] = {
        "is_synthetic": True,
        "scenario": "missing_address",
        "expected_verdict": "non_compliant",
        "expected_violations": ["LMPC-R6-MFR"],
        "mandatory_fields_present": ["mrp", "net_quantity", "mfg_date", "customer_care", "country_of_origin"],
    }

    # 5. Imported Without Origin
    f5 = os.path.join(target_dir, "05_imported_no_origin.png")
    create_label([
        "PREMIUM CHOCOLATE WAFER",
        "MRP Rs. 350.00 incl. of all taxes",
        "Net Qty: 300g",
        "Mfg Date: 05/2024",
        "Imported and Packed by: Global Traders Ltd, Nariman Point, Mumbai 400021",
        "Consumer Care: 1800-555-6666 / care@globaltraders.in",
        # Country of origin completely missing!
    ], f5, font_size=20, height=340)
    fixtures_meta["05_imported_no_origin.png"] = {
        "is_synthetic": True,
        "scenario": "imported_no_origin",
        "expected_verdict": "non_compliant",
        "expected_violations": ["LMPC-R6-COO"],
        "mandatory_fields_present": ["mrp", "net_quantity", "mfg_date", "manufacturer", "customer_care"],
    }

    # 6. Blurry Image
    f6 = os.path.join(target_dir, "06_blurry_label.png")
    create_label([
        "INSTANT COFFEE POWDER",
        "MRP Rs. 220.00 incl. of all taxes",
        "Net Qty: 100g",
        "Mfg Date: 08/2024",
        "Manufactured by: Southern Coffee Works, Chikmagalur 577101",
        "Consumer Care: 1800-666-7777 / contact@southerncoffee.in",
        "Country of Origin: India",
    ], f6, font_size=22, blur=True, height=360)
    fixtures_meta["06_blurry_label.png"] = {
        "is_synthetic": True,
        "scenario": "blurry_label",
        "expected_verdict": "needs_review",
        "expected_violations": ["IMAGE_QUALITY_LOW"],
        "mandatory_fields_present": [],
    }

    # 7. Hindi English Mix
    f7 = os.path.join(target_dir, "07_hindi_english_mix.png")
    create_label([
        "प्राकृतिक शुध्द शहद (NATURAL PURE HONEY)",
        "अधिकतम खुदरा मूल्य: ₹ 199.00 सभी कर सहित",
        "MRP Rs. 199.00 incl. of all taxes",
        "शुद्ध मात्रा: 250 ग्राम (Net Qty: 250g)",
        "पैकिंग तिथि: 09/2024 (Pkd Date: 09/2024)",
        "निर्माता: भारत ग्रामोद्योग संस्थान, खादी भवन, नई दिल्ली 110001",
        "ग्राहक सेवा: 1800-777-8888 / care@gramodyog.org",
        "मूल देश: भारत (Country of Origin: India)",
    ], f7, font_size=20, height=450)
    fixtures_meta["07_hindi_english_mix.png"] = {
        "is_synthetic": True,
        "scenario": "hindi_english_mix",
        "expected_verdict": "compliant",
        "expected_violations": [],
        "mandatory_fields_present": ["mrp", "net_quantity", "mfg_date", "manufacturer", "customer_care", "country_of_origin"],
    }

    # 8. Multi Panel Composite
    f8 = os.path.join(target_dir, "08_multi_panel.png")
    panel_img = Image.new("RGB", (800, 380), color=(245, 245, 245))
    draw_p = ImageDraw.Draw(panel_img)
    font = get_font(20)
    small_font = get_font(14)

    # Front Panel (Left)
    draw_p.rectangle([(10, 10), (390, 370)], outline=(150, 150, 150), width=2)
    draw_p.text((20, 20), "[PANEL: FRONT]", fill=(100, 100, 100), font=small_font)
    draw_p.text((30, 80), "GOLDEN ALMONDS", fill=(0, 0, 0), font=get_font(26))
    draw_p.text((30, 160), "100% California Premium", fill=(50, 50, 50), font=font)
    draw_p.text((30, 240), "Net Qty: 200g", fill=(0, 0, 0), font=font)

    # Back Panel (Right)
    draw_p.rectangle([(410, 10), (790, 370)], outline=(150, 150, 150), width=2)
    draw_p.text((420, 20), "[PANEL: BACK]", fill=(100, 100, 100), font=small_font)
    draw_p.text((430, 60), "MRP Rs. 320.00 incl. of all taxes", fill=(0, 0, 0), font=font)
    draw_p.text((430, 110), "Mfg Date: 09/2024", fill=(0, 0, 0), font=font)
    draw_p.text((430, 160), "Packed by: NutriPack Ltd, Sector 62, Noida 201309", fill=(0, 0, 0), font=font)
    draw_p.text((430, 210), "Customer Care: 1800-888-9999 / help@nutripack.com", fill=(0, 0, 0), font=font)
    draw_p.text((430, 260), "Country of Origin: USA", fill=(0, 0, 0), font=font)

    panel_img.save(f8, "PNG")
    print(f"Generated fixture: {f8}")
    fixtures_meta["08_multi_panel.png"] = {
        "is_synthetic": True,
        "scenario": "multi_panel",
        "expected_verdict": "compliant",
        "expected_violations": [],
        "mandatory_fields_present": ["mrp", "net_quantity", "mfg_date", "manufacturer", "customer_care", "country_of_origin"],
    }

    # Save expected_results.json
    json_path = os.path.join(target_dir, "expected_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(fixtures_meta, f, indent=2, ensure_ascii=False)
    print(f"Saved metadata: {json_path}")


if __name__ == "__main__":
    main()
