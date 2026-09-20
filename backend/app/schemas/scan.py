from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.enums import InspectionStatus, ComplianceStatus, AuditResultType, SeverityLevel

class QualityIssue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str
    severity: str # low, medium, high
    score: Optional[float] = None
    threshold: Optional[float] = None
    message: str
    actionable_advice: str

class ImageQualityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    acceptable: bool
    is_borderline: bool
    overall_quality_score: Optional[float] = None
    issues: List[QualityIssue]

class TextRegion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    bounding_box: List[int]
    estimated_text_height_px: Optional[int] = None
    estimated_text_height_mm: Optional[float] = None
    measurement_confidence: float
    measurement_reliable: bool
    notes: Optional[str] = None

class VisualMeasurements(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text_regions: List[TextRegion]
    overall_layout: Dict[str, Any]

class AuditResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inspection_id: UUID
    rule_version_id: UUID
    rule_code: str
    rule_version: int
    statutory_reference: str
    
    # 1. Automated engine evaluation (immutable output)
    automated_result: AuditResultType
    actual_value: Optional[str] = None
    expected_value: Optional[str] = None
    fact_confidence: Optional[float] = None
    measurement_reliable: Optional[bool] = None
    automated_reason: str
    severity: SeverityLevel
    
    # 2. Separate officer manual assessment
    manual_review_result: Optional[AuditResultType] = None
    manual_review_reason: Optional[str] = None
    manual_reviewed_by: Optional[UUID] = None
    manual_reviewed_at: Optional[datetime] = None

    # 3. Backend-computed effective result
    effective_result: AuditResultType

    evaluated_at: datetime

NIL_UUID = UUID("00000000-0000-0000-0000-000000000000")

class ScanUploadRequest(BaseModel):
    """
    Upload request validation.
    Enforces non-nil client_submission_id for offline idempotency and forbids extra fields.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    client_submission_id: UUID
    area_id: UUID
    retailer_id: Optional[UUID] = None
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None

    @field_validator("client_submission_id")
    @classmethod
    def validate_submission_id(cls, v: UUID) -> UUID:
        if v == NIL_UUID:
            raise ValueError("client_submission_id cannot be the nil UUID (00000000-0000-0000-0000-000000000000).")
        return v

class ScanUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: UUID
    client_submission_id: UUID # Offline idempotency key preserved
    status: InspectionStatus
    message: str

class ScanQualityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: UUID
    status: InspectionStatus
    image_quality: ImageQualityResponse
    warning: Optional[str] = None
    actions: Optional[List[str]] = None

class ScanResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: UUID
    client_submission_id: UUID
    status: InspectionStatus
    
    # Dual-layer compliance verdicts (both backend-computed)
    automated_compliance: Optional[ComplianceStatus] = None # Aggregated only from automated results
    final_compliance: Optional[ComplianceStatus] = None # Aggregated only from effective results
    
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    image_quality: Optional[ImageQualityResponse] = None
    extracted_facts: Optional[Dict[str, Any]] = None
    ocr_confidence_overall: Optional[float] = None
    ocr_field_confidences: Optional[Dict[str, Any]] = None
    visual_measurements: Optional[VisualMeasurements] = None
    audit_results: List[AuditResultItem]
    officer_notes: Optional[str] = None
    
    # Finalization and tamper-evidence locks
    is_finalized: bool
    finalized_at: Optional[datetime] = None
    signature_id: Optional[UUID] = None
    signature_hash_at_finalization: Optional[str] = None
    report_hash: Optional[str] = None

class ManualReviewItem(BaseModel):
    """
    Officer manual assessment of a specific rule result.
    The automated_result is never modified; effective_result will be computed by backend.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    rule_code: str = Field(..., min_length=1)
    manual_review_result: AuditResultType
    manual_review_reason: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_manual_review(self):
        if self.manual_review_result == AuditResultType.not_applicable:
            raise ValueError("not_applicable is not an allowed manual review assessment.")
        if self.manual_review_result in (AuditResultType.pass_, AuditResultType.fail, AuditResultType.needs_review):
            if not self.manual_review_reason or not self.manual_review_reason.strip():
                raise ValueError("manual_review_reason is mandatory and cannot be empty or whitespace-only.")
        return self

class FinalizeRequest(BaseModel):
    """
    Officer request to finalize an inspection.
    Client CANNOT submit arbitrary automated_compliance, final_compliance, or effective_result.
    Extra fields are strictly forbidden.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    officer_notes: Optional[str] = None


class FinalizeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspection_id: UUID
    status: InspectionStatus
    automated_compliance: ComplianceStatus
    final_compliance: ComplianceStatus
    is_finalized: bool
    finalized_at: datetime
    report_hash: str
    signature_id: Optional[UUID] = None
    signature_hash: Optional[str] = None
    violation_id: Optional[UUID] = None
    notifications_sent: List[str] = Field(default_factory=list)
    pdf_url: str

class InspectionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_submission_id: UUID
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    area_name: Optional[str] = None
    status: InspectionStatus
    automated_compliance: Optional[ComplianceStatus] = None
    final_compliance: Optional[ComplianceStatus] = None
    is_finalized: bool
    created_at: datetime

class InspectionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inspections: List[InspectionListItem]
    total: int
    page: int
    per_page: int

