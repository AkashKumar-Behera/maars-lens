from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, LargeBinary
from app.core.database import Base
from app.models.enums import NotificationType, EmailStatus
import datetime
from uuid import UUID
from typing import Optional

class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    title: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[NotificationType] = mapped_column()
    reference_type: Mapped[Optional[str]] = mapped_column(String)
    reference_id: Mapped[Optional[UUID]] = mapped_column()
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class EmailQueue(Base):
    __tablename__ = 'email_queue'

    id: Mapped[UUID] = mapped_column(primary_key=True)
    to_email_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    subject: Mapped[str] = mapped_column(String)
    body_html: Mapped[str] = mapped_column(Text)
    status: Mapped[EmailStatus] = mapped_column(default=EmailStatus.pending)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    related_notification_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey('notifications.id'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
