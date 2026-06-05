"""
Scheduling Service
===================
AI-assisted donor matching and hospital routing.
AI recommends — coordinator confirms. AI never schedules directly.
"""

from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import TransfusionStatus, UrgencyLevel
from app.repositories.donor_repo import DonorRepository
from app.repositories.hospital_repo import HospitalRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.transfusion_repo import TransfusionRepository
from app.repositories.friendship_repo import FriendshipRepository
from app.ai.matcher import DonorMatchingEngine
from app.ai.response_likelihood import ResponseLikelihoodEngine
from app.ai.friendship import FriendshipScoreEngine
from app.ai.capacity_forecaster import CapacityForecaster
from app.models.transfusion import Transfusion


patient_repo = PatientRepository()
donor_repo = DonorRepository()
hospital_repo = HospitalRepository()
transfusion_repo = TransfusionRepository()
friendship_repo = FriendshipRepository()
matcher = DonorMatchingEngine()
response_engine = ResponseLikelihoodEngine()
friendship_engine = FriendshipScoreEngine()
forecaster = CapacityForecaster()


class SchedulingService:

    async def get_donor_matches(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        limit: int = 10,
    ) -> list:
        """
        Run AI matching engine for a transfusion.
        Returns ranked list of DonorMatchResult objects.
        AI recommends — coordinator must still select the donor manually.
        """
        transfusion = await transfusion_repo.get_by_id(db, transfusion_id)
        if not transfusion:
            raise NotFoundException("Transfusion", str(transfusion_id))

        patient = await patient_repo.get_by_id(db, transfusion.patient_id)
        if not patient:
            raise NotFoundException("Patient", str(transfusion.patient_id))

        # Get hospital location for distance scoring
        hospital_lat, hospital_lng = 13.0827, 80.2707  # Default: Chennai
        if transfusion.hospital_id:
            hospital = await hospital_repo.get_by_id(db, transfusion.hospital_id)
            if hospital and hospital.latitude:
                hospital_lat = float(hospital.latitude)
                hospital_lng = float(hospital.longitude)

        # Get compatible blood groups
        from app.ai.matcher import COMPATIBILITY
        from app.models.enums import BloodGroup
        patient_bg_str = patient.blood_group.value if hasattr(patient.blood_group, 'value') else patient.blood_group
        compatible_groups = [
            bg for bg, recipients in COMPATIBILITY.items()
            if patient_bg_str in recipients
        ]
        compatible_enums = []
        for bg in compatible_groups:
            for enum_val in BloodGroup:
                if enum_val.value == bg:
                    compatible_enums.append(enum_val)
                    break

        # Get eligible compatible donors
        from app.models.donor import Donor
        from sqlalchemy import select, or_, and_
        from datetime import date, timedelta
        from app.models.enums import Gender
        from app.models.confirmation import Confirmation
        from app.models.enums import ConfirmationStatus, ConfirmationRole

        excluded_stmt = (
            select(Confirmation.user_id)
            .where(Confirmation.transfusion_id == transfusion_id)
            .where(Confirmation.role == ConfirmationRole.donor)
            .where(
                or_(
                    Confirmation.status == ConfirmationStatus.rejected,
                    Confirmation.status == ConfirmationStatus.timeout,
                )
            )
        )
        excluded_res = await db.execute(excluded_stmt)
        excluded_user_ids = [row[0] for row in excluded_res.all()]
        
        cooldown_male = date.today() - timedelta(days=90)
        cooldown_female = date.today() - timedelta(days=120)
        stmt = (
            select(Donor)
            .where(Donor.deleted_at.is_(None))
            .where(Donor.is_available == True)  # noqa: E712
            .where(Donor.blood_group.in_(compatible_enums))
            .where(Donor.medical_clearance_url.is_not(None))
            .where(Donor.medical_clearance_url != "")
        )
        if excluded_user_ids:
            stmt = stmt.where(Donor.user_id.not_in(excluded_user_ids))
            
        stmt = stmt.where(
            or_(
                Donor.last_donation_date.is_(None),
                and_(
                    Donor.gender == Gender.male,
                    Donor.last_donation_date <= cooldown_male,
                ),
                and_(
                    Donor.gender == Gender.female,
                    Donor.last_donation_date <= cooldown_female,
                ),
                and_(
                    Donor.gender.not_in([Gender.male, Gender.female]),
                    Donor.last_donation_date <= cooldown_male,
                ),
            )
        ).limit(100)

        res_candidates = await db.execute(stmt)
        candidates = list(res_candidates.scalars().all())

        if not candidates:
            return []

        # Learn the pattern of donor how frequently they accept requests
        from app.models.confirmation import Confirmation
        from app.models.enums import ConfirmationStatus, ConfirmationRole
        
        candidate_user_ids = [d.user_id for d in candidates]
        conf_stmt = (
            select(Confirmation)
            .where(Confirmation.user_id.in_(candidate_user_ids))
            .where(Confirmation.role == ConfirmationRole.donor)
            .where(Confirmation.status == ConfirmationStatus.confirmed)
            .order_by(Confirmation.user_id, Confirmation.responded_at.asc())
        )
        conf_res = await db.execute(conf_stmt)
        all_confirmations = list(conf_res.scalars().all())
        
        user_conf_dates = {}
        for c in all_confirmations:
            if c.responded_at:
                c_date = c.responded_at.date() if hasattr(c.responded_at, 'date') else c.responded_at
                user_conf_dates.setdefault(c.user_id, []).append(c_date)
                
        learned_gaps = {}
        for d in candidates:
            dates_list = user_conf_dates.get(d.user_id, [])
            if len(dates_list) >= 2:
                gaps = []
                for idx in range(1, len(dates_list)):
                    gaps.append((dates_list[idx] - dates_list[idx-1]).days)
                if gaps:
                    learned_gaps[d.id] = sum(gaps) / len(gaps)

        # Build friendship score map for this patient
        friendship_scores_raw = await friendship_repo.get_for_patient(db, patient.id)
        friendship_scores = {
            fs.donor_id: float(fs.score) for fs in friendship_scores_raw
        }

        # Build response likelihood map with personalized frequency learning
        response_likelihoods = {}
        for d in candidates:
            prob = response_engine.predict(
                donor=d,
                transfusion=transfusion,
                friendship_score=friendship_scores.get(d.id, 0.0),
            ).probability
            
            avg_gap = learned_gaps.get(d.id)
            if avg_gap and d.last_donation_date:
                days_since = (date.today() - d.last_donation_date).days
                if days_since < avg_gap:
                    multiplier = max(0.5, days_since / avg_gap)
                    prob = prob * multiplier
                    
            response_likelihoods[d.id] = prob

        # Build previous completed donations count for each candidate to the patient
        from app.models.donation import Donation
        from app.models.transfusion import Transfusion
        from app.models.enums import DonationStatus
        from sqlalchemy import func

        history_stmt = (
            select(Donation.donor_id, func.count(Donation.id))
            .join(Transfusion, Donation.transfusion_id == Transfusion.id)
            .where(Transfusion.patient_id == patient.id)
            .where(Donation.status == DonationStatus.completed)
            .group_by(Donation.donor_id)
        )
        history_res = await db.execute(history_stmt)
        previous_donations_counts = {row[0]: row[1] for row in history_res.all()}

        # Get last donor ID for rotation penalty
        from sqlalchemy import select
        last_donor_id = None
        last_transf_stmt = (
            select(Transfusion.donor_id)
            .where(Transfusion.patient_id == patient.id)
            .where(Transfusion.donor_id.is_not(None))
            .where(Transfusion.id != transfusion_id)
            .where(
                Transfusion.status.in_([
                    TransfusionStatus.completed,
                    TransfusionStatus.scheduled,
                    TransfusionStatus.in_progress,
                    TransfusionStatus.donor_confirmed,
                    TransfusionStatus.coordinator_confirmed,
                    TransfusionStatus.hospital_confirmed,
                ])
            )
            .order_by(Transfusion.created_at.desc())
            .limit(1)
        )
        last_transf_res = await db.execute(last_transf_stmt)
        last_donor_id = last_transf_res.scalar_one_or_none()

        # Run matching engine
        results = matcher.rank_donors(
            candidates=candidates,
            patient_blood_group=patient_bg_str,
            hospital_lat=hospital_lat,
            hospital_lng=hospital_lng,
            response_likelihoods=response_likelihoods,
            friendship_scores=friendship_scores,
            previous_donations_counts=previous_donations_counts,
            is_emergency=getattr(transfusion, 'is_emergency', False),
            last_donor_id=last_donor_id,
            learned_gaps=learned_gaps,
        )

        return results[:limit]

    async def get_upcoming_transfusions(
        self,
        db: AsyncSession,
        days: int = 14,
        urgency: UrgencyLevel | None = None,
    ) -> list:
        return await transfusion_repo.get_upcoming(db, days=days, urgency=urgency)

    async def route_alternate_hospital(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
    ) -> list:
        """
        When primary hospital rejects, find alternatives.
        Returns hospitals sorted by predicted availability.
        """
        transfusion = await transfusion_repo.get_by_id(db, transfusion_id)
        if not transfusion:
            raise NotFoundException("Transfusion", str(transfusion_id))

        patient = await patient_repo.get_by_id(db, transfusion.patient_id)
        alternatives = await hospital_repo.get_by_city(db, patient.city if patient else "")

        # Filter out the rejected hospital
        if transfusion.hospital_id:
            alternatives = [h for h in alternatives if h.id != transfusion.hospital_id]

        return alternatives

    async def get_unresponsive_donors(self, db: AsyncSession) -> list:
        """
        Query transfusion requests where the assigned donor hasn't responded.
        Condition: donor confirmation is pending, and confirmation request has
        been sent (created_at > 6 hours ago OR reminder_count >= 1).
        """
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import select, or_
        from app.models.transfusion import Transfusion
        from app.models.confirmation import Confirmation
        from app.models.enums import DonorConfirmation, ConfirmationStatus, ConfirmationRole
        from app.repositories.user_repo import UserRepository
        user_repo = UserRepository()

        from sqlalchemy.orm import selectinload

        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        
        stmt = (
            select(Confirmation)
            .options(selectinload(Confirmation.transfusion))
            .join(Transfusion, Confirmation.transfusion_id == Transfusion.id)
            .where(Confirmation.role == ConfirmationRole.donor)
            .where(Confirmation.status == ConfirmationStatus.pending)
            .where(Transfusion.donor_confirmation == DonorConfirmation.pending)
            .where(
                or_(
                    Confirmation.created_at < cutoff,
                    Confirmation.reminder_count >= 1
                )
            )
        )
        res = await db.execute(stmt)
        confirmations = list(res.scalars().all())
        
        results = []
        for c in confirmations:
            transfusion = c.transfusion
            donor = await donor_repo.get_by_id(db, transfusion.donor_id)
            if not donor:
                continue
            donor_user = await user_repo.get_by_id(db, donor.user_id)
            phone = donor_user.phone if donor_user else "N/A"
            
            patient = await patient_repo.get_by_id(db, transfusion.patient_id)
            patient_name = patient.name if patient else "N/A"
            
            hospital_name = "N/A"
            if transfusion.hospital_id:
                hosp = await hospital_repo.get_by_id(db, transfusion.hospital_id)
                hospital_name = hosp.name if hosp else "N/A"
                
            results.append({
                "transfusion_id": str(transfusion.id),
                "scheduled_date": transfusion.scheduled_date.isoformat() if transfusion.scheduled_date else transfusion.predicted_date.isoformat() if transfusion.predicted_date else None,
                "urgency_level": transfusion.urgency_level.value,
                "patient_name": patient_name,
                "hospital_name": hospital_name,
                "donor_id": str(donor.id),
                "donor_name": donor.name,
                "donor_phone": phone,
                "donor_upi": donor.upi_id,
                "donor_email": donor_user.email if donor_user else "N/A",
                "reminder_count": c.reminder_count,
                "created_at": c.created_at.isoformat(),
            })
        return results

    async def override_donor(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        new_donor_id: UUID,
    ) -> Transfusion:
        """
        Manually override the assigned donor.
        Penalizes the unresponsive donor by reducing their reliability score.
        Assigns the new donor and sets confirmation trail to pending.
        """
        from decimal import Decimal
        from sqlalchemy import select, update
        from app.models.confirmation import Confirmation
        from app.models.enums import ConfirmationStatus, ConfirmationRole, DonorConfirmation
        from app.models.donation import Donation
        from app.models.enums import DonationStatus
        from app.core.exceptions import BadRequestException
        
        t = await transfusion_repo.get_by_id(db, transfusion_id)
        if not t:
            raise NotFoundException("Transfusion", str(transfusion_id))
            
        previous_donor_id = t.donor_id
        if not previous_donor_id:
            raise BadRequestException("Transfusion does not have a donor assigned to override")

        patient_id = t.patient_id
        hospital_id = t.hospital_id
        coordinator_id = t.coordinator_id
        is_emergency = t.is_emergency
        patient_confirmation_value = t.patient_confirmation.value if hasattr(t.patient_confirmation, 'value') else str(t.patient_confirmation)

        # 1. Penalize previous donor reliability score (reduce by 15%)
        prev_donor = await donor_repo.get_by_id(db, previous_donor_id)
        if prev_donor:
            old_score = float(prev_donor.reliability_score or 50.0)
            new_score = max(0.0, old_score - 15.0)
            await donor_repo.update_reliability_score(db, previous_donor_id, Decimal(str(new_score)))
            
            from app.services.donor_service import DonorService
            await DonorService().recalculate_reliability(db, previous_donor_id)

        # 2. Update previous donor confirmation status to timeout
        if prev_donor:
            prev_conf_res = await db.execute(
                select(Confirmation)
                .where(Confirmation.transfusion_id == transfusion_id)
                .where(Confirmation.user_id == prev_donor.user_id)
                .where(Confirmation.role == ConfirmationRole.donor)
            )
            prev_conf = prev_conf_res.scalar_one_or_none()
            if prev_conf:
                await db.execute(
                    update(Confirmation)
                    .where(Confirmation.id == prev_conf.id)
                    .values(
                        status=ConfirmationStatus.timeout,
                        notes="Overridden by coordinator due to no response"
                    )
                )

        # 3. Cancel scheduled donation for previous donor
        donation_res = await db.execute(
            select(Donation)
            .where(Donation.transfusion_id == transfusion_id)
            .where(Donation.donor_id == previous_donor_id)
        )
        donation = donation_res.scalar_one_or_none()
        if donation:
            from app.repositories.base import BaseRepository
            donation_repo = BaseRepository(Donation)
            await donation_repo.update(db, donation.id, {
                "status": DonationStatus.cancelled,
                "notes": "Overridden by coordinator due to no response"
            })

        # 4. Update Transfusion donor link and reset status
        await transfusion_repo.update(db, transfusion_id, {
            "donor_id": new_donor_id,
            "donor_confirmation": DonorConfirmation.pending,
            "previous_donor_id": previous_donor_id,
        })

        # 5. Create confirmation trail for new donor
        new_donor = await donor_repo.get_by_id(db, new_donor_id)
        if new_donor:
            new_conf_res = await db.execute(
                select(Confirmation)
                .where(Confirmation.transfusion_id == transfusion_id)
                .where(Confirmation.user_id == new_donor.user_id)
                .where(Confirmation.role == ConfirmationRole.donor)
            )
            new_conf = new_conf_res.scalar_one_or_none()
            if new_conf:
                await db.execute(
                    update(Confirmation)
                    .where(Confirmation.id == new_conf.id)
                    .values(
                        status=ConfirmationStatus.pending,
                        notes=None,
                        responded_at=None,
                        reminder_count=0
                    )
                )
            else:
                from app.repositories.confirmation_repo import ConfirmationRepository
                c_repo = ConfirmationRepository()
                await c_repo.create(db, {
                    "transfusion_id": transfusion_id,
                    "user_id": new_donor.user_id,
                    "role": ConfirmationRole.donor,
                    "status": ConfirmationStatus.pending,
                })
            
            from app.services.donor_service import DonorService
            await DonorService().recalculate_reliability(db, new_donor_id)

            # --- Dispatches notifications & resets confirmations for other stakeholders ---
            from app.services.notification_service import NotificationService
            from app.models.enums import NotificationType, NotificationPriority
            notif_service = NotificationService()

            # Get patient and hospital profiles
            patient = await patient_repo.get_by_id(db, patient_id)
            hospital = await hospital_repo.get_by_id(db, hospital_id) if hospital_id else None
            coordinator = None
            if coordinator_id:
                from app.repositories.coordinator_repo import CoordinatorRepository
                coordinator = await CoordinatorRepository().get_by_id(db, coordinator_id)

            # Helper to create/reset confirmation
            async def create_or_reset_confirmation(user_id: UUID, role: ConfirmationRole, status: ConfirmationStatus):
                existing_conf_res = await db.execute(
                    select(Confirmation)
                    .where(Confirmation.transfusion_id == transfusion_id)
                    .where(Confirmation.user_id == user_id)
                    .where(Confirmation.role == role)
                )
                existing = existing_conf_res.scalar_one_or_none()
                if existing:
                    await db.execute(
                        update(Confirmation)
                        .where(Confirmation.id == existing.id)
                        .values(
                            status=status,
                            notes=None,
                            responded_at=None,
                            reminder_count=0
                        )
                    )
                else:
                    from app.repositories.confirmation_repo import ConfirmationRepository
                    c_repo = ConfirmationRepository()
                    await c_repo.create(db, {
                        "transfusion_id": transfusion_id,
                        "user_id": user_id,
                        "role": role,
                        "status": status,
                        "notes": None,
                    })

            # Send Notification to New Donor
            priority = NotificationPriority.emergency if is_emergency else NotificationPriority.high
            notif_type = NotificationType.emergency_alert if is_emergency else NotificationType.donation_request
            title = "🚨 Urgent: Donation Request Matched (Override)" if is_emergency else "New Donation Request (Override)"
            message = "An emergency transfusion matches your compatible blood profile. Please respond immediately." if is_emergency else "You have been matched for a transfusion request by override. Please confirm your availability."
            
            await notif_service.create_notification(
                db,
                user_id=new_donor.user_id,
                type=notif_type,
                title=title,
                message=message,
                transfusion_id=transfusion_id,
                priority=priority,
            )

            # Update and Notify Patient
            if patient:
                p_status = ConfirmationStatus.confirmed if patient_confirmation_value == "confirmed" else ConfirmationStatus.pending
                await create_or_reset_confirmation(patient.user_id, ConfirmationRole.patient, p_status)
                await notif_service.create_notification(
                    db,
                    user_id=patient.user_id,
                    type=NotificationType.system,
                    title="Donor Updated for Transfusion",
                    message=f"The matched donor for your transfusion has been updated to {new_donor.name}. We are waiting for their confirmation.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.normal,
                )

            # Update and Notify Hospital
            if hospital:
                await create_or_reset_confirmation(hospital.user_id, ConfirmationRole.hospital, ConfirmationStatus.pending)
                await notif_service.create_notification(
                    db,
                    user_id=hospital.user_id,
                    type=NotificationType.confirmation_request,
                    title="Capacity Confirmation Updated",
                    message=f"A new donor ({new_donor.name}) has been assigned to transfusion {transfusion_id} at your hospital. Please re-confirm capacity.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.high,
                )

            # Update Coordinator Confirmation
            if coordinator:
                await create_or_reset_confirmation(coordinator.user_id, ConfirmationRole.coordinator, ConfirmationStatus.pending)

        db.expire_all()
        return await transfusion_repo.get_by_id(db, transfusion_id)

    async def override_hospital(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        hospital_id: UUID,
    ) -> Transfusion:
        """
        Manually override/force-assign the hospital for a transfusion.
        Resets confirmations and notifies all parties.
        """
        from app.models.enums import ConfirmationStatus, ConfirmationRole, PatientConfirmation, DonorConfirmation, HospitalConfirmation
        from app.models.confirmation import Confirmation
        from sqlalchemy import select, delete
        
        t = await transfusion_repo.get_by_id(db, transfusion_id)
        if not t:
            raise NotFoundException("Transfusion", str(transfusion_id))
            
        # Update transfusion columns
        await transfusion_repo.update(db, transfusion_id, {
            "hospital_id": hospital_id,
            "alternate_hospital_id": None,
            "hospital_confirmation": HospitalConfirmation.pending,
            "patient_confirmation": PatientConfirmation.pending,
            "donor_confirmation": DonorConfirmation.pending,
        })
        
        # Reset confirmation records for this transfusion
        await db.execute(
            delete(Confirmation).where(Confirmation.transfusion_id == transfusion_id)
        )
        
        # Create new pending confirmation trail
        from app.repositories.confirmation_repo import ConfirmationRepository
        c_repo = ConfirmationRepository()
        
        # 1. Patient confirmation
        patient = await patient_repo.get_by_id(db, t.patient_id)
        if patient:
            await c_repo.create(db, {
                "transfusion_id": transfusion_id,
                "user_id": patient.user_id,
                "role": ConfirmationRole.patient,
                "status": ConfirmationStatus.pending,
            })
            
        # 2. Donor confirmation
        if t.donor_id:
            donor = await donor_repo.get_by_id(db, t.donor_id)
            if donor:
                await c_repo.create(db, {
                    "transfusion_id": transfusion_id,
                    "user_id": donor.user_id,
                    "role": ConfirmationRole.donor,
                    "status": ConfirmationStatus.pending,
                })
                
        # 3. New Hospital confirmation
        new_hosp = await hospital_repo.get_by_id(db, hospital_id)
        if new_hosp:
            await c_repo.create(db, {
                "transfusion_id": transfusion_id,
                "user_id": new_hosp.user_id,
                "role": ConfirmationRole.hospital,
                "status": ConfirmationStatus.pending,
            })
            
            # Send notification to the new hospital
            from app.services.notification_service import NotificationService
            from app.models.enums import NotificationType
            await NotificationService().create_notification(
                db,
                user_id=new_hosp.user_id,
                type=NotificationType.system,
                title="Hospital Assigned Manually",
                message=f"You have been manually assigned to transfusion request {transfusion_id}. Please confirm capacity.",
                transfusion_id=transfusion_id
            )
            
        db.expire_all()
        return await transfusion_repo.get_by_id(db, transfusion_id)

