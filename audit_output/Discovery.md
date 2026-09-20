# LM-Scan (MAARS Lens) System Discovery Report

**Audit Date**: September 20, 2026  
**Auditor Role**: Senior QA Auditor & Full-Stack Code Reviewer  
**Repository**: `c:\Users\Rajeev Kumar Behera\OneDrive\Desktop\MAARS-lens\maars-lens_original_backup_to continue`  
**System Under Audit**: MAARS Lens — Legal Metrology (Packaged Commodities) Rules, 2011 Compliance Platform (SIH 26034)

---

## 1. Stack & Architecture

### Backend
- **Runtime & Language**: Python 3.11 (`.venv-ocr`)
- **API Framework**: FastAPI `0.110.0` with Starlette
- **ORM & Database**: SQLAlchemy `2.0.28` (asyncio with `aiosqlite` on `sqlite+aiosqlite:///./test.db`)
- **Schema & Validation**: Pydantic `2.6.4` (strict validation, `ConfigDict(extra="forbid")` on audit submissions)
- **Computer Vision & OCR**:
  - `PaddleOCR 2.9.1` with `paddlepaddle 2.6.2` (Bilingual English + Hindi / Devanagari models loaded locally at `~/.paddleocr/whl`)
  - OpenCV `cv2 4.9.0.80` for image preprocessing (CLAHE, Fast Non-Local Means denoising, Hough line deskew)
  - `pyzbar` / `cv2.barcode` for barcode and QR code decoding
  - `rapidfuzz` for typo-tolerant statutory declaration keyword detection
- **Report & Document Generation**:
  - `ReportLab 4.1.0` for tamper-evident PDF inspection certificates with SHA-256 cryptographic sealing
  - `python-docx` for `.docx` export
  - `openpyxl` for `.xlsx` workbook export
- **Rate Limiting & Security**:
  - `slowapi` (`Limiter`) with IP-based rate-limiting middleware
  - `python-jose` for JWT signing and verification (HS256)
  - AES-256-GCM authenticated encryption utility in `app/core/security.py`

### Frontend
- **Framework & Build Tool**: React `18.2.0` with Vite `5.4.21`
- **Styling**: Tailwind CSS `3.4.1` with custom slate/indigo dark theme
- **Routing**: `react-router-dom 6.22.3` with hierarchical `ProtectedRoute` RBAC guards
- **PWA Capabilities**: `vite-plugin-pwa 0.17.5` with service worker registration and offline caching
- **HTTP Client**: Axios `1.6.7` with JWT Bearer interceptor and 401 redirect handling
- **Icons**: `lucide-react 0.358.0`

---

## 2. System Entry Points & Routing

### Backend API (`http://127.0.0.1:8001/api/v1`)
1. **Authentication Router** (`/api/v1/auth` in `app/routers/auth.py`):
   - `POST /register`: Registers admin/officer/retailer.
   - `POST /register/customer`: Anonymous customer registration returning customer code.
   - `POST /login`: Issues JWT tokens for credentials, with demo role resolution.
   - `GET /me`: Returns current user identity.
2. **Scans Router** (`/api/v1/scans` in `app/routers/scans.py`):
   - `POST /upload`: Creates inspection scan record with offline idempotency.
   - `POST /{id}/images`: Accepts multi-panel label evidence (front, back, side), runs PaddleOCR, merges declarations, auto-links Product entity, and executes statutory rule engine.
   - `GET /{id}/images`: Lists uploaded and annotated evidence images.
   - `POST /{id}/result`: Records officer manual review with mandatory reason and server-side effective result computation.
   - `POST /{id}/finalize`: Locks inspection immutability, computes SHA-256 report hash, and finalizes status.
   - `GET /{id}/result`: Retrieves full inspection details and audit evaluations.
   - `GET /`: Lists inspections.
   - `POST /listing`: E-commerce product listing text/field declaration auditor.
3. **Customer Router** (`/api/v1/customer` in `app/routers/customers.py`):
   - `POST /scan`: Real-time citizen label scanner executing OCR, declaration extraction, statutory rule engine, and returning violation breakdown.
   - `POST /reports`: Submits citizen grievance/violation reports.
   - `GET /reports`: Lists citizen reports.
   - `GET /reports/{id}`: Retrieves citizen report details.
4. **Rules Router** (`/api/v1/rules` in `app/routers/rules.py`):
   - `GET /`: Lists statutory compliance rules and active versions.
   - `GET /{rule_id}`: Retrieves rule versions.
   - `POST /`: Admin creation of new compliance rules.
   - `POST /{rule_id}/versions`: Admin publication of immutable rule version N+1.
   - `PATCH /{rule_id}/versions/{version_id}/activate`: Admin activation toggle.
5. **Reports Router** (`/api/v1/reports` in `app/routers/reports.py`):
   - `GET /{id}/pdf`: Streams official PDF inspection report.
   - `GET /{id}/docx`: Streams Word document report.
   - `GET /{id}/xlsx`: Streams Excel report.
   - `GET /{id}/summary`: JSON summary of finalized inspection.
   - `GET /{id}/verify`: Tamper-evident cryptographic SHA-256 verification.
6. **Violations Router** (`/api/v1/violations` in `app/routers/violations.py`):
   - `GET /`: Lists statutory violations.
   - `GET /{id}`: Violation details.
   - `POST /`: Creates violation from non-compliant inspection.
   - `PATCH /{id}/status`: Transitions violation status (open -> under_review -> appealed -> resolved/dismissed).
7. **Admin Router** (`/api/v1/admin` in `app/routers/admin.py`):
   - `GET /analytics/overview`: High-level compliance rate and inspection metrics.
   - `GET /analytics/trends`: Time-series inspection trends.
   - `GET /analytics/export`: Streaming CSV export of inspections.
   - `GET /users`: Paginated user registry.
   - `PATCH /users/{id}/status`: Toggles user active state.
8. **Products Router** (`/api/v1/products` in `app/routers/products.py`):
   - `GET /`: Lists recognized products.
   - `GET /{id}`: Product details.
   - `GET /{id}/history`: Inspection timeline for a specific product.
9. **Areas Router** (`/api/v1/areas` in `app/routers/areas.py`):
   - `GET /`: Lists enforcement areas and districts.

---

## 3. Database Schema & Data Models

Database engine: SQLite (`test.db`) with relational schema containing 18 tables:
- `profiles`: User identities with roles (`officer`, `admin`, `retailer`, `customer`).
- `retailers`: Store business name, license number, and shop address.
- `customers`: Citizen accounts with customer code.
- `areas` & `officer_area_assignments`: Geographic enforcement zoning.
- `products`: Commodity registry with barcode, brand, and name for repeat scan tracking.
- `inspections`: Central inspection entity with source (`officer`, `listing`, `customer`), status, automated/final compliance, and SHA-256 report hash.
- `inspection_images`: Uploaded panel evidence with SHA-256 hash, mime, size, and panel type (`front`, `back`, `side`, etc.).
- `image_quality_assessments`: Image quality metrics and issues.
- `compliance_rules`: Logical statutory rules.
- `compliance_rule_versions`: Immutable version snapshots with statutory references, rule type, target field, check definition JSON, and severity.
- `audit_results`: Evaluations linking inspections to rule versions with automated result, effective result, and officer override reason.
- `rule_audit_logs`: Audit trail for rule authoring actions.
- `violations` & `appeals`: Statutory violation records and retailer appeals.
- `officer_signatures`: Cryptographic signature tokens for officers.
- `notifications` & `email_queues`: Notification dispatch log.
- `public_compliance_records` & `customer_reports`: Public search registry and citizen grievance filings.

---

## 4. Demo Accounts & Credentials

Seeded via `backend/scripts/seed_db.py`:

| Role | Email | Password | Account ID | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Officer** | `officer@maars.gov.in` | `Password123!` | `a0000000-0000-0000-0000-000000000001` | Field inspection, multi-panel capture, manual review, finalization |
| **Admin** | `admin@maars.gov.in` | `Password123!` | `a0000000-0000-0000-0000-000000000002` | Rule authoring, analytics, user management, audit review |
| **Retailer** | `retailer@store.in` | `Password123!` | `a0000000-0000-0000-0000-000000000003` | Kirana / shop owner compliance review |
| **Consumer** | `consumer@maars.gov.in` | `Password123!` | `a0000000-0000-0000-0000-000000000004` | Citizen label scanner, rights portal, grievance reporting |

---

## 5. How to Run Locally

### Start Backend
```powershell
cd "c:\Users\Rajeev Kumar Behera\OneDrive\Desktop\MAARS-lens\maars-lens_original_backup_to continue\backend"
$env:PYTHONPATH="."
& ".\.venv-ocr\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Start Frontend
```powershell
cd "c:\Users\Rajeev Kumar Behera\OneDrive\Desktop\MAARS-lens\maars-lens_original_backup_to continue\frontend"
npm run dev -- --host 127.0.0.1
```

### Run Full Test Suite
```powershell
cd "c:\Users\Rajeev Kumar Behera\OneDrive\Desktop\MAARS-lens\maars-lens_original_backup_to continue\backend"
$env:PYTHONPATH="."
& ".\.venv-ocr\Scripts\python.exe" -m pytest -v
# Result: 103 passed, 0 failures (100% pass rate)
```
