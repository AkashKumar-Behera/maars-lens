"""
MAARS Lens: Rules Router Integration Tests
==========================================
Validates Rules Router requirements:
(1) Non-admin (officer, customer) cannot create a rule or version (403).
(2) Admin can create a new rule with version 1 (201).
(3) Duplicate rule_code returns 409 Conflict.
(4) Admin can create a new version v2 for existing rule (201).
(5) Nonexistent rule or version retrieval returns 404.
(6) Rule version immutability (no PUT/update endpoint exists to mutate existing versions).
(7) Admin can toggle is_active on a rule version (records audit log).
(8) Demo verification status is preserved and defaults to 'demo'.
(9) Listing rules returns active version and all historical versions.
(10) Admin can view rule audit log history.
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.enums import UserRole, RuleType, SeverityLevel, RuleVerificationStatus, RuleAuditAction
from app.models.user import Profile
from app.models.rule import ComplianceRule, ComplianceRuleVersion, RuleAuditLog
from app.routers.rules import router as rules_router

TEST_ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_OFFICER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest_asyncio.fixture
async def test_env():
    """Sets up an isolated SQLite in-memory engine and test client for rules router."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    Profile.__table__,
                    ComplianceRule.__table__,
                    ComplianceRuleVersion.__table__,
                    RuleAuditLog.__table__,
                ],
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Seed an admin profile and officer profile in the DB
    async with session_factory() as session:
        admin_prof = Profile(
            id=TEST_ADMIN_ID,
            role=UserRole.admin,
            full_name="System Admin",
            email="admin@maars.gov.in",
            is_active=True,
        )
        officer_prof = Profile(
            id=TEST_OFFICER_ID,
            role=UserRole.officer,
            full_name="Inspecting Officer",
            email="officer@maars.gov.in",
            is_active=True,
        )
        session.add(admin_prof)
        session.add(officer_prof)
        await session.commit()

    # Shared role state that can be toggled by tests
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

    app = FastAPI(title="MAARS Lens Rules Test API")
    app.include_router(rules_router, prefix="/api/v1/rules")

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


@pytest.mark.asyncio
async def test_non_admin_cannot_create_rule(test_env):
    """(1) Non-admin (officer) cannot create a rule -> 403 Forbidden."""
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "officer"
    test_env["user_state"]["id"] = str(TEST_OFFICER_ID)

    payload = {
        "rule_code": "TEST-RULE-001",
        "category": "Test Category",
        "statutory_reference": "Section 18(1)",
        "rule_type": "presence",
        "target_field": "mrp",
        "check_definition": {"operator": "exists"},
        "severity": "critical",
        "description_en": "MRP check",
        "failure_message_template": "MRP is missing",
    }

    resp = await client.post("/api/v1/rules/", json=payload)
    assert resp.status_code == 403
    assert "Not enough permissions" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_admin_can_create_rule_version_1(test_env):
    """(2) Admin can create a new rule with version 1 (201) and demo status default."""
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "admin"
    test_env["user_state"]["id"] = str(TEST_ADMIN_ID)

    payload = {
        "rule_code": "DEMO-MRP-CHECK",
        "category": "MRP",
        "statutory_reference": "[DEMO FIXTURE] Rule 6(1)(e)",
        "rule_type": "presence",
        "target_field": "mrp",
        "check_definition": {"operator": "exists"},
        "severity": "critical",
        "description_en": "Package must have an extracted MRP value.",
        "failure_message_template": "MRP declaration is missing.",
        "requires_visual_measurement": False,
    }

    resp = await client.post("/api/v1/rules/", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["rule_code"] == "DEMO-MRP-CHECK"
    assert data["category"] == "MRP"
    assert "id" in data

    active_v = data["active_version"]
    assert active_v is not None
    assert active_v["version"] == 1
    assert active_v["statutory_reference"] == "[DEMO FIXTURE] Rule 6(1)(e)"
    assert active_v["verification_status"] == "demo"
    assert active_v["is_active"] is True
    assert active_v["created_by"] == str(TEST_ADMIN_ID)

    # Check that audit log was created
    audit_resp = await client.get(f"/api/v1/rules/{data['id']}/audit-logs")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) == 1
    assert logs[0]["action"] == "created"


@pytest.mark.asyncio
async def test_duplicate_rule_code_returns_409(test_env):
    """(3) Duplicate rule_code returns 409 Conflict."""
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "admin"

    payload = {
        "rule_code": "DEMO-UNIQUE-CODE",
        "category": "MRP",
        "statutory_reference": "Ref A",
        "rule_type": "presence",
        "target_field": "mrp",
        "check_definition": {"operator": "exists"},
        "severity": "critical",
        "description_en": "Test desc",
        "failure_message_template": "Failed",
    }

    resp1 = await client.post("/api/v1/rules/", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/rules/", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_admin_can_publish_new_version(test_env):
    """(4) Admin can create a new version v2 for existing rule (201)."""
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "admin"

    # 1. Create rule v1
    v1_payload = {
        "rule_code": "DEMO-EXPIRY-DATE",
        "category": "Date Declarations",
        "statutory_reference": "Initial Clause",
        "rule_type": "presence",
        "target_field": "expiry_date",
        "check_definition": {"operator": "exists"},
        "severity": "major",
        "description_en": "Initial expiry date check",
        "failure_message_template": "Expiry date missing",
    }
    create_resp = await client.post("/api/v1/rules/", json=v1_payload)
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]

    # 2. Add version 2
    v2_payload = {
        "statutory_reference": "Amended Clause 2026",
        "rule_type": "presence",
        "target_field": "expiry_date",
        "check_definition": {"operator": "regex", "value": r"^\d{2}/\d{4}$"},
        "severity": "critical",
        "description_en": "Updated expiry date pattern check",
        "failure_message_template": "Expiry date missing or malformed",
        "requires_visual_measurement": False,
        "is_active": True,
    }
    v2_resp = await client.post(f"/api/v1/rules/{rule_id}/versions", json=v2_payload)
    assert v2_resp.status_code == 201
    v2_data = v2_resp.json()
    assert v2_data["version"] == 2
    assert v2_data["statutory_reference"] == "Amended Clause 2026"
    assert v2_data["severity"] == "critical"

    # 3. Retrieve rule details: should now list both versions, with v2 being the latest active version
    get_resp = await client.get(f"/api/v1/rules/{rule_id}")
    assert get_resp.status_code == 200
    rule_data = get_resp.json()
    assert len(rule_data["versions"]) == 2
    assert rule_data["active_version"]["version"] == 2


@pytest.mark.asyncio
async def test_nonexistent_rule_and_version_return_404(test_env):
    """(5) Nonexistent rule/version retrieval returns 404."""
    client = test_env["client"]
    random_id = uuid.uuid4()

    resp = await client.get(f"/api/v1/rules/{random_id}")
    assert resp.status_code == 404

    resp_v = await client.get(f"/api/v1/rules/versions/{random_id}")
    assert resp_v.status_code == 404


@pytest.mark.asyncio
async def test_rule_version_immutability_no_put_endpoint(test_env):
    """(6) Rule version immutability: no PUT/PATCH endpoint to mutate existing version definitions."""
    client = test_env["client"]
    random_id = uuid.uuid4()

    # Attempting PUT on a version or rule directly
    resp_put_rule = await client.put(f"/api/v1/rules/{random_id}", json={"category": "hacked"})
    assert resp_put_rule.status_code in (404, 405)

    resp_put_version = await client.put(f"/api/v1/rules/versions/{random_id}", json={"statutory_reference": "hacked"})
    assert resp_put_version.status_code in (404, 405)


@pytest.mark.asyncio
async def test_admin_can_toggle_is_active_on_rule_version(test_env):
    """(7) Admin can toggle is_active on a rule version and it is logged."""
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "admin"

    # Create rule v1
    create_resp = await client.post("/api/v1/rules/", json={
        "rule_code": "DEMO-TOGGLE-TEST",
        "category": "Test",
        "statutory_reference": "Ref T",
        "rule_type": "presence",
        "target_field": "test_field",
        "check_definition": {"operator": "exists"},
        "severity": "minor",
        "description_en": "Toggle test",
        "failure_message_template": "Missing",
    })
    v1_id = create_resp.json()["active_version"]["id"]
    rule_id = create_resp.json()["id"]

    # Deactivate version 1
    patch_resp = await client.patch(
        f"/api/v1/rules/versions/{v1_id}/activate",
        json={"is_active": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] is False

    # Check audit log records deactivation
    logs_resp = await client.get(f"/api/v1/rules/{rule_id}/audit-logs")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    actions = [l["action"] for l in logs]
    assert "deactivated" in actions

    # Reactivate version 1
    patch_resp2 = await client.patch(
        f"/api/v1/rules/versions/{v1_id}/activate",
        json={"is_active": True},
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["is_active"] is True

    logs_resp2 = await client.get(f"/api/v1/rules/{rule_id}/audit-logs")
    actions2 = [l["action"] for l in logs_resp2.json()]
    assert "activated" in actions2


@pytest.mark.asyncio
async def test_officer_can_list_and_read_rules(test_env):
    """(8) Officer role can list active rules and read rule definitions, but cannot toggle."""
    client = test_env["client"]

    # 1. Admin creates a rule
    test_env["user_state"]["user_metadata"]["role"] = "admin"
    create_resp = await client.post("/api/v1/rules/", json={
        "rule_code": "DEMO-READ-TEST",
        "category": "Readable",
        "statutory_reference": "Ref R",
        "rule_type": "presence",
        "target_field": "readable_field",
        "check_definition": {"operator": "exists"},
        "severity": "minor",
        "description_en": "Read test",
        "failure_message_template": "Missing",
    })
    rule_id = create_resp.json()["id"]
    v_id = create_resp.json()["active_version"]["id"]

    # 2. Switch to officer role
    test_env["user_state"]["user_metadata"]["role"] = "officer"
    test_env["user_state"]["id"] = str(TEST_OFFICER_ID)

    # List rules: should succeed
    list_resp = await client.get("/api/v1/rules/")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # Get single rule: should succeed
    get_resp = await client.get(f"/api/v1/rules/{rule_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["rule_code"] == "DEMO-READ-TEST"

    # Get version: should succeed
    ver_resp = await client.get(f"/api/v1/rules/versions/{v_id}")
    assert ver_resp.status_code == 200
    assert ver_resp.json()["id"] == v_id

    # Attempt to toggle activation as officer: should be rejected 403
    toggle_resp = await client.patch(
        f"/api/v1/rules/versions/{v_id}/activate",
        json={"is_active": False},
    )
    assert toggle_resp.status_code == 403


@pytest.mark.asyncio
async def test_rule_engine_evaluates_only_active_rules_from_database(test_env):
    """
    Verifies:
    1. Rule engine (run_audit) loads active rules directly from the database.
    2. Deactivated rules are NOT evaluated by the engine.
    3. Products are evaluated strictly against active database rules.
    """
    from app.services.rule_engine.engine import run_audit
    from app.models.enums import AuditResultType

    session_factory = test_env["session_factory"]

    # 1. Seed two rules directly in the database: one active, one inactive
    async with session_factory() as session:
        rule_a_id = uuid.uuid4()
        rule_b_id = uuid.uuid4()
        rule_a = ComplianceRule(id=rule_a_id, rule_code="DB-ACTIVE-RULE", category="Test")
        rule_b = ComplianceRule(id=rule_b_id, rule_code="DB-INACTIVE-RULE", category="Test")

        ver_a = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=rule_a_id,
            version=1,
            statutory_reference="Statutory Ref A",
            rule_type=RuleType.presence,
            target_field="mrp",
            check_definition={"operator": "exists"},
            severity=SeverityLevel.critical,
            description_en="Active MRP rule from DB",
            failure_message_template="MRP missing",
            verification_status=RuleVerificationStatus.verified,
            is_active=True,
            created_by=TEST_ADMIN_ID,
        )

        ver_b = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=rule_b_id,
            version=1,
            statutory_reference="Statutory Ref B",
            rule_type=RuleType.presence,
            target_field="unwanted_field",
            check_definition={"operator": "exists"},
            severity=SeverityLevel.critical,
            description_en="Inactive rule from DB",
            failure_message_template="Unwanted field missing",
            verification_status=RuleVerificationStatus.verified,
            is_active=False,  # INACTIVE!
            created_by=TEST_ADMIN_ID,
        )

        session.add_all([rule_a, rule_b, ver_a, ver_b])
        await session.commit()

    # 2. Run audit against facts with MRP present, but without unwanted_field
    facts = {"mrp": "Rs. 250.00"}
    async with session_factory() as session:
        audit_results = await run_audit(
            facts=facts,
            visual_measurements=None,
            ocr_confidences=None,
            db=session,
        )

    # 3. Assert only the active rule was evaluated
    evaluated_codes = [res["rule_code"] for res in audit_results]
    assert "DB-ACTIVE-RULE" in evaluated_codes
    assert "DB-INACTIVE-RULE" not in evaluated_codes

    active_result = next(res for res in audit_results if res["rule_code"] == "DB-ACTIVE-RULE")
    assert active_result["automated_result"] == AuditResultType.pass_
    assert active_result["rule_version"] == 1


@pytest.mark.asyncio
async def test_demo_rules_cannot_be_treated_as_verified_statutory_rules(test_env):
    """
    Verifies:
    1. Demo rules are strictly marked with verification_status = 'demo'.
    2. Verified statutory rules are strictly marked with verification_status = 'verified'.
    3. Creation endpoint defaults to 'demo' unless explicitly marked 'verified' by admin.
    4. Demo rules cannot masquerade as verified statutory rules.
    """
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "admin"

    # Default creation -> 'demo'
    resp_demo = await client.post("/api/v1/rules/", json={
        "rule_code": "DEMO-SAMPLE-RULE",
        "category": "Sample",
        "statutory_reference": "Demo Ref",
        "rule_type": "presence",
        "target_field": "demo_field",
        "check_definition": {"operator": "exists"},
        "severity": "minor",
        "description_en": "Sample demo rule",
        "failure_message_template": "Demo fail",
    })
    assert resp_demo.status_code == 201
    demo_v = resp_demo.json()["active_version"]
    assert demo_v["verification_status"] == "demo"
    assert demo_v["verification_status"] != "verified"

    # Attempted verified creation via general API -> force-overridden to 'demo' + audit security warning
    resp_verified = await client.post("/api/v1/rules/", json={
        "rule_code": "STATUTORY-PCR-RULE-01",
        "category": "Statutory MRP",
        "statutory_reference": "Legal Metrology Rules 2011, Rule 6(1)(e)",
        "rule_type": "presence",
        "target_field": "mrp",
        "check_definition": {"operator": "exists"},
        "severity": "critical",
        "description_en": "Official statutory declaration",
        "failure_message_template": "Statutory MRP missing",
        "verification_status": "verified",
    })
    assert resp_verified.status_code == 201
    verified_v = resp_verified.json()["active_version"]
    assert verified_v["verification_status"] == "demo"
    assert verified_v["verification_status"] != "verified"

    # Audit log confirms the override warning was captured
    audit_resp = await client.get(f"/api/v1/rules/{resp_verified.json()['id']}/audit-logs")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert "security_override_warning" in logs[0]["new_values"]
    assert "force-overridden to 'demo'" in logs[0]["new_values"]["security_override_warning"]


@pytest.mark.asyncio
async def test_statutory_rule_amendment_as_new_immutable_version(test_env):
    """
    Verifies that statutory amendments must be added as a new version (v2),
    preserving the original version (v1) immutable.
    """
    client = test_env["client"]
    test_env["user_state"]["user_metadata"]["role"] = "admin"

    # 1. Author initial statutory rule v1 (e.g. PCR 2011)
    create_resp = await client.post("/api/v1/rules/", json={
        "rule_code": "PCR-NET-QUANTITY",
        "category": "Net Quantity",
        "statutory_reference": "PCR 2011 Rule 12(1)",
        "rule_type": "presence",
        "target_field": "net_quantity",
        "check_definition": {"operator": "exists"},
        "severity": "major",
        "description_en": "Net quantity declaration",
        "failure_message_template": "Net quantity missing",
        "verification_status": "verified",
    })
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]
    v1_id = create_resp.json()["active_version"]["id"]

    # 2. Statutory Amendment arrives: add version 2 with pattern validation
    amendment_resp = await client.post(f"/api/v1/rules/{rule_id}/versions", json={
        "statutory_reference": "PCR Amendment 2026 Rule 12(1) Amended",
        "rule_type": "pattern",
        "target_field": "net_quantity",
        "check_definition": {"operator": "regex", "value": r"^\d+(\.\d+)?\s*(g|kg|ml|l)$"},
        "severity": "critical",
        "description_en": "Net quantity with mandatory standard unit",
        "failure_message_template": "Net quantity must include standard unit (g, kg, ml, l)",
        "verification_status": "verified",
        "is_active": True,
    })
    assert amendment_resp.status_code == 201
    v2_id = amendment_resp.json()["id"]
    assert amendment_resp.json()["version"] == 2

    # 3. Verify Version 1 remains unchanged and intact in the database
    v1_check = await client.get(f"/api/v1/rules/versions/{v1_id}")
    assert v1_check.status_code == 200
    assert v1_check.json()["version"] == 1
    assert v1_check.json()["statutory_reference"] == "PCR 2011 Rule 12(1)"
    assert v1_check.json()["rule_type"] == "presence"

    # 4. Verify Version 2 reflects the amended statutory requirement
    v2_check = await client.get(f"/api/v1/rules/versions/{v2_id}")
    assert v2_check.status_code == 200
    assert v2_check.json()["version"] == 2
    assert v2_check.json()["statutory_reference"] == "PCR Amendment 2026 Rule 12(1) Amended"
    assert v2_check.json()["rule_type"] == "pattern"

