# AUDIT RE-VERIFICATION ADDENDUM
## Empirical Re-verification of Previous Audit Claims (MAARS Lens / LM-Scan)

**Execution Date:** September 20, 2026  
**Lead Auditor / Senior Engineer:** Full-Stack Regulatory Systems Engineer  
**Target Branch:** ix/audit-remediation (Baseline commit: c11867c - Initial baseline before audit remediation)  
**Audit Policy:** Strict Empirical Verification — every claim grounded in actual command execution, verified file paths, and inspected byte payloads.

---

## (a) Automated Backend Test Suite Re-verification

The backend pytest suite was executed using the configured Python 3.11 environment (ackend/.venv-ocr/Scripts/pytest.exe):

`	ext
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Rajeev Kumar Behera\OneDrive\Desktop\MAARS-lens\maars-lens_original_backup_to continue\backend
configfile: pytest.ini
plugins: anyio-4.12.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO
collected 103 items

tests/test_admin_router.py .........................                     [ 24%]
tests/test_core_services.py .........                                    [ 33%]
tests/test_e2e_simulation.py .                                           [ 33%]
tests/test_focused_verifications.py .........                            [ 42%]
tests/test_listing_input.py ...                                          [ 45%]
tests/test_ocr_pipeline.py ......                                        [ 51%]
tests/test_ocr_robustness.py ......                                      [ 57%]
tests/test_paddle_ocr_e2e.py ..                                          [ 59%]
tests/test_products_history.py .                                         [ 60%]
tests/test_rbac_security.py .............                                [ 72%]
tests/test_reports_router.py .........                                   [ 81%]
tests/test_rules_router.py .........                                     [ 90%]
tests/test_scans_router.py ........                                      [ 98%]
tests/test_statutory_rules.py .                                          [ 99%]
tests/test_violations_router.py .                                        [100%]

===================== 103 passed, 100 warnings in 53.78s ======================
`
**Actual Result:** **103 passed, 0 failed, 100 warnings (DeprecationWarnings in paddle protobuf), 100% pass rate in 53.78 seconds.**

---

## (b) File Citation Audit & Line-Number Correction

The previous audit cited several files with inaccurate paths or invented line numbers. Every file has now been opened, inspected, and documented:

| Cited File | Previous Audit Claim | Re-verified Status & Real File Location | Real Line Numbers |
| :--- | :--- | :--- | :--- |
| pdf.py | Cited as ackend/app/services/reporting/pdf.py:45-220 | **WRONG PATH:** The actual file is [ackend/app/services/pdf/generator.py](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/services/pdf/generator.py) | generate_report_pdf is at generator.py:77-298 (222 lines) |
| docx.py | Cited as ackend/app/services/reporting/docx.py:25-110 | **WRONG PATH:** docx.py does NOT exist as an independent module. Implemented inside generator.py. | generate_report_docx is at generator.py:300-390 |
| xlsx.py | Cited as ackend/app/services/reporting/xlsx.py:20-80 | **WRONG PATH:** xlsx.py does NOT exist as an independent module. Implemented inside generator.py. | generate_report_xlsx is at generator.py:392-468 |
| eports.py | Cited as ackend/app/routers/reports.py:25-120 | Path confirmed at [ackend/app/routers/reports.py](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/routers/reports.py). | Total lines: 479. PDF endpoint at lines 142-205, DOCX at lines 207-268, XLSX at lines 270-332. |
| preprocessor.py | Cited as ackend/app/services/ocr/preprocessor.py:45-120 | Path confirmed at [ackend/app/services/ocr/preprocessor.py](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/services/ocr/preprocessor.py). | File has only 94 total lines. preprocess_image spans lines 24-93. |
| exemptions.py | Cited as ackend/app/services/rule_engine/exemptions.py:15-65 | Path confirmed at [ackend/app/services/rule_engine/exemptions.py](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/services/rule_engine/exemptions.py). | check_package_exemption spans lines 19-120 (121 total lines). |
| ImageUpload.jsx | Cited as rontend/src/components/ImageUpload.jsx:1-120 | Path confirmed at [rontend/src/components/ImageUpload.jsx](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/frontend/src/components/ImageUpload.jsx). | File has 112 lines. Mobile <input capture="environment"> is at lines 76-83. |
| evaluators.py | Cited as ackend/app/services/rule_engine/evaluators.py:12-140 | Path confirmed at [ackend/app/services/rule_engine/evaluators.py](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/services/rule_engine/evaluators.py). | File has 215 total lines. evaluate_rule_check spans lines 13-214. |
| security.py | Cited as ackend/app/core/security.py:20-60 for passwords | **INCORRECT CLAIM:** security.py contains AES-256-GCM encryption only (lines 1-56). Password hashing with bcrypt is NOT implemented. Login in [ackend/app/routers/auth.py:108-115](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/routers/auth.py#L108-L115) does plaintext equality checks against a hardcoded set {\"Password123!\", \"MAARS@123\"}! |

---

## (c) Full Officer Flow Dynamic Re-verification

The complete officer workflow was executed against live server endpoints (http://127.0.0.1:8001/api/v1):

`	ext
1. Officer Login: status=200, token_len=399
2. Create Scan (/scans/upload): status=201, scan_id=ab97c077-59fa-404f-a352-e8fe56a0e9b4
3. Upload Image (/scans/.../images): status=201, facts_count=10
4. Get Result (/scans/.../result): status=200, total_audit_results=10
5. Manual Override: status=200
6. Finalize: status=200, is_finalized=True, report_hash=sha256:3aa6e1d7940fa14be7...
7. Exports:
   PDF:  status=200, size=29048 bytes
   DOCX: status=200, size=37745 bytes
   XLSX: status=200, size=5937 bytes
Export files saved to audit_output/verified_exports/
`

### Export Content Inspection
The actual generated files in udit_output/verified_exports/ were opened and parsed:
- **PDF (erified_report.pdf, 29,048 bytes):** Valid %PDF-1.4 document generated via ReportLab. Contains title, inspection metadata block (Inspection ID, Officer ID, Product Name, Brand Name, Final Compliance), tabular breakdown of 10 statutory rules, and digital SHA-256 cryptographic seal.
- **DOCX (erified_report.docx, 37,745 bytes):** Valid OOXML Microsoft Word document with 6 paragraphs and 2 structured tables: Table 0 (Metadata, 6 rows x 2 cols), Table 1 (Statutory Audit Evaluations, 11 rows x 5 cols: Rule Code, Statutory Reference, Automated Result, Manual Review, Effective Result).
- **XLSX (erified_report.xlsx, 5,937 bytes):** Valid Excel workbook with worksheet named "Inspection Report" (22 rows x 5 columns), formatted with styled header fills, metadata rows, and evaluation table matching the PDF.

---

## (d) 13-Label Benchmark: OCR Accuracy, Precision/Recall & Latency

A dynamic benchmark was run using POST /api/v1/customer/scan across 13 label test images (8 existing fixtures + 5 new perturbation fixtures):

| Image File | Test Condition / Scenario | HTTP Status | Verdict | Facts Extracted | Statutory Violations Flagged | Measured Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
|  1_compliant_bilingual.png | Standard bilingual label | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 3.97s |
|  2_missing_mrp.png | Missing MRP declaration | 200 | 
on_compliant | 7 fields | 4 (LMPC-R6-MRP, etc.) | 3.96s |
|  3_tiny_font.png | Small font size | 200 | 
on_compliant | 6 fields | 2 (LMPC-R6-COO, LMPC-R7-FONT) | 4.16s |
|  4_missing_address.png | Missing manufacturer address | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 3.06s |
|  5_imported_no_origin.png | Imported with missing origin | 200 | 
on_compliant | 7 fields | 2 (LMPC-R6-COO, LMPC-R7-FONT) | 3.31s |
|  6_blurry_label.png | Severely blurred image | 200 | 
on_compliant | 1 fields | 9 (all presence rules failed) | 0.73s |
|  7_hindi_english_mix.png | Hindi & English mixed text | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 3.75s |
|  8_multi_panel.png | Multi-panel composite | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 2.99s |
|  9_rotated_15deg.png | **NEW:** Rotated ^\circ$ affine warp | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 3.29s |
| 10_glare_reflection.png | **NEW:** Intense glare artifact | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 3.03s |
| 11_low_light.png | **NEW:** Low-light (25% luminance) | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 2.18s |
| 12_non_permitted_units.png| **NEW:** Non-permitted units ("16 oz (450 gms)") | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 2.28s |
| 13_multi_mrp.png | **NEW:** Multi/conflicting MRPs | 200 | 
eeds_review | 8 fields | 1 (LMPC-R7-FONT-SIZE) | 2.38s |

### Critical Empirical Findings from Label Benchmark
1. **Font Size Fallback Behavior:** Notice that **all 8 valid labels received 
eeds_review** solely due to LMPC-R7-FONT-SIZE because optical millimeter scale cannot be verified without physical calibration! This confirms that the engine deterministically refuses to guess without physical calibration.
2. **Missing Unit / Conflict Check in Active Rule Pack:** In 12_non_permitted_units.png, "16 oz (450 gms)" was parsed into 
et_quantity, but the active rule pack did NOT flag a violation for non-permitted units. In 13_multi_mrp.png, multiple MRP declarations did NOT trigger a dual-pricing violation. **These confirm Gaps B3 and B6, and justify Task 4.**
3. **Deskew Performance:**  9_rotated_15deg.png was successfully deskewed by preprocessor.py Hough line transform, extracting 8 facts without error.
4. **Latency:** Mean end-to-end CPU latency across 13 images was **3.01 seconds** (ranging from 0.73s on blurry to 4.16s on high-density text).

---

## (e) RBAC Matrix Re-verification Across All Roles

Each protected endpoint was called under 5 identity states: Anonymous, Officer, Admin, Retailer, and Consumer:

| Endpoint Tested | Anonymous | Officer | Admin | Retailer | Consumer | Re-verified Access Enforcement |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| POST /scans/upload | 401 | **201** | 403 | 403 | 403 | **STRICT:** Officer-only scan creation enforced. |
| GET /rules/ | 401 | **200** | **200** | **200** | **200** | **STRICT:** Authenticated read-only access for all roles. |
| POST /rules/ | 401 | 403 | **422*** | 403 | 403 | **STRICT:** Admin-only mutation enforced (422 schema validation reached). |
| GET /admin/analytics/overview | 401 | 403 | **200** | 403 | 403 | **STRICT:** Admin-only analytics access enforced. |
| GET /admin/users | 401 | 403 | **200** | 403 | 403 | **STRICT:** Admin-only user management enforced. |
| GET /violations/{id} | 401 | **404**** | **404**** | 403 | 403 | **STRICT:** Officer & Admin only (404 not found reached; Retailer/Consumer get 403). |
| POST /customer/scan | 401 | 403 | 403 | 403 | **422***** | **STRICT:** Consumer-only scan portal enforced. |

*\* 422 indicates authentication passed and Pydantic request schema validation was executed.*  
*\*\* 404 indicates authorized access reached the database lookup for the nonexistent dummy ID.*

---

## (f) Wrong Statuses in Previous Audit & Required Downgrades

Based on actual empirical testing, the following statuses from the previous audit were factually wrong or overstated and are hereby downgraded:

1. **G1 (Secure auth — "bcrypt password hashing"):**  
   - *Previous Verdict:* ✅ Implemented & Working (Claimed "Passwords hashed with bcrypt").  
   - *Empirical Reality:* **FALSE.** [ackend/app/routers/auth.py:108-115](file:///c:/Users/Rajeev%20Kumar%20Behera/OneDrive/Desktop/MAARS-lens/maars-lens_original_backup_to%20continue/backend/app/routers/auth.py#L108-L115) compares passwords in plaintext against {\"Password123!\", \"MAARS@123\"}. Passwords are never hashed with bcrypt.  
   - *Downgraded Status:* **🟡 Partial (Stubbed Mock Authentication)**.
2. **B3 / B6 (Non-permitted units & Multi-MRP):**  
   - *Previous Verdict:* ✅ Implemented & Working.  
   - *Empirical Reality:* In benchmark testing (12_non_permitted_units.png and 13_multi_mrp.png), non-standard units ("oz", "gms") and dual prices were not flagged as violations by the active rule pack.  
   - *Downgraded Status:* **🟡 Partial**.
3. **E5 (Bulk / Batch scanning):**  
   - *Previous Verdict:* ❌ Missing. Confirmed missing.
4. **C1 (Font height measurement):**  
   - *Previous Verdict:* 🟡 Partial. Confirmed partial (pixel height measured, mm scale requires physical calibration).
