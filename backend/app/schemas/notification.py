"""
Notification Schemas
=====================
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    Language,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    transfusion_id: UUID | None
    type: NotificationType
    channel: NotificationChannel
    title: str
    message: str
    language: Language
    priority: NotificationPriority
    status: NotificationStatus
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int
