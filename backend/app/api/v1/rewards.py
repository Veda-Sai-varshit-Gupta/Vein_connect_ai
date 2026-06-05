"""
Reward Routes
==============
GET    /rewards/me/summary          current donor's points + tier
GET    /rewards/me/history          reward history
POST   /rewards/convert             convert points → INR wallet credit
GET    /rewards/leaderboard         top 10 donors
POST   /rewards/manual-award        (admin) manually award points
"""

from uuid import UUID
from fastapi import APIRouter
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.reward import (
    ConvertPointsRequest,
    ManualAwardRequest,
    RewardResponse,
    RewardSummaryResponse,
)
from app.services.reward_service import RewardService
from app.repositories.reward_repo import RewardRepository
from app.repositories.donor_repo import DonorRepository

router = APIRouter()
reward_service = RewardService()
reward_repo = RewardRepository()
donor_repo = DonorRepository()


@router.get("/me/summary", response_model=RewardSummaryResponse)
async def get_my_reward_summary(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.donor])
    donor = await donor_repo.get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
    return await reward_service.get_summary(db, donor.id)


@router.get("/me/history", response_model=list[RewardResponse])
async def get_my_reward_history(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
):
    require_role(current_user, [UserRole.donor])
    donor = await donor_repo.get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
    return await reward_repo.get_by_donor(db, donor.id, pagination.offset, pagination.page_size)


@router.post("/convert")
async def convert_points(
    data: ConvertPointsRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.donor])
    donor = await donor_repo.get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
    return await reward_service.convert_points(db, donor.id, data.points)


@router.get("/leaderboard")
async def get_leaderboard(current_user: CurrentUser, db: DbSession):
    """Top 10 donors by total reward points."""
    donors = await donor_repo.get_all(db, limit=100)
    leaderboard = []
    for donor in donors:
        total = await reward_repo.get_total_points(db, donor.id)
        leaderboard.append({
            "donor_id": donor.id,
            "donor_name": donor.name,
            "total_points": total,
            "total_donations": donor.total_donations,
        })
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    for i, entry in enumerate(leaderboard[:10], 1):
        entry["rank"] = i
    return leaderboard[:10]


@router.post("/manual-award", response_model=RewardResponse)
async def manual_award(
    data: ManualAwardRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.admin])
    return await reward_service.award_points(
        db, data.donor_id, data.type, description=data.description
    )
