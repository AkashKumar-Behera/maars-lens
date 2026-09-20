import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.models.product import Product
from app.models.enums import UserRole, InspectionStatus, ComplianceStatus, AuditResultType, SeverityLevel
from app.routers.scans import router as scans_router
from app.routers.auth import router as auth_router

OFFICER_A_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
OFFICER_B_ID = uuid.UUID("b0000000-0000-0000-0000-000000000002")
CURRENT_USER_STATE = {"id": str(OFFICER_A_ID), "role": "officer"}


@pytest_asyncio.fixture
async def rbac_test_env():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: sync_conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
        )
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[Product.__table__, Inspection.__table__, AuditResult.__table__],
                checkfirst=True,
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return {
            "id": CURRENT_USER_STATE["id"],
            "sub": CURRENT_USER_STATE["id"],
            "user_metadata": {"role": CURRENT_USER_STATE["role"]},
        }

    app = FastAPI()
    app.include_router(scans_router, prefix="/api/v1/scans")
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "session_factory": session_factory,
        }

    await engine.dispose()


@pytest.mark.asyncio
async def test_cross_officer_isolation(rbac_test_env):
    """Ensures Officer B cannot mutate or finalize an unfinalized inspection owned by Officer A."""
    client = rbac_test_env["client"]
    session_factory = rbac_test_env["session_factory"]

    insp_id = uuid.uuid4()
    audit_id = uuid.uuid4()
    version_id = uuid.uuid4()

    # Seed inspection owned by Officer A
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=uuid.uuid4(),
            officer_id=OFFICER_A_ID,
            product_name="Officer A Item",
            status=InspectionStatus.needs_review,
            is_finalized=False,
        )
        audit = AuditResult(
            id=audit_id,
            inspection_id=insp_id,
            rule_version_id=version_id,
            rule_code="DEMO-RULE",
            rule_version=1,
            statutory_reference="Rule 6",
            automated_result=AuditResultType.fail,
            automated_reason="Missing field",
            severity=SeverityLevel.critical,
            effective_result=AuditResultType.fail,
        )
        session.add_all([insp, audit])
        await session.commit()

    # Switch current user context to Officer B
    CURRENT_USER_STATE["id"] = str(OFFICER_B_ID)
    CURRENT_USER_STATE["role"] = "officer"

    # Officer B attempts to submit manual review for Officer A's inspection -> 403
    res_review = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-RULE",
            "manual_review_result": "pass",
            "manual_review_reason": "Officer B attempting unauthorized change",
        },
    )
    assert res_review.status_code == 403
    assert "Cross-officer isolation" in res_review.text

    # Officer B attempts to finalize Officer A's inspection -> 403
    res_fin = await client.post(
        f"/api/v1/scans/{insp_id}/finalize",
        json={},
    )
    assert res_fin.status_code == 403
    assert "Cross-officer isolation" in res_fin.text

    # Restore current user to Officer A -> Succeeds
    CURRENT_USER_STATE["id"] = str(OFFICER_A_ID)
    res_ok = await client.post(
        f"/api/v1/scans/{insp_id}/result",
        json={
            "rule_code": "DEMO-RULE",
            "manual_review_result": "pass",
            "manual_review_reason": "Officer A verified on physical package",
        },
    )
    assert res_ok.status_code == 200


@pytest.mark.asyncio
async def test_non_officer_cannot_scan_or_finalize(rbac_test_env):
    """Ensures customer/retailer roles cannot perform officer operations."""
    client = rbac_test_env["client"]

    # Customer user
    CURRENT_USER_STATE["id"] = str(uuid.uuid4())
    CURRENT_USER_STATE["role"] = "customer"

    res = await client.post(
        "/api/v1/scans/listing",
        json={"title": "Test Listing"},
    )
    assert res.status_code == 403
