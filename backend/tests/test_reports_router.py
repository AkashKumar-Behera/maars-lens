"""
MAARS Lens: Reports Router Integration Tests
============================================
Validates Step 5 requirements for backend/app/routers/reports.py:
(a) Requesting a PDF/summary/verify for a non-finalized inspection returns 400, not 200.
(b) Requesting for a nonexistent inspection_id returns 404.
(c) The /summary response body does NOT contain officer_id, officer internal notes,
    or any signature/raw signature fields (explicit absence assertions).
(d) /verify returns valid=true for an unmodified finalized inspection,
    and valid=false if simulated tampered in the DB after finalization.
(e) /pdf returns actual PDF bytes (starts with %PDF).
"""

import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.enums import UserRole, InspectionStatus, ComplianceStatus, AuditResultType, SeverityLevel
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.routers.reports import router as reports_router
from app.services.pdf.generator import compute_report_hash

TEST_OFFICER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
async def test_env():
    """Sets up an isolated SQLite in-memory engine and test client for reports router."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[Inspection.__table__, AuditResult.__table__],
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return {
            "id": str(TEST_OFFICER_ID),
            "sub": str(TEST_OFFICER_ID),
            "user_metadata": {"role": "officer"},
        }

    app = FastAPI(title="MAARS Lens Reports Test API")
    app.include_router(reports_router, prefix="/api/v1/reports")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "session_factory": session_factory,
        }

    await engine.dispose()


async def _create_test_inspection(
    session_factory,
    is_finalized: bool = True,
    officer_notes: str = "Confidential officer field notes 123",
) -> tuple[Inspection, list[AuditResult]]:
    """Helper to seed an inspection record and associated audit results."""
    async with session_factory() as session:
        insp_id = uuid.uuid4()
        client_sub_id = uuid.uuid4()
        ar_id = uuid.uuid4()
        rule_version_id = uuid.uuid4()

        canonical_payload = {
            "id": str(insp_id),
            "client_submission_id": str(client_sub_id),
            "officer_id": str(TEST_OFFICER_ID),
            "product_name": "Sunflower Oil 1L",
            "brand_name": "PureDrop",
            "automated_compliance": "compliant",
            "final_compliance": "compliant",
            "audit_results": [
                {
                    "rule_code": "LM-MRP-01",
                    "statutory_reference": "Rule 6(1)(e)",
                    "automated_result": "pass",
                    "manual_review_result": None,
                    "effective_result": "pass",
                }
            ],
        }
        report_hash = compute_report_hash(canonical_payload) if is_finalized else None

        inspection = Inspection(
            id=insp_id,
            client_submission_id=client_sub_id,
            officer_id=TEST_OFFICER_ID,
            area_id=uuid.uuid4(),
            retailer_id=uuid.uuid4(),
            product_name="Sunflower Oil 1L",
            brand_name="PureDrop",
            gps_lat=18.5204,
            gps_lng=73.8567,
            image_storage_path=f"inspections/{client_sub_id}/image.jpg",
            status=InspectionStatus.completed if is_finalized else InspectionStatus.processing,
            is_finalized=is_finalized,
            finalized_at=datetime.now(timezone.utc) if is_finalized else None,
            automated_compliance=ComplianceStatus.compliant if is_finalized else None,
            final_compliance=ComplianceStatus.compliant if is_finalized else None,
            report_hash=report_hash,
            officer_notes=officer_notes,
            signature_id=uuid.uuid4() if is_finalized else None,
            signature_hash_at_finalization="mock_sig_hash_456" if is_finalized else None,
        )

        audit_result = AuditResult(
            id=ar_id,
            inspection_id=insp_id,
            rule_version_id=rule_version_id,
            rule_code="LM-MRP-01",
            rule_version=1,
            statutory_reference="Rule 6(1)(e)",
            automated_result=AuditResultType.pass_,
            actual_value="Rs. 180.00",
            expected_value="Present",
            fact_confidence=0.95,
            automated_reason="Declaration complies with statutory requirement.",
            severity=SeverityLevel.major,
            effective_result=AuditResultType.pass_,
        )

        session.add(inspection)
        session.add(audit_result)
        await session.commit()
        await session.refresh(inspection)
        await session.refresh(audit_result)
        return inspection, [audit_result]


# ------------------------------------------------------------------------------
# Requirement (a): Unfinalized inspection returns 400
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reports_unfinalized_inspection_returns_400(test_env):
    """Validation (a): requesting PDF, summary, or verify for an unfinalized inspection returns 400."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    inspection, _ = await _create_test_inspection(session_factory, is_finalized=False)
    insp_id = inspection.id

    # 1. GET /pdf -> 400
    res_pdf = await client.get(f"/api/v1/reports/{insp_id}/pdf")
    assert res_pdf.status_code == 400
    assert "must be finalized" in res_pdf.json()["detail"].lower()

    # 2. GET /summary -> 400
    res_summary = await client.get(f"/api/v1/reports/{insp_id}/summary")
    assert res_summary.status_code == 400
    assert "must be finalized" in res_summary.json()["detail"].lower()

    # 3. GET /verify -> 400
    res_verify = await client.get(f"/api/v1/reports/{insp_id}/verify")
    assert res_verify.status_code == 400
    assert "unfinalized" in res_verify.json()["detail"].lower()


# ------------------------------------------------------------------------------
# Requirement (b): Nonexistent inspection returns 404
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reports_nonexistent_inspection_returns_404(test_env):
    """Validation (b): requesting nonexistent inspection returns 404 across all endpoints."""
    client = test_env["client"]
    nonexistent_id = uuid.uuid4()

    res_pdf = await client.get(f"/api/v1/reports/{nonexistent_id}/pdf")
    assert res_pdf.status_code == 404

    res_summary = await client.get(f"/api/v1/reports/{nonexistent_id}/summary")
    assert res_summary.status_code == 404

    res_verify = await client.get(f"/api/v1/reports/{nonexistent_id}/verify")
    assert res_verify.status_code == 404


# ------------------------------------------------------------------------------
# Requirement (c): Summary response excludes private/internal fields
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reports_summary_excludes_private_and_internal_fields(test_env):
    """
    Validation (c): The /summary response body does NOT contain officer_id,
    officer internal notes, customer GPS, retailer info, or signature fields.
    Explicitly asserts absence of private/internal attributes.
    """
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    inspection, _ = await _create_test_inspection(
        session_factory,
        is_finalized=True,
        officer_notes="TOP_SECRET_INTERNAL_OFFICER_NOTE",
    )
    insp_id = inspection.id

    res = await client.get(f"/api/v1/reports/{insp_id}/summary")
    assert res.status_code == 200
    data = res.json()

    # Expected public/summary fields present
    assert data["inspection_id"] == str(insp_id)
    assert data["product_name"] == "Sunflower Oil 1L"
    assert data["brand_name"] == "PureDrop"
    assert data["is_finalized"] is True
    assert data["report_hash"].startswith("sha256:")
    assert len(data["audit_results"]) == 1

    # LOCKED PRIVACY REQUIREMENT: Explicit absence assertions
    assert "officer_id" not in data, "Privacy violation: officer_id found in summary"
    assert "officer_notes" not in data, "Privacy violation: officer_notes found in summary"
    assert "notes" not in data, "Privacy violation: notes found in summary"
    assert "retailer_id" not in data, "Privacy violation: retailer_id found in summary"
    assert "retailer" not in data, "Privacy violation: retailer info found in summary"
    assert "gps_lat" not in data, "Privacy violation: gps_lat found in summary"
    assert "gps_lng" not in data, "Privacy violation: gps_lng found in summary"
    assert "signature_id" not in data, "Privacy violation: signature_id found in summary"
    assert "signature_hash" not in data, "Privacy violation: signature_hash found in summary"
    assert "signature_hash_at_finalization" not in data, "Privacy violation: signature_hash_at_finalization found in summary"

    # Also verify absence in serialized JSON string
    json_str = res.text
    assert "TOP_SECRET_INTERNAL_OFFICER_NOTE" not in json_str
    assert str(TEST_OFFICER_ID) not in json_str


# ------------------------------------------------------------------------------
# Requirement (d): Verify tamper detection
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reports_verify_detects_tampering(test_env):
    """
    Validation (d): /verify returns valid=true for unmodified finalized inspection,
    and valid=false if simulated tampered in the DB after finalization.
    """
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    inspection, _ = await _create_test_inspection(session_factory, is_finalized=True)
    insp_id = inspection.id

    # 1. Unmodified inspection verification -> valid=true
    res_clean = await client.get(f"/api/v1/reports/{insp_id}/verify")
    assert res_clean.status_code == 200
    clean_data = res_clean.json()
    assert clean_data["valid"] is True
    assert clean_data["report_hash"] == inspection.report_hash

    # 2. Simulate post-finalization database tampering (e.g. modify product_name directly in DB)
    async with session_factory() as session:
        db_insp = await session.get(Inspection, insp_id)
        db_insp.product_name = "Tampered Adulterated Oil 1L"
        await session.commit()

    # 3. Re-verify -> valid=false (hash mismatch detected)
    res_tampered = await client.get(f"/api/v1/reports/{insp_id}/verify")
    assert res_tampered.status_code == 200
    tampered_data = res_tampered.json()
    assert tampered_data["valid"] is False
    assert tampered_data["report_hash"] == inspection.report_hash


# ------------------------------------------------------------------------------
# Requirement (e): PDF returns actual PDF bytes
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reports_pdf_returns_valid_pdf_stream(test_env):
    """Validation (e): /pdf returns actual PDF bytes starting with %PDF."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    inspection, _ = await _create_test_inspection(session_factory, is_finalized=True)
    insp_id = inspection.id

    res = await client.get(f"/api/v1/reports/{insp_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert f"report_{insp_id}.pdf" in res.headers["content-disposition"]

    # Bytes verification: must start with '%PDF'
    pdf_bytes = res.content
    assert pdf_bytes.startswith(b"%PDF"), f"Expected %PDF header, got {pdf_bytes[:10]}"
    assert len(pdf_bytes) > 500, "PDF payload unexpectedly short"


@pytest.mark.asyncio
async def test_reports_docx_and_xlsx_export(test_env):
    """Verifies that /docx and /xlsx endpoints return valid document streams."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    inspection, _ = await _create_test_inspection(session_factory, is_finalized=True)
    insp_id = inspection.id

    # Test DOCX export
    res_docx = await client.get(f"/api/v1/reports/{insp_id}/docx")
    assert res_docx.status_code == 200
    assert "wordprocessingml.document" in res_docx.headers["content-type"]
    assert len(res_docx.content) > 1000

    # Test XLSX export
    res_xlsx = await client.get(f"/api/v1/reports/{insp_id}/xlsx")
    assert res_xlsx.status_code == 200
    assert "spreadsheetml.sheet" in res_xlsx.headers["content-type"]
    assert len(res_xlsx.content) > 1000

    # Test Summary Report endpoint
    res_summary = await client.get("/api/v1/reports/summary/export?format=json")
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert isinstance(data, list)
    assert len(data) >= 1
