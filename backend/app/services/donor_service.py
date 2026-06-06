"""
Donor Service
==============
Registration, profile, availability, and AI scoring.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.donor import Donor
from app.models.enums import UserRole
from app.repositories.donor_repo import DonorRepository
from app.repositories.friendship_repo import FriendshipRepository
from app.schemas.donor import DonorCreate, DonorUpdate, AvailabilityUpdate
from app.ai.reliability import ReliabilityEngine
from app.ai.response_likelihood import ResponseLikelihoodEngine

donor_repo = DonorRepository()
friendship_repo = FriendshipRepository()
reliability_engine = ReliabilityEngine()
response_engine = ResponseLikelihoodEngine()


class DonorService:

    async def register(self, db: AsyncSession, user_id: UUID, data: DonorCreate) -> Donor:
        donor = await donor_repo.get_by_user_id(db, user_id)

        donor_data = {
            "name": data.name,
            "age": data.age,
            "gender": data.gender,
            "blood_group": data.blood_group,
            "last_donation_date": data.last_donation_date,
            "preferred_days": data.preferred_days,
            "preferred_times": data.preferred_times,
            "max_travel_distance_km": data.max_travel_distance_km,
            "communication_preference": data.communication_preference,
            "language_preference": data.language_preference,
            "upi_id": data.upi_id,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "reliability_score": 50.0,  # Default neutral score
            "is_available": True,
            "total_donations": 0,
        }

        if donor:
            return await donor_repo.update(db, donor.id, donor_data)
        else:
            return await donor_repo.create(db, {
                "user_id": user_id,
                **donor_data
            })

    async def get_donor(self, db: AsyncSession, donor_id: UUID) -> Donor:
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor", str(donor_id))
        return donor

    async def get_my_profile(self, db: AsyncSession, user_id: UUID) -> Donor:
        donor = await donor_repo.get_by_user_id(db, user_id)
        if not donor:
            raise NotFoundException("Donor profile not found. Please complete registration.")
        return donor

    async def update_profile(
        self,
        db: AsyncSession,
        donor_id: UUID,
        data: DonorUpdate,
        requesting_user_id: UUID,
        requesting_role: UserRole,
    ) -> Donor:
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor", str(donor_id))

        if requesting_role == UserRole.donor and donor.user_id != requesting_user_id:
            raise ForbiddenException("You can only update your own profile")

        return await donor_repo.update(db, donor_id, data.model_dump(exclude_none=True))

    async def toggle_availability(
        self,
        db: AsyncSession,
        donor_id: UUID,
        data: AvailabilityUpdate,
        requesting_user_id: UUID,
    ) -> Donor:
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor", str(donor_id))
        if donor.user_id != requesting_user_id:
            raise ForbiddenException("You can only update your own availability")

        await donor_repo.toggle_availability(db, donor_id, data.is_available)
        donor.is_available = data.is_available
        return donor

    async def recalculate_reliability(self, db: AsyncSession, donor_id: UUID) -> float:
        """Recalculate and persist the donor's reliability score."""
        # Expire all to clear the identity map cache and reload fresh DB values
        db.expire_all()
        
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor", str(donor_id))

        from app.models.donation import Donation
        from app.models.confirmation import Confirmation
        from app.models.enums import ConfirmationRole
        from decimal import Decimal
        from sqlalchemy import select

        from sqlalchemy.orm import selectinload

        # Get all donations for this donor with eager loaded transfusions
        donations_res = await db.execute(
            select(Donation)
            .where(Donation.donor_id == donor_id)
            .where(Donation.deleted_at.is_(None))
            .options(selectinload(Donation.transfusion))
        )
        donations = list(donations_res.scalars().all())

        # Get all confirmations for this donor's user account
        confirmations_res = await db.execute(
            select(Confirmation)
            .where(Confirmation.user_id == donor.user_id)
            .where(Confirmation.role == ConfirmationRole.donor)
        )
        confirmations = list(confirmations_res.scalars().all())

        # Compute new score
        res = reliability_engine.compute(
            donor_id=donor_id,
            donations=donations,
            confirmations=confirmations,
        )
        
        # Save score
        score_decimal = Decimal(str(res.score))
        await donor_repo.update_reliability_score(db, donor_id, score_decimal)
        return float(res.score)

    async def get_scores(self, db: AsyncSession, donor_id: UUID) -> dict:
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor", str(donor_id))

        friendships = await friendship_repo.get_for_donor(db, donor_id)  # All pairs involving this donor
        return {
            "donor_id": donor_id,
            "reliability_score": float(donor.reliability_score),
            "reliability_trend": "stable",  # v2: compute from history
            "total_friendship_pairs": len(friendships),
        }

    async def list_donors(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Donor], int]:
        donors = await donor_repo.get_all(db, skip=skip, limit=limit)
        total = await donor_repo.count(db)
        return donors, total
