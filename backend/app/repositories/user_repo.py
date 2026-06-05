from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(
            select(User).where(User.email == email).where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(
            select(User).where(User.phone == phone).where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def update_last_login(self, db: AsyncSession, user_id: UUID) -> None:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        await db.flush()

    async def set_verified(self, db: AsyncSession, user_id: UUID) -> None:
        await db.execute(
            update(User).where(User.id == user_id).values(is_verified=True)
        )
        await db.flush()

    async def set_active(self, db: AsyncSession, user_id: UUID, is_active: bool) -> None:
        await db.execute(
            update(User).where(User.id == user_id).values(is_active=is_active)
        )
        await db.flush()
