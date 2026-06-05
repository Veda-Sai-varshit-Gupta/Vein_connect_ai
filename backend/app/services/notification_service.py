"""
Notification Service
=====================
Creates and manages in-app and channel notifications.
For v1: app channel is always created. WhatsApp/SMS are stubbed.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    Language,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    NotificationStatus,
)
from app.repositories.notification_repo import NotificationRepository

notif_repo = NotificationRepository()


class NotificationService:

    async def create_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        transfusion_id: UUID | None = None,
        channel: NotificationChannel = NotificationChannel.app,
        priority: NotificationPriority = NotificationPriority.normal,
        language: Language = Language.en,
    ):
        return await notif_repo.create(db, {
            "user_id": user_id,
            "transfusion_id": transfusion_id,
            "type": type,
            "channel": channel,
            "title": title,
            "message": message,
            "language": language,
            "priority": priority,
            "status": NotificationStatus.sent,
        })

    async def get_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ):
        return await notif_repo.get_for_user(db, user_id, skip, limit, unread_only)

    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        return await notif_repo.count_unread(db, user_id)

    async def mark_read(self, db: AsyncSession, notification_id: UUID, user_id: UUID) -> None:
        await notif_repo.mark_read(db, notification_id, user_id)

    async def mark_all_read(self, db: AsyncSession, user_id: UUID) -> None:
        await notif_repo.mark_all_read(db, user_id)
