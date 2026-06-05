from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.friendship_score import FriendshipScore


class FriendshipRepository:
    async def get_or_create(
        self,
        db: AsyncSession,
        patient_id: UUID,
        donor_id: UUID,
    ) -> tuple[FriendshipScore, bool]:
        """Returns (FriendshipScore, created: bool)."""
        existing = await db.execute(
            select(FriendshipScore)
            .where(FriendshipScore.patient_id == patient_id)
            .where(FriendshipScore.donor_id == donor_id)
        )
        obj = existing.scalar_one_or_none()
        if obj:
            return obj, False
        new_score = FriendshipScore(patient_id=patient_id, donor_id=donor_id)
        db.add(new_score)
        await db.flush()
        await db.refresh(new_score)
        return new_score, True

    async def get_for_patient(self, db: AsyncSession, patient_id: UUID) -> list[FriendshipScore]:
        result = await db.execute(
            select(FriendshipScore).where(FriendshipScore.patient_id == patient_id)
        )
        return list(result.scalars().all())

    async def get_for_donor(self, db: AsyncSession, donor_id: UUID) -> list[FriendshipScore]:
        result = await db.execute(
            select(FriendshipScore).where(FriendshipScore.donor_id == donor_id)
        )
        return list(result.scalars().all())

    async def update_score(
        self,
        db: AsyncSession,
        patient_id: UUID,
        donor_id: UUID,
        score: float,
        total_donations: int,
        positive: int,
        negative: int,
    ) -> None:
        from sqlalchemy import update
        from datetime import datetime, timezone
        await db.execute(
            update(FriendshipScore)
            .where(FriendshipScore.patient_id == patient_id)
            .where(FriendshipScore.donor_id == donor_id)
            .values(
                score=score,
                total_donations=total_donations,
                positive_interactions=positive,
                negative_interactions=negative,
                last_interaction_at=datetime.now(timezone.utc),
            )
        )
        await db.flush()
