from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from app.models.enums import AreaType, UserRole

class InspectionComplianceOverview(BaseModel):
    total: int
    finalized: int
    compliant: int
    non_compliant: int
    needs_review: int
    compliance_rate: float
    by_status: Dict[str, int]

class ViolationOverview(BaseModel):
    total: int
    by_status: Dict[str, int]

class RuleOverview(BaseModel):
    total_rules: int
    total_versions: int
    active_versions: int
    demo_versions: int
    verified_versions: int

class AnalyticsOverview(BaseModel):
    inspections: InspectionComplianceOverview
    violations: ViolationOverview
    rules: RuleOverview

class TrendDataPoint(BaseModel):
    date: str
    inspections: int
    violations: int

class TrendsResponse(BaseModel):
    trends: List[TrendDataPoint]

class UserStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    is_active: bool

class AreaStatsItem(BaseModel):
    area_id: UUID
    area_name: str
    total_inspections: int
    violations: int
    compliance_rate: float

class OfficerStatsItem(BaseModel):
    officer_id: UUID
    officer_name: str
    employee_id: Optional[str] = None
    total_inspections: int
    compliance_rate: float
    last_inspection: Optional[datetime] = None

class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: Optional[str] = None
    role: UserRole
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    users: List[UserListItem]
    total: int
    page: int
    per_page: int

class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class AreaCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: str
    area_type: AreaType
    parent_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_hierarchy(self):
        if self.area_type == AreaType.district and self.parent_id is not None:
            raise ValueError("Districts are top-level regions and cannot have a parent_id.")
        if self.area_type in (AreaType.ward, AreaType.area) and self.parent_id is None:
            raise ValueError(f"An area of type '{self.area_type.value}' must have a valid parent_id.")
        return self

class AreaUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    name: Optional[str] = None
    is_active: Optional[bool] = None

class AreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    area_type: AreaType
    parent_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime

class OfficerAssignmentRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    officer_id: UUID
    area_id: UUID


class OfficerAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    officer_id: UUID
    area_id: UUID
    assigned_at: datetime
    assigned_by: UUID

