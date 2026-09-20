from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, JSON, Enum, UniqueConstraint
from app.core.database import Base
from app.models.enums import RuleType, SeverityLevel, RuleAuditAction, RuleVerificationStatus
import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List

class ComplianceRule(Base):
    __tablename__ = 'compliance_rules'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    rule_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    versions: Mapped[List["ComplianceRuleVersion"]] = relationship("ComplianceRuleVersion", back_populates="rule", cascade="all, delete-orphan")

class ComplianceRuleVersion(Base):
    __tablename__ = 'compliance_rule_versions'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    rule_id: Mapped[UUID] = mapped_column(ForeignKey('compliance_rules.id', ondelete='CASCADE'), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    statutory_reference: Mapped[str] = mapped_column(String, nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType), nullable=False)
    target_field: Mapped[str] = mapped_column(String(64), nullable=False)
    check_definition: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), nullable=False)
    description_en: Mapped[str] = mapped_column(String, nullable=False)
    description_hi: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    failure_message_template: Mapped[str] = mapped_column(String, nullable=False)
    requires_visual_measurement: Mapped[bool] = mapped_column(Boolean, default=False)
    measurement_unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    verification_status: Mapped[RuleVerificationStatus] = mapped_column(Enum(RuleVerificationStatus), default=RuleVerificationStatus.demo, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    rule: Mapped["ComplianceRule"] = relationship("ComplianceRule", back_populates="versions")

    __table_args__ = (
        UniqueConstraint('rule_id', 'version', name='uq_rule_version'),
    )

class RuleAuditLog(Base):
    __tablename__ = 'rule_audit_logs'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    rule_id: Mapped[UUID] = mapped_column(ForeignKey('compliance_rules.id', ondelete='CASCADE'), nullable=False)
    action: Mapped[RuleAuditAction] = mapped_column(Enum(RuleAuditAction), nullable=False)
    changed_by: Mapped[UUID] = mapped_column(ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False)
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

