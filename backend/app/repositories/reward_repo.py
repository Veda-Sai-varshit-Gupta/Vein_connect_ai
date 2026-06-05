from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reward import Reward
from app.models.enums import RewardType


class RewardRepository:
    async def get_by_donor(self, db: AsyncSession, donor_id: UUID, skip: int = 0, limit: int = 20) -> list[Reward]:
        result = await db.execute(
            select(Reward)
            .where(Reward.donor_id == donor_id)
            .order_by(Reward.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_total_points(self, db: AsyncSession, donor_id: UUID) -> int:
        result = await db.execute(
            select(func.sum(Reward.points))
            .where(Reward.donor_id == donor_id)
        )
        return result.scalar_one() or 0

    async def get_points_by_type(self, db: AsyncSession, donor_id: UUID) -> dict:
        result = await db.execute(
            select(Reward.type, func.sum(Reward.points))
            .where(Reward.donor_id == donor_id)
            .group_by(Reward.type)
        )
        return {row[0].value: row[1] for row in result.all()}

    async def create(self, db: AsyncSession, data: dict) -> Reward:
        reward = Reward(**data)
        db.add(reward)
        await db.flush()
        await db.refresh(reward)
        return reward
