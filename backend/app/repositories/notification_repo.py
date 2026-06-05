from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.enums import NotificationStatus


class NotificationRepository:
    model = Notification

    async def get_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        result = await db.execute(
            stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_unread(self, db: AsyncSession, user_id: UUID) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.read_at.is_(None))
        )
        return result.scalar_one()

    async def mark_read(self, db: AsyncSession, notification_id: UUID, user_id: UUID) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.flush()

    async def mark_all_read(self, db: AsyncSession, user_id: UUID) -> None:
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.read_at.is_(None))
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.flush()

    async def create(self, db: AsyncSession, data: dict) -> Notification:
        notif = Notification(**data)
        db.add(notif)
        await db.flush()
        await db.refresh(notif)
        return notif
