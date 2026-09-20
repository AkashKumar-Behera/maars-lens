from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.enums import NotificationType

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    message: str
    notification_type: NotificationType
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    is_read: bool
    created_at: datetime

class NotificationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notifications: List[NotificationResponse]
    unread_count: int
    total: int

