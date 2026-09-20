from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Float, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from app.core.database import Base
import datetime
from uuid import UUID, uuid4
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    brand_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    manufacturer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False
    )

    inspections: Mapped[List["Inspection"]] = relationship("Inspection", back_populates="product")
