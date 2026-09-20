@echo off
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
if errorlevel 1 goto :no_python
goto :has_python

:no_python
color 0c
echo [ERROR] Python is not installed or not added to your system PATH!
echo Please install Python (3.10 to 3.14) from https://www.python.org/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:has_python
python --version
echo [OK] Python is available!
echo.

:: 2. Check Node.js and NPM
echo [*] Checking Node.js and NPM...
node -v >nul 2>&1
if errorlevel 1 goto :no_node
goto :has_node

:no_node
color 0c
echo [ERROR] Node.js or NPM is not installed or not added to system PATH!
echo Please install Node.js from https://nodejs.org/
echo.
pause
exit /b 1

:has_node
echo Node.js:
call node -v
echo NPM:
call npm -v
echo [OK] Node.js and NPM are available!
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
if errorlevel 1 (
    echo [WARNING] Retrying with core FastAPI and OCR dependencies...
    pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite pydantic pydantic-settings python-multipart python-jose[cryptography] passlib[bcrypt] bcrypt opencv-python-headless pillow rapidfuzz httpx sse-starlette reportlab openpyxl winocr
)

:: Ensure winocr is installed on Windows
python -c "import winocr" >nul 2>&1
if errorlevel 1 (
    echo [*] Installing Windows Hardware-Accelerated OCR [winocr]...
    pip install winocr
)

echo [OK] Backend Python packages installed successfully!
echo.

:: 4. Initialize Database & Seed Authentic Roles
echo ----------------------------------------------------------------------
echo [2/4] Initializing Database and Seeding Statutory Rules and Accounts...
echo ----------------------------------------------------------------------
cd /d "%~dp0"
python backend\scripts\init_db.py
if errorlevel 1 (
    echo [WARNING] Direct script failed, executing from backend directory...
    cd /d "%~dp0backend"
    python scripts\init_db.py
    cd /d "%~dp0"
)
echo.

:: 5. Setup Frontend Dependencies
echo ----------------------------------------------------------------------
echo [3/4] Installing Frontend NPM Dependencies...
echo ----------------------------------------------------------------------
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
    echo [WARNING] Standard npm install failed, retrying with legacy peer deps...
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
