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
    file: UploadFile = File(...),
    panel_type: Optional[str] = Form("front"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.customer)),
):
    """
    Consumer Real-Time Product Label Scan & Compliance Audit.
    1. Validates magic bytes, format (JPEG/PNG/WebP), and size (<= 15MB).
    2. Persists image evidence under uploads/customer_scans/{id}.
    3. Runs PaddleOCR (multilingual EN/HI) with preprocessor and extracts packaged commodity facts.
    4. Evaluates all active statutory Legal Metrology rules via the statutory rule engine.
    5. Computes overall compliance verdict (compliant, non_compliant, needs_review) and returns
       structured, field-level violations and statutory references.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select a product image.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty. Please select a valid product image.",
        )

    try:
        sha256, mime, size = validate_and_hash_image(file_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    scan_id = uuid.uuid4()
    ext = ".png" if "png" in mime else (".webp" if "webp" in mime else ".jpg")
    filename = f"{scan_id}_consumer_scan{ext}"
    storage_path = save_image_to_storage(file_bytes, scan_id, filename)

    # Prepare single or multi-panel input for OCR processing pipeline
    panel_inputs = [{
        "panel_type": (panel_type or "front").lower(),
        "file_bytes": file_bytes,
        "image_id": scan_id,
    }]

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
