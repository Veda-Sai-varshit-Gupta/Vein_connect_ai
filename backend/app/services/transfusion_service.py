"""
Transfusion Service
====================
Manages the full transfusion lifecycle (state machine).
AI NEVER schedules — AI recommends, humans confirm.
"""

from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, TransfusionStateException, ForbiddenException
from app.models.enums import TransfusionStatus, UserRole
from app.models.transfusion import Transfusion
from app.repositories.patient_repo import PatientRepository
from app.repositories.transfusion_repo import TransfusionRepository
from app.schemas.transfusion import TransfusionCreate, TransfusionUpdate, TransfusionCancel, TransfusionComplete

patient_repo = PatientRepository()
transfusion_repo = TransfusionRepository()

# States where cancellation is allowed
CANCELLABLE_STATES = {
    TransfusionStatus.predicted,
    TransfusionStatus.patient_confirmed,
    TransfusionStatus.matching_donors,
    TransfusionStatus.donor_confirmed,
    TransfusionStatus.coordinator_confirmed,
    TransfusionStatus.hospital_confirmed,
    TransfusionStatus.scheduled,
}


class TransfusionService:

    async def create_transfusion(
        self,
        db: AsyncSession,
        patient_id: UUID,
        data: TransfusionCreate,
    ) -> Transfusion:
        from datetime import date
        from app.core.exceptions import BadRequestException
        if data.predicted_date < date.today():
            raise BadRequestException("Transfusion date cannot be in the past")

        # Auto-assign coordinator based on patient's city/region
        patient = await patient_repo.get_by_id(db, patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))
            
        from app.repositories.coordinator_repo import CoordinatorRepository
        coordinator_repo = CoordinatorRepository()
        coords = await coordinator_repo.get_all(db, limit=100)
        assigned_coord_id = None
        patient_city = patient.city.lower() if patient.city else ""
        for c in coords:
            if c.assigned_region and c.assigned_region.lower() in patient_city:
                assigned_coord_id = c.id
                break
        if not assigned_coord_id and coords:
            assigned_coord_id = coords[0].id

        t = await transfusion_repo.create(db, {
            "patient_id": patient_id,
            "predicted_date": data.predicted_date,
            "urgency_level": data.urgency_level,
            "hospital_id": data.hospital_id,
            "coordinator_id": assigned_coord_id,
            "status": TransfusionStatus.predicted,
            "is_emergency": data.is_emergency,
            "emergency_reason": data.emergency_reason,
            "notes": data.notes,
        })
        
        if data.is_emergency:
            await self._notify_emergency(db, t)
            
        return await self.get_transfusion(db, t.id)

    async def _notify_emergency(self, db: AsyncSession, transfusion: Transfusion) -> None:
        from app.services.notification_service import NotificationService
        from app.models.enums import NotificationType, NotificationPriority
        from app.repositories.coordinator_repo import CoordinatorRepository
        from app.repositories.donor_repo import DonorRepository
        from app.repositories.hospital_repo import HospitalRepository
        
        notif_service = NotificationService()
        
        # 1. Notify all coordinators
        coords = await CoordinatorRepository().get_all(db, limit=100)
        for c in coords:
            await notif_service.create_notification(
                db,
                user_id=c.user_id,
                type=NotificationType.emergency_alert,
                title="🚨 Emergency Transfusion Alert",
                message=f"Patient requires an emergency transfusion. Transfusion ID: {transfusion.id}.",
                transfusion_id=transfusion.id,
                priority=NotificationPriority.emergency
            )
            
        # 2. Notify hospital if assigned
        if transfusion.hospital_id:
            hosp = await HospitalRepository().get_by_id(db, transfusion.hospital_id)
            if hosp:
                await notif_service.create_notification(
                    db,
                    user_id=hosp.user_id,
                    type=NotificationType.emergency_alert,
                    title="🚨 Emergency Transfusion Assigned",
                    message=f"Emergency transfusion assigned to your hospital. Transfusion ID: {transfusion.id}.",
                    transfusion_id=transfusion.id,
                    priority=NotificationPriority.emergency
                )

        # 3. Notify eligible compatible donors
        from app.services.scheduling_service import SchedulingService
        try:
            matches = await SchedulingService().get_donor_matches(db, transfusion.id, limit=10)
            donor_repo = DonorRepository()
            for m in matches:
                donor = await donor_repo.get_by_id(db, m.donor_id)
                if donor:
                    await notif_service.create_notification(
                        db,
                        user_id=donor.user_id,
                        type=NotificationType.emergency_alert,
                        title="🚨 Urgent: Emergency Donation Request",
                        message=f"An emergency transfusion matches your compatible blood profile. Please respond immediately.",
                        transfusion_id=transfusion.id,
                        priority=NotificationPriority.emergency
                    )
        except Exception:
            pass


    async def get_transfusion(self, db: AsyncSession, transfusion_id: UUID) -> Transfusion:
        t = await transfusion_repo.get_by_id(db, transfusion_id)
        if not t:
            raise NotFoundException("Transfusion", str(transfusion_id))
        return t

    async def patient_confirm(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        patient_user_id: UUID,
    ) -> Transfusion:
        """Patient confirms they want to proceed with this transfusion."""
        t = await self.get_transfusion(db, transfusion_id)

        if t.status != TransfusionStatus.predicted:
            raise TransfusionStateException(t.status.value, "patient_confirm")

        # Verify the patient owns this transfusion
        patient = await patient_repo.get_by_user_id(db, patient_user_id)
        if not patient or patient.id != t.patient_id:
            raise ForbiddenException("You can only confirm your own transfusions")

        from app.models.enums import PatientConfirmation
        updated_t = await transfusion_repo.update(db, transfusion_id, {
            "patient_confirmation": PatientConfirmation.confirmed,
            "status": TransfusionStatus.patient_confirmed,
        })

        # Auto-assign the top AI recommended donor
        from app.services.scheduling_service import SchedulingService
        try:
            matches = await SchedulingService().get_donor_matches(db, transfusion_id, limit=1)
            if matches:
                top_match = matches[0]
                updated_t = await self.assign_donor(db, transfusion_id, top_match.donor_id)
        except Exception:
            pass

        return updated_t

    async def assign_donor(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        donor_id: UUID,
    ) -> Transfusion:
        """Coordinator assigns a matched donor to the transfusion."""
        t = await self.get_transfusion(db, transfusion_id)
        if t.status not in {
            TransfusionStatus.patient_confirmed,
            TransfusionStatus.matching_donors,
        }:
            raise TransfusionStateException(t.status.value, "assign_donor")

        updated_t = await transfusion_repo.update(db, transfusion_id, {
            "donor_id": donor_id,
            "status": TransfusionStatus.matching_donors,
        })

        from app.repositories.patient_repo import PatientRepository
        from app.repositories.donor_repo import DonorRepository
        from app.repositories.hospital_repo import HospitalRepository
        from app.repositories.coordinator_repo import CoordinatorRepository
        from app.repositories.confirmation_repo import ConfirmationRepository
        from app.services.notification_service import NotificationService
        from app.models.enums import ConfirmationRole, ConfirmationStatus, NotificationType, NotificationPriority

        p_repo = PatientRepository()
        d_repo = DonorRepository()
        h_repo = HospitalRepository()
        c_repo = CoordinatorRepository()
        conf_repo = ConfirmationRepository()
        notif_service = NotificationService()

        # Get stakeholder profiles
        patient = await p_repo.get_by_id(db, updated_t.patient_id)
        donor = await d_repo.get_by_id(db, donor_id)
        hospital = await h_repo.get_by_id(db, updated_t.hospital_id) if updated_t.hospital_id else None
        coordinator = await c_repo.get_by_id(db, updated_t.coordinator_id) if updated_t.coordinator_id else None

        # Helper to create/reset confirmation
        async def create_or_reset_confirmation(user_id: UUID, role: ConfirmationRole, status: ConfirmationStatus):
            existing = await conf_repo.get_by_user_and_transfusion(db, user_id, updated_t.id)
            if existing:
                await conf_repo.update(db, existing.id, {
                    "status": status,
                    "notes": None,
                    "responded_at": None,
                    "reminder_count": 0,
                })
            else:
                await conf_repo.create(db, {
                    "transfusion_id": updated_t.id,
                    "user_id": user_id,
                    "role": role,
                    "status": status,
                    "notes": None,
                })

        # 1. Patient Confirmation
        if patient:
            p_status = ConfirmationStatus.confirmed if updated_t.patient_confirmation.value == "confirmed" else ConfirmationStatus.pending
            await create_or_reset_confirmation(patient.user_id, ConfirmationRole.patient, p_status)
            
            # Send Notification to Patient
            await notif_service.create_notification(
                db,
                user_id=patient.user_id,
                type=NotificationType.system,
                title="Donor Matched for Transfusion",
                message=f"A compatible donor ({donor.name if donor else 'Name unavailable'}) has been matched for your scheduled transfusion. We are waiting for their confirmation.",
                transfusion_id=updated_t.id,
                priority=NotificationPriority.normal,
            )

        # 2. Donor Confirmation
        if donor:
            await create_or_reset_confirmation(donor.user_id, ConfirmationRole.donor, ConfirmationStatus.pending)

            # Send Notification to Donor
            priority = NotificationPriority.emergency if updated_t.is_emergency else NotificationPriority.high
            notif_type = NotificationType.emergency_alert if updated_t.is_emergency else NotificationType.donation_request
            title = "🚨 Urgent: Donation Request Matched" if updated_t.is_emergency else "New Donation Request"
            message = "An emergency transfusion matches your compatible blood profile. Please respond immediately." if updated_t.is_emergency else "You have been matched for a transfusion request. Please confirm your availability."
            
            await notif_service.create_notification(
                db,
                user_id=donor.user_id,
                type=notif_type,
                title=title,
                message=message,
                transfusion_id=updated_t.id,
                priority=priority,
            )

        # 3. Hospital Confirmation
        if hospital:
            await create_or_reset_confirmation(hospital.user_id, ConfirmationRole.hospital, ConfirmationStatus.pending)

            # Send Notification to Hospital
            priority = NotificationPriority.emergency if updated_t.is_emergency else NotificationPriority.high
            notif_type = NotificationType.emergency_alert if updated_t.is_emergency else NotificationType.confirmation_request
            title = "🚨 Emergency Capacity Request" if updated_t.is_emergency else "Hospital Capacity Request"
            message = f"Emergency capacity request received for transfusion {updated_t.id}. Please confirm bed/chair availability." if updated_t.is_emergency else f"A donor has been assigned to transfusion {updated_t.id} at your hospital. Please confirm bed/chair availability."
            
            await notif_service.create_notification(
                db,
                user_id=hospital.user_id,
                type=notif_type,
                title=title,
                message=message,
                transfusion_id=updated_t.id,
                priority=priority,
            )

        # 4. Coordinator Confirmation
        if coordinator:
            await create_or_reset_confirmation(coordinator.user_id, ConfirmationRole.coordinator, ConfirmationStatus.pending)

        db.expire_all()
        return await transfusion_repo.get_by_id(db, transfusion_id)

    async def update_transfusion(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        data: TransfusionUpdate,
    ) -> Transfusion:
        """Update transfusion properties like scheduled date or notes."""
        t = await self.get_transfusion(db, transfusion_id)
        
        update_data = {}
        if data.scheduled_date is not None:
            update_data["scheduled_date"] = data.scheduled_date
        if data.hospital_id is not None:
            update_data["hospital_id"] = data.hospital_id
        if data.coordinator_id is not None:
            update_data["coordinator_id"] = data.coordinator_id
        if data.notes is not None:
            update_data["notes"] = data.notes

        if not update_data:
            return t

        updated_t = await transfusion_repo.update(db, transfusion_id, update_data)
        
        # If scheduled date is updated, we should update the donation date of any associated donation record
        if data.scheduled_date is not None and updated_t.donor_id:
            from app.models.donation import Donation
            from sqlalchemy import select
            
            donation_res = await db.execute(
                select(Donation)
                .where(Donation.transfusion_id == transfusion_id)
                .where(Donation.donor_id == updated_t.donor_id)
            )
            donation = donation_res.scalar_one_or_none()
            if donation:
                from app.repositories.base import BaseRepository
                donation_repo = BaseRepository(Donation)
                await donation_repo.update(db, donation.id, {"donation_date": data.scheduled_date})

        db.expire_all()
        return await transfusion_repo.get_by_id(db, transfusion_id)

    async def cancel_transfusion(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        reason: str,
        requesting_role: UserRole,
    ) -> Transfusion:
        t = await self.get_transfusion(db, transfusion_id)
        if t.status not in CANCELLABLE_STATES:
            raise TransfusionStateException(t.status.value, "cancel")

        res_transfusion = await transfusion_repo.update(db, transfusion_id, {
            "status": TransfusionStatus.cancelled,
            "notes": f"Cancelled by {requesting_role.value}: {reason}",
        })

        if t.donor_id and t.donor_confirmation.value == "confirmed":
            from app.models.donation import Donation
            from app.models.enums import DonationStatus
            from sqlalchemy import select
            
            is_no_show = "no show" in reason.lower() or "no-show" in reason.lower() or "absent" in reason.lower() or "failed to show" in reason.lower()
            donation_status = DonationStatus.no_show if is_no_show else DonationStatus.cancelled
            
            donation_res = await db.execute(
                select(Donation)
                .where(Donation.transfusion_id == transfusion_id)
                .where(Donation.donor_id == t.donor_id)
            )
            donation = donation_res.scalar_one_or_none()
            if donation:
                from app.repositories.base import BaseRepository
                donation_repo = BaseRepository(Donation)
                await donation_repo.update(db, donation.id, {"status": donation_status})
            
            from app.services.donor_service import DonorService
            await DonorService().recalculate_reliability(db, t.donor_id)

        return res_transfusion

    async def mark_completed(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        data: TransfusionComplete,
    ) -> Transfusion:
        t = await self.get_transfusion(db, transfusion_id)
        if t.status != TransfusionStatus.in_progress:
            raise TransfusionStateException(t.status.value, "complete")

        # Eagerly extract user IDs from relationships BEFORE update expires them!
        patient_user_id = t.patient.user_id if t.patient else None
        donor_user_id = t.donor.user_id if t.donor else None
        coordinator_user_id = t.coordinator.user_id if t.coordinator else None
        hospital_user_id = t.hospital.user_id if t.hospital else None
        hospital_name = t.hospital.name if t.hospital else "Hospital"
        is_emergency = t.is_emergency

        # Update actual_date and notes on transfusion but keep status in_progress
        res_transfusion = await transfusion_repo.update(db, transfusion_id, {
            "actual_date": data.actual_date,
            "notes": data.notes,
        })

        # Create CompletionConfirmation records for the 4 stakeholders
        from app.models.completion_confirmation import CompletionConfirmation
        from app.models.enums import ConfirmationStatus, ConfirmationRole, NotificationType, NotificationPriority
        from app.services.notification_service import NotificationService
        from datetime import datetime, timezone
        from sqlalchemy import select

        notif_service = NotificationService()

        confirmations_to_create = []

        if hospital_user_id:
            confirmations_to_create.append({
                "user_id": hospital_user_id,
                "role": ConfirmationRole.hospital,
                "status": ConfirmationStatus.confirmed,
                "responded_at": datetime.now(timezone.utc),
            })
        if patient_user_id:
            confirmations_to_create.append({
                "user_id": patient_user_id,
                "role": ConfirmationRole.patient,
                "status": ConfirmationStatus.pending,
            })
        if donor_user_id:
            confirmations_to_create.append({
                "user_id": donor_user_id,
                "role": ConfirmationRole.donor,
                "status": ConfirmationStatus.pending,
            })
        if coordinator_user_id:
            confirmations_to_create.append({
                "user_id": coordinator_user_id,
                "role": ConfirmationRole.coordinator,
                "status": ConfirmationStatus.pending,
            })

        for conf_data in confirmations_to_create:
            # Check if one already exists for this user/transfusion
            existing_res = await db.execute(
                select(CompletionConfirmation)
                .where(CompletionConfirmation.transfusion_id == transfusion_id)
                .where(CompletionConfirmation.user_id == conf_data["user_id"])
            )
            existing = existing_res.scalar_one_or_none()
            if not existing:
                new_conf = CompletionConfirmation(
                    transfusion_id=transfusion_id,
                    user_id=conf_data["user_id"],
                    role=conf_data["role"],
                    status=conf_data["status"],
                    responded_at=conf_data.get("responded_at"),
                )
                db.add(new_conf)

        await db.flush()

        # Notify Patient, Donor, Coordinator that transfusion is completed and they need to confirm
        recipients = []
        if patient_user_id:
            recipients.append((patient_user_id, "Patient"))
        if donor_user_id:
            recipients.append((donor_user_id, "Donor"))
        if coordinator_user_id:
            recipients.append((coordinator_user_id, "Coordinator"))

        for recipient_user_id, role_name in recipients:
            try:
                await notif_service.create_notification(
                    db,
                    user_id=recipient_user_id,
                    type=NotificationType.confirmation_request,
                    title="Transfusion Completion Confirmation Needed",
                    message=f"Hospital {hospital_name} has marked transfusion Run #{transfusion_id} as completed. Please confirm from your dashboard that the transfusion was completed successfully.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.high if is_emergency else NotificationPriority.normal
                )
            except Exception as e:
                print(f"Failed to send completion notification to {role_name}: {e}")

        # Check if all completion confirmations are already confirmed (just in case)
        all_confs_res = await db.execute(
            select(CompletionConfirmation)
            .where(CompletionConfirmation.transfusion_id == transfusion_id)
        )
        all_confs = all_confs_res.scalars().all()
        if all_confs and all(c.status == ConfirmationStatus.confirmed for c in all_confs):
            await self._finalise_completion(db, transfusion_id)

        db.expire_all()
        return await transfusion_repo.get_by_id(db, transfusion_id)

    async def _finalise_completion(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
    ) -> None:
        t = await transfusion_repo.get_by_id(db, transfusion_id)
        if not t:
            return

        if t.status == TransfusionStatus.completed:
            return  # Already finalised

        # Eagerly load user IDs and other attributes before update expires them
        patient_user_id = t.patient.user_id if t.patient else None
        donor_user_id = t.donor.user_id if t.donor else None
        coordinator_user_id = t.coordinator.user_id if t.coordinator else None
        hospital_user_id = t.hospital.user_id if t.hospital else None
        
        is_emergency = t.is_emergency
        donor_id = t.donor_id
        hospital_id = t.hospital_id
        actual_date = t.actual_date or date.today()

        # Update status to completed
        await transfusion_repo.update(db, transfusion_id, {
            "status": TransfusionStatus.completed,
        })

        # Process donation record
        if donor_id:
            from app.models.donation import Donation
            from app.models.enums import DonationStatus
            from sqlalchemy import select
            
            donation_res = await db.execute(
                select(Donation)
                .where(Donation.transfusion_id == transfusion_id)
                .where(Donation.donor_id == donor_id)
            )
            donation = donation_res.scalar_one_or_none()
            from app.repositories.base import BaseRepository
            donation_repo = BaseRepository(Donation)
            
            donation_actual_id = None
            if donation:
                await donation_repo.update(db, donation.id, {
                    "status": DonationStatus.completed,
                    "donation_date": actual_date,
                })
                donation_actual_id = donation.id
            else:
                new_donation = await donation_repo.create(db, {
                    "transfusion_id": transfusion_id,
                    "donor_id": donor_id,
                    "hospital_id": hospital_id,
                    "donation_date": actual_date,
                    "status": DonationStatus.completed,
                })
                donation_actual_id = new_donation.id

            from app.repositories.donor_repo import DonorRepository
            donor_repo = DonorRepository()
            await donor_repo.increment_total_donations(db, donor_id)
            await donor_repo.update(db, donor_id, {"last_donation_date": actual_date})

            # Award Reward Points to Donor
            from app.services.reward_service import RewardService
            from app.models.enums import RewardType
            
            reward_type = RewardType.emergency_donation if is_emergency else RewardType.donation
            await RewardService().award_points(
                db,
                donor_id=donor_id,
                reward_type=reward_type,
                donation_id=donation_actual_id
            )

            from app.services.donor_service import DonorService
            await DonorService().recalculate_reliability(db, donor_id)

        # Broadcast completion system notifications to everyone
        from app.models.enums import NotificationType, NotificationPriority
        from app.services.notification_service import NotificationService
        notif_service = NotificationService()

        recipients = []
        if patient_user_id:
            recipients.append(patient_user_id)
        if donor_user_id:
            recipients.append(donor_user_id)
        if coordinator_user_id:
            recipients.append(coordinator_user_id)
        if hospital_user_id:
            recipients.append(hospital_user_id)

        for recipient_user_id in recipients:
            try:
                await notif_service.create_notification(
                    db,
                    user_id=recipient_user_id,
                    type=NotificationType.system,
                    title="Transfusion Completed",
                    message=f"Consensus achieved: Transfusion Run #{transfusion_id} status has been finalized to COMPLETED.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.high if is_emergency else NotificationPriority.normal
                )
            except Exception as e:
                print(f"Failed to send final completion notification to user {recipient_user_id}: {e}")

    async def get_consensus_status(self, db: AsyncSession, transfusion_id: UUID) -> dict:
        t = await self.get_transfusion(db, transfusion_id)
        from app.models.enums import PatientConfirmation, DonorConfirmation, CoordinatorConfirmation, HospitalConfirmation

        all_confirmed = (
            t.patient_confirmation == PatientConfirmation.confirmed
            and t.donor_confirmation == DonorConfirmation.confirmed
            and t.coordinator_confirmation == CoordinatorConfirmation.confirmed
            and t.hospital_confirmation == HospitalConfirmation.confirmed
        )

        def state(status_enum, confirmed_val, rejected_vals=None):
            if hasattr(status_enum, 'value'):
                val = status_enum.value
            else:
                val = str(status_enum)
            return {"status": val, "confirmed_at": None}

        pending_count = sum([
            t.patient_confirmation.value == "pending",
            t.donor_confirmation.value == "pending",
            t.coordinator_confirmation.value == "pending",
            t.hospital_confirmation.value == "pending",
        ])

        return {
            "transfusion_id": t.id,
            "patient": {"status": t.patient_confirmation.value},
            "donor": {"status": t.donor_confirmation.value},
            "coordinator": {"status": t.coordinator_confirmation.value},
            "hospital": {"status": t.hospital_confirmation.value},
            "all_confirmed": all_confirmed,
            "pending_count": pending_count,
        }

    async def list_transfusions(
        self,
        db: AsyncSession,
        patient_id: UUID | None = None,
        coordinator_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Transfusion], int]:
        if patient_id:
            items = await transfusion_repo.get_by_patient(db, patient_id, skip, limit, status)
            total = len(items)  # Approximate for v1
            return items, total
        if coordinator_id:
            items = await transfusion_repo.get_by_coordinator(db, coordinator_id, skip, limit, status)
            return items, len(items)
        if status:
            items = await transfusion_repo.get_by_status(db, status, skip, limit)
            return items, len(items)
        items = await transfusion_repo.get_all(db, skip=skip, limit=limit)
        total = await transfusion_repo.count(db)
        return items, total
