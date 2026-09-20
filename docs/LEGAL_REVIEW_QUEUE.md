# LEGAL REVIEW QUEUE — STATUTORY RULES & THRESHOLDS
## Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC) Compliance Verifications

**Document Version:** 1.0.0  
**Status:** Mandatory Legal Audit Queue (`needs_legal_review: true`)  
**Statutory Framework:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (including subsequent gazette amendments up to 2024).  
**Notice to Legal Counsel / Metrology Officers:**  
The algorithmic rules, citations, mathematical formulas, and thresholds listed in this document are encoded in `backend/app/core/statutory_rules.json` and evaluated deterministically by the MAARS Lens rule engine. All rules are flagged with `legal_verified: false` and `needs_legal_review: true`. Every item below requires official verification against the current Gazette of India notifications before deployment into sovereign enforcement environments.

---

### Item 1: Common or Generic Name of the Commodity
- **Current System Rule Code:** `LMPC-R6-GENERIC-NAME`
- **Current Citation in Code:** Legal Metrology (Packaged Commodities) Rules, 2011 — **Rule 6(1)(b)**
- **System Assumption / Logic:** Every package must bear the common or generic name of the commodity contained therein.
- **Applicability:** Applies to all retail packaged commodities unless explicitly exempted.
- **Gazette Verification Note for Counsel:** Confirm whether generic name falls under Rule 6(1)(b) while Month/Year of Manufacture is Rule 6(1)(c) or 6(1)(d) following the 2017 and 2021 LMPC Amendment orders.

### Item 2: Importer Identity and Country of Origin for Imported Packages
- **Current System Rule Code:** `LMPC-R6-IMPORTER-DETAILS` & `LMPC-R6-COUNTRY-OF-ORIGIN`
- **Current Citation in Code:** Rule 6(1)(a) & Rule 6(10) / Rule 6(1)(aa)
- **System Assumption / Logic:** For imported commodities, the package must prominently declare:
  1. The name and complete address of the importer.
  2. The name of the country of origin or manufacture.
  - If a package is flagged as imported (`is_imported: true` or containing foreign origin terms), absence of importer name/address is an automatic statutory violation.
- **Gazette Verification Note for Counsel:** Verify specific phrasing requirements for imported commodities under Gazette Notification G.S.R. 529(E) and circulars regarding e-commerce imports.

### Item 3: Dimensions and Number of Pieces (Where Applicable)
- **Current System Rule Code:** `LMPC-R6-DIMENSIONS-PIECES`
- **Current Citation in Code:** Rule 6(1)(f) / Rule 12 / Second Schedule
- **System Assumption / Logic:** Where goods are sold by number or size/dimensions (e.g. bedsheets, garments, paper, hardware, tiles), the size, dimensions, or total piece count (`pcs`, `units`, `cm x cm`) must be declared.
- **Applicability Condition:** Conditioned on commodity categories where piece count or dimensions are required by Schedule II.
- **Gazette Verification Note for Counsel:** Review commodity exemptions under the Second Schedule where declaration by weight or measure is alternative to count.

### Item 4: Multi-piece / Combi-Packs / Wholesale Package Declarations
- **Current System Rule Code:** `LMPC-R24-MULTI-PACK`
- **Current Citation in Code:** Rule 24 / Rule 2(r)
- **System Assumption / Logic:** On multi-piece packages or combination packs, the package must declare the total number of individual retail packs contained inside, individual net quantity of each pack, and aggregate MRP.
- **Applicability Condition:** Conditioned on `is_multi_pack: true` or `is_wholesale: true`.
- **Gazette Verification Note for Counsel:** Confirm statutory definition of "combination package" vs "group package" vs "multi-piece package" under Rule 24.

### Item 5: Consumer Redressal / Customer Care Declaration
- **Current System Rule Code:** `LMPC-R6-CONSUMER-CARE`
- **Current Citation in Code:** Rule 6(1)(da)
- **System Assumption / Logic:** System checks for: (1) name/designation of grievance contact, (2) complete address, (3) telephone / toll-free number, and (4) email address.
- **Gazette Verification Note for Counsel:** Confirm whether missing email alone constitutes a compoundable offence under Rule 32, or whether telephone + address satisfies compliance for small-scale local manufacturers.

### Item 6: Unit Sale Price (USP) Calculation and Rounding
- **Current System Rule Code:** `LMPC-R6-UNIT-SALE-PRICE`
- **Current Citation in Code:** Rule 6(11) (introduced via 2021 amendment)
- **System Assumption / Logic:**
  - USP = MRP / Net Quantity in standard metric units (Rs. per g/kg/ml/l/piece).
  - A statutory tolerance of 5.0% is allowed in the automated engine to account for rounding to two decimal places.
  - Exempts packages with net quantity <= 10g or <= 10ml.
- **Gazette Verification Note for Counsel:** Verify whether USP is mandatory for packages containing more than 1kg or 1litre, and exact rules for rounding (Rule 6(11) sub-clauses).

### Item 7: Minimum Height of Numerals & Letters (Rule 7 Table)
- **Current System Rule Code:** `LMPC-R7-FONT-SIZE`
- **Current Citation in Code:** Legal Metrology (Packaged Commodities) Rules, 2011 — **Rule 7 Table**
- **System Assumption / Logic:**
  - Net Qty <= 50g/ml: Minimum height 1.0mm (or 2.0mm if blown/formed/embossed).
  - Net Qty 50-200g/ml: Minimum height 2.0mm (or 4.0mm if embossed).
  - Net Qty 200-1000g/ml: Minimum height 4.0mm (or 6.0mm if embossed).
  - Net Qty > 1000g/ml: Minimum height 6.0mm.
  - System requires physical gauge / optical calibration; uncalibrated scans deterministically return `needs_review`.
- **Gazette Verification Note for Counsel:** Confirm the exact Schedule table heights for non-woven vs paper labels, and whether font height applies to all declarations or specifically to Net Quantity and MRP numerals.

### Item 8: Principal Display Panel (PDP) Surface Area Calculation (The 40% Area Figure)
- **Current System Parameter:** `pdp_surface_area_ratio`
- **Current Citation in Code:** Rule 6 / Rule 7 (Area of Principal Display Panel)
- **System Assumption / Logic:**
  - In rectangular containers: PDP is 40% of total height x width of the face.
  - In cylindrical containers: PDP is 40% of height x circumference of the container (40% x h x pi x d).
  - In other shapes: 20% of the total surface area.
- **Gazette Verification Note for Counsel:** Review whether 40% PDP rule mandates that all declarations reside exclusively within this area, or whether manufacturer address may appear on side/back panels under Rule 6(2).

### Item 9: Dual Pricing / Conflicting MRP Prohibition
- **Current System Rule Code:** `LMPC-R18-DUAL-MRP`
- **Current Citation in Code:** Rule 18(2) & Advisory on Dual MRP
- **System Assumption / Logic:** No commodity package shall bear more than one Maximum Retail Price. If distinct conflicting MRPs are identified on the packaging (e.g. overstickered price without statutory authority), the package is declared strictly `non_compliant`.
- **Gazette Verification Note for Counsel:** Review statutory exemptions under the Goods and Services Tax transition notifications where temporary dual-stickering was permitted under Commissioner approval.

### Item 10: Permitted Standard Units of Weight and Measure
- **Current System Rule Code:** `LMPC-R13-PERMITTED-UNITS`
- **Current Citation in Code:** Rule 13 — Units of weight or measure to be used for declarations
- **System Assumption / Logic:**
  - Permitted standard symbols: Weight -> `g`, `kg`, `mg`; Volume -> `ml`, `l`, `L`; Length -> `cm`, `m`, `mm`; Count -> `N`, `U`, `pieces`, `units`.
  - Strictly non-permitted units: Imperial units (`oz`, `lbs`, `fluid oz`), non-standard symbols (`gms`, `kgs`, `gm`, `kilo`, `ltr`, `ct`).
  - Presence of non-permitted units flags a statutory infraction.
- **Gazette Verification Note for Counsel:** Confirm permitted use of bracketed equivalent declarations (e.g. metric primary with imperial secondary).
