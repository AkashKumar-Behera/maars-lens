"""
MAARS Lens: Scans Router
========================
Handles officer scan uploads, manual review assessments, and tamper-evident finalization.
Enforces locked architectural constraints:
- Clients cannot submit automated_result, effective_result, automated_compliance, or final_compliance.
- assert_inspection_unfinalized() strictly guards against mutating finalized inspections.
- effective_result is computed server-side via compute_effective_result().
- manual_review_result cannot be not_applicable; manual_review_reason is mandatory.
- report_hash is computed and persisted via compute_report_hash().
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.core.ratelimit import limiter

from app.core.database import get_db
from app.core.auth import require_role
from app.models.enums import (
    UserRole,
    InspectionStatus,
    ComplianceStatus,
    AuditResultType,
    InspectionSource,
)
from app.models.inspection import Inspection, InspectionImage
from app.models.product import Product
from app.models.audit import AuditResult
from app.schemas.scan import (
    ScanUploadRequest,
    ScanUploadResponse,
    FinalizeRequest,
    FinalizeResponse,
    ManualReviewItem,
)
from app.services.compliance import (
    assert_inspection_unfinalized,
    compute_effective_result,
    compute_inspection_compliance,
    InspectionAlreadyFinalizedError,
    InvalidManualReviewError,
)
from app.services.pdf.generator import compute_report_hash
from app.services.ocr.multi_image import (
    validate_and_hash_image,
    save_image_to_storage,
    process_and_merge_panels,
)
from app.services.ocr.annotator import annotate_evidence_image
from app.services.rule_engine.engine import run_audit
from fastapi import File, UploadFile, Form


router = APIRouter(tags=["scans"])


class ManualReviewSubmissionRequest(BaseModel):
    """
    Officer manual review submission for an audit item.
    extra='forbid' strictly rejects any client-submitted automated_result,
    effective_result, automated_compliance, or final_compliance.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    rule_code: Optional[str] = None
    rule_version_id: Optional[uuid.UUID] = None
    manual_review_result: AuditResultType
    manual_review_reason: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_manual_review(self):
        if not self.rule_code and not self.rule_version_id:
            raise ValueError("Either rule_code or rule_version_id is required.")
        if self.manual_review_result == AuditResultType.not_applicable:
            raise ValueError("not_applicable is not an allowed manual review assessment.")
        if not self.manual_review_reason or not self.manual_review_reason.strip():
            raise ValueError("manual_review_reason is mandatory and cannot be empty or whitespace-only.")
        return self


# ------------------------------------------------------------------------------
# 1. POST /api/v1/scans/upload
# ------------------------------------------------------------------------------
@router.post("/upload", response_model=ScanUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_scan(
    payload: ScanUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """
    Accepts inspection scan input from an officer.
    Rejects automated_result, effective_result, automated_compliance, or final_compliance
    via ScanUploadRequest (extra='forbid').
    Persists the inspection record using SQLAlchemy models with offline idempotency.
    """
    # 1. Check idempotency key (client_submission_id)
    stmt = select(Inspection).where(Inspection.client_submission_id == payload.client_submission_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return ScanUploadResponse(
            inspection_id=existing.id,
            client_submission_id=existing.client_submission_id,
            status=existing.status,
            message="Inspection already uploaded (idempotent submission preserved).",
        )

    # 2. Extract officer identity
    officer_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        officer_uuid = uuid.UUID(str(officer_id_raw))
    except (ValueError, TypeError):
        officer_uuid = uuid.uuid4()

    # 3. Create inspection record
    inspection = Inspection(
        id=uuid.uuid4(),
        client_submission_id=payload.client_submission_id,
        officer_id=officer_uuid,
        area_id=payload.area_id,
        retailer_id=payload.retailer_id,
        product_name=payload.product_name,
        brand_name=payload.brand_name,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        image_storage_path=f"inspections/{payload.client_submission_id}/image.jpg",
        status=InspectionStatus.pending_quality_check,
        is_finalized=False,
    )

    db.add(inspection)
    await db.commit()
    await db.refresh(inspection)

    return ScanUploadResponse(
        inspection_id=inspection.id,
        client_submission_id=inspection.client_submission_id,
        status=inspection.status,
        message="Inspection scan uploaded successfully.",
    )


# ------------------------------------------------------------------------------
# 1b. POST /api/v1/scans/{inspection_id}/images (Multi-Panel Evidence Upload)
# ------------------------------------------------------------------------------
@router.post("/{inspection_id}/images", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def upload_inspection_images(
    request: Request,
    inspection_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    panel_types: Optional[List[str]] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """
    Accepts multiple label panel images for an inspection (e.g. front, back, side).
    - Validates magic bytes (JPEG/PNG/WebP).
    - Computes sha256 and isolates storage under UPLOAD_DIR / inspections / {id}.
    - Performs OCR across all panels and aggregates facts into inspection.extracted_facts.
    - Never overwrites original images.
    """
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")

    try:
        assert_inspection_unfinalized(inspection)
    except InspectionAlreadyFinalizedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    officer_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        officer_uuid = uuid.UUID(str(officer_id_raw))
    except (ValueError, TypeError):
        officer_uuid = inspection.officer_id

    uploaded_records: List[InspectionImage] = []
    panel_inputs: List[dict] = []

    for idx, upload_file in enumerate(files):
        file_bytes = await upload_file.read()
        try:
            sha256, mime, size = validate_and_hash_image(file_bytes)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File {upload_file.filename}: {str(e)}")

        ptype = (panel_types[idx] if panel_types and idx < len(panel_types) else "other").lower()
        img_id = uuid.uuid4()
        ext = ".png" if "png" in mime else (".webp" if "webp" in mime else ".jpg")
        filename = f"{img_id}_original{ext}"
        storage_path = save_image_to_storage(file_bytes, inspection_id, filename)

        img_record = InspectionImage(
            id=img_id,
            inspection_id=inspection_id,
            panel_type=ptype,
            storage_path=storage_path,
            sha256=sha256,
            mime=mime,
            size=size,
            uploaded_by=officer_uuid,
            original=True,
            parent_image_id=None,
        )
        db.add(img_record)
        uploaded_records.append(img_record)

        panel_inputs.append({
            "panel_type": ptype,
            "file_bytes": file_bytes,
            "image_id": img_id,
        })

    # Process OCR and merge across all panels
    merged_result = process_and_merge_panels(panel_inputs, inspection_id)

    inspection.extracted_facts = merged_result["merged_facts"]
    inspection.ocr_raw_text = merged_result["raw_text"]
    inspection.ocr_confidence_overall = merged_result["overall_confidence"]
    inspection.ocr_field_confidences = merged_result["per_field_confidences"]
    inspection.status = InspectionStatus.needs_review

    # Auto-link or create Product for repeat scan tracking
    brand = merged_result["merged_facts"].get("brand") or inspection.brand_name
    pname = merged_result["merged_facts"].get("commodity_name") or merged_result["merged_facts"].get("product_name") or inspection.product_name
    mfg = merged_result["merged_facts"].get("manufacturer_name")
    barcode = merged_result["merged_facts"].get("barcode")

    matched_product = None
    if barcode:
        p_stmt = select(Product).where(Product.barcode == barcode)
        matched_product = (await db.execute(p_stmt)).scalar_one_or_none()
    
    if not matched_product and brand and pname:
        p_stmt = select(Product).where(
            Product.brand_name.ilike(brand),
            Product.product_name.ilike(pname)
        )
        matched_product = (await db.execute(p_stmt)).scalars().first()

    if not matched_product and (barcode or (brand and pname)):
        matched_product = Product(
            id=uuid.uuid4(),
            brand_name=brand,
            product_name=pname,
            manufacturer_name=mfg,
            barcode=barcode,
        )
        db.add(matched_product)
        await db.flush()

    if matched_product:
        inspection.product_id = matched_product.id
        if brand:
            inspection.brand_name = brand
        if pname:
            inspection.product_name = pname

    # Run compliance rules on the newly merged facts
    audit_evals = await run_audit(
        facts=merged_result["merged_facts"],
        visual_measurements=inspection.visual_measurements,
        ocr_confidences=merged_result["per_field_confidences"],
        db=db,
    )

    # Delete previous audit evaluations for this inspection to prevent duplicate key errors
    await db.execute(delete(AuditResult).where(AuditResult.inspection_id == inspection_id))

    created_audits: List[AuditResult] = []
    for ev in audit_evals:
        ar = AuditResult(
            id=uuid.uuid4(),
            inspection_id=inspection_id,
            rule_version_id=ev["rule_version_id"],
            rule_code=ev["rule_code"],
            rule_version=ev["rule_version"],
            statutory_reference=ev["statutory_reference"],
            automated_result=ev["automated_result"],
            actual_value=ev.get("actual_value"),
            expected_value=ev.get("expected_value"),
            fact_confidence=ev.get("fact_confidence"),
            measurement_reliable=ev.get("measurement_reliable"),
            automated_reason=ev.get("automated_reason", ""),
            severity=ev["severity"],
            effective_result=ev["automated_result"],
        )
        db.add(ar)
        created_audits.append(ar)

    if created_audits:
        auto_comp, final_comp = compute_inspection_compliance(created_audits)
        inspection.automated_compliance = auto_comp
        inspection.final_compliance = final_comp

    await db.commit()
    await db.refresh(inspection)

    return {
        "inspection_id": inspection.id,
        "images_uploaded": len(uploaded_records),
        "panels": [
            {
                "image_id": rec.id,
                "panel_type": rec.panel_type,
                "storage_path": rec.storage_path,
                "sha256": rec.sha256,
                "size": rec.size,
            }
            for rec in uploaded_records
        ],
        "extracted_facts": inspection.extracted_facts,
        "ocr_confidence_overall": inspection.ocr_confidence_overall,
        "automated_compliance": inspection.automated_compliance,
        "final_compliance": inspection.final_compliance,
        "product_id": inspection.product_id,
        "status": inspection.status,
    }


# ------------------------------------------------------------------------------
# 1c. GET /api/v1/scans/{inspection_id}/images (List Inspection Evidence Images)
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/images")
async def list_inspection_images(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """Retrieves all evidence images and annotated variants for an inspection."""
    stmt = (
        select(InspectionImage)
        .where(InspectionImage.inspection_id == inspection_id)
        .order_by(InspectionImage.uploaded_at.asc())
    )
    result = await db.execute(stmt)
    images = result.scalars().all()

    return [
        {
            "id": img.id,
            "panel_type": img.panel_type,
            "storage_path": img.storage_path,
            "sha256": img.sha256,
            "mime": img.mime,
            "size": img.size,
            "original": img.original,
            "parent_image_id": img.parent_image_id,
            "uploaded_at": img.uploaded_at,
        }
        for img in images
    ]



# ------------------------------------------------------------------------------
# 2. POST /api/v1/scans/{id}/result (Manual Review Submission)
# ------------------------------------------------------------------------------
@router.post("/{inspection_id}/result")
async def submit_manual_review(
    inspection_id: uuid.UUID,
    payload: ManualReviewSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """
    Accepts a manual review submission from an officer.
    - Asserts unfinalized status BEFORE any write.
    - Rejects manual_review_result == not_applicable.
    - Rejects empty/whitespace manual_review_reason.
    - Computes effective_result server-side via compute_effective_result().
    - Recomputes automated_compliance and final_compliance via compute_inspection_compliance().
    """
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")

    # Guard: assert unfinalized
    try:
        assert_inspection_unfinalized(inspection)
    except InspectionAlreadyFinalizedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Cross-officer isolation: officer can only mutate draft inspections created by themselves
    caller_role = current_user.get("user_metadata", {}).get("role") or current_user.get("role")
    caller_id = str(current_user.get("id") or current_user.get("sub") or "")
    if caller_role == UserRole.officer and str(inspection.officer_id) != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-officer isolation: You cannot modify inspections initiated by another officer.",
        )

    # Reject not_applicable & empty reason (enforced at both schema and endpoint level)
    if payload.manual_review_result == AuditResultType.not_applicable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="not_applicable is not an allowed manual review assessment.",
        )
    if not payload.manual_review_reason or not payload.manual_review_reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="manual_review_reason is mandatory and cannot be empty or whitespace-only.",
        )

    # Locate target AuditResult
    stmt = select(AuditResult).where(AuditResult.inspection_id == inspection_id)
    if payload.rule_version_id:
        stmt = stmt.where(AuditResult.rule_version_id == payload.rule_version_id)
    elif payload.rule_code:
        stmt = stmt.where(AuditResult.rule_code == payload.rule_code)

    audit_item = (await db.execute(stmt)).scalar_one_or_none()
    if not audit_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit result for rule '{payload.rule_code or payload.rule_version_id}' not found.",
        )

    # Compute effective_result server-side (cannot be submitted by client)
    try:
        effective_res = compute_effective_result(
            automated_result=audit_item.automated_result,
            manual_review_result=payload.manual_review_result,
            manual_review_reason=payload.manual_review_reason.strip(),
        )
    except InvalidManualReviewError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    officer_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        officer_uuid = uuid.UUID(str(officer_id_raw))
    except (ValueError, TypeError):
        officer_uuid = inspection.officer_id

    # Update audit result
    audit_item.manual_review_result = payload.manual_review_result
    audit_item.manual_review_reason = payload.manual_review_reason.strip()
    audit_item.effective_result = effective_res
    audit_item.manual_reviewed_by = officer_uuid
    audit_item.manual_reviewed_at = datetime.now(timezone.utc)

    # Recompute compliance across all audit items
    stmt_all = select(AuditResult).where(AuditResult.inspection_id == inspection_id)
    all_res = (await db.execute(stmt_all)).scalars().all()

    auto_comp, final_comp = compute_inspection_compliance(all_res)
    inspection.automated_compliance = auto_comp
    inspection.final_compliance = final_comp

    await db.commit()
    await db.refresh(audit_item)
    await db.refresh(inspection)

    return {
        "inspection_id": inspection.id,
        "audit_result_id": audit_item.id,
        "rule_code": audit_item.rule_code,
        "automated_result": audit_item.automated_result,
        "manual_review_result": audit_item.manual_review_result,
        "manual_review_reason": audit_item.manual_review_reason,
        "effective_result": audit_item.effective_result,
        "automated_compliance": inspection.automated_compliance,
        "final_compliance": inspection.final_compliance,
        "message": "Manual review recorded and compliance recomputed successfully.",
    }


# ------------------------------------------------------------------------------
# 3. POST /api/v1/scans/{id}/finalize
# ------------------------------------------------------------------------------
@router.post("/{inspection_id}/finalize", response_model=FinalizeResponse)
async def finalize_scan(
    inspection_id: uuid.UUID,
    payload: FinalizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """
    Finalizes an inspection:
    - Calls assert_inspection_unfinalized() first.
    - Optionally applies manual reviews provided in payload.
    - Marks inspection finalized (immutable).
    - Computes and stores the SHA-256 report hash via compute_report_hash().
    """
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")

    # Guard: assert unfinalized FIRST
    try:
        assert_inspection_unfinalized(inspection)
    except InspectionAlreadyFinalizedError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Cross-officer isolation: officer can only finalize draft inspections created by themselves
    caller_role = current_user.get("user_metadata", {}).get("role") or current_user.get("role")
    caller_id = str(current_user.get("id") or current_user.get("sub") or "")
    if caller_role == UserRole.officer and str(inspection.officer_id) != caller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-officer isolation: You cannot finalize inspections initiated by another officer.",
        )

    # Recompute compliance across all audit items
    stmt_all = (
        select(AuditResult)
        .where(AuditResult.inspection_id == inspection_id)
        .order_by(AuditResult.rule_code.asc())
    )
    all_audit_results = (await db.execute(stmt_all)).scalars().all()

    auto_comp, final_comp = compute_inspection_compliance(all_audit_results)
    inspection.automated_compliance = auto_comp
    inspection.final_compliance = final_comp

    if payload.officer_notes:
        inspection.officer_notes = payload.officer_notes.strip()

    # Build canonical payload and compute SHA-256 report hash
    inspection_payload = {
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
            for ar in all_audit_results
        ],
    }

    report_hash = compute_report_hash(inspection_payload)
    inspection.report_hash = report_hash

    # Finalization locks - do NOT synthesize fake signature_id or signature_hash
    inspection.is_finalized = True
    inspection.finalized_at = datetime.now(timezone.utc)
    inspection.status = InspectionStatus.completed

    await db.commit()
    await db.refresh(inspection)

    return FinalizeResponse(
        inspection_id=inspection.id,
        status=inspection.status,
        automated_compliance=inspection.automated_compliance,
        final_compliance=inspection.final_compliance,
        is_finalized=inspection.is_finalized,
        finalized_at=inspection.finalized_at,
        report_hash=inspection.report_hash,
        signature_id=inspection.signature_id,
        signature_hash=inspection.signature_hash_at_finalization,
        violation_id=None,
        notifications_sent=[],
        pdf_url=f"/api/v1/reports/{inspection.id}/pdf",
    )


# ------------------------------------------------------------------------------
# 4. GET /api/v1/scans/{id}/result (Retrieve Scan Details & Audit Results)
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}/result")
async def get_scan_result(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """Retrieves full inspection details and associated audit results."""
    inspection = await db.get(Inspection, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found.")

    stmt = select(AuditResult).where(AuditResult.inspection_id == inspection_id)
    audit_results = (await db.execute(stmt)).scalars().all()

    return {
        "inspection_id": inspection.id,
        "client_submission_id": inspection.client_submission_id,
        "status": inspection.status,
        "automated_compliance": inspection.automated_compliance,
        "final_compliance": inspection.final_compliance,
        "product_name": inspection.product_name,
        "brand_name": inspection.brand_name,
        "product_id": inspection.product_id,
        "is_finalized": inspection.is_finalized,
        "finalized_at": inspection.finalized_at,
        "report_hash": inspection.report_hash,
        "audit_results": [
            {
                "id": ar.id,
                "rule_version_id": ar.rule_version_id,
                "rule_code": ar.rule_code,
                "rule_version": ar.rule_version,
                "statutory_reference": ar.statutory_reference,
                "automated_result": ar.automated_result,
                "manual_review_result": ar.manual_review_result,
                "manual_review_reason": ar.manual_review_reason,
                "effective_result": ar.effective_result,
                "severity": ar.severity,
            }
            for ar in audit_results
        ],
    }


# ------------------------------------------------------------------------------
# 5. GET /api/v1/scans/ (List Scans)
# ------------------------------------------------------------------------------
@router.get("/")
async def list_scans(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """Lists inspection scans."""
    stmt = select(Inspection).order_by(Inspection.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


# ------------------------------------------------------------------------------
# 6. POST /api/v1/scans/listing (E-Commerce Listing Scan Evaluation)
# ------------------------------------------------------------------------------
class ListingScanRequest(BaseModel):
    client_submission_id: Optional[uuid.UUID] = None
    area_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    mrp: Optional[str] = None
    net_quantity: Optional[str] = None
    manufacturer: Optional[str] = None
    country_of_origin: Optional[str] = None
    customer_care: Optional[str] = None
    unit_sale_price: Optional[str] = None
    pasted_text: Optional[str] = None


@router.post("/listing")
async def scan_listing(
    payload: ListingScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.officer)),
):
    """
    Accepts e-commerce product listing input (structured fields or pasted text),
    extracts declarations, runs statutory rule engine with source='listing',
    and creates an inspection record.
    """
    from app.services.listing_parser import parse_listing_text

    facts: dict = {}
    if payload.pasted_text:
        facts = parse_listing_text(payload.pasted_text)

    # Structured fields take precedence if provided
    if payload.mrp:
        facts["mrp"] = payload.mrp
        if any(t in payload.mrp.lower() for t in ["incl", "inclusive", "कर सहित"]):
            facts["mrp_tax_inclusive"] = True
    if payload.net_quantity:
        facts["net_quantity"] = payload.net_quantity
    if payload.manufacturer:
        facts["manufacturer"] = payload.manufacturer
    if payload.country_of_origin:
        facts["country_of_origin"] = payload.country_of_origin
    if payload.customer_care:
        facts["customer_care"] = payload.customer_care
    if payload.unit_sale_price:
        facts["unit_sale_price"] = payload.unit_sale_price

    pname = payload.title or facts.get("commodity_name") or "E-Commerce Listed Commodity"
    brand = payload.brand or facts.get("brand")

    # Officer identity
    officer_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        officer_uuid = uuid.UUID(str(officer_id_raw))
    except (ValueError, TypeError):
        officer_uuid = uuid.uuid4()

    sub_id = payload.client_submission_id or uuid.uuid4()

    # Create Inspection record
    inspection = Inspection(
        id=uuid.uuid4(),
        client_submission_id=sub_id,
        officer_id=officer_uuid,
        area_id=payload.area_id,
        product_name=pname,
        brand_name=brand,
        status=InspectionStatus.needs_review,
        source=InspectionSource.listing,
        extracted_facts=facts,
        ocr_raw_text=payload.pasted_text or "",
        ocr_confidence_overall=1.0,
        is_finalized=False,
    )
    db.add(inspection)
    await db.flush()

    # Link to Product if brand & product name present
    if brand and pname:
        p_stmt = select(Product).where(
            Product.brand_name.ilike(brand),
            Product.product_name.ilike(pname)
        )
        matched_prod = (await db.execute(p_stmt)).scalars().first()
        if not matched_prod:
            matched_prod = Product(
                id=uuid.uuid4(),
                brand_name=brand,
                product_name=pname,
                manufacturer_name=facts.get("manufacturer"),
            )
            db.add(matched_prod)
            await db.flush()
        inspection.product_id = matched_prod.id

    # Run audit rules
    audit_evals = await run_audit(
        facts=facts,
        visual_measurements=None,
        ocr_confidences={k: 0.99 for k in facts if facts[k] is not None},
        db=db,
    )

    created_audits: List[AuditResult] = []
    for ev in audit_evals:
        ar = AuditResult(
            id=uuid.uuid4(),
            inspection_id=inspection.id,
            rule_version_id=ev["rule_version_id"],
            rule_code=ev["rule_code"],
            rule_version=ev["rule_version"],
            statutory_reference=ev["statutory_reference"],
            automated_result=ev["automated_result"],
            actual_value=ev.get("actual_value"),
            expected_value=ev.get("expected_value"),
            fact_confidence=ev.get("fact_confidence"),
            measurement_reliable=ev.get("measurement_reliable"),
            automated_reason=ev.get("automated_reason", ""),
            severity=ev["severity"],
            effective_result=ev["automated_result"],
        )
        db.add(ar)
        created_audits.append(ar)

    if created_audits:
        auto_comp, final_comp = compute_inspection_compliance(created_audits)
        inspection.automated_compliance = auto_comp
        inspection.final_compliance = final_comp

    await db.commit()
    await db.refresh(inspection)

    return {
        "inspection_id": inspection.id,
        "client_submission_id": inspection.client_submission_id,
        "source": inspection.source,
        "product_name": inspection.product_name,
        "brand_name": inspection.brand_name,
        "product_id": inspection.product_id,
        "automated_compliance": inspection.automated_compliance,
        "final_compliance": inspection.final_compliance,
        "status": inspection.status,
        "extracted_facts": inspection.extracted_facts,
        "audit_results_count": len(created_audits),
    }
