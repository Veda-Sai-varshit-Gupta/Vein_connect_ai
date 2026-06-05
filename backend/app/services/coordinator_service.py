"""
Coordinator Service
====================
Registration, approval workflow, and region management.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ForbiddenException
from app.models.coordinator import Coordinator
from app.models.enums import ApprovalStatus
from app.repositories.coordinator_repo import CoordinatorRepository
from app.repositories.user_repo import UserRepository
from app.schemas.coordinator import CoordinatorCreate, CoordinatorUpdate

coordinator_repo = CoordinatorRepository()
user_repo = UserRepository()


class CoordinatorService:

    async def register(self, db: AsyncSession, user_id: UUID, data: CoordinatorCreate) -> Coordinator:
        if await coordinator_repo.get_by_user_id(db, user_id):
            raise ConflictException("Coordinator profile already exists for this account")

        return await coordinator_repo.create(db, {
            "user_id": user_id,
            "name": data.name,
            "phone": data.phone,
            "organization": data.organization,
            "assigned_region": data.assigned_region,
            "approval_status": ApprovalStatus.approved,
        })

    async def get_coordinator(self, db: AsyncSession, coordinator_id: UUID) -> Coordinator:
        coord = await coordinator_repo.get_by_id(db, coordinator_id)
        if not coord:
            raise NotFoundException("Coordinator", str(coordinator_id))
        return coord

    async def approve(self, db: AsyncSession, coordinator_id: UUID, approved_by: UUID) -> Coordinator:
        coord = await coordinator_repo.get_by_id(db, coordinator_id)
        if not coord:
            raise NotFoundException("Coordinator", str(coordinator_id))
        if coord.approval_status == ApprovalStatus.approved:
            raise ConflictException("Coordinator is already approved")

        await coordinator_repo.approve(db, coordinator_id, approved_by)
        # Activate the user account
        await user_repo.set_active(db, coord.user_id, True)
        return await coordinator_repo.get_by_id(db, coordinator_id)

    async def reject(self, db: AsyncSession, coordinator_id: UUID, reason: str) -> Coordinator:
        coord = await coordinator_repo.get_by_id(db, coordinator_id)
        if not coord:
            raise NotFoundException("Coordinator", str(coordinator_id))

        await coordinator_repo.reject(db, coordinator_id, reason)
        return await coordinator_repo.get_by_id(db, coordinator_id)

    async def get_pending_approvals(self, db: AsyncSession) -> list[Coordinator]:
        return await coordinator_repo.get_pending_approvals(db)
