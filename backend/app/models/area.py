from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
import datetime
from uuid import UUID
from typing import Optional
from app.core.database import Base
from app.models.enums import AreaType

class Area(Base):
    __tablename__ = "areas"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    area_type: Mapped[AreaType] = mapped_column(Enum(AreaType), nullable=False)
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class OfficerAreaAssignment(Base):
    __tablename__ = "officer_area_assignments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    officer_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    assigned_by: Mapped[UUID] = mapped_column(ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False)

