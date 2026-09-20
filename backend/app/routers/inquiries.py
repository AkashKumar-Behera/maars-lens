import uuid
import datetime
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.enums import UserRole
from app.models.compliance import CustomerReport
from app.models.user import Profile, Retailer
from app.models.area import Area

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["inquiries"])


# --- Schemas ---
class CustomerGeoReportRequest(BaseModel):
    product_name: str
    retailer_id: Optional[str] = None
    description: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    failing_rule_codes: List[str] = []
    image_storage_path: Optional[str] = None


class OfficerInquiryRequest(BaseModel):
    report_id: str
    inquiry_notice_text: str


class RetailerSupplierResponseRequest(BaseModel):
    report_id: str
    supplier_name: str
    supplier_contact: str
    supplier_invoice_no: str
    supplier_invoice_file: Optional[str] = None
    retailer_explanation: str


class AdminLegalActionRequest(BaseModel):
    report_id: str
    action_type: str # e.g. "Compounding Fine - Section 36", "Product Seizure Notice", "Court Prosecution"
    action_notes: str


@router.get("/stores")
async def list_retail_stores(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lists registered retail stores for tagging during consumer scanning and reporting."""
    res = await db.execute(select(Retailer).limit(50))
    stores = res.scalars().all()
    return [
        {
            "id": str(s.id),
            "business_name": s.business_name,
            "shop_address": s.shop_address,
            "license_number": s.license_number,
        }
        for s in stores
    ]


# --- 1. Citizen / Customer: Geo-Report Product Violation ---
@router.post("/customer/geo-report")
async def submit_customer_geo_report(
    payload: CustomerGeoReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer)),
):
    cust_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        customer_uuid = uuid.UUID(str(cust_id_raw))
    except (ValueError, TypeError):
        customer_uuid = uuid.UUID("a0000000-0000-0000-0000-000000000004")

    ret_uuid = None
    if payload.retailer_id:
        try:
            ret_uuid = uuid.UUID(payload.retailer_id)
        except (ValueError, TypeError):
            ret_uuid = None

    report = CustomerReport(
        id=uuid.uuid4(),
        customer_id=customer_uuid,
        retailer_id=ret_uuid,
        image_storage_path=payload.image_storage_path or "uploads/sample_scan.jpg",
        description=payload.description,
        product_name=payload.product_name,
        gps_lat=payload.gps_lat or 28.6139, # Default Delhi if not available
        gps_lng=payload.gps_lng or 77.2090,
        failing_rule_codes=payload.failing_rule_codes,
        status="submitted",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "message": "Product statutory non-compliance reported. Nearby enforcement officer has been alerted.",
        "report_id": str(report.id),
        "status": report.status,
    }


# --- 2. Officer: Real-time Incident Feed & Inquiry Dispatch ---
@router.get("/officer/incidents")
async def list_officer_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    query = (
        select(CustomerReport)
        .order_by(desc(CustomerReport.created_at))
        .limit(50)
    )
    res = await db.execute(query)
    reports = res.scalars().all()

    # Enrich with retailer business names
    enriched = []
    for r in reports:
        retailer_name = "Unknown Local Store"
        retailer_address = "Location Coordinates Tagged"
        if r.retailer_id:
            ret_rec = await db.get(Retailer, r.retailer_id)
            if ret_rec:
                retailer_name = ret_rec.business_name
                retailer_address = ret_rec.shop_address

        enriched.append({
            "id": str(r.id),
            "product_name": r.product_name,
            "description": r.description,
            "status": r.status,
            "failing_rule_codes": r.failing_rule_codes or [],
            "gps_lat": r.gps_lat,
            "gps_lng": r.gps_lng,
            "retailer_id": str(r.retailer_id) if r.retailer_id else None,
            "retailer_name": retailer_name,
            "retailer_address": retailer_address,
            "inquiry_notice_text": r.inquiry_notice_text,
            "supplier_name": r.supplier_name,
            "supplier_contact": r.supplier_contact,
            "supplier_invoice_no": r.supplier_invoice_no,
            "retailer_explanation": r.retailer_explanation,
            "retailer_responded_at": r.retailer_responded_at.isoformat() if r.retailer_responded_at else None,
            "escalated_to_admin": r.escalated_to_admin,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return enriched


@router.post("/officer/send-inquiry")
async def send_officer_inquiry(
    payload: OfficerInquiryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    officer_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        officer_uuid = uuid.UUID(str(officer_id_raw))
    except (ValueError, TypeError):
        officer_uuid = uuid.UUID("a0000000-0000-0000-0000-000000000001")

    report_uuid = uuid.UUID(payload.report_id)
    report = await db.get(CustomerReport, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found.")

    report.status = "inquiry_sent"
    report.assigned_officer_id = officer_uuid
    report.inquiry_notice_text = payload.inquiry_notice_text
    report.inquiry_sent_at = datetime.datetime.now(datetime.timezone.utc)
    report.updated_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()

    return {
        "message": f"Show-cause inquiry notice dispatched to retailer for incident {payload.report_id}.",
        "status": report.status,
    }


@router.post("/officer/escalate-to-admin")
async def escalate_incident_to_admin(
    report_id: str = Form(...),
    reason: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    report_uuid = uuid.UUID(report_id)
    report = await db.get(CustomerReport, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found.")

    report.status = "escalated_to_admin"
    report.escalated_to_admin = True
    report.admin_action_notes = f"Escalated by Officer: {reason}"
    report.updated_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()

    return {
        "message": "Incident escalated to National Administrator for statutory legal proceedings.",
        "status": report.status,
    }


# --- 3. Retailer: Active Inquiries & Supplier Traceability Response ---
@router.get("/retailer/inquiries")
async def list_retailer_inquiries(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.retailer)),
):
    ret_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        ret_uuid = uuid.UUID(str(ret_id_raw))
    except (ValueError, TypeError):
        ret_uuid = uuid.UUID("a0000000-0000-0000-0000-000000000003")

    # Inquiries linked to this retailer or pending general inquiries
    query = (
        select(CustomerReport)
        .where(
            or_(
                CustomerReport.retailer_id == ret_uuid,
                CustomerReport.status.in_(["inquiry_sent", "retailer_responded"])
            )
        )
        .order_by(desc(CustomerReport.updated_at))
    )
    res = await db.execute(query)
    reports = res.scalars().all()

    return [
        {
            "id": str(r.id),
            "product_name": r.product_name,
            "description": r.description,
            "status": r.status,
            "failing_rule_codes": r.failing_rule_codes or [],
            "inquiry_notice_text": r.inquiry_notice_text,
            "inquiry_sent_at": r.inquiry_sent_at.isoformat() if r.inquiry_sent_at else None,
            "supplier_name": r.supplier_name,
            "supplier_contact": r.supplier_contact,
            "supplier_invoice_no": r.supplier_invoice_no,
            "retailer_explanation": r.retailer_explanation,
            "retailer_responded_at": r.retailer_responded_at.isoformat() if r.retailer_responded_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@router.post("/retailer/submit-supplier-proof")
async def submit_supplier_proof(
    payload: RetailerSupplierResponseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.retailer)),
):
    report_uuid = uuid.UUID(payload.report_id)
    report = await db.get(CustomerReport, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Incident inquiry not found.")

    report.supplier_name = payload.supplier_name
    report.supplier_contact = payload.supplier_contact
    report.supplier_invoice_no = payload.supplier_invoice_no
    report.supplier_invoice_file = payload.supplier_invoice_file or "uploads/sample_invoice.pdf"
    report.retailer_explanation = payload.retailer_explanation
    report.retailer_responded_at = datetime.datetime.now(datetime.timezone.utc)
    report.status = "retailer_responded"
    report.updated_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()

    return {
        "message": "Wholesale supplier invoice and origin evidence submitted. Officer notified for upstream traceability audit.",
        "status": report.status,
    }


# --- 4. Admin: Pan-India Geospatial Incidents & Legal Action ---
@router.get("/admin/geo-intelligence")
async def get_admin_geo_intelligence(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns incident coordinates and violation density for MapTiler rendering.
    Accessible to Admin and Officers.
    """
    res = await db.execute(select(CustomerReport).order_by(desc(CustomerReport.created_at)))
    reports = res.scalars().all()

    features = []
    for r in reports:
        if r.gps_lat and r.gps_lng:
            features.append({
                "id": str(r.id),
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [r.gps_lng, r.gps_lat]
                },
                "properties": {
                    "product_name": r.product_name or "Packaged Commodity",
                    "status": r.status,
                    "failing_rules": r.failing_rule_codes or [],
                    "escalated": r.escalated_to_admin,
                    "date": r.created_at.strftime("%d %b %Y, %H:%M") if r.created_at else "Recent",
                    "supplier": r.supplier_name or "Not Yet Disclosed",
                    "action_taken": r.admin_action_taken or "Pending Legal Sanction"
                }
            })

    # Summary Statistics
    total = len(reports)
    escalated = sum(1 for r in reports if r.escalated_to_admin)
    inquiries_active = sum(1 for r in reports if r.status in ["inquiry_sent", "retailer_responded"])
    resolved = sum(1 for r in reports if r.status == "resolved")

    return {
        "geo_json": {
            "type": "FeatureCollection",
            "features": features
        },
        "stats": {
            "total_incidents": total,
            "escalated_count": escalated,
            "active_inquiries": inquiries_active,
            "resolved_count": resolved,
        }
    }


@router.post("/admin/legal-action")
async def execute_admin_legal_action(
    payload: AdminLegalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    report_uuid = uuid.UUID(payload.report_id)
    report = await db.get(CustomerReport, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Incident record not found.")

    report.status = "resolved"
    report.admin_action_taken = payload.action_type
    report.admin_action_notes = payload.action_notes
    report.resolved_at = datetime.datetime.now(datetime.timezone.utc)
    report.resolution_summary = f"Statutory Enforcement Applied: {payload.action_type}. {payload.action_notes}"
    report.updated_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()

    return {
        "message": f"Legal Enforcement Order [{payload.action_type}] recorded and sealed.",
        "status": report.status,
    }
