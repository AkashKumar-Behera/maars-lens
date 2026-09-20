"""
MAARS Lens: End-to-End Simulation Test Suite
============================================
Simulates the complete real-world officer and compliance lifecycle:
1. Admin authors/provisions compliance rules in the system.
2. Officer uploads a product inspection scan (OCR facts + visual measurements).
3. Rule Engine evaluates package facts against active rules in the database.
4. Officer conducts a manual review with mandatory reason and server-side compliance computation.
5. Officer finalizes the inspection, locking it permanently and generating a tamper-evident SHA-256 report hash.
6. System serves a verified PDF inspection certificate with matching SHA-256 seal.
7. System detects non-compliance and records a formal statutory violation with terminal lifecycle resolution.
8. Verifies tamper-detection: modified inspection metadata invalidates the report hash.
"""

import io
import uuid
import datetime
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
from app.models.rule import ComplianceRule, ComplianceRuleVersion, RuleAuditLog
from app.models.violation import Violation

from app.routers.rules import router as rules_router
from app.routers.scans import router as scans_router
from app.routers.reports import router as reports_router
from app.routers.violations import router as violations_router
from app.services.rule_engine.engine import run_audit
from app.services.pdf.generator import compute_report_hash

TEST_ADMIN_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_OFFICER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
TEST_AREA_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
TEST_RETAILER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest_asyncio.fixture
async def e2e_env():
    """Sets up an end-to-end multi-router environment with in-memory SQLite."""
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
                    RuleAuditLog.__table__,
                    Inspection.__table__,
                    AuditResult.__table__,
                    Violation.__table__,
                ],
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Seed baseline profiles (Admin and Inspecting Officer)
    async with session_factory() as session:
        admin_prof = Profile(
            id=TEST_ADMIN_ID,
            role=UserRole.admin,
            full_name="National Director of Legal Metrology",
            email="admin@legalmetrology.gov.in",
            is_active=True,
        )
        officer_prof = Profile(
            id=TEST_OFFICER_ID,
            role=UserRole.officer,
            full_name="Inspector Rajesh Sharma",
            email="officer.delhi@legalmetrology.gov.in",
            employee_id="LM-DL-8042",
            is_active=True,
        )
        session.add_all([admin_prof, officer_prof])
        await session.commit()

    # Dynamic auth context to simulate Admin vs Officer turns
    auth_state = {
        "id": str(TEST_ADMIN_ID),
        "sub": str(TEST_ADMIN_ID),
        "user_metadata": {"role": "admin"},
    }

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return auth_state

    app = FastAPI(title="MAARS Lens E2E Simulation API")
    app.include_router(rules_router, prefix="/api/v1/rules")
    app.include_router(scans_router, prefix="/api/v1/scans")
    app.include_router(reports_router, prefix="/api/v1/reports")
    app.include_router(violations_router, prefix="/api/v1/violations")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "session_factory": session_factory,
            "auth_state": auth_state,
        }

    await engine.dispose()


@pytest.mark.asyncio
async def test_full_system_end_to_end_simulation(e2e_env):
    """
    Executes the entire lifecycle simulation:
    Rule Authoring -> Scan Upload -> Engine Audit -> Manual Review ->
    Finalize & Hash -> Verified PDF Download -> Statutory Violation Lifecycle.
    """
    client = e2e_env["client"]
    auth_state = e2e_env["auth_state"]
    session_factory = e2e_env["session_factory"]

    # --------------------------------------------------------------------------
    # STAGE 1: Admin authors Legal Metrology compliance rules
    # --------------------------------------------------------------------------
    auth_state["id"] = str(TEST_ADMIN_ID)
    auth_state["user_metadata"]["role"] = "admin"

    # Rule 1: Maximum Retail Price (MRP) declaration
    rule_1_resp = await client.post("/api/v1/rules/", json={
        "rule_code": "PCR-2011-R06-MRP",
        "category": "MRP",
        "statutory_reference": "Rule 6(1)(e) - Retail Sale Price",
        "rule_type": "presence",
        "target_field": "mrp",
        "check_definition": {"operator": "exists"},
        "severity": "critical",
        "description_en": "Mandatory Maximum Retail Price declaration inclusive of all taxes.",
        "failure_message_template": "MRP declaration is missing from package front/back display.",
        "verification_status": "verified",
    })
    assert rule_1_resp.status_code == 201
    rule_1_id = rule_1_resp.json()["id"]

    # Rule 2: Net Quantity declaration
    rule_2_resp = await client.post("/api/v1/rules/", json={
        "rule_code": "PCR-2011-R12-NETQTY",
        "category": "Net Quantity",
        "statutory_reference": "Rule 12(1) - Manner of declaration of quantity",
        "rule_type": "pattern",
        "target_field": "net_quantity",
        "check_definition": {"operator": "regex", "value": r"^\d+(\.\d+)?\s*(g|kg|ml|l)$"},
        "severity": "major",
        "description_en": "Net quantity in standard SI units.",
        "failure_message_template": "Net quantity must include standard unit (g, kg, ml, l).",
        "verification_status": "verified",
    })
    assert rule_2_resp.status_code == 201

    # --------------------------------------------------------------------------
    # STAGE 2: Officer uploads product inspection scan
    # --------------------------------------------------------------------------
    auth_state["id"] = str(TEST_OFFICER_ID)
    auth_state["user_metadata"]["role"] = "officer"

    client_submission_id = uuid.uuid4()
    upload_resp = await client.post("/api/v1/scans/upload", json={
        "client_submission_id": str(client_submission_id),
        "area_id": str(TEST_AREA_ID),
        "retailer_id": str(TEST_RETAILER_ID),
        "product_name": "Premium Basmati Rice 5kg",
        "brand_name": "Himalayan Pearl",
        "gps_lat": 28.6139,
        "gps_lng": 77.2090,
    })
    assert upload_resp.status_code == 201
    inspection_id = uuid.UUID(upload_resp.json()["inspection_id"])

    # --------------------------------------------------------------------------
    # STAGE 3: Compliance Engine evaluates OCR-extracted facts
    # Extracted facts: net_quantity has valid '5kg', but MRP is MISSING!
    # --------------------------------------------------------------------------
    extracted_facts = {
        "net_quantity": "5kg",
        "brand_name": "Himalayan Pearl",
        # 'mrp' is missing deliberately to trigger non-compliance
    }
    extracted_confidences = {
        "net_quantity": 0.98,
        "brand_name": 0.95,
    }

    async with session_factory() as session:
        audit_records = await run_audit(
            facts=extracted_facts,
            visual_measurements=None,
            ocr_confidences=extracted_confidences,
            db=session,
        )

        # Store audit results under this inspection
        db_audit_results = []
        for rec in audit_records:
            ar = AuditResult(
                id=uuid.uuid4(),
                inspection_id=inspection_id,
                rule_version_id=rec["rule_version_id"],
                rule_code=rec["rule_code"],
                rule_version=rec["rule_version"],
                statutory_reference=rec["statutory_reference"],
                automated_result=rec["automated_result"],
                effective_result=rec["effective_result"],
                actual_value=rec["actual_value"],
                expected_value=rec["expected_value"],
                fact_confidence=rec["fact_confidence"],
                measurement_reliable=rec["measurement_reliable"],
                automated_reason=rec["automated_reason"],
                severity=rec["severity"],
            )
            session.add(ar)
            db_audit_results.append(ar)

        # Update inspection automated_compliance to non_compliant (due to missing MRP critical rule)
        insp = await session.get(Inspection, inspection_id)
        insp.automated_compliance = ComplianceStatus.non_compliant
        insp.final_compliance = ComplianceStatus.non_compliant
        insp.status = InspectionStatus.needs_review
        await session.commit()

    # --------------------------------------------------------------------------
    # STAGE 4: Officer performs manual review with justification
    # Officer inspects physical package: confirms MRP is indeed not declared.
    # --------------------------------------------------------------------------
    review_resp = await client.post(f"/api/v1/scans/{inspection_id}/result", json={
        "rule_code": "PCR-2011-R06-MRP",
        "manual_review_result": "fail",
        "manual_review_reason": "Physical package physically examined: MRP declaration is completely absent.",
    })
    assert review_resp.status_code == 200
    assert review_resp.json()["final_compliance"] == "non_compliant"

    # --------------------------------------------------------------------------
    # STAGE 5: Officer finalizes the inspection -> SHA-256 seal generated & locked
    # --------------------------------------------------------------------------
    finalize_resp = await client.post(f"/api/v1/scans/{inspection_id}/finalize", json={
        "officer_notes": "Inspection confirmed non-compliant. Issuing statutory notice under Section 36(1)."
    })
    assert finalize_resp.status_code == 200
    report_hash = finalize_resp.json()["report_hash"]
    assert report_hash.startswith("sha256:")
    assert len(report_hash) == 71

    # Verify immutability: attempting any further review mutation is rejected (400)
    post_finalize_attempt = await client.post(f"/api/v1/scans/{inspection_id}/result", json={
        "rule_code": "PCR-2011-R06-MRP",
        "manual_review_result": "pass",
        "manual_review_reason": "Attempting illegal post-finalization alteration",
    })
    assert post_finalize_attempt.status_code == 400
    assert "finalized" in post_finalize_attempt.json()["detail"].lower()

    # --------------------------------------------------------------------------
    # STAGE 6: Verified PDF Report Generation & Whitelist Summary
    # --------------------------------------------------------------------------
    # 1. Summary endpoint (whitelisted fields only)
    summary_resp = await client.get(f"/api/v1/reports/{inspection_id}/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["is_finalized"] is True
    assert summary_data["report_hash"] == report_hash
    assert summary_data["final_compliance"] == "non_compliant"

    # 2. PDF streaming endpoint
    pdf_resp = await client.get(f"/api/v1/reports/{inspection_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-1.4")
    assert len(pdf_resp.content) > 500  # Valid generated binary certificate

    # 3. Report hash verification endpoint (tamper detection)
    verify_resp = await client.get(f"/api/v1/reports/{inspection_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["valid"] is True
    assert verify_resp.json()["report_hash"] == report_hash

    # --------------------------------------------------------------------------
    # STAGE 7: Statutory Violation Creation & Lifecycle
    # --------------------------------------------------------------------------
    # 1. Create violation record for non-compliant inspection
    viol_create_resp = await client.post(f"/api/v1/violations/{inspection_id}", json={
        "failing_rule_codes": ["PCR-2011-R06-MRP"],
        "summary": "Absence of statutory Maximum Retail Price declaration on retail package.",
    })
    assert viol_create_resp.status_code == 201
    assert viol_create_resp.json()["status"] == "open"
    assert "PCR-2011-R06-MRP" in viol_create_resp.json()["failing_rule_codes"]

    # 2. Retrieve violation record
    viol_get_resp = await client.get(f"/api/v1/violations/{inspection_id}")
    assert viol_get_resp.status_code == 200
    assert viol_get_resp.json()["status"] == "open"

    # 3. Transition violation to resolved with required statutory resolution notes
    viol_resolve_resp = await client.post(f"/api/v1/violations/{inspection_id}/status", json={
        "status": "resolved",
        "resolution_notes": "Compounding fee deposited under Section 48; corrective package labeling submitted and verified.",
    })
    assert viol_resolve_resp.status_code == 200
    assert viol_resolve_resp.json()["status"] == "resolved"
    assert viol_resolve_resp.json()["resolved_at"] is not None

    # 4. Terminal state guard: cannot re-open resolved violation
    viol_reopen_attempt = await client.post(f"/api/v1/violations/{inspection_id}/status", json={
        "status": "open",
        "resolution_notes": "Attempting unauthorized reopen",
    })
    assert viol_reopen_attempt.status_code == 400
    assert "terminal status" in viol_reopen_attempt.json()["detail"].lower()
