from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, Float, Enum
from app.core.database import Base
from app.models.enums import PublicComplianceStatus
import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List

class PublicComplianceRecord(Base):
    __tablename__ = 'public_compliance_records'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # Retention protection: Finalized inspection evidence must not be lost
    inspection_id: Mapped[UUID] = mapped_column(ForeignKey('inspections.id', ondelete='RESTRICT'), unique=True, nullable=False)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    area_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('areas.id', ondelete='SET NULL'), nullable=True)
    compliance_status: Mapped[PublicComplianceStatus] = mapped_column(Enum(PublicComplianceStatus), nullable=False)
    last_verified_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    public_checks: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CustomerReport(Base):
    __tablename__ = 'customer_reports'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False)
    image_storage_path: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False) # Internal only
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    area_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('areas.id', ondelete='SET NULL'), nullable=True)
    gps_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Internal only
    gps_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Internal only
    status: Mapped[str] = mapped_column(String(32), default='submitted', nullable=False)
    assigned_officer_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

