from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, List, Dict
from uuid import UUID
from datetime import datetime
from app.models.enums import RuleType, SeverityLevel, RuleVerificationStatus, RuleAuditAction

class CheckDefinition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operator: str # exists, regex, contains, gte, lte, eq, between, formula
    value: Optional[Any] = None
    case_sensitive: Optional[bool] = None
    formula: Optional[str] = None
    compare_field: Optional[str] = None
    tolerance_pct: Optional[float] = None
    unit: Optional[str] = None
    confidence_threshold: Optional[float] = None
    fallback: Optional[str] = None

class RuleCreate(BaseModel):
    """
    Creates a new logical ComplianceRule and its initial immutable ComplianceRuleVersion (v1).
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    rule_code: str
    category: str
    statutory_reference: str
    rule_type: RuleType
    target_field: str
    check_definition: Dict[str, Any]
    severity: SeverityLevel
    description_en: str
    description_hi: Optional[str] = None
    failure_message_template: str
    requires_visual_measurement: bool = False
    measurement_unit: Optional[str] = None
    verification_status: Optional[RuleVerificationStatus] = None # Left to backend handling if omitted

class RuleVersionCreate(BaseModel):
    """
    Creates a new immutable version for an existing rule.
    Historical versions are never mutated.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    statutory_reference: str
    rule_type: RuleType
    target_field: str
    check_definition: Dict[str, Any]
    severity: SeverityLevel
    description_en: str
    description_hi: Optional[str] = None
    failure_message_template: str
    requires_visual_measurement: bool = False
    measurement_unit: Optional[str] = None
    verification_status: Optional[RuleVerificationStatus] = None # Left to backend handling if omitted
    is_active: bool = True

class ComplianceRuleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    version: int
    statutory_reference: str
    rule_type: RuleType
    target_field: str
    check_definition: Dict[str, Any]
    severity: SeverityLevel
    description_en: str
    description_hi: Optional[str] = None
    failure_message_template: str
    requires_visual_measurement: bool
    measurement_unit: Optional[str] = None
    verification_status: RuleVerificationStatus
    is_active: bool
    created_by: UUID
    created_at: datetime

class ComplianceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_code: str
    category: str
    created_at: datetime
    active_version: Optional[ComplianceRuleVersionResponse] = None
    versions: Optional[List[ComplianceRuleVersionResponse]] = None

class RuleListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rules: List[ComplianceRuleResponse]
    total: int
    page: int
    per_page: int

class RuleActivateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    is_active: bool


class RuleAuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    action: RuleAuditAction
    changed_by: UUID
    old_values: Optional[Dict[str, Any]] = None
    new_values: Dict[str, Any]
    changed_at: datetime

