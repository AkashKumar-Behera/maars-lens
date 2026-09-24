import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models import CustomerReport, Product
from app.models.enums import UserRole, AuditResultType, ComplianceStatus
from app.services.ocr.multi_image import validate_and_hash_image, save_image_to_storage, process_and_merge_panels
from app.services.rule_engine.engine import run_audit
from app.services.compliance import aggregate_compliance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["customers"])


@router.post("/scan")
async def scan_product_label(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
    panel_types: Optional[str] = Form(None), # JSON string or comma-separated list of panel types
    panel_type: Optional[str] = Form("front"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer, UserRole.retailer, UserRole.officer, UserRole.admin)),
):
    """
    Consumer Real-Time Product Label Scan & Compliance Audit.
    Supports 1 mandatory image + up to 4 additional optional images (5 total package faces).
    Merges OCR extracted facts across all submitted panels.
    """
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend([f for f in files if f and f.filename])
    if file and file.filename and file not in upload_list:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload at least 1 commodity package image (e.g. Front / MRP Panel).",
        )

    scan_id = uuid.uuid4()
    panel_inputs = []

    # Parse panel types
    parsed_types = ["front", "back", "side", "top", "other"]
    if panel_types:
        try:
            import json
            pt_data = json.loads(panel_types)
            if isinstance(pt_data, list):
                parsed_types = [str(x).lower() for x in pt_data]
        except Exception:
            parsed_types = [x.strip().lower() for x in panel_types.split(",")]

    for idx, uf in enumerate(upload_list[:5]): # Maximum 5 images
        file_bytes = await uf.read()
        if not file_bytes:
            continue

        try:
            sha256, mime, size = validate_and_hash_image(file_bytes)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image {idx+1} ({uf.filename}) error: {str(e)}",
            )

        img_id = uuid.uuid4()
        ext = ".png" if "png" in mime else (".webp" if "webp" in mime else ".jpg")
        filename = f"{scan_id}_panel_{idx}_{img_id}{ext}"
        save_image_to_storage(file_bytes, scan_id, filename)

        ptype = parsed_types[idx] if idx < len(parsed_types) else (panel_type or "front").lower()
        panel_inputs.append({
            "panel_type": ptype,
            "file_bytes": file_bytes,
            "image_id": img_id,
        })

    if not panel_inputs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image files are empty. Please select valid product images.",
        )

    try:
        merged_result = process_and_merge_panels(panel_inputs, scan_id)
    except Exception as exc:
        logger.error("Consumer scan OCR processing failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing failed: {str(exc)}",
        )

    extracted_facts = merged_result.get("merged_facts", {})
    ocr_confidences = merged_result.get("per_field_confidences", {})
    overall_confidence = merged_result.get("overall_confidence", 0.0)
    raw_text = merged_result.get("raw_text", "")

    # Run the real statutory compliance audit engine
    try:
        audit_evals = await run_audit(
            facts=extracted_facts,
            visual_measurements=None,
            ocr_confidences=ocr_confidences,
            db=db,
        )
    except Exception as exc:
        logger.error("Consumer scan statutory rule evaluation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance evaluation failed: {str(exc)}",
        )

    # Compute overall compliance status
    automated_results = [ev.get("automated_result") for ev in audit_evals if ev.get("automated_result") is not None]
    overall_status = aggregate_compliance(automated_results)

    # Separate violations, warnings, and passed checks
    violations: List[Dict[str, Any]] = []
    checks: List[Dict[str, Any]] = []

    for ev in audit_evals:
        res_val = ev["automated_result"].value if hasattr(ev["automated_result"], "value") else str(ev["automated_result"])
        check_item = {
            "rule_code": ev["rule_code"],
            "statutory_reference": ev["statutory_reference"],
            "result": res_val,
            "actual_value": ev.get("actual_value"),
            "expected_value": ev.get("expected_value"),
            "reason": ev.get("automated_reason", ""),
            "severity": ev["severity"].value if hasattr(ev["severity"], "value") else str(ev["severity"]),
        }
        checks.append(check_item)

        if res_val in ("fail", "needs_review"):
            violations.append(check_item)

    # Clean display facts (remove internal keys)
    display_facts = {k: v for k, v in extracted_facts.items() if not k.startswith("_")}

    return {
        "scan_id": scan_id,
        "status": overall_status.value if hasattr(overall_status, "value") else str(overall_status),
        "compliance_status": overall_status.value if hasattr(overall_status, "value") else str(overall_status),
        "ocr_confidence_overall": overall_confidence,
        "raw_text": raw_text,
        "extracted_facts": display_facts,
        "violations": violations,
        "checks": checks,
        "summary": {
            "total_rules_evaluated": len(audit_evals),
            "passed_count": sum(1 for c in checks if c["result"] == "pass"),
            "violations_count": sum(1 for c in checks if c["result"] == "fail"),
            "review_count": sum(1 for c in checks if c["result"] == "needs_review"),
        },
    }


@router.post("/reports")
async def create_report(
    image: UploadFile = File(...),
    description: str = Form(...),
    product_name: Optional[str] = Form(None),
    area_id: Optional[uuid.UUID] = Form(None),
    gps_coordinates: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer))
):
    cust_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        customer_uuid = uuid.UUID(str(cust_id_raw))
    except (ValueError, TypeError):
        customer_uuid = uuid.UUID("a0000000-0000-0000-0000-000000000004")

    image_url = f"uploads/customer_reports/{uuid.uuid4()}_{image.filename}"
    
    report = CustomerReport(
        id=uuid.uuid4(),
        customer_id=customer_uuid,
        image_storage_path=image_url,
        description=description,
        product_name=product_name,
        area_id=area_id,
        status="pending"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return {"report_id": report.id}


@router.get("/reports")
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer))
):
    cust_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        customer_uuid = uuid.UUID(str(cust_id_raw))
    except (ValueError, TypeError):
        customer_uuid = uuid.UUID("a0000000-0000-0000-0000-000000000004")

    result = await db.execute(select(CustomerReport).where(CustomerReport.customer_id == customer_uuid))
    return result.scalars().all()


@router.get("/reports/{report_id}")
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer))
):
    cust_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        customer_uuid = uuid.UUID(str(cust_id_raw))
    except (ValueError, TypeError):
        customer_uuid = uuid.UUID("a0000000-0000-0000-0000-000000000004")

    report = await db.get(CustomerReport, report_id)
    if not report or report.customer_id != customer_uuid:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


from pydantic import BaseModel
from app.models.user import RoleApplication, Profile as UserProfile


class RoleApplicationSubmitRequest(BaseModel):
    requested_role: UserRole
    badge_number: Optional[str] = None
    department: Optional[str] = None
    business_name: Optional[str] = None
    license_number: Optional[str] = None
    shop_address: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


@router.post("/role-application")
async def submit_role_application(
    payload: RoleApplicationSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer))
):
    """
    Submits a role elevation accreditation application for the authenticated customer/user.
    Valid requested roles: officer or retailer.
    """
    if payload.requested_role not in [UserRole.officer, UserRole.retailer]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role elevation is only permissible towards 'officer' or 'retailer' designations."
        )

    cust_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        user_uuid = uuid.UUID(str(cust_id_raw))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user session ID.")

    # Check if a pending application already exists
    pending_res = await db.execute(
        select(RoleApplication).where(
            RoleApplication.user_id == user_uuid,
            RoleApplication.status == "pending"
        )
    )
    if pending_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active role elevation application pending administrative review."
        )

    application = RoleApplication(
        id=uuid.uuid4(),
        user_id=user_uuid,
        requested_role=payload.requested_role,
        status="pending",
        badge_number=payload.badge_number,
        department=payload.department,
        business_name=payload.business_name,
        license_number=payload.license_number,
        shop_address=payload.shop_address,
        phone=payload.phone,
        notes=payload.notes
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)

    return {
        "message": "Role elevation application submitted successfully for administrator review.",
        "application_id": str(application.id),
        "status": application.status,
        "requested_role": application.requested_role.value
    }


@router.get("/role-application/me")
async def get_my_role_application(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer))
):
    """
    Retrieves the latest role elevation application for the authenticated user.
    """
    cust_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        user_uuid = uuid.UUID(str(cust_id_raw))
    except (ValueError, TypeError):
        return {"has_application": False}

    res = await db.execute(
        select(RoleApplication)
        .where(RoleApplication.user_id == user_uuid)
        .order_by(RoleApplication.created_at.desc())
    )
    app_record = res.scalars().first()
    if not app_record:
        return {"has_application": False}

    return {
        "has_application": True,
        "id": str(app_record.id),
        "requested_role": app_record.requested_role.value,
        "status": app_record.status,
        "badge_number": app_record.badge_number,
        "department": app_record.department,
        "business_name": app_record.business_name,
        "shop_address": app_record.shop_address,
        "license_number": app_record.license_number,
        "notes": app_record.notes,
        "admin_remarks": app_record.admin_remarks,
        "created_at": app_record.created_at.isoformat() if app_record.created_at else None,
        "reviewed_at": app_record.reviewed_at.isoformat() if app_record.reviewed_at else None
    }

