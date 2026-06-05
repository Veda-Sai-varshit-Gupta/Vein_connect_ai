from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense_request import ExpenseRequest
from app.models.enums import ExpenseStatus
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository[ExpenseRequest]):
    def __init__(self):
        super().__init__(ExpenseRequest)

    async def get_by_donor(self, db: AsyncSession, donor_id: UUID, skip: int = 0, limit: int = 20) -> list[ExpenseRequest]:
        result = await db.execute(
            select(ExpenseRequest)
            .where(ExpenseRequest.donor_id == donor_id)
            .where(ExpenseRequest.deleted_at.is_(None))
            .order_by(ExpenseRequest.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending(self, db: AsyncSession, flagged_only: bool = False) -> list[ExpenseRequest]:
        stmt = (
            select(ExpenseRequest)
            .where(ExpenseRequest.status == ExpenseStatus.pending)
            .where(ExpenseRequest.deleted_at.is_(None))
        )
        if flagged_only:
            stmt = stmt.where(ExpenseRequest.is_flagged_by_ai == True)  # noqa: E712
        result = await db.execute(stmt.order_by(ExpenseRequest.created_at.asc()))
        return list(result.scalars().all())
