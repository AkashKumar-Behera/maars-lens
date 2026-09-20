"""
MAARS Lens: Admin Router
========================
Provides administrative and regulatory governance endpoints:
1. GET  /analytics/overview: Aggregated inspection, violation, and rule metrics.
2. GET  /analytics/trends: Time-series inspection and violation activity.
3. GET  /analytics/export: Sanitized streaming CSV export of inspection metadata.
4. GET  /users: Paginated registry of user profiles (excluding credentials/tokens).
5. PATCH /users/{user_id}/status: Toggles user activation state with self-lockout guard.

All endpoints strictly require UserRole.admin.
No mutations are cascaded to inspections, violations, or audit records.
"""

import io
import csv
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, cast, Date, delete

from app.core.database import get_db
from app.core.auth import require_role
from app.models.enums import (
    UserRole,
    InspectionStatus,
    ComplianceStatus,
    ViolationStatus,
    RuleVerificationStatus,
)
from app.models.user import Profile, RoleApplication, Retailer, Customer
from app.models.inspection import Inspection
from app.models.violation import Violation
from app.models.rule import ComplianceRule, ComplianceRuleVersion
from app.schemas.admin import (
    AnalyticsOverview,
    InspectionComplianceOverview,
    ViolationOverview,
    RuleOverview,
    TrendsResponse,
    TrendDataPoint,
    UserListItem,
    UserListResponse,
    UserStatusUpdateRequest,
)

router = APIRouter(prefix="", tags=["admin"])


def _extract_admin_profile_id(current_user: dict) -> uuid.UUID:
    """Extracts or derives a valid UUID for the authenticated admin profile."""
    raw_id = current_user.get("id") or current_user.get("sub")
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user token does not contain a valid profile UUID.",
        )


# ------------------------------------------------------------------------------
# 1. GET /analytics/overview (Aggregated summary metrics)
# ------------------------------------------------------------------------------
@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Computes real aggregate metrics across inspections, violations, and rules.
    - Restricted to admin role.
    """
    # 1. Inspection Aggregations
    insp_stmt = select(
        func.count(Inspection.id).label("total"),
        func.count(case((Inspection.is_finalized == True, 1))).label("finalized"),
        func.count(case((Inspection.final_compliance == ComplianceStatus.compliant, 1))).label("compliant"),
        func.count(case((Inspection.final_compliance == ComplianceStatus.non_compliant, 1))).label("non_compliant"),
        func.count(case((Inspection.final_compliance == ComplianceStatus.needs_review, 1))).label("needs_review"),
    )
    insp_row = (await db.execute(insp_stmt)).one()
    total_insp = insp_row.total or 0
    finalized_insp = insp_row.finalized or 0
    compliant_insp = insp_row.compliant or 0
    non_compliant_insp = insp_row.non_compliant or 0
    needs_review_insp = insp_row.needs_review or 0

    decided = compliant_insp + non_compliant_insp
    compliance_rate = round(compliant_insp / decided, 4) if decided > 0 else 0.0

    # Inspection status breakdown
    status_stmt = select(Inspection.status, func.count(Inspection.id)).group_by(Inspection.status)
    status_rows = (await db.execute(status_stmt)).all()
    by_status: Dict[str, int] = {
        (s.value if hasattr(s, "value") else str(s)): count for s, count in status_rows
    }

    # 2. Violation Aggregations
    viol_total_stmt = select(func.count(Violation.id))
    total_violations = (await db.execute(viol_total_stmt)).scalar() or 0

    viol_status_stmt = select(Violation.status, func.count(Violation.id)).group_by(Violation.status)
    viol_status_rows = (await db.execute(viol_status_stmt)).all()
    viol_by_status: Dict[str, int] = {
        (s.value if hasattr(s, "value") else str(s)): count for s, count in viol_status_rows
    }

    # 3. Rule Aggregations
    total_rules = (await db.execute(select(func.count(ComplianceRule.id)))).scalar() or 0
    total_versions = (await db.execute(select(func.count(ComplianceRuleVersion.id)))).scalar() or 0
    active_versions = (await db.execute(select(func.count(ComplianceRuleVersion.id)).where(ComplianceRuleVersion.is_active == True))).scalar() or 0
    demo_versions = (await db.execute(select(func.count(ComplianceRuleVersion.id)).where(ComplianceRuleVersion.verification_status == RuleVerificationStatus.demo))).scalar() or 0
    verified_versions = (await db.execute(select(func.count(ComplianceRuleVersion.id)).where(ComplianceRuleVersion.verification_status == RuleVerificationStatus.verified))).scalar() or 0

    return AnalyticsOverview(
        inspections=InspectionComplianceOverview(
            total=total_insp,
            finalized=finalized_insp,
            compliant=compliant_insp,
            non_compliant=non_compliant_insp,
            needs_review=needs_review_insp,
            compliance_rate=compliance_rate,
            by_status=by_status,
        ),
        violations=ViolationOverview(
            total=total_violations,
            by_status=viol_by_status,
        ),
        rules=RuleOverview(
            total_rules=total_rules,
            total_versions=total_versions,
            active_versions=active_versions,
            demo_versions=demo_versions,
            verified_versions=verified_versions,
        ),
    )


# ------------------------------------------------------------------------------
# 2. GET /analytics/trends (Time-series daily activity)
# ------------------------------------------------------------------------------
@router.get("/analytics/trends", response_model=TrendsResponse)
async def get_analytics_trends(
    days: int = Query(7, ge=1, le=90, description="Window size in days (1 to 90)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Returns daily inspection and violation counts grouped by date over the past N days.
    Executed as two single grouped aggregation queries (one for inspections, one for violations),
    never N+1 per day.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    # Grouped inspection and violation queries (dialect-aware: strftime for sqlite, cast(Date) for postgres)
    is_sqlite = db.bind.dialect.name == "sqlite" if db.bind else True
    if is_sqlite:
        insp_date_col = func.strftime("%Y-%m-%d", Inspection.created_at)
        viol_date_col = func.strftime("%Y-%m-%d", Violation.created_at)
    else:
        insp_date_col = cast(Inspection.created_at, Date)
        viol_date_col = cast(Violation.created_at, Date)

    insp_stmt = (
        select(insp_date_col.label("day"), func.count(Inspection.id).label("count"))
        .where(Inspection.created_at >= cutoff)
        .group_by(insp_date_col)
    )
    insp_rows = (await db.execute(insp_stmt)).all()
    insp_by_date: Dict[str, int] = {str(row.day): row.count for row in insp_rows}

    viol_stmt = (
        select(viol_date_col.label("day"), func.count(Violation.id).label("count"))
        .where(Violation.created_at >= cutoff)
        .group_by(viol_date_col)
    )
    viol_rows = (await db.execute(viol_stmt)).all()
    viol_by_date: Dict[str, int] = {str(row.day): row.count for row in viol_rows}

    # Build dense chronological date range
    trends: List[TrendDataPoint] = []
    for i in range(days):
        day_date = (cutoff + timedelta(days=i + 1)).date()
        date_str = str(day_date)
        trends.append(
            TrendDataPoint(
                date=date_str,
                inspections=insp_by_date.get(date_str, 0),
                violations=viol_by_date.get(date_str, 0),
            )
        )

    return TrendsResponse(trends=trends)


# ------------------------------------------------------------------------------
# 3. GET /analytics/export (Sanitized CSV Export)
# ------------------------------------------------------------------------------
@router.get("/analytics/export")
async def export_inspections_csv(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Streams a sanitized CSV export of inspection records.
    Header: ID,ClientSubmissionId,CreatedAt,Status,AutomatedCompliance,FinalCompliance,IsFinalized,ReportHash
    Explicitly EXCLUDES: officer_id, retailer_id, gps_lat, gps_lng, product_name, brand_name, notes, customer data.
    """
    stmt = select(Inspection).order_by(Inspection.created_at.desc())
    result = await db.execute(stmt)
    inspections = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID",
        "ClientSubmissionId",
        "CreatedAt",
        "Status",
        "AutomatedCompliance",
        "FinalCompliance",
        "IsFinalized",
        "ReportHash",
    ])

    for ins in inspections:
        status_val = ins.status.value if hasattr(ins.status, "value") else str(ins.status)
        auto_comp = ins.automated_compliance.value if ins.automated_compliance and hasattr(ins.automated_compliance, "value") else (str(ins.automated_compliance) if ins.automated_compliance else "")
        final_comp = ins.final_compliance.value if ins.final_compliance and hasattr(ins.final_compliance, "value") else (str(ins.final_compliance) if ins.final_compliance else "")
        writer.writerow([
            str(ins.id),
            str(ins.client_submission_id),
            ins.created_at.isoformat() if ins.created_at else "",
            status_val,
            auto_comp,
            final_comp,
            str(ins.is_finalized),
            ins.report_hash or "",
        ])

    csv_data = output.getvalue()
    output.close()

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inspections_export.csv"},
    )


# ------------------------------------------------------------------------------
# 4. GET /users (User and Officer Registry)
# ------------------------------------------------------------------------------
@router.get("/users", response_model=UserListResponse)
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Lists system profiles with optional role and status filters.
    Returns only non-sensitive profile metadata: id, role, full_name, email, employee_id, is_active, created_at.
    No credentials or token fields.
    """
    stmt = select(Profile).order_by(Profile.created_at.desc())
    if role is not None:
        stmt = stmt.where(Profile.role == role)
    if is_active is not None:
        stmt = stmt.where(Profile.is_active == is_active)

    result = await db.execute(stmt)
    all_profiles = result.scalars().all()

    total = len(all_profiles)
    start = (page - 1) * per_page
    end = start + per_page
    paged = all_profiles[start:end]

    user_items = [
        UserListItem(
            id=p.id,
            full_name=p.full_name,
            email=p.email,
            role=p.role,
            employee_id=p.employee_id,
            phone=p.phone,
            is_active=p.is_active,
            created_at=p.created_at,
        )
        for p in paged
    ]

    return UserListResponse(
        users=user_items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ------------------------------------------------------------------------------
# 5. PATCH /users/{user_id}/status (Toggle user active status)
# ------------------------------------------------------------------------------
@router.patch("/users/{user_id}/status", response_model=UserListItem)
async def toggle_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Toggles a user's is_active status.
    - Admin cannot deactivate their own profile (self-lockout guard returns 400).
    - Touches Profile.is_active exclusively; does not cascade to inspection, audit, or violation records.
    """
    admin_id = _extract_admin_profile_id(current_user)

    if user_id == admin_id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot deactivate their own profile. Self-lockout is forbidden.",
        )

    profile = await db.get(Profile, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile '{user_id}' not found.",
        )

    profile.is_active = payload.is_active
    await db.commit()
    await db.refresh(profile)

    return UserListItem(
        id=profile.id,
        full_name=profile.full_name,
        email=profile.email,
        role=profile.role,
        employee_id=profile.employee_id,
        phone=profile.phone,
        is_active=profile.is_active,
        created_at=profile.created_at,
    )


# ------------------------------------------------------------------------------
# 6. Role Elevation Governance Endpoints
# ------------------------------------------------------------------------------
class RoleApplicationRejectRequest(BaseModel):
    remarks: Optional[str] = None


@router.get("/role-applications")
async def list_role_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    query = select(RoleApplication, Profile).join(Profile, RoleApplication.user_id == Profile.id)
    if status_filter:
        query = query.where(RoleApplication.status == status_filter)
    query = query.order_by(
        case((RoleApplication.status == "pending", 0), else_=1),
        RoleApplication.created_at.desc()
    )
    res = await db.execute(query)
    rows = res.all()
    
    items = []
    for app_rec, prof in rows:
        items.append({
            "id": str(app_rec.id),
            "user_id": str(prof.id),
            "applicant_name": prof.full_name,
            "applicant_email": prof.email,
            "current_role": prof.role.value,
            "requested_role": app_rec.requested_role.value,
            "status": app_rec.status,
            "badge_number": app_rec.badge_number,
            "department": app_rec.department,
            "business_name": app_rec.business_name,
            "shop_address": app_rec.shop_address,
            "license_number": app_rec.license_number,
            "phone": app_rec.phone or prof.phone,
            "notes": app_rec.notes,
            "admin_remarks": app_rec.admin_remarks,
            "created_at": app_rec.created_at.isoformat() if app_rec.created_at else None,
            "reviewed_at": app_rec.reviewed_at.isoformat() if app_rec.reviewed_at else None,
        })
    return {"applications": items, "total": len(items)}


@router.post("/role-applications/{application_id}/approve")
async def approve_role_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    app_rec = await db.get(RoleApplication, application_id)
    if not app_rec:
        raise HTTPException(status_code=404, detail="Role elevation application not found.")
    
    if app_rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve an application that is already '{app_rec.status}'.")

    prof = await db.get(Profile, app_rec.user_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Applicant user profile not found.")

    # Promote role
    prof.role = app_rec.requested_role
    if app_rec.requested_role == UserRole.officer:
        if app_rec.badge_number:
            prof.employee_id = app_rec.badge_number
        if app_rec.phone:
            prof.phone = app_rec.phone
    elif app_rec.requested_role == UserRole.retailer:
        existing_retailer = await db.get(Retailer, prof.id)
        if not existing_retailer:
            new_retailer = Retailer(
                id=prof.id,
                business_name=app_rec.business_name or f"{prof.full_name}'s Store",
                shop_address=app_rec.shop_address or "Unspecified",
                license_number=app_rec.license_number
            )
            db.add(new_retailer)
        else:
            if app_rec.business_name:
                existing_retailer.business_name = app_rec.business_name
            if app_rec.shop_address:
                existing_retailer.shop_address = app_rec.shop_address
            if app_rec.license_number:
                existing_retailer.license_number = app_rec.license_number

    app_rec.status = "approved"
    app_rec.reviewed_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "message": f"Application approved! User '{prof.full_name}' promoted to '{prof.role.value}'.",
        "user_id": str(prof.id),
        "new_role": prof.role.value,
        "status": "approved"
    }


@router.post("/role-applications/{application_id}/reject")
async def reject_role_application(
    application_id: uuid.UUID,
    payload: Optional[RoleApplicationRejectRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    app_rec = await db.get(RoleApplication, application_id)
    if not app_rec:
        raise HTTPException(status_code=404, detail="Role elevation application not found.")

    if app_rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot reject an application that is already '{app_rec.status}'.")

    app_rec.status = "rejected"
    app_rec.admin_remarks = payload.remarks if payload and payload.remarks else "Application declined by administrator."
    app_rec.reviewed_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "message": "Role elevation application rejected.",
        "application_id": str(app_rec.id),
        "status": "rejected"
    }


class DirectRoleChangeRequest(BaseModel):
    role: UserRole


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: uuid.UUID,
    payload: DirectRoleChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Directly updates a user's role (officer, retailer, admin, customer).
    Protects the primary system administrator from demotion.
    """
    prof = await db.get(Profile, user_id)
    if not prof:
        raise HTTPException(status_code=404, detail="User profile not found.")

    # Primary administrator protection rule
    if prof.email == "admin@maars.gov.in" and payload.role != UserRole.admin:
        raise HTTPException(
            status_code=400,
            detail="Primary System Administrator (admin@maars.gov.in) role cannot be changed or demoted."
        )

    old_role = prof.role
    prof.role = payload.role

    # Ensure supporting table records exist
    if payload.role == UserRole.retailer:
        ret = await db.get(Retailer, prof.id)
        if not ret:
            ret = Retailer(
                id=prof.id,
                business_name=f"{prof.full_name}'s Enterprise",
                shop_address="Registered Commercial Outlet",
                license_number=f"LMPC-RET-{prof.id.hex[:6].upper()}"
            )
            db.add(ret)
    elif payload.role == UserRole.customer:
        cust = await db.get(Customer, prof.id)
        if not cust:
            cust = Customer(
                id=prof.id,
                customer_code=f"CUST-{prof.id.hex[:8].upper()}",
                onboarding_completed=True
            )
            db.add(cust)

    await db.commit()
    return {
        "message": f"User '{prof.full_name}' role changed from {old_role.value} to {prof.role.value}.",
        "user_id": str(prof.id),
        "new_role": prof.role.value
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Deletes a user account.
    Protects the primary system administrator from being deleted.
    """
    prof = await db.get(Profile, user_id)
    if not prof:
        raise HTTPException(status_code=404, detail="User profile not found.")

    # Primary administrator protection rule
    if prof.email == "admin@maars.gov.in":
        raise HTTPException(
            status_code=400,
            detail="Primary System Administrator (admin@maars.gov.in) cannot be deleted or removed."
        )

    caller_id = current_user.get("id") or current_user.get("sub")
    if str(prof.id) == str(caller_id):
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own active administrator account."
        )

    # Clean up dependent entities
    await db.execute(delete(RoleApplication).where(RoleApplication.user_id == prof.id))
    ret = await db.get(Retailer, prof.id)
    if ret:
        await db.delete(ret)
    cust = await db.get(Customer, prof.id)
    if cust:
        await db.delete(cust)

    await db.delete(prof)
    await db.commit()

    return {
        "message": f"User account '{prof.full_name}' ({prof.email}) permanently deleted.",
        "user_id": str(user_id)
    }


