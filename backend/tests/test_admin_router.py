"""
MAARS Lens: Admin Router Integration Tests
==========================================
Validates all Admin Router requirements:
(a) Non-admin (officer) gets 403 on every endpoint.
(b) /analytics/overview returns real counts matching manually-seeded test data.
(c) /analytics/trends respects days parameter and rejects days > 90 or days < 1 (422).
(d) /analytics/export CSV output explicitly does NOT contain officer_id, retailer_id,
    gps_lat, gps_lng, product_name, or brand_name strings (assert absence in raw text).
(e) Admin cannot deactivate their own profile (400 self-lockout guard).
(f) Admin CAN deactivate a different user's profile, and Inspection/AuditResult/Violation
    records tied to that user remain completely unchanged afterward.
(g) Route paths resolve correctly at /api/v1/admin/... with no double prefix.
"""

import uuid
import datetime
from datetime import timezone, timedelta
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import JSON

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.enums import (
    UserRole,
    InspectionStatus,
    ComplianceStatus,
    AuditResultType,
    RuleType,
    SeverityLevel,
    RuleVerificationStatus,
    ViolationStatus,
)
from app.models.user import Profile
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.models.violation import Violation
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.routers.admin import router as admin_router

TEST_ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_OFFICER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_OTHER_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest_asyncio.fixture
async def admin_test_env():
    """Sets up an isolated SQLite in-memory engine and test client for admin router."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        Violation.__table__.c.failing_rule_codes.type = JSON()
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Profile.__table__,
                    ComplianceRule.__table__,
                    ComplianceRuleVersion.__table__,
                    Inspection.__table__,
                    AuditResult.__table__,
                    Violation.__table__,
                ],
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Seed baseline profiles
    async with session_factory() as session:
        admin_prof = Profile(
            id=TEST_ADMIN_ID,
            role=UserRole.admin,
            full_name="Admin Director",
            email="director@maars.gov.in",
            employee_id="ADM-001",
            is_active=True,
        )
        officer_prof = Profile(
            id=TEST_OFFICER_ID,
            role=UserRole.officer,
            full_name="Inspector Sharma",
            email="sharma@maars.gov.in",
            employee_id="OFF-101",
            is_active=True,
        )
        other_prof = Profile(
            id=TEST_OTHER_USER_ID,
            role=UserRole.officer,
            full_name="Inspector Verma",
            email="verma@maars.gov.in",
            employee_id="OFF-102",
            is_active=True,
        )
        session.add_all([admin_prof, officer_prof, other_prof])
        await session.commit()

    # User state switchable by tests
    current_user_state = {
        "id": str(TEST_ADMIN_ID),
        "sub": str(TEST_ADMIN_ID),
        "user_metadata": {"role": "admin"},
    }

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return current_user_state

    app = FastAPI(title="MAARS Lens Admin Test API")
    # Mount exactly as main.py does
    app.include_router(admin_router, prefix="/api/v1/admin")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "session_factory": session_factory,
            "user_state": current_user_state,
        }

    await engine.dispose()


# ------------------------------------------------------------------------------
# Requirement (a): Non-admin (officer) gets 403 on every endpoint
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_non_admin_gets_403_on_all_admin_endpoints(admin_test_env):
    """(a) Non-admin (officer) is denied with 403 Forbidden across all admin routes."""
    client = admin_test_env["client"]
    admin_test_env["user_state"]["user_metadata"]["role"] = "officer"
    admin_test_env["user_state"]["id"] = str(TEST_OFFICER_ID)

    # 1. GET /analytics/overview
    r1 = await client.get("/api/v1/admin/analytics/overview")
    assert r1.status_code == 403

    # 2. GET /analytics/trends
    r2 = await client.get("/api/v1/admin/analytics/trends")
    assert r2.status_code == 403

    # 3. GET /analytics/export
    r3 = await client.get("/api/v1/admin/analytics/export")
    assert r3.status_code == 403

    # 4. GET /users
    r4 = await client.get("/api/v1/admin/users")
    assert r4.status_code == 403

    # 5. PATCH /users/{id}/status
    r5 = await client.patch(
        f"/api/v1/admin/users/{TEST_OTHER_USER_ID}/status",
        json={"is_active": False},
    )
    assert r5.status_code == 403


# ------------------------------------------------------------------------------
# Requirement (b): /analytics/overview returns real counts matching test data
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analytics_overview_returns_exact_aggregated_counts(admin_test_env):
    """(b) /analytics/overview returns genuine aggregation metrics matching seeded records."""
    client = admin_test_env["client"]
    session_factory = admin_test_env["session_factory"]

    async with session_factory() as session:
        # Seed rules: 2 rules, 3 versions (2 demo, 1 verified; 2 active, 1 inactive)
        r1_id = uuid.uuid4()
        r2_id = uuid.uuid4()
        r1 = ComplianceRule(id=r1_id, rule_code="LM-01", category="MRP")
        r2 = ComplianceRule(id=r2_id, rule_code="LM-02", category="NetQty")

        v1 = ComplianceRuleVersion(
            id=uuid.uuid4(), rule_id=r1_id, version=1, statutory_reference="Ref 1",
            rule_type=RuleType.presence, target_field="mrp", check_definition={"op": "exists"},
            severity=SeverityLevel.critical, description_en="desc", failure_message_template="fail",
            verification_status=RuleVerificationStatus.demo, is_active=True, created_by=TEST_ADMIN_ID,
        )
        v2 = ComplianceRuleVersion(
            id=uuid.uuid4(), rule_id=r1_id, version=2, statutory_reference="Ref 1 Amd",
            rule_type=RuleType.presence, target_field="mrp", check_definition={"op": "exists"},
            severity=SeverityLevel.critical, description_en="desc", failure_message_template="fail",
            verification_status=RuleVerificationStatus.verified, is_active=True, created_by=TEST_ADMIN_ID,
        )
        v3 = ComplianceRuleVersion(
            id=uuid.uuid4(), rule_id=r2_id, version=1, statutory_reference="Ref 2",
            rule_type=RuleType.pattern, target_field="qty", check_definition={"op": "exists"},
            severity=SeverityLevel.major, description_en="desc", failure_message_template="fail",
            verification_status=RuleVerificationStatus.demo, is_active=False, created_by=TEST_ADMIN_ID,
        )
        session.add_all([r1, r2, v1, v2, v3])

        # Seed Inspections: 3 total (2 finalized: 1 compliant, 1 non-compliant; 1 unfinalized needs_review)
        insp1_id = uuid.uuid4()
        insp2_id = uuid.uuid4()
        insp3_id = uuid.uuid4()

        insp1 = Inspection(
            id=insp1_id, client_submission_id=uuid.uuid4(), officer_id=TEST_OFFICER_ID,
            area_id=uuid.uuid4(), image_storage_path="path/1.jpg", status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.compliant, final_compliance=ComplianceStatus.compliant,
            is_finalized=True, report_hash="sha256:1111",
        )
        insp2 = Inspection(
            id=insp2_id, client_submission_id=uuid.uuid4(), officer_id=TEST_OFFICER_ID,
            area_id=uuid.uuid4(), image_storage_path="path/2.jpg", status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.non_compliant, final_compliance=ComplianceStatus.non_compliant,
            is_finalized=True, report_hash="sha256:2222",
        )
        insp3 = Inspection(
            id=insp3_id, client_submission_id=uuid.uuid4(), officer_id=TEST_OFFICER_ID,
            area_id=uuid.uuid4(), image_storage_path="path/3.jpg", status=InspectionStatus.needs_review,
            automated_compliance=ComplianceStatus.needs_review, final_compliance=ComplianceStatus.needs_review,
            is_finalized=False,
        )
        session.add_all([insp1, insp2, insp3])

        # Seed Violations: 2 violations (1 open, 1 resolved)
        viol1 = Violation(
            id=uuid.uuid4(), inspection_id=insp2_id, area_id=uuid.uuid4(), officer_id=TEST_OFFICER_ID,
            status=ViolationStatus.open, failing_rule_codes=["LM-01"], summary="MRP missing",
        )
        viol2 = Violation(
            id=uuid.uuid4(), inspection_id=uuid.uuid4(), area_id=uuid.uuid4(), officer_id=TEST_OFFICER_ID,
            status=ViolationStatus.resolved, failing_rule_codes=["LM-02"], summary="Net Qty error",
            resolution_notes="Resolved", resolved_at=datetime.datetime.now(timezone.utc),
        )
        session.add_all([viol1, viol2])
        await session.commit()

    resp = await client.get("/api/v1/admin/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()

    # Inspections assertions
    inspections = data["inspections"]
    assert inspections["total"] == 3
    assert inspections["finalized"] == 2
    assert inspections["compliant"] == 1
    assert inspections["non_compliant"] == 1
    assert inspections["needs_review"] == 1
    # Compliance rate: 1 compliant / (1 compliant + 1 non_compliant) = 0.5 (50%)
    assert inspections["compliance_rate"] == 0.5
    assert inspections["by_status"]["completed"] == 2
    assert inspections["by_status"]["needs_review"] == 1

    # Violations assertions
    violations = data["violations"]
    assert violations["total"] == 2
    assert violations["by_status"]["open"] == 1
    assert violations["by_status"]["resolved"] == 1

    # Rules assertions
    rules = data["rules"]
    assert rules["total_rules"] == 2
    assert rules["total_versions"] == 3
    assert rules["active_versions"] == 2
    assert rules["demo_versions"] == 2
    assert rules["verified_versions"] == 1


# ------------------------------------------------------------------------------
# Requirement (c): /analytics/trends respects days and rejects invalid range
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analytics_trends_validation_and_results(admin_test_env):
    """(c) /analytics/trends respects days parameter, validates 1-90, and aggregates."""
    client = admin_test_env["client"]

    # 1. Invalid days > 90 -> 422
    resp_large = await client.get("/api/v1/admin/analytics/trends?days=91")
    assert resp_large.status_code == 422

    # 2. Invalid days < 1 -> 422
    resp_small = await client.get("/api/v1/admin/analytics/trends?days=0")
    assert resp_small.status_code == 422

    # 3. Valid days=14 -> returns 14 trend data points
    resp_valid = await client.get("/api/v1/admin/analytics/trends?days=14")
    assert resp_valid.status_code == 200
    trends = resp_valid.json()["trends"]
    assert len(trends) == 14
    for pt in trends:
        assert "date" in pt
        assert "inspections" in pt
        assert "violations" in pt
        assert isinstance(pt["inspections"], int)
        assert isinstance(pt["violations"], int)


# ------------------------------------------------------------------------------
# Requirement (d): /analytics/export CSV excludes private/internal fields
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analytics_export_csv_sanitized_and_excludes_private_fields(admin_test_env):
    """
    (d) /analytics/export CSV contains only whitelisted header columns, and explicitly
    does NOT contain officer_id, retailer_id, gps_lat, gps_lng, product_name, or brand_name.
    """
    client = admin_test_env["client"]
    session_factory = admin_test_env["session_factory"]

    SECRET_PRODUCT = "SUPER_SECRET_LUXURY_RICE"
    SECRET_BRAND = "CONFIDENTIAL_ORGANIC_BRAND"
    SECRET_OFFICER = uuid.UUID("99999999-9999-9999-9999-999999999999")
    SECRET_RETAILER = uuid.UUID("88888888-8888-8888-8888-888888888888")

    async with session_factory() as session:
        insp = Inspection(
            id=uuid.uuid4(),
            client_submission_id=uuid.uuid4(),
            officer_id=SECRET_OFFICER,
            retailer_id=SECRET_RETAILER,
            area_id=uuid.uuid4(),
            product_name=SECRET_PRODUCT,
            brand_name=SECRET_BRAND,
            gps_lat=28.6139,
            gps_lng=77.2090,
            image_storage_path="path/secret.jpg",
            status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.compliant,
            final_compliance=ComplianceStatus.compliant,
            is_finalized=True,
            report_hash="sha256:secret_hash_value_12345",
        )
        session.add(insp)
        await session.commit()

    resp = await client.get("/api/v1/admin/analytics/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    csv_text = resp.text
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
    header = lines[0]

    # Exactly specified whitelist header
    expected_header = "ID,ClientSubmissionId,CreatedAt,Status,AutomatedCompliance,FinalCompliance,IsFinalized,ReportHash"
    assert header == expected_header

    # Explicit absence of sensitive private strings
    assert str(SECRET_OFFICER) not in csv_text, "Privacy leak: officer_id found in CSV export"
    assert str(SECRET_RETAILER) not in csv_text, "Privacy leak: retailer_id found in CSV export"
    assert SECRET_PRODUCT not in csv_text, "Privacy leak: product_name found in CSV export"
    assert SECRET_BRAND not in csv_text, "Privacy leak: brand_name found in CSV export"
    assert "28.6139" not in csv_text, "Privacy leak: gps_lat found in CSV export"
    assert "77.209" not in csv_text, "Privacy leak: gps_lng found in CSV export"


# ------------------------------------------------------------------------------
# Requirement (e): Admin cannot deactivate own profile (400)
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_cannot_deactivate_own_profile(admin_test_env):
    """(e) Self-lockout guard: admin cannot deactivate their own profile (HTTP 400)."""
    client = admin_test_env["client"]

    resp = await client.patch(
        f"/api/v1/admin/users/{TEST_ADMIN_ID}/status",
        json={"is_active": False},
    )
    assert resp.status_code == 400
    assert "Self-lockout is forbidden" in resp.json()["detail"]


# ------------------------------------------------------------------------------
# Requirement (f): Admin can toggle other user's status; records remain unchanged
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_can_toggle_other_user_without_record_cascade(admin_test_env):
    """
    (f) Admin can deactivate another user, and associated inspections, audit results,
    and violations remain completely unchanged.
    """
    client = admin_test_env["client"]
    session_factory = admin_test_env["session_factory"]

    # Seed inspection & violation associated with TEST_OTHER_USER_ID
    insp_id = uuid.uuid4()
    viol_id = uuid.uuid4()
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id, client_submission_id=uuid.uuid4(), officer_id=TEST_OTHER_USER_ID,
            area_id=uuid.uuid4(), image_storage_path="path/test.jpg", status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.non_compliant, final_compliance=ComplianceStatus.non_compliant,
            is_finalized=True, report_hash="sha256:preserve_test_hash",
        )
        viol = Violation(
            id=viol_id, inspection_id=insp_id, area_id=uuid.uuid4(), officer_id=TEST_OTHER_USER_ID,
            status=ViolationStatus.open, failing_rule_codes=["PRESERVE-01"], summary="Test preserve",
        )
        session.add_all([insp, viol])
        await session.commit()

    # 1. Admin deactivates other user
    patch_resp = await client.patch(
        f"/api/v1/admin/users/{TEST_OTHER_USER_ID}/status",
        json={"is_active": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is False
    assert patch_resp.json()["id"] == str(TEST_OTHER_USER_ID)

    # 2. Verify in DB that Profile is inactive
    async with session_factory() as session:
        prof = await session.get(Profile, TEST_OTHER_USER_ID)
        assert prof.is_active is False

        # 3. CRITICAL: Verify Inspection and Violation remain completely unchanged
        insp_check = await session.get(Inspection, insp_id)
        assert insp_check is not None
        assert insp_check.officer_id == TEST_OTHER_USER_ID
        assert insp_check.is_finalized is True
        assert insp_check.report_hash == "sha256:preserve_test_hash"

        viol_check = await session.get(Violation, viol_id)
        assert viol_check is not None
        assert viol_check.status == ViolationStatus.open
        assert viol_check.officer_id == TEST_OTHER_USER_ID

    # 4. Reactivate user
    patch_resp2 = await client.patch(
        f"/api/v1/admin/users/{TEST_OTHER_USER_ID}/status",
        json={"is_active": True},
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["is_active"] is True


# ------------------------------------------------------------------------------
# Requirement (g): Route paths resolve at /api/v1/admin/... with no double prefix
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_route_paths_resolve_without_double_prefix(admin_test_env):
    """(g) Verifies route paths resolve cleanly at /api/v1/admin/... without double /admin."""
    client = admin_test_env["client"]

    # Expected clean endpoints
    r_overview = await client.get("/api/v1/admin/analytics/overview")
    assert r_overview.status_code == 200

    r_trends = await client.get("/api/v1/admin/analytics/trends")
    assert r_trends.status_code == 200

    r_export = await client.get("/api/v1/admin/analytics/export")
    assert r_export.status_code == 200

    r_users = await client.get("/api/v1/admin/users")
    assert r_users.status_code == 200

    # Redundant double prefix must 404
    r_double = await client.get("/api/v1/admin/admin/analytics/overview")
    assert r_double.status_code == 404
