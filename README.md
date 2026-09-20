# MAARS Lens 👁️🇮🇳
### National Legal Metrology Digital Verification System (LMPC Rules, 2011)
**Problem Statement ID:** 26034  
**Category:** Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 via Multi-Image & OCR Label Analysis.

---

## 🌟 Key Features

1. **360° Multi-Panel Image Upload**:
   - Upload up to **5 package photos at once** (1 Mandatory Principal Display Panel + up to 4 Optional Panels: Back, Side, Nutritional, Outer).
   - Fast batch multi-file picker or individual camera captures.
2. **Statutory 10 Rules Legal Metrology Compliance Engine**:
   - Rule 6(1)(a): Manufacturer, Packer, or Importer Name & Complete Address
   - Rule 6(1)(b): Generic / Common Name of Commodity
   - Rule 6(1)(d): Net Quantity in Standard SI Metric Units (g, kg, ml, l)
   - Rule 6(1)(b): Month & Year of Manufacture / Packing / Import
   - Rule 6(1)(e): Maximum Retail Price (MRP in ₹)
   - Rule 6(1)(e): Tax-Inclusive Phrasing ("Inclusive of all taxes")
   - Rule 6(1)(da): Consumer Grievance / Care Helpline, Email & Contact
   - Rule 6(10): Country of Origin / Manufacture
   - Rule 6(11): Unit Sale Price (USP per unit / per 100g)
   - Rule 10 / FSSAI: FSSAI Food Safety License Number & Logo (14 digits)
3. **Hardware-Accelerated OCR**:
   - High-accuracy Windows Native OCR (`winocr`) + multilingual fallback.
   - Extracts dot-matrix print, batch numbers, MRP strings, and FSSAI license numbers verbatim.
4. **Geo-Spatial Violation Radar Map**:
   - Integrated with MapTiler dark vector radar maps for Enforcement Officers.
   - Live marker clusters showing consumer complaints and non-compliant retail shops across India.
5. **Role-Based Portals**:
   - **Citizen / Consumer (`/customer`)**: Instant photo scan, rule-by-rule audit checklist, and GPS incident reporting.
   - **Retailer (`/retailer`)**: Inventory compliance self-audits and pre-clearance certificates.
   - **Enforcement Officer (`/officer`)**: Field inspection workflow, violation ticketing, radar map.
   - **Administrator (`/admin`)**: System analytics, rule versions management, and user accounts.

---

## 🚀 One-Click Quick Setup (Windows)

The repository includes pre-built batch scripts for fully automated setup and execution.

### Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.10 to 3.14+** (Python 3.14.2 fully supported!)
  - *Make sure to check "Add Python to PATH" during installation.*
- **Node.js** (v18 or higher) from [https://nodejs.org/](https://nodejs.org/)

### Step 1: Run Automated Setup
Simply double-click:
```bat
SETUP.bat
```
*(Or run `.\SETUP.bat` in Command Prompt / PowerShell).*

**What `SETUP.bat` does automatically:**
1. Checks Python and Node.js environments.
2. Installs all required Python backend dependencies.
3. Automatically configures the native Windows OCR engine (`winocr`).
4. Creates and seeds the SQLite database (`backend/test.db`) with 13 verified statutory rules and 4 authentic role-based accounts.
5. Installs frontend NPM packages and compiles production assets.

---

### Step 2: Start the Application
Double-click:
```bat
START_SERVERS.bat
```
This will automatically launch:
- **Backend Server** on `http://localhost:8001` (and `0.0.0.0:8001`)
- **Frontend Vite Server** on `http://localhost:5173` (and LAN IP for mobile access)

---

## 🔑 Authentic Role Login Credentials

| Role | Email | Password | Access Portal |
|---|---|---|---|
| **Citizen / Public** | `citizen@maars.gov.in` | `citizen123` | `http://localhost:5173/customer` |
| **Retailer / Store** | `retailer@store.in` | `retailer123` | `http://localhost:5173/retailer` |
| **Legal Officer** | `officer@maars.gov.in` | `officer123` | `http://localhost:5173/officer` |
| **National Admin** | `admin@maars.gov.in` | `admin123` | `http://localhost:5173/admin` |

---

## 🛠️ Manual Setup Instructions (Alternative)

If you prefer setting up via terminal:

### 1. Backend Setup
```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install winocr

# Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 📂 Project Architecture

```
maars-lens/
├── SETUP.bat                  # One-click automated setup & installer
├── START_SERVERS.bat          # One-click server launcher (Backend + Frontend)
├── README.md                  # System documentation & usage guide
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI main application
│   │   ├── core/              # Database, JWT auth, and statutory rules config
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── routers/           # Customer, Officer, Admin, Retailer API routes
│   │   └── services/          # OCR engines (winocr), rule evaluator, radar map
│   └── requirements.txt       # Python dependencies (Python 3.10 - 3.14+)
└── frontend/
    ├── src/
    │   ├── pages/             # Customer, Officer, Retailer, and Admin dashboards
    │   ├── components/        # Multi-image picker, India radar map, cards
    │   └── api/               # Axios API client functions
    ├── package.json           # React 18, Vite, Tailwind CSS, Lucide icons
    └── vite.config.js
```

---

## 🏛️ Statutory Compliance Reference
Developed strictly adhering to:
- **The Legal Metrology Act, 2009 (No. 1 of 2010)**
- **The Legal Metrology (Packaged Commodities) Rules, 2011** (as amended)
- **FSSAI (Labelling & Display) Regulations, 2020**
