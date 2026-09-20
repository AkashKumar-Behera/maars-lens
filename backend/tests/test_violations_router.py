"""
MAARS Lens: Violations Router Integration Tests
===============================================
Validates Step 5 requirements for backend/app/routers/violations.py:
(a) Creating a violation for a non-finalized inspection returns 400.
(b) Creating a violation for a finalized but compliant/needs_review inspection returns 400.
(c) Creating a violation with empty failing_rule_codes or empty/whitespace summary returns 400/422.
(d) Creating a duplicate violation for the same inspection_id returns 409/400 (not a raw DB error).
(e) GET returns 404 when inspection exists but has no violation.
(f) GET response explicitly excludes officer_id, retailer_id, area_id, resolved_by (assert absence).
(g) Transitioning to resolved/dismissed without resolution_notes returns 400.
(h) Transitioning to resolved/dismissed WITH resolution_notes succeeds and sets resolved_at/resolved_by.
(i) Attempting any transition after status is already resolved or dismissed returns 400.
"""

import uuid
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import JSON

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.enums import UserRole, InspectionStatus, ComplianceStatus, ViolationStatus
from app.models.inspection import Inspection
from app.models.violation import Violation
from app.routers.violations import router as violations_router

TEST_OFFICER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
TEST_AREA_ID = uuid.UUID("b0000000-0000-0000-0000-000000000002")
TEST_RETAILER_ID = uuid.UUID("c0000000-0000-0000-0000-000000000003")


@pytest_asyncio.fixture
async def test_env():
    """Sets up an isolated SQLite in-memory engine and test client for violations router."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # SQLite does not support native ARRAY; compile ARRAY as JSON in SQLite tests
    async with engine.begin() as conn:
        # Override failing_rule_codes column type for SQLite compatibility
        Violation.__table__.c.failing_rule_codes.type = JSON()

        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[Inspection.__table__, Violation.__table__],
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

    app = FastAPI(title="MAARS Lens Violations Test API")
    app.include_router(violations_router, prefix="/api/v1/violations")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "session_factory": session_factory,
        }

    await engine.dispose()


async def _seed_inspection(
    session_factory,
    is_finalized: bool = True,
    final_compliance: ComplianceStatus = ComplianceStatus.non_compliant,
) -> Inspection:
    """Helper to create an inspection record with specified status and compliance."""
    async with session_factory() as session:
        insp = Inspection(
            id=uuid.uuid4(),
            client_submission_id=uuid.uuid4(),
            officer_id=TEST_OFFICER_ID,
            area_id=TEST_AREA_ID,
            retailer_id=TEST_RETAILER_ID,
            product_name="Biscuits 200g",
            brand_name="Crunchy",
            image_storage_path="inspections/test/image.jpg",
            is_finalized=is_finalized,
            finalized_at=datetime.now(timezone.utc) if is_finalized else None,
            status=InspectionStatus.completed if is_finalized else InspectionStatus.processing,
            automated_compliance=final_compliance if is_finalized else None,
            final_compliance=final_compliance if is_finalized else None,
        )
        session.add(insp)
        await session.commit()
        await session.refresh(insp)
        return insp


# ------------------------------------------------------------------------------
# Validation (a): Creating violation on non-finalized inspection returns 400
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_violation_unfinalized_inspection_rejected(test_env):
    """Validation (a): creating a violation for an unfinalized inspection returns 400."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=False)

    payload = {
        "failing_rule_codes": ["LM-MRP-01"],
        "summary": "MRP not declared on outer package.",
    }
    res = await client.post(f"/api/v1/violations/{insp.id}", json=payload)
    assert res.status_code == 400
    assert "must be finalized" in res.json()["detail"].lower()


# ------------------------------------------------------------------------------
# Validation (b): Creating violation on compliant/needs_review inspection returns 400
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_violation_compliant_or_needs_review_rejected(test_env):
    """Validation (b): creating a violation for compliant or needs_review inspection returns 400."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    # 1. Compliant inspection
    insp_comp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.compliant)
    payload = {"failing_rule_codes": ["LM-MRP-01"], "summary": "MRP absent"}
    res1 = await client.post(f"/api/v1/violations/{insp_comp.id}", json=payload)
    assert res1.status_code == 400
    assert "must be 'non_compliant'" in res1.json()["detail"]

    # 2. Needs_review inspection
    insp_rev = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.needs_review)
    res2 = await client.post(f"/api/v1/violations/{insp_rev.id}", json=payload)
    assert res2.status_code == 400
    assert "must be 'non_compliant'" in res2.json()["detail"]


# ------------------------------------------------------------------------------
# Validation (c): Empty failing_rule_codes or summary returns 400/422
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_violation_empty_fields_rejected(test_env):
    """Validation (c): empty failing_rule_codes or whitespace summary rejected with 400/422."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.non_compliant)

    # Empty list
    res1 = await client.post(f"/api/v1/violations/{insp.id}", json={"failing_rule_codes": [], "summary": "Valid summary"})
    assert res1.status_code in (400, 422)

    # Empty/whitespace-only summary
    res2 = await client.post(f"/api/v1/violations/{insp.id}", json={"failing_rule_codes": ["LM-MRP-01"], "summary": "   "})
    assert res2.status_code in (400, 422)

    # Whitespace-only rule codes
    res3 = await client.post(f"/api/v1/violations/{insp.id}", json={"failing_rule_codes": ["   "], "summary": "Valid summary"})
    assert res3.status_code in (400, 422)


# ------------------------------------------------------------------------------
# Validation (d): Duplicate violation for same inspection returns 409/400
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_violation_duplicate_returns_409(test_env):
    """Validation (d): creating a duplicate violation for the same inspection_id returns 409 Conflict."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.non_compliant)
    payload = {"failing_rule_codes": ["LM-MRP-01"], "summary": "Missing MRP"}

    # First creation succeeds (201)
    res1 = await client.post(f"/api/v1/violations/{insp.id}", json=payload)
    assert res1.status_code == 201

    # Second creation rejected with clean 409
    res2 = await client.post(f"/api/v1/violations/{insp.id}", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


# ------------------------------------------------------------------------------
# Validation (e): GET returns 404 when inspection has no violation
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_violation_returns_404_when_absent(test_env):
    """Validation (e): GET returns 404 when inspection exists but has no violation."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.compliant)

    res = await client.get(f"/api/v1/violations/{insp.id}")
    assert res.status_code == 404
    assert "no violation record found" in res.json()["detail"].lower()


# ------------------------------------------------------------------------------
# Validation (f): GET response explicitly excludes private/internal fields
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_violation_response_excludes_internal_fields(test_env):
    """
    Validation (f): GET response explicitly excludes officer_id, retailer_id,
    area_id, resolved_by. Asserts absence of internal attributes.
    """
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.non_compliant)
    create_payload = {"failing_rule_codes": ["LM-MRP-01", "LM-DATE-02"], "summary": "Multiple statutory non-compliances"}
    await client.post(f"/api/v1/violations/{insp.id}", json=create_payload)

    res = await client.get(f"/api/v1/violations/{insp.id}")
    assert res.status_code == 200
    data = res.json()

    # Whitelisted fields present
    assert data["inspection_id"] == str(insp.id)
    assert data["status"] == "open"
    assert data["failing_rule_codes"] == ["LM-MRP-01", "LM-DATE-02"]
    assert data["summary"] == "Multiple statutory non-compliances"
    assert "created_at" in data

    # Privacy / Whitelist absence assertions
    assert "officer_id" not in data, "Privacy violation: officer_id leaked in response"
    assert "retailer_id" not in data, "Privacy violation: retailer_id leaked in response"
    assert "area_id" not in data, "Privacy violation: area_id leaked in response"
    assert "resolved_by" not in data, "Privacy violation: resolved_by leaked in response"

    # Verify absence in serialized text
    json_text = res.text
    assert str(TEST_OFFICER_ID) not in json_text
    assert str(TEST_AREA_ID) not in json_text
    assert str(TEST_RETAILER_ID) not in json_text


# ------------------------------------------------------------------------------
# Validation (g): Transitioning to resolved/dismissed without notes returns 400
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transition_to_resolved_without_notes_returns_400(test_env):
    """Validation (g): transitioning to resolved/dismissed without resolution_notes returns 400."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.non_compliant)
    await client.post(f"/api/v1/violations/{insp.id}", json={"failing_rule_codes": ["LM-MRP-01"], "summary": "MRP absent"})

    # 1. Attempt resolved without notes
    res1 = await client.post(f"/api/v1/violations/{insp.id}/status", json={"status": "resolved"})
    assert res1.status_code == 400
    assert "resolution_notes is mandatory" in res1.json()["detail"]

    # 2. Attempt dismissed with whitespace notes
    res2 = await client.post(f"/api/v1/violations/{insp.id}/status", json={"status": "dismissed", "resolution_notes": "   "})
    assert res2.status_code == 400
    assert "resolution_notes is mandatory" in res2.json()["detail"]


# ------------------------------------------------------------------------------
# Validation (h): Transitioning to resolved/dismissed WITH notes succeeds
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transition_to_resolved_with_notes_succeeds(test_env):
    """Validation (h): transitioning to resolved WITH resolution_notes sets status and resolved_at."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.non_compliant)
    await client.post(f"/api/v1/violations/{insp.id}", json={"failing_rule_codes": ["LM-MRP-01"], "summary": "MRP absent"})

    transition_payload = {
        "status": "resolved",
        "resolution_notes": "Retailer paid compounding fee of Rs. 5000 and rectified package labeling.",
    }
    res = await client.post(f"/api/v1/violations/{insp.id}/status", json=transition_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "resolved"
    assert data["resolution_notes"] == "Retailer paid compounding fee of Rs. 5000 and rectified package labeling."
    assert data["resolved_at"] is not None

    # In DB, verify resolved_by was set
    async with session_factory() as session:
        from sqlalchemy import select
        stmt = select(Violation).where(Violation.inspection_id == insp.id)
        db_v = (await session.execute(stmt)).scalar_one()
        assert db_v.resolved_by == TEST_OFFICER_ID
        assert db_v.resolved_at is not None


# ------------------------------------------------------------------------------
# Validation (i): Attempting transition after status is terminal returns 400
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transition_after_terminal_state_rejected(test_env):
    """Validation (i): attempting any transition after status is already resolved or dismissed returns 400."""
    client = test_env["client"]
    session_factory = test_env["session_factory"]

    insp = await _seed_inspection(session_factory, is_finalized=True, final_compliance=ComplianceStatus.non_compliant)
    await client.post(f"/api/v1/violations/{insp.id}", json={"failing_rule_codes": ["LM-MRP-01"], "summary": "MRP absent"})

    # Transition to resolved
    await client.post(
        f"/api/v1/violations/{insp.id}/status",
        json={"status": "resolved", "resolution_notes": "Settled by compounding."},
    )

    # Attempt transition from resolved -> under_review (must be rejected)
    res_reopen = await client.post(
        f"/api/v1/violations/{insp.id}/status",
        json={"status": "under_review", "resolution_notes": "Reopening attempt"},
    )
    assert res_reopen.status_code == 400
    assert "terminal status" in res_reopen.json()["detail"].lower()
    assert "reopening is not permitted" in res_reopen.json()["detail"].lower()
