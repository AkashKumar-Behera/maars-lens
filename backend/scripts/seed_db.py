import asyncio
import uuid
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, Base, AsyncSessionLocal
import app.models
from app.models.user import Profile, Retailer, Customer
from app.models.area import Area
from app.models.enums import UserRole, AreaType, RuleType, SeverityLevel, RuleVerificationStatus
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.core.statutory_rules import build_statutory_rule_entities

async def init_and_seed():
    print("1. Creating tables in SQLite test.db...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        print("2. Ensuring default areas exist...")
        area_id = uuid.UUID("b0000000-0000-0000-0000-000000000002")
        res_area = await session.execute(select(Area).where(Area.id == area_id))
        if not res_area.scalar_one_or_none():
            area = Area(
                id=area_id,
                name="New Delhi Central Enforcement Zone",
                area_type=AreaType.district,
                is_active=True
            )
            session.add(area)
            await session.flush()

        print("3. Seeding real demo login profiles...")
        # 1. Enforcement Officer
        officer_id = uuid.UUID("a0000000-0000-0000-0000-000000000001")
        res_off = await session.execute(select(Profile).where(Profile.id == officer_id))
        if not res_off.scalar_one_or_none():
            officer = Profile(
                id=officer_id,
                role=UserRole.officer,
                full_name="Inspector Rajesh Kumar",
                email="officer@maars.gov.in",
                employee_id="LM-OFFICER-001",
                phone="+919876543210",
                is_active=True,
                onboarding_completed=True
            )
            session.add(officer)

        # 2. System Administrator
        admin_id = uuid.UUID("a0000000-0000-0000-0000-000000000002")
        res_adm = await session.execute(select(Profile).where(Profile.id == admin_id))
        if not res_adm.scalar_one_or_none():
            admin = Profile(
                id=admin_id,
                role=UserRole.admin,
                full_name="Director Sharma (Admin)",
                email="admin@maars.gov.in",
                employee_id="LM-ADMIN-001",
                phone="+919876543211",
                is_active=True,
                onboarding_completed=True
            )
            session.add(admin)

        # 2b. Secondary local dev admin: admin@maars.local
        admin_local_id = uuid.UUID("a0000000-0000-0000-0000-000000000012")
        res_adm_loc = await session.execute(select(Profile).where(Profile.id == admin_local_id))
        if not res_adm_loc.scalar_one_or_none():
            admin_local = Profile(
                id=admin_local_id,
                role=UserRole.admin,
                full_name="Local Dev Administrator",
                email="admin@maars.local",
                employee_id="LM-ADMIN-DEV",
                phone="+919876543299",
                is_active=True,
                onboarding_completed=True
            )
            session.add(admin_local)

        # 3. Retailer Profile & Record
        retailer_user_id = uuid.UUID("a0000000-0000-0000-0000-000000000003")
        res_ret = await session.execute(select(Profile).where(Profile.id == retailer_user_id))
        if not res_ret.scalar_one_or_none():
            retailer_prof = Profile(
                id=retailer_user_id,
                role=UserRole.retailer,
                full_name="Sunil Gupta (Kirana Owner)",
                email="retailer@store.in",
                employee_id="RET-STORE-001",
                phone="+919876543212",
                is_active=True,
                onboarding_completed=True
            )
            session.add(retailer_prof)
            await session.flush()

            retailer = Retailer(
                id=retailer_user_id,
                business_name="Gupta Supermart & General Store",
                shop_address="Shop 14, Connaught Place, New Delhi",
                area_id=area_id,
                license_number="DL-LM-2024-8891"
            )
            session.add(retailer)

        # 4. Consumer
        cust_user_id = uuid.UUID("a0000000-0000-0000-0000-000000000004")
        res_cust = await session.execute(select(Customer).where(Customer.id == cust_user_id))
        if not res_cust.scalar_one_or_none():
            customer = Customer(
                id=cust_user_id,
                customer_code="CUST-DEMO01",
                onboarding_completed=True
            )
            session.add(customer)

        print("4. Seeding statutory compliance rules...")
        rule_versions = build_statutory_rule_entities(author_id=admin_id)
        for v in rule_versions:
            r = v.rule
            existing_r = (await session.execute(select(ComplianceRule).where(ComplianceRule.rule_code == r.rule_code))).scalar_one_or_none()
            if not existing_r:
                session.add(r)
                await session.flush()
                v.rule_id = r.id
                session.add(v)
            else:
                existing_v = (await session.execute(select(ComplianceRuleVersion).where(ComplianceRuleVersion.rule_id == existing_r.id))).scalar_one_or_none()
                if not existing_v:
                    v.rule_id = existing_r.id
                    session.add(v)

        await session.commit()
        print("Database initialized and seeded successfully!")

if __name__ == "__main__":
    asyncio.run(init_and_seed())
