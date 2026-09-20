import asyncio
import uuid
import datetime
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import engine, Base, AsyncSessionLocal
from app.models.user import Profile, Retailer, Customer, RoleApplication
from app.models.area import Area
from app.models.enums import UserRole, AreaType, ViolationStatus, SeverityLevel, ComplianceStatus
from app.models.inspection import Inspection, InspectionImage
from app.models.violation import Violation
from app.models.rule import ComplianceRule

def hash_pw(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode('utf-8')

async def enrich_database():
    print("Enriching and organizing prototype database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Update/Ensure all standard demo profiles with secure passwords
        demo_accounts = [
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000001"),
                "email": "officer@maars.gov.in",
                "role": UserRole.officer,
                "full_name": "Inspector Rajesh Kumar",
                "employee_id": "LM-OFFICER-001",
                "password": "officer123"
            },
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000002"),
                "email": "admin@maars.gov.in",
                "role": UserRole.admin,
                "full_name": "Director Sharma (Admin)",
                "employee_id": "LM-ADMIN-001",
                "password": "admin123"
            },
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
                "email": "retailer@store.in",
                "role": UserRole.retailer,
                "full_name": "Sunil Gupta (Kirana Owner)",
                "employee_id": "RET-STORE-001",
                "password": "retailer123"
            },
            {
                "id": uuid.UUID("a0000000-0000-0000-0000-000000000004"),
                "email": "citizen@maars.gov.in",
                "role": UserRole.customer,
                "full_name": "Aakash Verma (Citizen)",
                "employee_id": "CUST-001",
                "password": "citizen123"
            },
        ]

        for acc in demo_accounts:
            res = await session.execute(select(Profile).where(Profile.email == acc["email"]))
            p = res.scalar_one_or_none()
            if not p:
                p = Profile(
                    id=acc["id"],
                    email=acc["email"],
                    role=acc["role"],
                    full_name=acc["full_name"],
                    employee_id=acc["employee_id"],
                    password_hash=hash_pw(acc["password"]),
                    is_active=True,
                    onboarding_completed=True,
                    phone="+919876543210"
                )
                session.add(p)
            else:
                p.password_hash = hash_pw(acc["password"])
                p.is_active = True
                p.role = acc["role"]
                p.full_name = acc["full_name"]

        await session.flush()

        await session.commit()
        print("Prototype database initialized with clean authentic accounts!")

if __name__ == "__main__":
    asyncio.run(enrich_database())
