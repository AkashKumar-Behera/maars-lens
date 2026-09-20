from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Enum, Text
from app.core.database import Base
from app.models.enums import AuditResultType, SeverityLevel
import datetime
from uuid import UUID
from typing import Optional

class AuditResult(Base):
    __tablename__ = 'audit_results'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    inspection_id: Mapped[UUID] = mapped_column(ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False)
    rule_version_id: Mapped[UUID] = mapped_column(ForeignKey('compliance_rule_versions.id', ondelete='RESTRICT'), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    statutory_reference: Mapped[str] = mapped_column(String, nullable=False)
    
    # Evaluation flow: automated_result -> optional manual_review_result -> effective_result
    automated_result: Mapped[AuditResultType] = mapped_column(Enum(AuditResultType), nullable=False) # Immutable engine verdict
    actual_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expected_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fact_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    measurement_reliable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    automated_reason: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), nullable=False)

    # Separate officer manual assessment
    manual_review_result: Mapped[Optional[AuditResultType]] = mapped_column(Enum(AuditResultType), nullable=True)
    manual_review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manual_reviewed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True)
    manual_reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # System effective result
    effective_result: Mapped[AuditResultType] = mapped_column(Enum(AuditResultType), nullable=False)

    evaluated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('inspection_id', 'rule_version_id', name='uq_audit_result_inspection_rule_version'),
    )

