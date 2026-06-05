from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.confirmation import Confirmation
from app.models.enums import ConfirmationRole, ConfirmationStatus
from app.repositories.base import BaseRepository


class ConfirmationRepository(BaseRepository[Confirmation]):
    def __init__(self):
        super().__init__(Confirmation)

    async def get_by_transfusion(self, db: AsyncSession, transfusion_id: UUID) -> list[Confirmation]:
        result = await db.execute(
            select(Confirmation)
            .where(Confirmation.transfusion_id == transfusion_id)
            .order_by(Confirmation.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_pending_for_user(self, db: AsyncSession, user_id: UUID) -> list[Confirmation]:
        result = await db.execute(
            select(Confirmation)
            .where(Confirmation.user_id == user_id)
            .where(Confirmation.status == ConfirmationStatus.pending)
        )
        return list(result.scalars().all())

    async def get_by_user_and_transfusion(
        self,
        db: AsyncSession,
        user_id: UUID,
        transfusion_id: UUID,
    ) -> Confirmation | None:
        result = await db.execute(
            select(Confirmation)
            .where(Confirmation.user_id == user_id)
            .where(Confirmation.transfusion_id == transfusion_id)
        )
        return result.scalar_one_or_none()
