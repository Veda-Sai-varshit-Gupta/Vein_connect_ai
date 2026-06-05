from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donation import Donation
from app.repositories.base import BaseRepository


class DonationRepository(BaseRepository[Donation]):
    def __init__(self):
        super().__init__(Donation)

    async def get_by_transfusion_id(self, db: AsyncSession, transfusion_id: UUID) -> list[Donation]:
        result = await db.execute(
            select(Donation)
            .where(Donation.transfusion_id == transfusion_id)
            .where(Donation.deleted_at.is_(None))
        )
        return list(result.scalars().all())
