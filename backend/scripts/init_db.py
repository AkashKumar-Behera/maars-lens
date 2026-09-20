"""
MAARS Lens: Database Initializer & Statutory Rules Seeder
=========================================================
Idempotent script called by SETUP.bat to ensure tables, authentic accounts,
and 13 statutory rules are seeded.
"""
import sys
import os
import asyncio
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import engine, Base, AsyncSessionLocal
import app.models
from scripts.enrich_prototype_db import enrich_database
from app.core.statutory_rules import build_statutory_rule_entities
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from sqlalchemy import select

async def run_setup():
    print("[*] Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[*] Seeding 4 authentic role accounts (Admin, Officer, Retailer, Citizen)...")
    await enrich_database()

    print("[*] Seeding verified statutory rules...")
    admin_id = uuid.UUID('a0000000-0000-0000-0000-000000000002')
    rule_versions = build_statutory_rule_entities(author_id=admin_id)
    async with AsyncSessionLocal() as session:
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
                else:
                    existing_v.verification_status = v.verification_status
                    existing_v.is_active = True
        await session.commit()
    print("[OK] Database schema initialized and 4 authentic role accounts seeded successfully!")

if __name__ == '__main__':
    asyncio.run(run_setup())
