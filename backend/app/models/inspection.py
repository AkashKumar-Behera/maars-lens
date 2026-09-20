from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from app.core.database import Base
from app.models.enums import InspectionStatus, ComplianceStatus, InspectionSource
import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.product import Product


class Inspection(Base):
    __tablename__ = 'inspections'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    client_submission_id: Mapped[UUID] = mapped_column(unique=True, index=True, nullable=False) # Offline idempotency key
    officer_id: Mapped[UUID] = mapped_column(ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False)
    retailer_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('retailers.id', ondelete='SET NULL'), nullable=True)
    area_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('areas.id', ondelete='RESTRICT'), nullable=True)
    gps_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    image_storage_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    product_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[InspectionStatus] = mapped_column(default=InspectionStatus.pending_quality_check, nullable=False)
    
    # Engine compliance vs Final aggregated compliance
    automated_compliance: Mapped[Optional[ComplianceStatus]] = mapped_column(nullable=True)
    final_compliance: Mapped[Optional[ComplianceStatus]] = mapped_column(nullable=True)

    extracted_facts: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ocr_raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence_overall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ocr_field_confidences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    visual_measurements: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    officer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Finalization locks
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finalized_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signature_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('officer_signatures.id', ondelete='RESTRICT'), nullable=True)
    signature_hash_at_finalization: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    report_hash: Mapped[Optional[str]] = mapped_column(String(71), nullable=True)
    report_storage_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    source: Mapped[InspectionSource] = mapped_column(default=InspectionSource.officer, nullable=False)
    triggered_by_report_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('customer_reports.id', ondelete='SET NULL'), nullable=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Multi-image relationship
    images: Mapped[List["InspectionImage"]] = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan", order_by="InspectionImage.uploaded_at")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="inspections")


class InspectionImage(Base):
    __tablename__ = 'inspection_images'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    inspection_id: Mapped[UUID] = mapped_column(ForeignKey('inspections.id', ondelete='CASCADE'), nullable=False, index=True)
    panel_type: Mapped[str] = mapped_column(String(50), default="other", nullable=False) # front/back/side/top/other
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), default="image/jpeg", nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    original: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_image_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('inspection_images.id', ondelete='CASCADE'), nullable=True)

    inspection: Mapped["Inspection"] = relationship("Inspection", back_populates="images")


class ImageQualityAssessment(Base):
    __tablename__ = 'image_quality_assessments'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    inspection_id: Mapped[UUID] = mapped_column(ForeignKey('inspections.id'), unique=True)
    is_acceptable: Mapped[bool] = mapped_column(Boolean)
    is_borderline: Mapped[bool] = mapped_column(Boolean, default=False)
    overall_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    issues: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    preprocessing_applied: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    assessed_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
