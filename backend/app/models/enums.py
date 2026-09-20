import enum

class UserRole(str, enum.Enum):
    officer = "officer"
    admin = "admin"
    retailer = "retailer"
    customer = "customer"

class ContactChannelType(str, enum.Enum):
    email = "email"
    phone = "phone"
    none = "none"

class AreaType(str, enum.Enum):
    area = "area"
    ward = "ward"
    district = "district"

class RuleType(str, enum.Enum):
    presence = "presence"
    pattern = "pattern"
    computed = "computed"
    visual = "visual"

class SeverityLevel(str, enum.Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    info = "info"

class InspectionStatus(str, enum.Enum):
    pending_quality_check = "pending_quality_check"
    quality_rejected = "quality_rejected"
    processing = "processing"
    completed = "completed"
    needs_review = "needs_review"
    failed = "failed"

class ComplianceStatus(str, enum.Enum):
    compliant = "compliant"
    non_compliant = "non_compliant"
    needs_review = "needs_review"

class PublicComplianceStatus(str, enum.Enum):
    compliant = "compliant"
    non_compliant = "non_compliant"
    under_review = "under_review"
    resolved = "resolved"

class ViolationStatus(str, enum.Enum):
    open = "open"
    under_review = "under_review"
    appealed = "appealed"
    resolved = "resolved"
    dismissed = "dismissed"

class AppealStatus(str, enum.Enum):
    submitted = "submitted"
    under_review = "under_review"
    accepted = "accepted"
    rejected = "rejected"

class RuleAuditAction(str, enum.Enum):
    created = "created"
    updated = "updated"
    activated = "activated"
    deactivated = "deactivated"

class NotificationType(str, enum.Enum):
    violation_new = "violation_new"
    violation_resolved = "violation_resolved"
    appeal_submitted = "appeal_submitted"
    appeal_outcome = "appeal_outcome"
    report_assigned = "report_assigned"
    report_resolved = "report_resolved"
    system = "system"

class EmailStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"

class RuleVerificationStatus(str, enum.Enum):
    demo = "demo"
    verified = "verified"

class InspectionSource(str, enum.Enum):
    officer = "officer"
    listing = "listing"
    customer = "customer"

class AuditResultType(str, enum.Enum):
    pass_ = "pass"
    fail = "fail"
    needs_review = "needs_review"
    not_applicable = "not_applicable"
