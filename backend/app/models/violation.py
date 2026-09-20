from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum, JSON
from app.core.database import Base
from app.models.enums import ViolationStatus, AppealStatus
import datetime
from uuid import UUID
from typing import Optional, List

class Violation(Base):
    __tablename__ = 'violations'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    inspection_id: Mapped[UUID] = mapped_column(ForeignKey('inspections.id', ondelete='RESTRICT'), unique=True, nullable=False)
    retailer_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('retailers.id', ondelete='SET NULL'), nullable=True)
    area_id: Mapped[UUID] = mapped_column(ForeignKey('areas.id', ondelete='RESTRICT'), nullable=False)
    officer_id: Mapped[UUID] = mapped_column(ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False)
    status: Mapped[ViolationStatus] = mapped_column(Enum(ViolationStatus), default=ViolationStatus.open, nullable=False)
    failing_rule_codes: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Appeal(Base):
    __tablename__ = 'appeals'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    violation_id: Mapped[UUID] = mapped_column(ForeignKey('violations.id', ondelete='CASCADE'), nullable=False)
    retailer_id: Mapped[UUID] = mapped_column(ForeignKey('retailers.id', ondelete='RESTRICT'), nullable=False)
    appeal_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_storage_paths: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[AppealStatus] = mapped_column(Enum(AppealStatus), default=AppealStatus.submitted, nullable=False)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

