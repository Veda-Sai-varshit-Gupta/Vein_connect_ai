from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coordinator import Coordinator
from app.models.enums import ApprovalStatus
from app.repositories.base import BaseRepository


class CoordinatorRepository(BaseRepository[Coordinator]):
    def __init__(self):
        super().__init__(Coordinator)

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Coordinator | None:
        result = await db.execute(
            select(Coordinator)
            .where(Coordinator.user_id == user_id)
            .where(Coordinator.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_pending_approvals(self, db: AsyncSession) -> list[Coordinator]:
        result = await db.execute(
            select(Coordinator)
            .where(Coordinator.approval_status == ApprovalStatus.pending)
            .where(Coordinator.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def get_by_region(self, db: AsyncSession, region: str) -> list[Coordinator]:
        result = await db.execute(
            select(Coordinator)
            .where(Coordinator.assigned_region.ilike(f"%{region}%"))
            .where(Coordinator.approval_status == ApprovalStatus.approved)
            .where(Coordinator.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def approve(self, db: AsyncSession, coordinator_id: UUID, approved_by: UUID) -> None:
        await db.execute(
            update(Coordinator)
            .where(Coordinator.id == coordinator_id)
            .values(
                approval_status=ApprovalStatus.approved,
                approved_by=approved_by,
                approved_at=datetime.now(timezone.utc),
            )
        )
        await db.flush()

    async def reject(self, db: AsyncSession, coordinator_id: UUID, reason: str) -> None:
        await db.execute(
            update(Coordinator)
            .where(Coordinator.id == coordinator_id)
            .values(
                approval_status=ApprovalStatus.rejected,
                rejection_reason=reason,
            )
        )
        await db.flush()
