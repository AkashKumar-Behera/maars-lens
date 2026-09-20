"""
MAARS Lens: Scans Router Integration & Security Validation Suite
===============================================================
Proves strictly required Step 3 behaviors:
(a) Client-submitted automated_result/effective_result/automated_compliance/final_compliance
    are rejected (schema-level extra='forbid').
(b) manual_review_result == not_applicable is rejected.
(c) empty/whitespace manual_review_reason is rejected.
(d) effective_result is computed server-side and cannot be set by the client.
(e) a finalized inspection rejects any further mutation attempt via /result and /finalize.
(f) report_hash is populated and matches compute_report_hash() output after finalize.
"""

import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import require_role
from app.models.enums import UserRole, InspectionStatus, ComplianceStatus, AuditResultType, SeverityLevel
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.routers.scans import router as scans_router
from app.services.pdf.generator import compute_report_hash


# ------------------------------------------------------------------------------
# Test Fixtures & Setup
# ------------------------------------------------------------------------------

TEST_OFFICER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
TEST_AREA_ID = uuid.UUID("b0000000-0000-0000-0000-000000000002")
TEST_RETAILER_ID = uuid.UUID("c0000000-0000-0000-0000-000000000003")


@pytest_asyncio.fixture
async def test_env():
    """Sets up an isolated SQLite in-memory engine and FastAPI test client."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Create tables needed for inspection & audit evaluations
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[Inspection.__table__, AuditResult.__table__],
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    from app.core.auth import get_current_user

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return {
            "id": str(TEST_OFFICER_ID),
            "sub": str(TEST_OFFICER_ID),
            "user_metadata": {"role": "officer"},
        }

    # Isolated test app mounting scans router
    app = FastAPI(title="MAARS Lens Scans Test API")
    app.include_router(scans_router, prefix="/api/v1/scans")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "session_factory": session_factory,
        }

    await engine.dispose()


# ------------------------------------------------------------------------------
# (a) Client-submitted forbidden fields rejection
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_rejects_client_controlled_verdicts(test_env):
    client = test_env["client"]

    # 1. Attempt to submit automated_compliance on upload
    res = await client.post(
        "/api/v1/scans/upload",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "area_id": str(TEST_AREA_ID),
            "automated_compliance": "compliant",
        },
    )
    assert res.status_code == 422
    assert "extra_forbidden" in res.text or "extra fields" in res.text.lower()

    # 2. Attempt to submit final_compliance on upload
    res = await client.post(
        "/api/v1/scans/upload",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "area_id": str(TEST_AREA_ID),
            "final_compliance": "compliant",
        },
    )
    assert res.status_code == 422

    # 3. Attempt to submit effective_result on upload
    res = await client.post(
        "/api/v1/scans/upload",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "area_id": str(TEST_AREA_ID),
            "effective_result": "pass",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_manual_review_rejects_client_controlled_verdicts(test_env):
    client = test_env["client"]
    fake_id = str(uuid.uuid4())

    # Attempt to submit effective_result directly in manual review payload
    res = await client.post(
        f"/api/v1/scans/{fake_id}/result",
        json={
            "rule_code": "DEMO-MRP",
            "manual_review_result": "pass",
            "manual_review_reason": "Visible declaration",
            "effective_result": "pass",  # Client cannot control effective_result
        },
    )
    assert res.status_code == 422
    assert "extra_forbidden" in res.text or "extra fields" in res.text.lower()

    # Attempt to submit automated_result directly
    res = await client.post(
        f"/api/v1/scans/{fake_id}/result",
        json={
            "rule_code": "DEMO-MRP",
            "manual_review_result": "pass",
            "manual_review_reason": "Visible declaration",
            "automated_result": "pass",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_finalize_rejects_client_controlled_verdicts(test_env):
    client = test_env["client"]
    fake_id = str(uuid.uuid4())

    # 1. Attempt to submit final_compliance directly in finalize payload
    res = await client.post(
        f"/api/v1/scans/{fake_id}/finalize",
        json={
            "officer_notes": "All checks look fine",
            "final_compliance": "compliant",
        },
    )
    assert res.status_code == 422

    # 2. Attempt to submit manual_reviews in finalize payload (forbidden: manual reviews only allowed on /result)
    res_mr = await client.post(
        f"/api/v1/scans/{fake_id}/finalize",
        json={
            "officer_notes": "All checks look fine",
            "manual_reviews": [{"rule_code": "DEMO-MRP", "manual_review_result": "pass", "manual_review_reason": "test"}],
        },
    )
    assert res_mr.status_code == 422


# ------------------------------------------------------------------------------
# (b) Reject manual_review_result == not_applicable
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manual_review_not_applicable_rejected(test_env):
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    # Seed an inspection
    insp_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=sub_id,
            officer_id=TEST_OFFICER_ID,
            area_id=TEST_AREA_ID,
            image_storage_path="mock/path.jpg",
            status=InspectionStatus.pending_quality_check,
            is_finalized=False,
        )
        session.add(insp)
        await session.commit()

    # Attempt to review as not_applicable
    res = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-MRP",
            "manual_review_result": "not_applicable",
            "manual_review_reason": "Rule does not apply to this package",
        },
    )
    assert res.status_code in (400, 422)
    assert "not_applicable is not an allowed manual review assessment" in res.text


# ------------------------------------------------------------------------------
# (c) Reject empty or whitespace-only manual_review_reason
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_manual_review_empty_or_whitespace_reason_rejected(test_env):
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    # Seed an inspection
    insp_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=sub_id,
            officer_id=TEST_OFFICER_ID,
            area_id=TEST_AREA_ID,
            image_storage_path="mock/path.jpg",
            status=InspectionStatus.pending_quality_check,
            is_finalized=False,
        )
        session.add(insp)
        await session.commit()

    # Empty string
    res_empty = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-MRP",
            "manual_review_result": "pass",
            "manual_review_reason": "",
        },
    )
    assert res_empty.status_code in (400, 422)

    # Whitespace only
    res_ws = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-MRP",
            "manual_review_result": "pass",
            "manual_review_reason": "     \t \n   ",
        },
    )
    assert res_ws.status_code in (400, 422)
    assert "mandatory and cannot be empty or whitespace-only" in res_ws.text


# ------------------------------------------------------------------------------
# (d) effective_result is computed server-side and cannot be set by client
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_effective_result_computed_server_side(test_env):
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    rule_v_id = uuid.uuid4()

    # Seed an inspection with an automated failure
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=sub_id,
            officer_id=TEST_OFFICER_ID,
            area_id=TEST_AREA_ID,
            product_name="Atta 10kg",
            brand_name="Aashirvaad",
            image_storage_path="mock/path.jpg",
            status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.non_compliant,
            final_compliance=ComplianceStatus.non_compliant,
            is_finalized=False,
        )
        audit = AuditResult(
            id=uuid.uuid4(),
            inspection_id=insp_id,
            rule_version_id=rule_v_id,
            rule_code="DEMO-TEST-MRP-PRESENCE",
            rule_version=1,
            statutory_reference="Rule 6(1)(e)",
            automated_result=AuditResultType.fail,
            automated_reason="MRP not detected by OCR engine",
            severity=SeverityLevel.critical,
            effective_result=AuditResultType.fail,
        )
        session.add(insp)
        session.add(audit)
        await session.commit()

    # Officer submits valid manual review (overturning fail to pass)
    res = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-TEST-MRP-PRESENCE",
            "manual_review_result": "pass",
            "manual_review_reason": "Declaration clearly visible upon manual inspection; OCR missed faint embossed print.",
        },
    )
    assert res.status_code == 200
    data = res.json()

    # Prove server-side calculation:
    # 1. automated_result remained untouched as 'fail'
    assert data["automated_result"] == "fail"
    # 2. manual_review_result is 'pass'
    assert data["manual_review_result"] == "pass"
    # 3. effective_result was computed by the server as 'pass'
    assert data["effective_result"] == "pass"
    # 4. final_compliance was recomputed to 'compliant'
    assert data["final_compliance"] == "compliant"
    # 5. automated_compliance remained 'non_compliant'
    assert data["automated_compliance"] == "non_compliant"


# ------------------------------------------------------------------------------
# (e) Finalized inspection rejects any further mutation attempt
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finalized_inspection_rejects_further_mutations(test_env):
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    rule_v_id = uuid.uuid4()

    # Seed inspection & audit item
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=sub_id,
            officer_id=TEST_OFFICER_ID,
            area_id=TEST_AREA_ID,
            product_name="Mustard Oil 1L",
            brand_name="Fortune",
            image_storage_path="mock/path.jpg",
            status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.compliant,
            final_compliance=ComplianceStatus.compliant,
            is_finalized=False,
        )
        audit = AuditResult(
            id=uuid.uuid4(),
            inspection_id=insp_id,
            rule_version_id=rule_v_id,
            rule_code="DEMO-TEST-NET-QTY",
            rule_version=1,
            statutory_reference="Rule 6(1)(f)",
            automated_result=AuditResultType.pass_,
            automated_reason="Valid declaration",
            severity=SeverityLevel.major,
            effective_result=AuditResultType.pass_,
        )
        session.add(insp)
        session.add(audit)
        await session.commit()

    # 1. Finalize inspection via POST /api/v1/scans/{id}/finalize
    finalize_res = await client.post(
        f"/api/v1/scans/{insp_id}/finalize",
        json={"officer_notes": "Official inspection finalized and signed."},
    )
    assert finalize_res.status_code == 200
    fin_data = finalize_res.json()
    assert fin_data["is_finalized"] is True
    assert fin_data["report_hash"].startswith("sha256:")
    assert fin_data["signature_id"] is None
    assert fin_data["signature_hash"] is None

    # 2. Attempt mutation via /result -> Must raise 400 Bad Request
    res_mutate = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-TEST-NET-QTY",
            "manual_review_result": "fail",
            "manual_review_reason": "Post-finalization attempt to tamper verdict",
        },
    )
    assert res_mutate.status_code == 400
    assert "finalized and immutable" in res_mutate.json()["detail"].lower()

    # 3. Attempt re-finalization via /finalize -> Must raise 400 Bad Request
    res_refinalize = await client.post(
        f"/api/v1/scans/{insp_id}/finalize",
        json={"officer_notes": "Attempt to change finalized notes"},
    )
    assert res_refinalize.status_code == 400
    assert "finalized and immutable" in res_refinalize.json()["detail"].lower()


# ------------------------------------------------------------------------------
# (f) report_hash is populated and matches compute_report_hash() output
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_report_hash_populated_and_matches_compute_report_hash(test_env):
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    rule_v_id = uuid.uuid4()

    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=sub_id,
            officer_id=TEST_OFFICER_ID,
            area_id=TEST_AREA_ID,
            product_name="Basmati Rice 5kg",
            brand_name="Daawat",
            image_storage_path="mock/path.jpg",
            status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.compliant,
            final_compliance=ComplianceStatus.compliant,
            is_finalized=False,
        )
        audit = AuditResult(
            id=uuid.uuid4(),
            inspection_id=insp_id,
            rule_version_id=rule_v_id,
            rule_code="DEMO-TEST-MRP-PRESENCE",
            rule_version=1,
            statutory_reference="Rule 6(1)(e)",
            automated_result=AuditResultType.pass_,
            automated_reason="Declaration compliant",
            severity=SeverityLevel.critical,
            effective_result=AuditResultType.pass_,
        )
        session.add(insp)
        session.add(audit)
        await session.commit()

    # Finalize inspection
    res = await client.post(
        f"/api/v1/scans/{insp_id}/finalize",
        json={"officer_notes": "Passed verified metrology inspection."},
    )
    assert res.status_code == 200
    final_data = res.json()
    returned_hash = final_data["report_hash"]

    # Verify formatting: sha256:<64 hex chars>, len == 71
    assert returned_hash.startswith("sha256:")
    assert len(returned_hash) == 71

    # Verify persisted value in DB
    async with session_factory() as session:
        db_insp = await session.get(Inspection, insp_id)
        assert db_insp.report_hash == returned_hash
        assert db_insp.is_finalized is True

        # Re-compute expected hash from the canonical payload
        expected_payload = {
            "id": str(db_insp.id),
            "client_submission_id": str(db_insp.client_submission_id),
            "officer_id": str(db_insp.officer_id),
            "product_name": db_insp.product_name,
            "brand_name": db_insp.brand_name,
            "automated_compliance": db_insp.automated_compliance.value if db_insp.automated_compliance else None,
            "final_compliance": db_insp.final_compliance.value if db_insp.final_compliance else None,
            "audit_results": [
                {
                    "rule_code": audit.rule_code,
                    "statutory_reference": audit.statutory_reference,
                    "automated_result": audit.automated_result.value,
                    "manual_review_result": None,
                    "effective_result": audit.effective_result.value,
                }
            ],
        }
        computed = compute_report_hash(expected_payload)
        assert returned_hash == computed
