from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, LargeBinary, Index
import datetime
from uuid import UUID
from typing import Optional
from app.core.database import Base
from app.models.enums import UserRole, ContactChannelType

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True) # Matches Supabase auth.users.id
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        Index('uq_profiles_employee_id', 'employee_id', unique=True, postgresql_where=(employee_id.isnot(None))),
    )

class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    business_name: Mapped[str] = mapped_column(String, nullable=False)
    shop_address: Mapped[str] = mapped_column(String, nullable=False)
    area_id: Mapped[UUID] = mapped_column(ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False)
    license_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[UUID] = mapped_column(primary_key=True) # Matches Supabase auth.users.id (Anonymous Auth)
    customer_code: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Reference identifier only
    contact_channel_encrypted: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    contact_channel_type: Mapped[ContactChannelType] = mapped_column(Enum(ContactChannelType), default=ContactChannelType.none)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
