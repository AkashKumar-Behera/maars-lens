from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.enums import ViolationStatus, AppealStatus

class ViolationRetailerInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_name: str
    shop_address: str
    area_name: Optional[str] = None

class ViolationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inspection_id: UUID
    retailer: Optional[ViolationRetailerInfo] = None
    retailer_id: Optional[UUID] = None
    area_id: UUID
    officer_id: UUID
    status: ViolationStatus
    failing_rule_codes: List[str]
    summary: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ViolationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    violations: List[ViolationResponse]
    total: int
    page: int
    per_page: int

class AppealCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    appeal_text: str

class AppealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    violation_id: UUID
    retailer_id: UUID
    appeal_text: str
    evidence_storage_paths: List[str]
    status: AppealStatus
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

class AppealReviewRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    status: AppealStatus # accepted or rejected
    review_notes: str


class AppealReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appeal_id: UUID
    status: AppealStatus
    violation_status: ViolationStatus
    reviewed_at: datetime

