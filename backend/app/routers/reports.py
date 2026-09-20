"""
MAARS Lens: Reports Router
===========================
Handles generation, retrieval, and cryptographic verification of inspection reports.
Enforces:
- Role-based authorization (officer or admin).
- Inspection existence (404 if not found).
- Inspection finalization guard: unfinalized inspections cannot generate a PDF, summary, or report hash (returns 400).
- Strict privacy audit: summary response body excludes officer internal identifiers, internal notes,
  retailer private data, customer complaint text, customer GPS, or raw signature assets.
- Cryptographic verification: recomputes canonical SHA-256 report hash from current database state
  and verifies against stored inspection.report_hash without exposing internal content.
"""

import uuid
from typing import List, Optional
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.enums import UserRole, ComplianceStatus, AuditResultType
from app.models.inspection import Inspection
from app.models.audit import AuditResult
from app.services.pdf.generator import (
    generate_report_pdf,
    generate_report_docx,
    generate_report_xlsx,
    compute_report_hash,
)

router = APIRouter(prefix="", tags=["reports"])


def require_officer_or_admin(user: dict = Depends(get_current_user)) -> dict:
    """Ensures caller has officer or admin privileges."""
    user_role = (
        user.get("user_metadata", {}).get("role")
        or user.get("app_metadata", {}).get("role")
        or user.get("role", "customer")
    )
    if user_role not in (UserRole.officer, UserRole.admin, "officer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions: officer or admin role required.",
        )
    return user



# ------------------------------------------------------------------------------
# Privacy-safe Response Schemas (Strictly audited)
# ------------------------------------------------------------------------------
class AuditResultSummaryItem(BaseModel):
    """
    Public/officer-facing audit result summary item.
    Excludes internal officer UUIDs, internal reviewer details, or raw coordinates.
    """
    model_config = ConfigDict(from_attributes=True)

    rule_code: str
    statutory_reference: str
    automated_result: AuditResultType
    manual_review_result: Optional[AuditResultType] = None
    effective_result: AuditResultType


class InspectionReportSummaryResponse(BaseModel):
    """
    Sanitized inspection summary report.
    LOCKED PRIVACY REQUIREMENT:
    Does NOT include:
    - officer_id or internal officer info
    - retailer private information
    - customer complaint text
    - customer/officer GPS coordinates
    - internal investigation notes (officer_notes)
    - raw signature assets or tokens
    """
    model_config = ConfigDict(from_attributes=True)

    inspection_id: uuid.UUID
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    automated_compliance: Optional[ComplianceStatus] = None
    final_compliance: Optional[ComplianceStatus] = None
    is_finalized: bool
    finalized_at: Optional[datetime] = None
    report_hash: Optional[str] = None
    audit_results: List[AuditResultSummaryItem]


class ReportVerificationResponse(BaseModel):
    """
    Cryptographic report verification response.
    Validates integrity without exposing internal operational content.
    """
    model_config = ConfigDict(from_attributes=True)

    valid: bool
    report_hash: Optional[str] = None


# ------------------------------------------------------------------------------
# 1. GET /api/v1/reports/{inspection_id}/pdf
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/pdf")
async def get_report_pdf(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Generates and streams the official inspection report PDF.
    - Requires officer or admin role.
    - 404 if inspection does not exist.
    - 400 if inspection is not yet finalized (is_finalized == False).
    """
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found.",
        )

    if not inspection.is_finalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate report PDF for unfinalized inspection. Inspection must be finalized first.",
        )

    # Fetch associated audit results to include in canonical report payload
    stmt = (
        select(AuditResult)
        .where(AuditResult.inspection_id == inspection_id)
        .order_by(AuditResult.rule_code.asc())
    )
    audit_results = (await db.execute(stmt)).scalars().all()

    inspection_payload = {
        "id": str(inspection.id),
        "client_submission_id": str(inspection.client_submission_id),
        "officer_id": str(inspection.officer_id),
        "product_name": inspection.product_name,
        "brand_name": inspection.brand_name,
        "automated_compliance": inspection.automated_compliance.value if inspection.automated_compliance else None,
        "final_compliance": inspection.final_compliance.value if inspection.final_compliance else None,
        "report_hash": inspection.report_hash,
        "audit_results": [
            {
                "rule_code": ar.rule_code,
                "statutory_reference": ar.statutory_reference,
                "automated_result": ar.automated_result.value if hasattr(ar.automated_result, "value") else str(ar.automated_result),
                "manual_review_result": ar.manual_review_result.value if ar.manual_review_result and hasattr(ar.manual_review_result, "value") else (str(ar.manual_review_result) if ar.manual_review_result else None),
                "effective_result": ar.effective_result.value if hasattr(ar.effective_result, "value") else str(ar.effective_result),
            }
            for ar in audit_results
        ],
    }

    pdf_bytes = generate_report_pdf(inspection_payload)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{inspection_id}.pdf"},
    )


# ------------------------------------------------------------------------------
# 2. GET /api/v1/reports/{inspection_id}/summary
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/summary", response_model=InspectionReportSummaryResponse)
async def get_report_summary(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Returns a sanitized inspection report summary.
    - Requires officer or admin role.
    - 404 if inspection does not exist.
    - 400 if inspection is not yet finalized.
    - Strictly audited: excludes officer identity, internal notes, retailer private data,
      customer GPS/notes, or raw signature assets.
    """
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found.",
        )

    if not inspection.is_finalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retrieve summary for unfinalized inspection. Inspection must be finalized first.",
        )

    stmt = (
        select(AuditResult)
        .where(AuditResult.inspection_id == inspection_id)
        .order_by(AuditResult.rule_code.asc())
    )
    audit_results = (await db.execute(stmt)).scalars().all()

    return InspectionReportSummaryResponse(
        inspection_id=inspection.id,
        product_name=inspection.product_name,
        brand_name=inspection.brand_name,
        automated_compliance=inspection.automated_compliance,
        final_compliance=inspection.final_compliance,
        is_finalized=inspection.is_finalized,
        finalized_at=inspection.finalized_at,
        report_hash=inspection.report_hash,
        audit_results=[
            AuditResultSummaryItem(
                rule_code=ar.rule_code,
                statutory_reference=ar.statutory_reference,
                automated_result=ar.automated_result,
                manual_review_result=ar.manual_review_result,
                effective_result=ar.effective_result,
            )
            for ar in audit_results
        ],
    )


# ------------------------------------------------------------------------------
# 3. GET /api/v1/reports/{inspection_id}/verify
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/verify", response_model=ReportVerificationResponse)
async def verify_report(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Cryptographically verifies an inspection report.
    - Requires officer or admin role.
    - 404 if inspection does not exist.
    - 400 if inspection is not yet finalized.
    - Recomputes compute_report_hash() against the current canonical database state
      and compares against stored inspection.report_hash.
    - Returns {'valid': True/False, 'report_hash': '...'} without exposing internal content.
    """
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found.",
        )

    if not inspection.is_finalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot verify unfinalized inspection.",
        )

    stmt = (
        select(AuditResult)
        .where(AuditResult.inspection_id == inspection_id)
        .order_by(AuditResult.rule_code.asc())
    )
    audit_results = (await db.execute(stmt)).scalars().all()

    canonical_payload = {
        "id": str(inspection.id),
        "client_submission_id": str(inspection.client_submission_id),
        "officer_id": str(inspection.officer_id),
        "product_name": inspection.product_name,
        "brand_name": inspection.brand_name,
        "automated_compliance": inspection.automated_compliance.value if inspection.automated_compliance else None,
        "final_compliance": inspection.final_compliance.value if inspection.final_compliance else None,
        "audit_results": [
            {
                "rule_code": ar.rule_code,
                "statutory_reference": ar.statutory_reference,
                "automated_result": ar.automated_result.value if hasattr(ar.automated_result, "value") else str(ar.automated_result),
                "manual_review_result": ar.manual_review_result.value if ar.manual_review_result and hasattr(ar.manual_review_result, "value") else (str(ar.manual_review_result) if ar.manual_review_result else None),
                "effective_result": ar.effective_result.value if hasattr(ar.effective_result, "value") else str(ar.effective_result),
            }
            for ar in audit_results
        ],
    }

    recomputed_hash = compute_report_hash(canonical_payload)
    is_valid = bool(inspection.report_hash and inspection.report_hash == recomputed_hash)

    return ReportVerificationResponse(
        valid=is_valid,
        report_hash=inspection.report_hash,
    )


# ------------------------------------------------------------------------------
# 4. GET /api/v1/reports/{inspection_id}/docx
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/docx")
async def get_report_docx(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """Generates and streams the official inspection report Word DOCX document."""
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")

    if not inspection.is_finalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate report for unfinalized inspection.")

    stmt = select(AuditResult).where(AuditResult.inspection_id == inspection_id).order_by(AuditResult.rule_code.asc())
    audit_results = (await db.execute(stmt)).scalars().all()

    payload = {
        "id": str(inspection.id),
        "officer_id": str(inspection.officer_id),
        "product_name": inspection.product_name,
        "brand_name": inspection.brand_name,
        "final_compliance": inspection.final_compliance.value if inspection.final_compliance else None,
        "report_hash": inspection.report_hash,
        "audit_results": [
            {
                "rule_code": ar.rule_code,
                "statutory_reference": ar.statutory_reference,
                "automated_result": ar.automated_result.value if hasattr(ar.automated_result, "value") else str(ar.automated_result),
                "manual_review_result": ar.manual_review_result.value if ar.manual_review_result and hasattr(ar.manual_review_result, "value") else (str(ar.manual_review_result) if ar.manual_review_result else None),
                "effective_result": ar.effective_result.value if hasattr(ar.effective_result, "value") else str(ar.effective_result),
            }
            for ar in audit_results
        ],
    }

    docx_bytes = generate_report_docx(payload)
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=report_{inspection_id}.docx"},
    )


# ------------------------------------------------------------------------------
# 5. GET /api/v1/reports/{inspection_id}/xlsx
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/xlsx")
async def get_report_xlsx(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """Generates and streams the official inspection report Excel XLSX workbook."""
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")

    if not inspection.is_finalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate report for unfinalized inspection.")

    stmt = select(AuditResult).where(AuditResult.inspection_id == inspection_id).order_by(AuditResult.rule_code.asc())
    audit_results = (await db.execute(stmt)).scalars().all()

    payload = {
        "id": str(inspection.id),
        "officer_id": str(inspection.officer_id),
        "product_name": inspection.product_name,
        "brand_name": inspection.brand_name,
        "final_compliance": inspection.final_compliance.value if inspection.final_compliance else None,
        "report_hash": inspection.report_hash,
        "audit_results": [
            {
                "rule_code": ar.rule_code,
                "statutory_reference": ar.statutory_reference,
                "automated_result": ar.automated_result.value if hasattr(ar.automated_result, "value") else str(ar.automated_result),
                "manual_review_result": ar.manual_review_result.value if ar.manual_review_result and hasattr(ar.manual_review_result, "value") else (str(ar.manual_review_result) if ar.manual_review_result else None),
                "effective_result": ar.effective_result.value if hasattr(ar.effective_result, "value") else str(ar.effective_result),
            }
            for ar in audit_results
        ],
    }

    xlsx_bytes = generate_report_xlsx(payload)
    return StreamingResponse(
        BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=report_{inspection_id}.xlsx"},
    )


# ------------------------------------------------------------------------------
# 6. GET /api/v1/reports/summary (Aggregate Summary Filtered by Dates and Status)
# ------------------------------------------------------------------------------
@router.get("/summary/export")
async def export_summary_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    compliance_status: Optional[ComplianceStatus] = None,
    format: str = "xlsx",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Exports aggregate summary report across multiple inspections filtered by date range and status.
    Format can be 'xlsx' or 'json'.
    """
    stmt = select(Inspection).order_by(Inspection.created_at.desc())
    if start_date:
        stmt = stmt.where(Inspection.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Inspection.created_at <= end_date)
    if compliance_status:
        stmt = stmt.where(Inspection.final_compliance == compliance_status)

    result = await db.execute(stmt)
    inspections = result.scalars().all()

    if format == "json":
        return [
            {
                "inspection_id": i.id,
                "product_name": i.product_name,
                "brand_name": i.brand_name,
                "status": i.status,
                "automated_compliance": i.automated_compliance,
                "final_compliance": i.final_compliance,
                "is_finalized": i.is_finalized,
                "created_at": i.created_at,
            }
            for i in inspections
        ]

    # Default: Excel export
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary Report"

    ws["A1"] = "MAARS LENS — COMPLIANCE SUMMARY REPORT"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)

    headers = ["Inspection ID", "Product", "Brand", "Status", "Automated", "Final Compliance", "Finalized", "Created At"]
    header_fill = PatternFill(start_color="CBD5E1", end_color="CBD5E1", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True)

    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    for r_idx, insp in enumerate(inspections, start=4):
        ws.cell(row=r_idx, column=1, value=str(insp.id))
        ws.cell(row=r_idx, column=2, value=insp.product_name or "N/A")
        ws.cell(row=r_idx, column=3, value=insp.brand_name or "N/A")
        ws.cell(row=r_idx, column=4, value=str(insp.status))
        ws.cell(row=r_idx, column=5, value=str(insp.automated_compliance or "N/A"))
        ws.cell(row=r_idx, column=6, value=str(insp.final_compliance or "N/A"))
        ws.cell(row=r_idx, column=7, value="Yes" if insp.is_finalized else "No")
        ws.cell(row=r_idx, column=8, value=insp.created_at.strftime("%Y-%m-%d %H:%M"))

    for col_letter in ["A", "B", "C", "D", "E", "F", "G", "H"]:
        ws.column_dimensions[col_letter].width = 20

    out = BytesIO()
    wb.save(out)
    return StreamingResponse(
        BytesIO(out.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inspections_summary.xlsx"},
    )

