from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from app.core.database import Base
import datetime
from uuid import UUID

class OfficerSignature(Base):
    __tablename__ = 'officer_signatures'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    officer_id: Mapped[UUID] = mapped_column(ForeignKey('profiles.id', ondelete='RESTRICT'), nullable=False)
    signature_storage_path: Mapped[str] = mapped_column(String, nullable=False)
    signature_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        Index('uq_active_officer_signature', 'officer_id', unique=True, postgresql_where=(is_active == True)),
    )

