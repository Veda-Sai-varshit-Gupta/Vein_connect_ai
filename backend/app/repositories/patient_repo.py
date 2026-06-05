from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.models.enums import BloodGroup
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self):
        super().__init__(Patient)

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Patient | None:
        result = await db.execute(
            select(Patient)
            .where(Patient.user_id == user_id)
            .where(Patient.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_with_preferences(self, db: AsyncSession, patient_id: UUID) -> Patient | None:
        result = await db.execute(
            select(Patient)
            .options(selectinload(Patient.hospital_preferences))
            .where(Patient.id == patient_id)
            .where(Patient.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_blood_group(self, db: AsyncSession, blood_group: BloodGroup) -> list[Patient]:
        result = await db.execute(
            select(Patient)
            .where(Patient.blood_group == blood_group)
            .where(Patient.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def get_by_city(self, db: AsyncSession, city: str, skip: int = 0, limit: int = 20) -> list[Patient]:
        result = await db.execute(
            select(Patient)
            .where(Patient.city.ilike(f"%{city}%"))
            .where(Patient.deleted_at.is_(None))
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())
