import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Table, Column, String, DateTime, Boolean, ForeignKey, Float, Text, JSON
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from app.core.database import Base, get_db
from app.core.auth import get_current_user
from app.models.product import Product
from app.models.inspection import Inspection
from app.models.enums import InspectionStatus, ComplianceStatus, InspectionSource
from app.routers.products import router as products_router

TEST_USER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
async def product_test_env():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Disable foreign key constraints in sqlite so partial table sets can be tested in isolation
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: sync_conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
        )
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[Product.__table__, Inspection.__table__],
                checkfirst=True,
            )
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_current_user():
        return {
            "id": str(TEST_USER_ID),
            "sub": str(TEST_USER_ID),
            "user_metadata": {"role": "officer"},
        }

    app = FastAPI()
    app.include_router(products_router, prefix="/api/v1/products")
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
async def test_product_history_endpoint(product_test_env):
    client = product_test_env["client"]
    session_factory = product_test_env["session_factory"]

    prod_id = uuid.uuid4()
    area_id = uuid.uuid4()
    officer_id = uuid.uuid4()

    async with session_factory() as session:
        prod = Product(
            id=prod_id,
            brand_name="Tata Tea",
            product_name="Premium Gold 500g",
            manufacturer_name="Tata Consumer Products Ltd",
            barcode="8901234567890",
        )
        session.add(prod)

        insp1 = Inspection(
            id=uuid.uuid4(),
            client_submission_id=uuid.uuid4(),
            officer_id=officer_id,
            area_id=area_id,
            product_id=prod_id,
            product_name="Premium Gold 500g",
            brand_name="Tata Tea",
            status=InspectionStatus.needs_review,
            automated_compliance=ComplianceStatus.non_compliant,
            source=InspectionSource.officer,
        )
        insp2 = Inspection(
            id=uuid.uuid4(),
            client_submission_id=uuid.uuid4(),
            officer_id=officer_id,
            area_id=area_id,
            product_id=prod_id,
            product_name="Premium Gold 500g",
            brand_name="Tata Tea",
            status=InspectionStatus.completed,
            automated_compliance=ComplianceStatus.compliant,
            final_compliance=ComplianceStatus.compliant,
            is_finalized=True,
            source=InspectionSource.officer,
        )
        session.add_all([insp1, insp2])
        await session.commit()

    resp = await client.get(f"/api/v1/products/{prod_id}/history")
    assert resp.status_code == 200
    data = resp.json()

    assert data["product_id"] == str(prod_id)
    assert data["brand_name"] == "Tata Tea"
    assert data["product_name"] == "Premium Gold 500g"
    assert data["barcode"] == "8901234567890"
    assert data["total_inspections"] == 2
    assert len(data["inspections"]) == 2
    assert data["inspections"][0]["is_finalized"] in (True, False)
