"""
MAARS Lens: Rules Router
========================
Manages two-level statutory compliance rules:
1. ComplianceRule (logical rule identity: rule_code, category, created_at)
2. ComplianceRuleVersion (immutable version snapshots: version, statutory_reference, rule_type,
   target_field, check_definition, severity, description_en/hi, failure_message_template,
   requires_visual_measurement, measurement_unit, verification_status, is_active, created_by, created_at)

Key architectural guarantees:
- Strict Rule Version Immutability: Once a version is authored, it is never mutated in-place.
  New statutory requirements or logic adjustments must be published as a new version (N+1).
- Version Uniqueness: (rule_id, version) is strictly unique; conflict returns 409 Conflict.
- Demo status preservation: Default verification_status is 'demo' unless explicitly marked.
- Role-based authorization: Rule creation, version publication, and activation toggles require UserRole.admin.
  Listing and retrieval are available to authenticated users.
- Full audit logging: RuleAuditLog records every create, new version, activation, and deactivation.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.enums import (
    UserRole,
    RuleAuditAction,
    RuleVerificationStatus,
)
from app.models.rule import ComplianceRule, ComplianceRuleVersion, RuleAuditLog
from app.models.user import Profile
from app.schemas.rule import (
    RuleCreate,
    RuleVersionCreate,
    RuleActivateRequest,
    ComplianceRuleResponse,
    ComplianceRuleVersionResponse,
    RuleListResponse,
    RuleAuditLogEntry,
)

router = APIRouter(prefix="", tags=["rules"])


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
# 1. GET /api/v1/rules/ (List rules)
# ------------------------------------------------------------------------------
@router.get("/", response_model=RuleListResponse)
async def list_rules(
    category: Optional[str] = Query(None, description="Filter by category"),
    only_active: bool = Query(True, description="Only include rules that have active versions"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Lists compliance rules with their active and/or latest versions.
    Available to all authenticated users (officers, admins, etc.).
    """
    stmt = (
        select(ComplianceRule)
        .options(selectinload(ComplianceRule.versions))
        .order_by(ComplianceRule.rule_code.asc())
    )

    if category:
        stmt = stmt.where(ComplianceRule.category == category)

    result = await db.execute(stmt)
    all_rules = result.scalars().all()

    filtered_rules: List[ComplianceRuleResponse] = []
    for r in all_rules:
        # Sort versions descending by version number
        sorted_versions = sorted(r.versions, key=lambda v: v.version, reverse=True)
        active_v = next((v for v in sorted_versions if v.is_active), None)

        if only_active and not active_v:
            continue

        active_v_resp = ComplianceRuleVersionResponse.model_validate(active_v) if active_v else None
        all_v_resps = [ComplianceRuleVersionResponse.model_validate(v) for v in sorted_versions]

        rule_resp = ComplianceRuleResponse(
            id=r.id,
            rule_code=r.rule_code,
            category=r.category,
            created_at=r.created_at,
            active_version=active_v_resp,
            versions=all_v_resps,
        )
        filtered_rules.append(rule_resp)

    total = len(filtered_rules)
    start = (page - 1) * per_page
    end = start + per_page
    paged_rules = filtered_rules[start:end]

    return RuleListResponse(
        rules=paged_rules,
        total=total,
        page=page,
        per_page=per_page,
    )


# ------------------------------------------------------------------------------
# 2. GET /api/v1/rules/versions/{version_id} (Retrieve specific immutable version)
# ------------------------------------------------------------------------------
@router.get("/versions/{version_id}", response_model=ComplianceRuleVersionResponse)
async def get_rule_version(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves a specific immutable ComplianceRuleVersion snapshot.
    404 if not found.
    """
    version = await db.get(ComplianceRuleVersion, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule version '{version_id}' not found.",
        )
    return version


# ------------------------------------------------------------------------------
# 3. GET /api/v1/rules/{rule_id} (Retrieve logical rule and its versions)
# ------------------------------------------------------------------------------
@router.get("/{rule_id}", response_model=ComplianceRuleResponse)
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieves a logical ComplianceRule with all its immutable versions and active version.
    404 if not found.
    """
    stmt = (
        select(ComplianceRule)
        .where(ComplianceRule.id == rule_id)
        .options(selectinload(ComplianceRule.versions))
    )
    result = await db.execute(stmt)
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance rule '{rule_id}' not found.",
        )

    sorted_versions = sorted(rule.versions, key=lambda v: v.version, reverse=True)
    active_v = next((v for v in sorted_versions if v.is_active), None)

    return ComplianceRuleResponse(
        id=rule.id,
        rule_code=rule.rule_code,
        category=rule.category,
        created_at=rule.created_at,
        active_version=ComplianceRuleVersionResponse.model_validate(active_v) if active_v else None,
        versions=[ComplianceRuleVersionResponse.model_validate(v) for v in sorted_versions],
    )


# ------------------------------------------------------------------------------
# 4. POST /api/v1/rules/ (Create logical rule + version 1) - ADMIN ONLY
# ------------------------------------------------------------------------------
@router.post("/", response_model=ComplianceRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Creates a new logical ComplianceRule and its initial immutable ComplianceRuleVersion (v1).
    - Restricted strictly to admin role.
    - 409 Conflict if rule_code already exists.
    - Default verification_status is 'demo' if omitted.
    - Records RuleAuditLog entry.
    """
    admin_profile_id = _extract_admin_profile_id(current_user)

    # Check rule_code uniqueness
    stmt = select(ComplianceRule).where(ComplianceRule.rule_code == payload.rule_code.strip())
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Rule with rule_code '{payload.rule_code.strip()}' already exists.",
        )

    clean_rule_code = payload.rule_code.strip()
    clean_category = payload.category.strip()
    if not clean_rule_code or not clean_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rule_code and category cannot be empty or whitespace.",
        )

    rule_id = uuid.uuid4()
    version_id = uuid.uuid4()

    # SAFEGUARD: All rules authored via general API strictly default to 'demo' status.
    # Verified statutory rules must only enter via verified migrations or authoritative promotion.
    override_attempted = (payload.verification_status == RuleVerificationStatus.verified)
    ver_status = RuleVerificationStatus.demo

    rule = ComplianceRule(
        id=rule_id,
        rule_code=clean_rule_code,
        category=clean_category,
    )

    version_1 = ComplianceRuleVersion(
        id=version_id,
        rule_id=rule_id,
        version=1,
        statutory_reference=payload.statutory_reference,
        rule_type=payload.rule_type,
        target_field=payload.target_field,
        check_definition=payload.check_definition,
        severity=payload.severity,
        description_en=payload.description_en,
        description_hi=payload.description_hi,
        failure_message_template=payload.failure_message_template,
        requires_visual_measurement=payload.requires_visual_measurement,
        measurement_unit=payload.measurement_unit,
        verification_status=ver_status,
        is_active=True,
        created_by=admin_profile_id,
    )

    audit_new_values = {
        "rule_code": clean_rule_code,
        "category": clean_category,
        "version": 1,
        "statutory_reference": payload.statutory_reference,
        "verification_status": ver_status.value,
    }
    if override_attempted:
        audit_new_values["security_override_warning"] = (
            "Caller attempted to set verification_status='verified' via general API; "
            "force-overridden to 'demo' per statutory governance policy."
        )

    audit_log = RuleAuditLog(
        id=uuid.uuid4(),
        rule_id=rule_id,
        action=RuleAuditAction.created,
        changed_by=admin_profile_id,
        old_values=None,
        new_values=audit_new_values,
    )

    db.add(rule)
    db.add(version_1)
    db.add(audit_log)
    await db.commit()
    await db.refresh(rule)
    await db.refresh(version_1)

    v1_resp = ComplianceRuleVersionResponse.model_validate(version_1)
    return ComplianceRuleResponse(
        id=rule.id,
        rule_code=rule.rule_code,
        category=rule.category,
        created_at=rule.created_at,
        active_version=v1_resp,
        versions=[v1_resp],
    )


# ------------------------------------------------------------------------------
# 5. POST /api/v1/rules/{rule_id}/versions (Publish new immutable version) - ADMIN ONLY
# ------------------------------------------------------------------------------
@router.post("/{rule_id}/versions", response_model=ComplianceRuleVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_rule_version(
    rule_id: uuid.UUID,
    payload: RuleVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Creates a new immutable version (N+1) for an existing ComplianceRule.
    - Restricted strictly to admin role.
    - 404 if rule does not exist.
    - Automatically assigns max(existing_versions) + 1.
    - Respects unique constraint uq_rule_version.
    - Records RuleAuditLog entry.
    """
    admin_profile_id = _extract_admin_profile_id(current_user)

    rule = await db.get(ComplianceRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance rule '{rule_id}' not found.",
        )

    # Calculate next version
    stmt = select(func.max(ComplianceRuleVersion.version)).where(ComplianceRuleVersion.rule_id == rule_id)
    current_max = (await db.execute(stmt)).scalar() or 0
    next_version = current_max + 1

    # SAFEGUARD: All versions published via general API strictly default to 'demo' status.
    # Verified statutory rules must only enter via verified migrations or authoritative promotion.
    override_attempted = (payload.verification_status == RuleVerificationStatus.verified)
    ver_status = RuleVerificationStatus.demo
    new_version_id = uuid.uuid4()

    new_version = ComplianceRuleVersion(
        id=new_version_id,
        rule_id=rule_id,
        version=next_version,
        statutory_reference=payload.statutory_reference,
        rule_type=payload.rule_type,
        target_field=payload.target_field,
        check_definition=payload.check_definition,
        severity=payload.severity,
        description_en=payload.description_en,
        description_hi=payload.description_hi,
        failure_message_template=payload.failure_message_template,
        requires_visual_measurement=payload.requires_visual_measurement,
        measurement_unit=payload.measurement_unit,
        verification_status=ver_status,
        is_active=payload.is_active,
        created_by=admin_profile_id,
    )

    audit_new_values = {
        "version": next_version,
        "statutory_reference": payload.statutory_reference,
        "verification_status": ver_status.value,
        "is_active": payload.is_active,
    }
    if override_attempted:
        audit_new_values["security_override_warning"] = (
            "Caller attempted to set verification_status='verified' via general API; "
            "force-overridden to 'demo' per statutory governance policy."
        )

    audit_log = RuleAuditLog(
        id=uuid.uuid4(),
        rule_id=rule_id,
        action=RuleAuditAction.updated,
        changed_by=admin_profile_id,
        old_values={"latest_version": current_max},
        new_values=audit_new_values,
    )

    db.add(new_version)
    db.add(audit_log)
    await db.commit()
    await db.refresh(new_version)

    return new_version


# ------------------------------------------------------------------------------
# 6. PATCH /api/v1/rules/versions/{version_id}/activate (Toggle activation) - ADMIN ONLY
# ------------------------------------------------------------------------------
@router.patch("/versions/{version_id}/activate", response_model=ComplianceRuleVersionResponse)
async def toggle_rule_version_activation(
    version_id: uuid.UUID,
    payload: RuleActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Activates or deactivates a specific rule version.
    - Restricted strictly to admin role.
    - 404 if rule version does not exist.
    - Does NOT mutate any statutory definition or check definition fields (version remains immutable).
    - Records RuleAuditLog entry with action 'activated' or 'deactivated'.
    """
    admin_profile_id = _extract_admin_profile_id(current_user)

    version = await db.get(ComplianceRuleVersion, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule version '{version_id}' not found.",
        )

    old_active = version.is_active
    version.is_active = payload.is_active

    action = RuleAuditAction.activated if payload.is_active else RuleAuditAction.deactivated
    audit_log = RuleAuditLog(
        id=uuid.uuid4(),
        rule_id=version.rule_id,
        action=action,
        changed_by=admin_profile_id,
        old_values={"is_active": old_active, "version": version.version},
        new_values={"is_active": payload.is_active, "version": version.version},
    )

    db.add(audit_log)
    await db.commit()
    await db.refresh(version)

    return version


# ------------------------------------------------------------------------------
# 7. GET /api/v1/rules/{rule_id}/audit-logs (Audit Trail) - ADMIN ONLY
# ------------------------------------------------------------------------------
@router.get("/{rule_id}/audit-logs", response_model=List[RuleAuditLogEntry])
async def get_rule_audit_logs(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.admin)),
):
    """
    Retrieves the audit log history for a specific compliance rule.
    - Admin only.
    - 404 if rule does not exist.
    """
    rule = await db.get(ComplianceRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance rule '{rule_id}' not found.",
        )

    stmt = (
        select(RuleAuditLog)
        .where(RuleAuditLog.rule_id == rule_id)
        .order_by(RuleAuditLog.changed_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

