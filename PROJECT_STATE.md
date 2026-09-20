# MAARS Lens — Project State

## 1. Completed

* **Database Architecture & Migrations**:
  * `backend/app/migrations/001_initial_schema.sql` finalized as pure schema-only DDL (18 tables, 17 enums, performance indexes, strict `ON DELETE RESTRICT` integrity). Untouched and unexecuted.
  * `backend/app/migrations/seed_demo_rules.sql` optional demo fixture (idempotent, checks for active admin, touches no `auth.users`). Untouched and unexecuted.
* **SQLAlchemy Models**:
  * Clean declarative models in `backend/app/models/` (`user`, `area`, `inspection`, `rule`, `audit`, `violation`, `notification`, `compliance`, `signature`, `enums`).
* **Pydantic Schemas**:
  * Complete schemas in `backend/app/schemas/` (`scan`, `rule`, `auth`, `customer`, `admin`, `violation`, `notification`, `report`, `signature`).
* **Step 2 — Core Services (SIH Prototype)**:
  * `assert_inspection_unfinalized()`: Guards inspection mutability; raises `InspectionAlreadyFinalizedError` on finalized inspection instances or flags.
  * **Compliance Aggregation**: Hierarchical rule evaluation (`fail` short-circuits to `non_compliant`, followed by `needs_review`). Strictly enforces locked rule: zero applicable rules (empty list or all `not_applicable`) → `needs_review`. Evaluates dual-layer `automated_compliance` and `final_compliance`.
  * **Effective-Result Computation**: Evaluates `effective_result` from `automated_result` + optional `manual_review_result`. Enforces mandatory non-empty `manual_review_reason` and forbids `not_applicable` manual review outcomes.
  * **Cryptographic Report Hashing**: `compute_report_hash()` generates a canonical, deterministic SHA-256 string (`sha256:<64-hex>`, length 71) resistant to JSON key reordering.
  * **AES-256-GCM Cryptographic Utility**: Generic reusable utility in `app/core/security.py` using Python's `cryptography` library with 12-byte random nonce and 16-byte GCM tag. Scope is strictly reserved for sensitive customer contact data; kept completely unapplied to officer notifications and signature tokens.
  * **Rule Engine**: Evaluates `ComplianceRuleVersion.check_definition` across multiple operators (`exists`, `regex`, `contains`, `eq`, `gte`, `lte`, `between`, `compare_field`), OCR confidence threshold gating (triggers `needs_review`), and visual measurement flags.
  * **PDF Report Generator**: Built with `reportlab` producing compliant `%PDF-1.4` inspection certificates complete with product metadata, officer info, audit table, and tamper-evident SHA-256 seal.
  * **Automated Test Suite**: 22 unit tests passing in `backend/tests/test_core_services.py` (100% pass rate).
* **Step 3 — API Scans Router (`backend/app/routers/scans.py`)**:
  * `POST /api/v1/scans/upload`: Accepts officer scan uploads with offline idempotency via `client_submission_id`. Rejects client-supplied `automated_result`, `effective_result`, `automated_compliance`, or `final_compliance` (`extra="forbid"`).
  * `POST /api/v1/scans/{id}/result`: Accepts manual review submissions; calls `assert_inspection_unfinalized()` first; rejects `manual_review_result == not_applicable` and empty/whitespace reasons; computes `effective_result` server-side; recomputes `automated_compliance` and `final_compliance`.
  * `POST /api/v1/scans/{id}/finalize`: Calls `assert_inspection_unfinalized()` first; locks inspection immutability; computes and records SHA-256 `report_hash`. All subsequent mutation attempts on finalized inspections raise 400 Bad Request.
  * `GET /api/v1/scans/{id}/result` and `GET /api/v1/scans/`: Inspection query and listing.
  * **Integration Test Suite**: 8 integration tests passing in `backend/tests/test_scans_router.py` (Total 30 tests passing, 100% pass rate).

* **Step 4 — OCR/OpenCV Integration**:
  * Clean `BaseOCRExtractor` interface with `MockOCRExtractor` returning deterministic text and confidence scores; OpenCV preprocessing (grayscale, bilateral denoising, adaptive thresholding); confidence gating wired to rule engine. 5 integration tests passing in `backend/tests/test_ocr_pipeline.py`.
* **Step 5 Part 1 — Reports Router (`backend/app/routers/reports.py`)**:
  * PDF streaming (`/pdf`), report summary (`/summary`), and tamper verification (`/verify`) endpoints. Enforces finalization check (400 if unfinalized), role checks, and strict whitelist response. 5 integration tests passing in `backend/tests/test_reports_router.py`.
* **Step 5 Part 2 — Violations Router (`backend/app/routers/violations.py`)**:
  * Statutory violation creation, retrieval, and status transitions for finalized non-compliant inspections. Enforces terminal state immutability, mandatory resolution notes, and privacy whitelist. 9 integration tests passing in `backend/tests/test_violations_router.py`.
* **Step 6 — Rules Router & Statutory Engine Readiness (`backend/app/routers/rules.py`, `rule_engine/engine.py`)**:
  * Implemented two-level rule architecture: `ComplianceRule` (logical identity) and `ComplianceRuleVersion` (immutable snapshots).
  * Strict version immutability: no in-place update endpoints; new requirements must be published as version N+1.
  * Version uniqueness (`rule_id`, `version`) and duplicate `rule_code` conflict checks return 409 Conflict.
  * Demo verification status defaults to `'demo'` and is strictly segregated from verified rules (`'verified'`).
  * Role authorization: rule creation, version publishing, and activation toggles strictly require `UserRole.admin` (403 for non-admins). Authenticated officers can list and read rules.
  * Full audit trail logging via `RuleAuditLog` for create, new version, activate, and deactivate actions.
  * Engine database integration: `run_audit()` dynamically loads only active rule versions (`is_active == True`) with `selectinload(ComplianceRuleVersion.rule)`.
  * Prepared separate production seed script template: `backend/app/migrations/seed_statutory_rules.sql`.
  * 11 integration tests passing in `backend/tests/test_rules_router.py` (Total 60 tests passing, 100% pass rate).

## 2. In Progress

* Ready to receive final Legal Metrology statutory rules tomorrow morning. Transition towards remaining routers (`admin.py`, `auth.py`, `customers.py`).

## 3. Next Step

* Await user review and approval of Rules Router before proceeding to `admin.py`.

## 4. Known Issues

* Remaining routers (`admin.py`, `auth.py`, `customers.py`, `notifications.py`, `areas.py`) remain in their scaffold state until their dedicated steps.
* **OCR Extractor Upstream Limitation (PaddleOCR on Windows / Python 3.13)**: 
  * PaddleOCR/paddlepaddle 3.x (`paddlepaddle==3.3.1` + `paddleocr==3.7.0`) is blocked on Windows CPU / Python 3.13 by an upstream unhandled oneDNN PIR executor C++ exception:
    `NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]  (at ..\paddle\fluid\framework\new_executor\instruction\onednn\onednn_instruction.cc:118)`
  * Pre-PIR stable `paddlepaddle==2.6.2` has no Python 3.13 wheel or prebuilt distribution available on PyPI for Windows x64.
  * `MockOCRExtractor` in `backend/app/services/ocr/extractor.py` is a deterministic placeholder, NOT real OCR, and must be replaced with a real PaddleOCR-backed implementation (via the `BaseOCRExtractor` interface) once either a compatible paddlepaddle build exists or the environment moves to a supported Python version (e.g. 3.12 or Linux container).
  * The clean plug-in interface `BaseOCRExtractor` is defined in `backend/app/services/ocr/extractor.py` so a future teammate knows exactly where to plug in a real implementation without altering any downstream consumers (`extract_facts`, rule engine gating, or inspection routers).
* **Violation Terminal State Lifecycle Limitation**:
  * In `backend/app/routers/violations.py`, once a statutory violation enters terminal status (`resolved` or `dismissed`), subsequent transition attempts are strictly rejected with HTTP 400 Bad Request.
  * No admin-reopen path is built in this step; any administrative reopening workflow is reserved for future administrative escalation tasks.
* Database has not been migrated on live PostgreSQL instance (as per instruction: no migrations run yet).



