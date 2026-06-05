from uuid import UUID
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transfusion import Transfusion
from app.models.enums import TransfusionStatus, UrgencyLevel
from app.repositories.base import BaseRepository


class TransfusionRepository(BaseRepository[Transfusion]):
    def __init__(self):
        super().__init__(Transfusion)

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Transfusion | None:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Transfusion)
            .where(Transfusion.id == id)
            .where(Transfusion.deleted_at.is_(None))
            .options(
                selectinload(Transfusion.patient),
                selectinload(Transfusion.donor),
                selectinload(Transfusion.hospital),
                selectinload(Transfusion.coordinator),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_by_patient(
        self,
        db: AsyncSession,
        patient_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> list[Transfusion]:
        stmt = (
            select(Transfusion)
            .where(Transfusion.patient_id == patient_id)
            .where(Transfusion.deleted_at.is_(None))
        )
        if status:
            if status == "active":
                stmt = stmt.where(Transfusion.status.not_in([
                    TransfusionStatus.completed,
                    TransfusionStatus.cancelled,
                    TransfusionStatus.failed,
                ]))
            else:
                stmt = stmt.where(Transfusion.status == status)
        stmt = stmt.order_by(Transfusion.predicted_date.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        db: AsyncSession,
        status: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Transfusion]:
        stmt = (
            select(Transfusion)
            .where(Transfusion.deleted_at.is_(None))
        )
        if status == "active":
            stmt = stmt.where(Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
                TransfusionStatus.failed,
            ]))
        else:
            stmt = stmt.where(Transfusion.status == status)
        stmt = stmt.order_by(Transfusion.predicted_date.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        db: AsyncSession,
        days: int = 14,
        urgency: UrgencyLevel | None = None,
    ) -> list[Transfusion]:
        from datetime import timedelta
        from sqlalchemy.orm import selectinload
        future_cutoff = date.today() + timedelta(days=days)
        stmt = (
            select(Transfusion)
            .where(Transfusion.predicted_date <= future_cutoff)
            .where(Transfusion.predicted_date >= date.today())
            .where(Transfusion.deleted_at.is_(None))
            .where(Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
                TransfusionStatus.failed,
            ]))
            .options(
                selectinload(Transfusion.patient),
                selectinload(Transfusion.donor),
                selectinload(Transfusion.hospital),
                selectinload(Transfusion.coordinator),
            )
        )
        if urgency:
            stmt = stmt.where(Transfusion.urgency_level == urgency)
        result = await db.execute(stmt.order_by(Transfusion.predicted_date.asc()))
        return list(result.scalars().all())

    async def get_emergency(
        self,
        db: AsyncSession,
    ) -> list[Transfusion]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Transfusion)
            .where(Transfusion.is_emergency == True)  # noqa: E712
            .where(Transfusion.deleted_at.is_(None))
            .where(Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
            ]))
            .options(
                selectinload(Transfusion.patient),
                selectinload(Transfusion.donor),
                selectinload(Transfusion.hospital),
                selectinload(Transfusion.coordinator),
            )
            .order_by(Transfusion.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_coordinator(
        self,
        db: AsyncSession,
        coordinator_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> list[Transfusion]:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Transfusion)
            .where(Transfusion.coordinator_id == coordinator_id)
            .where(Transfusion.deleted_at.is_(None))
        )
        if status:
            if status == "active":
                stmt = stmt.where(Transfusion.status.not_in([
                    TransfusionStatus.completed,
                    TransfusionStatus.cancelled,
                    TransfusionStatus.failed,
                ]))
            else:
                stmt = stmt.where(Transfusion.status == status)
        stmt = stmt.options(
            selectinload(Transfusion.patient),
            selectinload(Transfusion.donor),
            selectinload(Transfusion.hospital),
            selectinload(Transfusion.coordinator),
        ).order_by(Transfusion.predicted_date.asc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_completed_for_patient(self, db: AsyncSession, patient_id: UUID) -> list[Transfusion]:
        result = await db.execute(
            select(Transfusion)
            .where(Transfusion.patient_id == patient_id)
            .where(Transfusion.status == TransfusionStatus.completed)
            .where(Transfusion.deleted_at.is_(None))
            .order_by(Transfusion.actual_date.asc())
        )
        return list(result.scalars().all())
