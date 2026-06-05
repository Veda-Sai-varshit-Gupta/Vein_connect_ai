from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import Donor
from app.models.enums import BloodGroup
from app.repositories.base import BaseRepository


class DonorRepository(BaseRepository[Donor]):
    def __init__(self):
        super().__init__(Donor)

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Donor | None:
        result = await db.execute(
            select(Donor)
            .where(Donor.user_id == user_id)
            .where(Donor.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_eligible_donors(
        self,
        db: AsyncSession,
        blood_group: BloodGroup,
        city: str | None = None,
        limit: int = 50,
    ) -> list[Donor]:
        """Fetch available donors matching blood group, optionally filtered by city."""
        from datetime import date, timedelta
        from sqlalchemy import or_
        cooldown_date = date.today() - timedelta(days=90)
        stmt = (
            select(Donor)
            .where(Donor.deleted_at.is_(None))
            .where(Donor.is_available == True)  # noqa: E712
            .where(Donor.blood_group == blood_group)
            .where(
                or_(
                    Donor.last_donation_date.is_(None),
                    Donor.last_donation_date <= cooldown_date,
                )
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_available(self, db: AsyncSession, limit: int = 100) -> list[Donor]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Donor)
            .options(selectinload(Donor.user))
            .where(Donor.is_available == True)  # noqa: E712
            .where(Donor.deleted_at.is_(None))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_reliability_score(self, db: AsyncSession, donor_id: UUID, score: Decimal) -> None:
        await db.execute(
            update(Donor).where(Donor.id == donor_id).values(reliability_score=score)
        )
        await db.flush()

    async def toggle_availability(self, db: AsyncSession, donor_id: UUID, is_available: bool) -> None:
        await db.execute(
            update(Donor).where(Donor.id == donor_id).values(is_available=is_available)
        )
        await db.flush()

    async def increment_total_donations(self, db: AsyncSession, donor_id: UUID) -> None:
        await db.execute(
            update(Donor).where(Donor.id == donor_id).values(
                total_donations=Donor.total_donations + 1
            )
        )
        await db.flush()
