"""
MAARS Lens: Violations Router
==============================
Handles statutory violation creation, retrieval, and status transitions for non-compliant inspections.

Enforces:
- Role-based authorization: officer or admin required for all operations.
- Finalization and compliance guard: violations can ONLY be created for finalized inspections
  whose final_compliance is strictly non_compliant (ComplianceStatus.non_compliant).
- 1-to-1 uniqueness check: explicit 409 Conflict check preventing duplicate violation records per inspection.
- Input validation: failing_rule_codes (non-empty list of strings) and summary (non-empty, non-whitespace).
- Whitelisted response schema: strictly excludes officer_id, retailer_id, area_id, resolved_by,
  and internal investigation artifacts.
- Terminal state immutability: once a violation is 'resolved' or 'dismissed', further status transitions
  are rejected with 400 Bad Request.
- Mandatory resolution notes: transitioning to 'resolved' or 'dismissed' requires non-empty resolution_notes,
  and sets resolved_at and resolved_by.
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.enums import UserRole, ComplianceStatus, ViolationStatus
from app.models.inspection import Inspection
from app.models.violation import Violation

router = APIRouter(prefix="", tags=["violations"])


def require_officer_or_admin(user: dict = Depends(get_current_user)) -> dict:
    """Ensures caller has officer or admin privileges."""
    user_role = user.get("user_metadata", {}).get("role", "customer")
    if user_role not in (UserRole.officer, UserRole.admin, "officer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions: officer or admin role required.",
        )
    return user


# ------------------------------------------------------------------------------
# Schemas (Strict Whitelist Enforcement)
# ------------------------------------------------------------------------------
class ViolationCreateRequest(BaseModel):
    """
    Officer input for creating a statutory violation on a non-compliant finalized inspection.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    failing_rule_codes: List[str] = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)

    @field_validator("failing_rule_codes")
    @classmethod
    def validate_failing_rule_codes(cls, v: List[str]) -> List[str]:
        if not v or not any(code.strip() for code in v):
            raise ValueError("failing_rule_codes must contain at least one non-empty rule code.")
        cleaned = [c.strip() for c in v if c.strip()]
        if not cleaned:
            raise ValueError("failing_rule_codes cannot contain only empty or whitespace items.")
        return cleaned

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("summary cannot be empty or whitespace-only.")
        return v.strip()


class ViolationStatusTransitionRequest(BaseModel):
    """
    Status transition request for an existing violation.
    Uses real ViolationStatus enum values (open, under_review, appealed, resolved, dismissed).
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    status: ViolationStatus
    resolution_notes: Optional[str] = None

    @field_validator("resolution_notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_stripped = v.strip()
            return v_stripped if v_stripped else None
        return None


class ViolationResponseWhitelist(BaseModel):
    """
    Whitelisted public/officer-facing response for violation entities.
    LOCKED PRIVACY REQUIREMENT:
    Explicitly excludes officer_id, retailer_id, area_id, resolved_by,
    and internal system notes.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    inspection_id: uuid.UUID
    status: ViolationStatus
    failing_rule_codes: List[str]
    summary: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


# ------------------------------------------------------------------------------
# 1. POST /api/v1/violations/{inspection_id} (Create)
# ------------------------------------------------------------------------------
@router.post("/{inspection_id}", response_model=ViolationResponseWhitelist, status_code=status.HTTP_201_CREATED)
async def create_violation(
    inspection_id: uuid.UUID,
    payload: ViolationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Creates a statutory violation for a finalized, non-compliant inspection.
    - 404 if inspection does not exist.
    - 400 if inspection is not finalized.
    - 400 if final_compliance != ComplianceStatus.non_compliant.
    - 409 Conflict if a violation already exists for this inspection.
    - failing_rule_codes and summary are mandatory and cannot be empty.
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
            detail="Cannot create violation for unfinalized inspection. Inspection must be finalized first.",
        )

    if inspection.final_compliance != ComplianceStatus.non_compliant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create violation: inspection final_compliance is '{inspection.final_compliance.value if inspection.final_compliance else None}', but must be 'non_compliant'.",
        )

    # Explicit 1-to-1 existence check to prevent raw DB unique constraint error
    stmt = select(Violation).where(Violation.inspection_id == inspection_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A violation record already exists for inspection '{inspection_id}'.",
        )

    # Officer identity
    officer_id_raw = current_user.get("id") or current_user.get("sub")
    try:
        officer_uuid = uuid.UUID(str(officer_id_raw))
    except (ValueError, TypeError):
        officer_uuid = inspection.officer_id

    violation = Violation(
        id=uuid.uuid4(),
        inspection_id=inspection.id,
        retailer_id=inspection.retailer_id,
        area_id=inspection.area_id,
        officer_id=officer_uuid,
        status=ViolationStatus.open,
        failing_rule_codes=payload.failing_rule_codes,
        summary=payload.summary,
    )

    db.add(violation)
    await db.commit()
    await db.refresh(violation)

    return violation


# ------------------------------------------------------------------------------
# 2. GET /api/v1/violations/{inspection_id} (Retrieve)
# ------------------------------------------------------------------------------
@router.get("/{inspection_id}", response_model=ViolationResponseWhitelist)
async def get_violation(
    inspection_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Retrieves the violation associated with an inspection.
    - 404 if inspection does not exist or has no violation recorded.
    - Whitelisted schema: explicitly excludes officer_id, retailer_id, area_id, resolved_by.
    """
    stmt = select(Violation).where(Violation.inspection_id == inspection_id)
    violation = (await db.execute(stmt)).scalar_one_or_none()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No violation record found for inspection '{inspection_id}'.",
        )

    return violation


# ------------------------------------------------------------------------------
# 3. POST /api/v1/violations/{inspection_id}/status (Transition)
# ------------------------------------------------------------------------------
@router.post("/{inspection_id}/status", response_model=ViolationResponseWhitelist)
async def transition_violation_status(
    inspection_id: uuid.UUID,
    payload: ViolationStatusTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_officer_or_admin),
):
    """
    Transitions the lifecycle status of a statutory violation.
    - 404 if violation does not exist for this inspection.
    - Rejects transition if CURRENT status is 'resolved' or 'dismissed' (terminal state -> 400).
    - If transitioning to 'resolved' or 'dismissed': resolution_notes is mandatory (400 if missing/blank),
      and sets resolved_at and resolved_by.
    - If transitioning to 'open', 'under_review', or 'appealed': resolution_notes is optional;
      resolved_at and resolved_by remain unset.
    """
    stmt = select(Violation).where(Violation.inspection_id == inspection_id)
    violation = (await db.execute(stmt)).scalar_one_or_none()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No violation record found for inspection '{inspection_id}'.",
        )

    # Guard: terminal state check
    if violation.status in (ViolationStatus.resolved, ViolationStatus.dismissed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition violation: violation is already in terminal status '{violation.status.value}'. Reopening is not permitted.",
        )

    # Transitioning to resolved or dismissed requires non-empty resolution notes
    new_status = payload.status
    if new_status in (ViolationStatus.resolved, ViolationStatus.dismissed):
        if not payload.resolution_notes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"resolution_notes is mandatory when transitioning violation to '{new_status.value}'.",
            )

        officer_id_raw = current_user.get("id") or current_user.get("sub")
        try:
            resolver_uuid = uuid.UUID(str(officer_id_raw))
        except (ValueError, TypeError):
            resolver_uuid = violation.officer_id

        violation.status = new_status
        violation.resolution_notes = payload.resolution_notes
        violation.resolved_at = datetime.now(timezone.utc)
        violation.resolved_by = resolver_uuid
    else:
        # Non-terminal transition (open, under_review, appealed)
        violation.status = new_status
        if payload.resolution_notes:
            violation.resolution_notes = payload.resolution_notes

    await db.commit()
    await db.refresh(violation)

    return violation

