from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hospital import Hospital
from app.models.hospital_capacity import HospitalCapacity
from app.repositories.base import BaseRepository


class HospitalRepository(BaseRepository[Hospital]):
    def __init__(self):
        super().__init__(Hospital)

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Hospital | None:
        result = await db.execute(
            select(Hospital)
            .where(Hospital.user_id == user_id)
            .where(Hospital.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_city(self, db: AsyncSession, city: str) -> list[Hospital]:
        result = await db.execute(
            select(Hospital)
            .where(Hospital.city.ilike(f"%{city}%"))
            .where(Hospital.is_active == True)  # noqa: E712
            .where(Hospital.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def get_with_capacity(self, db: AsyncSession, hospital_id: UUID) -> Hospital | None:
        result = await db.execute(
            select(Hospital)
            .options(selectinload(Hospital.capacity))
            .where(Hospital.id == hospital_id)
            .where(Hospital.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_capacity(self, db: AsyncSession, hospital_id: UUID) -> HospitalCapacity | None:
        result = await db.execute(
            select(HospitalCapacity).where(HospitalCapacity.hospital_id == hospital_id)
        )
        return result.scalar_one_or_none()

    async def upsert_capacity(self, db: AsyncSession, hospital_id: UUID, data: dict) -> HospitalCapacity:
        """Update capacity if exists, create if not."""
        from datetime import datetime, timezone
        existing = await self.get_capacity(db, hospital_id)
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            existing.last_updated_at = datetime.now(timezone.utc)
            await db.flush()
            return existing
        else:
            capacity = HospitalCapacity(hospital_id=hospital_id, **data)
            db.add(capacity)
            await db.flush()
            await db.refresh(capacity)
            return capacity
