import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.models.enums import InspectionStatus, ComplianceStatus, InspectionSource, UserRole, RuleType, SeverityLevel
from app.routers.scans import router as scans_router

TEST_OFFICER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
async def listing_test_env():
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

    # Seed sample statutory rules for listing evaluation
    async with session_factory() as session:
        r1 = ComplianceRule(
            id=uuid.uuid4(),
            rule_code="LMPC-R6-MRP",
            category="Retail Price",
        )
        r2 = ComplianceRule(
            id=uuid.uuid4(),
            rule_code="LMPC-R6-NET-QTY",
            category="Net Quantity",
        )
        session.add_all([r1, r2])
        await session.flush()

        v1 = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=r1.id,
            version=1,
            statutory_reference="Rule 6(1)(e)",
            rule_type=RuleType.presence,
            target_field="mrp",
            check_definition={"operator": "exists"},
            severity=SeverityLevel.critical,
            description_en="MRP must be declared",
            failure_message_template="MRP missing",
            created_by=TEST_OFFICER_ID,
            is_active=True,
        )
        v2 = ComplianceRuleVersion(
            id=uuid.uuid4(),
            rule_id=r2.id,
            version=1,
            statutory_reference="Rule 6(1)(d)",
            rule_type=RuleType.presence,
            target_field="net_quantity",
            check_definition={"operator": "exists"},
            severity=SeverityLevel.critical,
            description_en="Net quantity must be declared",
            failure_message_template="Net quantity missing",
            created_by=TEST_OFFICER_ID,
            is_active=True,
        )
        session.add_all([v1, v2])
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return {
            "id": str(TEST_OFFICER_ID),
            "sub": str(TEST_OFFICER_ID),
            "user_metadata": {"role": "officer"},
        }

    app = FastAPI()
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


@pytest.mark.asyncio
async def test_listing_scan_with_pasted_text(listing_test_env):
    client = listing_test_env["client"]

    pasted_text = """
    Brand: Amul Gold
    Product: Homogenised Standardised Milk
    MRP: Rs. 66.00 (Inclusive of all taxes)
    Net Quantity: 1000 ml
    Country of Origin: India
    Manufacturer: Gujarat Co-operative Milk Marketing Federation Ltd.
    Customer Care: 1800-258-3333
    """

    resp = await client.post(
        "/api/v1/scans/listing",
        json={
            "title": "Amul Gold Milk 1L",
            "brand": "Amul",
            "pasted_text": pasted_text,
        },
    )

    assert resp.status_code == 200
    data = resp.json()

    assert data["source"] == "listing"
    assert data["brand_name"] == "Amul"
    assert data["product_name"] == "Amul Gold Milk 1L"
    assert data["product_id"] is not None
    assert data["extracted_facts"]["mrp"] is not None
    assert data["extracted_facts"]["net_quantity"] is not None
    assert data["extracted_facts"]["mrp_tax_inclusive"] is True
    assert data["automated_compliance"] == "compliant"
    assert data["audit_results_count"] == 2
