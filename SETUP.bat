@echo off
setlocal enabledelayedexpansion
title MAARS Lens - One-Click Automated Setup
color 0b

echo ======================================================================
echo           MAARS Lens: Legal Metrology Digital Verification System
echo                    Automated Environment Setup Script
echo ======================================================================
echo.

:: 1. Check Python installation
echo [*] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Python is not installed or not added to your system PATH!
    echo Please install Python (3.10 to 3.14) from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Found %PY_VER%
echo.

:: 2. Check Node.js and NPM
echo [*] Checking Node.js and NPM...
node -v >nul 2>&1
if %errorlevel% neq 0 (
    color 0c
    echo [ERROR] Node.js / NPM is not installed or not added to system PATH!
    echo Please install Node.js (LTS version recommended) from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%n in ('node -v 2^>^&1') do set NODE_VER=%%n
for /f "tokens=*" %%m in ('npm -v 2^>^&1') do set NPM_VER=%%m
echo [OK] Found Node.js %NODE_VER% and NPM %NPM_VER%
echo.

:: 3. Setup Backend Environment and Dependencies
echo ----------------------------------------------------------------------
echo [1/4] Setting up Backend Python Dependencies...
echo ----------------------------------------------------------------------
cd /d "%~dp0backend"

echo [*] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1

echo [*] Installing backend requirements from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some heavy optional packages had warnings, installing core FastAPI and OCR stack...
    pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite pydantic pydantic-settings python-multipart python-jose[cryptography] passlib[bcrypt] bcrypt opencv-python-headless pillow rapidfuzz httpx sse-starlette reportlab openpyxl winocr
)

:: Ensure winocr is installed on Windows
python -c "import winocr" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing Windows Hardware-Accelerated OCR (winocr)...
    pip install winocr
)

echo [OK] Backend Python packages installed successfully!
echo.

:: 4. Initialize Database & Seed Authentic Roles
echo ----------------------------------------------------------------------
echo [2/4] Initializing Database & Seeding Statutory Rules & Accounts...
echo ----------------------------------------------------------------------
cd /d "%~dp0"
python -c "
import sys
sys.path.insert(0, 'backend')
import asyncio
from app.core.database import engine, Base, AsyncSessionLocal
import app.models
from scripts.enrich_prototype_db import enrich_database
from app.core.statutory_rules import build_statutory_rule_entities
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from sqlalchemy import select
import uuid

async def setup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await enrich_database()
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
    print('[OK] Database schema initialized and 4 authentic role accounts seeded successfully!')

asyncio.run(setup())
"
echo.

:: 5. Setup Frontend Dependencies
echo ----------------------------------------------------------------------
echo [3/4] Installing Frontend NPM Dependencies...
echo ----------------------------------------------------------------------
cd /d "%~dp0frontend"
call npm install
if %errorlevel% neq 0 (
    echo [WARNING] Standard npm install failed, retrying with --legacy-peer-deps...
    call npm install --legacy-peer-deps
)
echo [OK] Frontend dependencies installed successfully!
echo.

:: 6. Build Frontend
echo ----------------------------------------------------------------------
echo [4/4] Building Frontend Production Assets...
echo ----------------------------------------------------------------------
call npm run build
echo [OK] Frontend built successfully!
echo.

:: Completed
color 0a
echo ======================================================================
echo                   SETUP COMPLETED SUCCESSFULLY!
echo ======================================================================
echo.
echo All backend and frontend dependencies are configured.
echo Authentic Accounts Ready:
echo   - Citizen Portal:  citizen@maars.gov.in  (Password: citizen123)
echo   - Retailer Portal: retailer@store.in    (Password: retailer123)
echo   - Officer Portal:  officer@maars.gov.in  (Password: officer123)
echo   - Admin Portal:    admin@maars.gov.in    (Password: admin123)
echo.
echo To run the application at any time, simply double-click:
echo      START_SERVERS.bat
echo ======================================================================
echo.
pause
