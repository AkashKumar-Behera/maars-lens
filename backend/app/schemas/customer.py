from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.enums import PublicComplianceStatus

class CustomerReportCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    description: str # Citizen free-text description (internal only)
    product_name: Optional[str] = None
    area_id: Optional[UUID] = None
    gps_lat: Optional[float] = None # Internal only
    gps_lng: Optional[float] = None # Internal only


class CustomerReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: Optional[str] = None
    status: str
    created_at: datetime
    resolution_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None

class CustomerReportDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: Optional[str] = None
    description: str
    area_id: Optional[UUID] = None
    status: str
    resolution_summary: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

class CustomerReportListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reports: List[CustomerReportResponse]

class PublicCheck(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    check_category: str
    statutory_reference: str
    result: str # pass, fail, needs_review
    description: str

class PublicComplianceResult(BaseModel):
    """
    Sanitized customer-facing compliance record.
    Strictly excludes officer identity, internal notes, retailer PII, customer PII, and GPS coordinates.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    compliance_status: PublicComplianceStatus
    last_verified_date: datetime
    area_name: Optional[str] = None
    public_checks: List[PublicCheck]

class ComplianceSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    results: List[PublicComplianceResult]
    total: int
    page: int
    per_page: int

