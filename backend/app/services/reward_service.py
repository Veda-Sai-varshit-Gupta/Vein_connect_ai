"""
Reward Service
===============
Points management, tier calculation, and leaderboard.
"""

from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.enums import RewardType, TransactionCategory, TransactionType, TransactionStatus
from app.repositories.donor_repo import DonorRepository
from app.repositories.reward_repo import RewardRepository
from app.repositories.wallet_repo import WalletRepository

donor_repo = DonorRepository()
reward_repo = RewardRepository()
wallet_repo = WalletRepository()

# Tier thresholds
TIERS = [
    (2000, "Platinum"),
    (1000, "Gold"),
    (500, "Silver"),
    (0, "Bronze"),
]

# Points per reward type
POINTS_MAP = {
    RewardType.donation: 100,
    RewardType.emergency_donation: 200,
    RewardType.consistency_bonus: 50,
    RewardType.rare_blood_group: 150,
    RewardType.referral: 50,
    RewardType.milestone: 500,
}

POINTS_TO_INR_RATIO = 0.5  # 1 point = ₹0.50
MIN_CONVERSION = 100  # Min 100 points to convert


def compute_tier(total_points: int) -> str:
    for threshold, tier in TIERS:
        if total_points >= threshold:
            return tier
    return "Bronze"


class RewardService:

    async def award_points(
        self,
        db: AsyncSession,
        donor_id: UUID,
        reward_type: RewardType,
        donation_id: UUID | None = None,
        description: str | None = None,
    ):
        points = POINTS_MAP.get(reward_type, 50)
        return await reward_repo.create(db, {
            "donor_id": donor_id,
            "donation_id": donation_id,
            "type": reward_type,
            "points": points,
            "description": description or reward_type.value.replace("_", " ").title(),
        })

    async def get_summary(self, db: AsyncSession, donor_id: UUID) -> dict:
        total = await reward_repo.get_total_points(db, donor_id)
        breakdown = await reward_repo.get_points_by_type(db, donor_id)
        
        tier = compute_tier(total)
        
        # Determine levels and next tier metrics
        if tier == "Platinum":
            tier_level = 4
            points_to_next = 0
            next_tier = None
        elif tier == "Gold":
            tier_level = 3
            points_to_next = 2000 - total
            next_tier = "Platinum"
        elif tier == "Silver":
            tier_level = 2
            points_to_next = 1000 - total
            next_tier = "Gold"
        else:
            tier_level = 1
            points_to_next = 500 - total
            next_tier = "Silver"

        return {
            "donor_id": donor_id,
            "total_points": total,
            "tier": tier,
            "tier_level": tier_level,
            "points_to_next_tier": max(0, points_to_next),
            "next_tier": next_tier,
            "breakdown": breakdown,
        }

    async def convert_points(
        self,
        db: AsyncSession,
        donor_id: UUID,
        points: int,
    ) -> dict:
        if points < MIN_CONVERSION:
            raise BadRequestException(f"Minimum {MIN_CONVERSION} points required for conversion")

        total = await reward_repo.get_total_points(db, donor_id)
        if total < points:
            raise BadRequestException(f"Insufficient points. You have {total}, requested {points}")

        inr_amount = points * POINTS_TO_INR_RATIO
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor profile not found")
        
        wallet = await wallet_repo.get_by_user_id(db, donor.user_id)
        if not wallet:
            # Create wallet on the fly for legacy or test users
            wallet = await wallet_repo.create_wallet(db, donor.user_id)
            
        decimal_amount = Decimal(str(inr_amount))
        await wallet_repo.credit(db, wallet.id, decimal_amount)
        await wallet_repo.create_transaction(db, {
            "wallet_id": wallet.id,
            "type": TransactionType.credit,
            "category": TransactionCategory.reward_conversion,
            "amount": decimal_amount,
            "description": f"{points} reward points converted to ₹{inr_amount}",
            "status": TransactionStatus.completed,
        })

        # Deduct by creating a negative reward entry
        await reward_repo.create(db, {
            "donor_id": donor_id,
            "type": RewardType.milestone,
            "points": -points,
            "description": f"Converted {points} points to ₹{inr_amount}",
        })

        return {"converted_points": points, "inr_credited": inr_amount}
