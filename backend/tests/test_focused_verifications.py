import uuid
import pytest
import pytest_asyncio
from io import BytesIO
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.models.enums import InspectionStatus, ComplianceStatus, InspectionSource, UserRole, RuleType, SeverityLevel, AuditResultType
from app.routers.scans import router as scans_router
from app.routers.reports import router as reports_router
from app.routers.auth import router as auth_router
from app.services.rule_engine.engine import run_audit
from app.services.pdf.generator import generate_report_docx, generate_report_xlsx

OFFICER_1_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
OFFICER_2_ID = uuid.UUID("b0000000-0000-0000-0000-000000000002")
CURRENT_AUTH = {"id": str(OFFICER_1_ID), "role": "officer"}

@pytest_asyncio.fixture
async def focused_env():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(lambda sc: sc.exec_driver_sql("PRAGMA foreign_keys = OFF"))
        await conn.run_sync(
            lambda sc: Base.metadata.create_all(
                sc,
                tables=[
                    Product.__table__,
                    Inspection.__table__,
                    AuditResult.__table__,
                    ComplianceRule.__table__,
                    ComplianceRuleVersion.__table__,
                ],
                checkfirst=True,
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return {
            "id": CURRENT_AUTH["id"],
            "sub": CURRENT_AUTH["id"],
            "user_metadata": {"role": CURRENT_AUTH["role"]},
        }

    app = FastAPI()
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    app.include_router(scans_router, prefix="/api/v1/scans")
    app.include_router(reports_router, prefix="/api/v1/reports")
    app.include_router(auth_router, prefix="/api/v1/auth")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {"client": client, "session_factory": session_factory}

    await engine.dispose()


# Test 1: Repeat scan with same barcode links to the exact same Product entity
@pytest.mark.asyncio
async def test_repeat_barcode_links_same_product(focused_env):
    session_factory = focused_env["session_factory"]
    client = focused_env["client"]

    # Seed an existing product with known barcode
    async with session_factory() as session:
        p = Product(
            id=uuid.uuid4(),
            brand_name="Parle",
            product_name="Parle-G 250g",
            barcode="8901719101011",
        )
        session.add(p)
        await session.commit()
        existing_pid = p.id

    # Create inspection linking barcode
    async with session_factory() as session:
        # Simulate multi-image merge linking
        p_match = (await session.execute(select(Product).where(Product.barcode == "8901719101011"))).scalar_one()
        insp = Inspection(
            id=uuid.uuid4(),
            client_submission_id=uuid.uuid4(),
            officer_id=OFFICER_1_ID,
            product_id=p_match.id,
            product_name=p_match.product_name,
            brand_name=p_match.brand_name,
            status=InspectionStatus.needs_review,
        )
        session.add(insp)
        await session.commit()
        assert insp.product_id == existing_pid


# Test 2: Listing scan flags missing mandatory declarations as non-compliant
@pytest.mark.asyncio
async def test_listing_scan_flags_violations(focused_env):
    client = focused_env["client"]
    session_factory = focused_env["session_factory"]

    # Seed a mandatory MRP rule
    async with session_factory() as session:
        r = ComplianceRule(id=uuid.uuid4(), rule_code="TEST-R6-MRP", category="Price")
        session.add(r)
        await session.flush()
        rv = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=r.id,
            version=1,
            statutory_reference="Rule 6(1)(e)",
            rule_type=RuleType.presence,
            target_field="mrp",
            check_definition={"operator": "exists"},
            severity=SeverityLevel.critical,
            description_en="MRP required",
            failure_message_template="MRP missing",
            verification_status="demo",
            created_by=OFFICER_1_ID,
        )
        session.add(rv)
        await session.commit()

    # Submit listing missing MRP
    resp = await client.post(
        "/api/v1/scans/listing",
        json={
            "title": "Mystery Biscuits",
            "pasted_text": "Net Quantity: 200g, Made in India",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["automated_compliance"] == "non_compliant"


# Test 3: Uncalibrated font height defaults to Needs Manual Review
@pytest.mark.asyncio
async def test_uncalibrated_font_needs_manual_review(focused_env):
    session_factory = focused_env["session_factory"]
    async with session_factory() as session:
        r = ComplianceRule(id=uuid.uuid4(), rule_code="LMPC-R7-FONT", category="Legibility")
        session.add(r)
        await session.flush()
        rv = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=r.id,
            version=1,
            statutory_reference="Rule 7 Table",
            rule_type=RuleType.visual,
            target_field="numeral_height_mm",
            check_definition={"operator": "font_size_band", "default_min_height_mm": 2.0},
            severity=SeverityLevel.minor,
            description_en="Font height",
            failure_message_template="Too small",
            verification_status="demo",
            requires_visual_measurement=True,
            created_by=OFFICER_1_ID,
        )
        session.add(rv)
        await session.commit()

        # Run audit with uncalibrated visual measurements
        results = await run_audit(
            facts={"net_quantity": "500g"},
            visual_measurements={"text_regions": [{"label": "numeral_height_mm", "measurement_reliable": False}]},
            ocr_confidences={"net_quantity": 0.95},
            db=session,
        )
        font_res = next((res for res in results if res["rule_code"] == "LMPC-R7-FONT"), None)
        assert font_res is not None
        assert font_res["automated_result"] == AuditResultType.needs_review
        assert font_res["measurement_reliable"] is False


# Test 4: Security headers are present on API responses
@pytest.mark.asyncio
async def test_security_headers_present(focused_env):
    client = focused_env["client"]
    resp = await client.get("/api/v1/scans/")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert "1; mode=block" in resp.headers.get("x-xss-protection", "")


# Test 5: Officer 2 cannot mutate Officer 1's draft inspection
@pytest.mark.asyncio
async def test_officer_draft_isolation(focused_env):
    client = focused_env["client"]
    session_factory = focused_env["session_factory"]

    insp_id = uuid.uuid4()
    async with session_factory() as session:
        insp = Inspection(
            id=insp_id,
            client_submission_id=uuid.uuid4(),
            officer_id=OFFICER_1_ID,
            product_name="Draft Item",
            status=InspectionStatus.needs_review,
            is_finalized=False,
        )
        session.add(insp)
        await session.commit()

    # Switch caller to Officer 2
    CURRENT_AUTH["id"] = str(OFFICER_2_ID)
    CURRENT_AUTH["role"] = "officer"

    resp = await client.post(
        f"/api/v1/scans/{insp_id}/finalize",
        json={},
    )
    assert resp.status_code == 403
    assert "Cross-officer isolation" in resp.text

    # Restore Officer 1
    CURRENT_AUTH["id"] = str(OFFICER_1_ID)


# Test 6: DOCX export generation produces valid binary with statutory disclaimer
def test_docx_export_content():
    payload = {
        "inspection_id": str(uuid.uuid4()),
        "product_name": "Organic Honey",
        "brand_name": "PureBee",
        "status": "completed",
        "automated_compliance": "compliant",
        "final_compliance": "compliant",
        "is_finalized": True,
        "finalized_at": "2026-09-20T00:00:00Z",
        "report_hash": "sha256:abcd1234efgh5678",
        "audit_results": [],
    }
    docx_bytes = generate_report_docx(payload)
    assert len(docx_bytes) > 1000
    assert docx_bytes.startswith(b"PK\x03\x04")  # Standard docx zip header


# Test 7: XLSX export generation produces valid spreadsheet binary
def test_xlsx_export_content():
    payload = {
        "inspection_id": str(uuid.uuid4()),
        "product_name": "Atta 10kg",
        "brand_name": "Aashirvaad",
        "status": "completed",
        "automated_compliance": "compliant",
        "final_compliance": "compliant",
        "is_finalized": True,
        "finalized_at": "2026-09-20T00:00:00Z",
        "report_hash": "sha256:99887766",
        "audit_results": [
            {
                "rule_code": "PCR-R6-MRP",
                "statutory_reference": "Rule 6(1)(e)",
                "automated_result": "pass",
                "manual_review_result": None,
                "effective_result": "pass",
            }
        ],
    }
    xlsx_bytes = generate_report_xlsx(payload)
    assert len(xlsx_bytes) > 1000
    assert xlsx_bytes.startswith(b"PK\x03\x04")  # Standard xlsx zip header
