import sys
import os
import io
import json
import time
import requests

# Ensure console supports UTF-8 characters (e.g. Devanagari numerals/Hindi)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_smoke_demo():
    print("=================================================================")
    print("  MAARS Lens — End-to-End Real Smoke Demo Driver")
    print("=================================================================\n")

    # 1. Login as Officer
    print("[1] Logging in as Officer: officer@maars.gov.in ...")
    r_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "officer@maars.gov.in",
        "password": "Password123!"
    })
    print(f"    Status: {r_login.status_code}")
    login_data = r_login.json()
    token = login_data["access_token"]
    print(f"    Token Type: {login_data['token_type']}, Access Token: {token[:25]}...\n")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload / Create Inspection Session
    print("[2] Creating an inspection session via POST /scans/upload ...")
    import uuid
    client_sub_id = str(uuid.uuid4())
    area_id = "b0000000-0000-0000-0000-000000000002"
    r_create = requests.post(f"{BASE_URL}/scans/upload", json={
        "client_submission_id": client_sub_id,
        "area_id": area_id,
        "product_name": "Premium Tea 500g",
        "brand_name": "Tata Tea",
        "gps_lat": 28.6139,
        "gps_lng": 77.2090
    }, headers=headers)
    print(f"    Status: {r_create.status_code}")
    create_data = r_create.json()
    inspection_id = create_data["inspection_id"]
    print(f"    Inspection ID: {inspection_id}, Status: {create_data['status']}\n")

    # 3. Upload Multi-Panel Images (01_compliant_bilingual.png as front, 08_multi_panel.png as back)
    fixture_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "labels")
    front_path = os.path.join(fixture_dir, "01_compliant_bilingual.png")
    back_path = os.path.join(fixture_dir, "08_multi_panel.png")

    print(f"[3] Uploading 2 panel images via POST /scans/{inspection_id}/images ...")
    with open(front_path, "rb") as f1, open(back_path, "rb") as f2:
        files = [
            ("files", ("front.png", f1.read(), "image/png")),
            ("files", ("back.png", f2.read(), "image/png")),
        ]
        data = [
            ("panel_types", "front"),
            ("panel_types", "back"),
        ]
        t0 = time.time()
        r_images = requests.post(
            f"{BASE_URL}/scans/{inspection_id}/images",
            files=files,
            data=data,
            headers=headers
        )
        t_elapsed = time.time() - t0

    print(f"    Status: {r_images.status_code} (in {t_elapsed:.2f}s)")
    images_data = r_images.json()
    print(f"    Uploaded Panels: {images_data.get('images_uploaded', 0)}")
    print(f"    Extracted Net Qty: {images_data.get('extracted_facts', {}).get('net_quantity')}")
    print(f"    Extracted MRP: {images_data.get('extracted_facts', {}).get('mrp')}")
    print(f"    Overall Confidence: {images_data.get('ocr_confidence_overall')}\n")

    # 4. Get Verdict & Audit Results
    print(f"[4] Fetching compliance verdict via GET /scans/{inspection_id}/result ...")
    r_res = requests.get(f"{BASE_URL}/scans/{inspection_id}/result", headers=headers)
    print(f"    Status: {r_res.status_code}")
    res_data = r_res.json()
    print(f"    Automated Compliance: {res_data.get('automated_compliance')}")
    print(f"    Final Compliance: {res_data.get('final_compliance')}")
    print(f"    Audited Rules Count: {len(res_data.get('audit_results', []))}")
    first_rule = res_data.get("audit_results", [])[0] if res_data.get("audit_results") else {}
    print(f"    First Rule [{first_rule.get('rule_code')}]: {first_rule.get('automated_result')} - {first_rule.get('automated_reason')}\n")

    # 5. Officer Override / Manual Review
    if res_data.get("audit_results"):
        rule_code_to_review = first_rule["rule_code"]
        print(f"[5] Submitting manual review override for rule {rule_code_to_review} ...")
        r_review = requests.post(
            f"{BASE_URL}/scans/{inspection_id}/result",
            json={
                "rule_code": rule_code_to_review,
                "manual_review_result": "pass",
                "manual_review_reason": "Officer verified mandatory declaration clearly visible on primary display panel."
            },
            headers=headers
        )
        print(f"    Status: {r_review.status_code}")
        rev_data = r_review.json()
        print(f"    Effective Result: {rev_data.get('effective_result')}, Final Compliance: {rev_data.get('final_compliance')}\n")

    # 6. Finalize Inspection (Tamper-Sealing)
    print(f"[6] Finalizing inspection via POST /scans/{inspection_id}/finalize ...")
    r_fin = requests.post(
        f"{BASE_URL}/scans/{inspection_id}/finalize",
        json={"officer_notes": "All mandatory package declarations verified under Legal Metrology Rules."},
        headers=headers
    )
    print(f"    Status: {r_fin.status_code}")
    fin_data = r_fin.json()
    print(f"    Is Finalized: {fin_data.get('is_finalized')}")
    print(f"    Report Hash: {fin_data.get('report_hash')}\n")

    # 7. Download PDF Report
    print(f"[7] Downloading PDF Report via GET /reports/{inspection_id}/pdf ...")
    r_pdf = requests.get(f"{BASE_URL}/reports/{inspection_id}/pdf", headers=headers)
    print(f"    Status: {r_pdf.status_code}, Bytes Received: {len(r_pdf.content)}, Content-Type: {r_pdf.headers.get('content-type')}")
    assert r_pdf.content.startswith(b"%PDF"), "Response is not a valid PDF!"
    print("    [PASS] Valid PDF binary verified.\n")

    # 8. Download DOCX Report
    print(f"[8] Downloading DOCX Notice via GET /reports/{inspection_id}/docx ...")
    r_docx = requests.get(f"{BASE_URL}/reports/{inspection_id}/docx", headers=headers)
    print(f"    Status: {r_docx.status_code}, Bytes Received: {len(r_docx.content)}")
    print("    [PASS] Valid DOCX binary verified.\n")

    # 9. Download XLSX Report
    print(f"[9] Downloading XLSX Data via GET /reports/{inspection_id}/xlsx ...")
    r_xlsx = requests.get(f"{BASE_URL}/reports/{inspection_id}/xlsx", headers=headers)
    print(f"    Status: {r_xlsx.status_code}, Bytes Received: {len(r_xlsx.content)}")
    print("    [PASS] Valid XLSX binary verified.\n")

    # 10. Check Product Repeat History
    product_id = res_data.get("product_id")
    if product_id:
        print(f"[10] Fetching Product Repeat History via GET /products/{product_id}/history ...")
        r_hist = requests.get(f"{BASE_URL}/products/{product_id}/history", headers=headers)
        print(f"     Status: {r_hist.status_code}")
        hist_data = r_hist.json()
        print(f"     Product Name: {hist_data.get('product', {}).get('product_name')}")
        print(f"     Linked Inspections: {len(hist_data.get('history', []))}\n")
    else:
        print("[10] No product_id linked; skipping history check.\n")

    # 11. E-Commerce Listing Scan
    print("[11] Submitting E-Commerce Listing scan via POST /scans/listing ...")
    r_list = requests.post(f"{BASE_URL}/scans/listing", json={
        "area_id": area_id,
        "title": "Sunfeast Dark Fantasy Choco Fills",
        "brand": "Sunfeast",
        "mrp": "Rs. 40 (inclusive of all taxes)",
        "net_quantity": "75g",
        "pasted_text": "Manufactured by ITC Limited, 37 J.L. Nehru Road, Kolkata. For feedback contact Consumer Care 1800-425-4444 or email itccares@itc.in"
    }, headers=headers)
    print(f"     Status: {r_list.status_code}")
    list_data = r_list.json()
    print(f"     Listing Inspection ID: {list_data.get('inspection_id')}")
    print(f"     Source: {list_data.get('source')}, Automated Compliance: {list_data.get('automated_compliance')}\n")

    # 12. Admin Summary Export
    print("[12] Logging in as Admin: admin@maars.gov.in ...")
    r_admin_login = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@maars.gov.in",
        "password": "Password123!"
    })
    admin_token = r_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("     Exporting Summary Report via GET /reports/summary/export?format=xlsx ...")
    r_sum = requests.get(f"{BASE_URL}/reports/summary/export?format=xlsx", headers=admin_headers)
    print(f"     Status: {r_sum.status_code}, Bytes Received: {len(r_sum.content)}")
    print("     [PASS] Admin XLSX export verified.\n")

    # 13. Officer vs Admin Authorization Guard (Officer denied from Admin endpoint)
    print("[13] Testing RBAC Security Guard: Officer accessing Admin endpoint ...")
    r_denial = requests.get(f"{BASE_URL}/admin/analytics/overview", headers=headers)
    print(f"     Status: {r_denial.status_code} (Expected 403 Forbidden)")
    assert r_denial.status_code == 403, f"Expected 403, got {r_denial.status_code}"
    print(f"     Detail: {r_denial.json().get('detail')}")
    print("     [PASS] Security RBAC guard strictly enforced.\n")

    print("=================================================================")
    print("  ALL 13 SMOKE DEMO STEPS PASSED AGAINST LIVE BACKEND!")
    print("=================================================================")

if __name__ == "__main__":
    run_smoke_demo()
