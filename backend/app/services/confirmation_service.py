"""
Confirmation Service
=====================
4-party consensus management.
Each party (patient, donor, coordinator, hospital) must explicitly confirm.
"""

from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.models.enums import (
    ConfirmationStatus,
    ConfirmationRole,
    CoordinatorConfirmation,
    DonorConfirmation,
    HospitalConfirmation,
    PatientConfirmation,
    TransfusionStatus,
    UserRole,
)
from app.repositories.confirmation_repo import ConfirmationRepository
from app.repositories.transfusion_repo import TransfusionRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.donor_repo import DonorRepository
from app.models.confirmation import Confirmation
from app.models.completion_confirmation import CompletionConfirmation

confirmation_repo = ConfirmationRepository()
transfusion_repo = TransfusionRepository()
patient_repo = PatientRepository()
donor_repo = DonorRepository()

# Role → field to update on transfusion
ROLE_FIELD_MAP = {
    ConfirmationRole.patient: "patient_confirmation",
    ConfirmationRole.donor: "donor_confirmation",
    ConfirmationRole.coordinator: "coordinator_confirmation",
    ConfirmationRole.hospital: "hospital_confirmation",
}

ROLE_CONFIRMED_VALUE = {
    ConfirmationRole.patient: PatientConfirmation.confirmed,
    ConfirmationRole.donor: DonorConfirmation.confirmed,
    ConfirmationRole.coordinator: CoordinatorConfirmation.confirmed,
    ConfirmationRole.hospital: HospitalConfirmation.confirmed,
}


class ConfirmationService:

    def _get_role_for_user_role(self, user_role: UserRole) -> ConfirmationRole:
        mapping = {
            UserRole.patient: ConfirmationRole.patient,
            UserRole.donor: ConfirmationRole.donor,
            UserRole.coordinator: ConfirmationRole.coordinator,
            UserRole.hospital: ConfirmationRole.hospital,
        }
        role = mapping.get(user_role)
        if not role:
            raise ForbiddenException("Admins cannot confirm transfusions directly")
        return role

    async def confirm(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        user_id: UUID,
        user_role: UserRole,
        notes: str | None = None,
    ) -> Confirmation:
        role = self._get_role_for_user_role(user_role)
        transfusion = await transfusion_repo.get_by_id(db, transfusion_id)
        if not transfusion:
            raise NotFoundException("Transfusion", str(transfusion_id))

        # Eagerly extract and cache related stakeholder fields to avoid async lazy-loading exceptions
        patient_user_id = transfusion.patient.user_id if transfusion.patient else None
        patient_name = transfusion.patient.name if transfusion.patient else None
        
        donor_user_id = transfusion.donor.user_id if transfusion.donor else None
        donor_name = transfusion.donor.name if transfusion.donor else None
        
        hospital_user_id = transfusion.hospital.user_id if transfusion.hospital else None
        hospital_name = transfusion.hospital.name if transfusion.hospital else None
        
        alternate_hospital_user_id = transfusion.alternate_hospital.user_id if transfusion.alternate_hospital else None
        alternate_hospital_name = transfusion.alternate_hospital.name if transfusion.alternate_hospital else None
        
        coordinator_user_id = transfusion.coordinator.user_id if transfusion.coordinator else None
        coordinator_name = transfusion.coordinator.name if transfusion.coordinator else None
        
        is_emergency = transfusion.is_emergency

        # Find or create confirmation record
        existing = await confirmation_repo.get_by_user_and_transfusion(db, user_id, transfusion_id)
        if existing and existing.status == ConfirmationStatus.confirmed:
            raise BadRequestException("You have already confirmed this transfusion")

        # Update the confirmation record
        now = datetime.now(timezone.utc)
        if existing:
            confirmation = await confirmation_repo.update(db, existing.id, {
                "status": ConfirmationStatus.confirmed,
                "notes": notes,
                "responded_at": now,
            })
        else:
            confirmation = await confirmation_repo.create(db, {
                "transfusion_id": transfusion_id,
                "user_id": user_id,
                "role": role,
                "status": ConfirmationStatus.confirmed,
                "notes": notes,
                "responded_at": now,
            })

        # Update the transfusion's confirmation field
        field = ROLE_FIELD_MAP[role]
        value = ROLE_CONFIRMED_VALUE[role]
        await transfusion_repo.update(db, transfusion_id, {field: value})

        # Check if all 4 confirmed → advance to scheduled
        await self._check_and_advance_status(db, transfusion_id)

        if role == ConfirmationRole.donor:
            donor = await donor_repo.get_by_user_id(db, user_id)
            if donor:
                from app.models.donation import Donation
                from app.models.enums import DonationStatus
                from sqlalchemy import select
                
                # Check if a donation record already exists
                existing_res = await db.execute(
                    select(Donation)
                    .where(Donation.transfusion_id == transfusion_id)
                    .where(Donation.donor_id == donor.id)
                )
                existing_donation = existing_res.scalar_one_or_none()
                if not existing_donation:
                    from app.repositories.base import BaseRepository
                    donation_repo = BaseRepository(Donation)
                    await donation_repo.create(db, {
                        "transfusion_id": transfusion_id,
                        "donor_id": donor.id,
                        "hospital_id": transfusion.hospital_id or transfusion.alternate_hospital_id,
                        "donation_date": transfusion.scheduled_date or transfusion.predicted_date,
                        "status": DonationStatus.scheduled,
                    })
                
                from app.services.donor_service import DonorService
                await DonorService().recalculate_reliability(db, donor.id)

        # Notify other stakeholders
        try:
            confirming_name = "A stakeholder"
            if user_role == UserRole.patient and patient_name:
                confirming_name = f"Patient {patient_name}"
            elif user_role == UserRole.donor and donor_name:
                confirming_name = f"Donor {donor_name}"
            elif user_role == UserRole.hospital:
                hosp_name = alternate_hospital_name if alternate_hospital_user_id else hospital_name
                confirming_name = f"Hospital {hosp_name}" if hosp_name else "Hospital"
            elif user_role == UserRole.coordinator and coordinator_name:
                confirming_name = f"Coordinator {coordinator_name}"

            from app.services.notification_service import NotificationService
            from app.models.enums import NotificationType, NotificationPriority
            notif_service = NotificationService()

            recipients = []
            if patient_user_id and patient_user_id != user_id:
                recipients.append(patient_user_id)
            if donor_user_id and donor_user_id != user_id:
                recipients.append(donor_user_id)

            active_hospital_user_id = alternate_hospital_user_id if alternate_hospital_user_id else hospital_user_id
            if active_hospital_user_id and active_hospital_user_id != user_id:
                recipients.append(active_hospital_user_id)
            if coordinator_user_id and coordinator_user_id != user_id:
                recipients.append(coordinator_user_id)

            for recipient_user_id in recipients:
                await notif_service.create_notification(
                    db,
                    user_id=recipient_user_id,
                    type=NotificationType.system,
                    title="Transfusion Slot Update",
                    message=f"{confirming_name} has accepted the transfusion request (Run #{transfusion_id}).",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.high if is_emergency else NotificationPriority.normal
                )
        except Exception as notif_err:
            print("Failed to dispatch stakeholder notifications: ", notif_err)

        return confirmation

    async def reject(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        user_id: UUID,
        user_role: UserRole,
        reason: str | None = None,
    ) -> Confirmation:
        role = self._get_role_for_user_role(user_role)
        transfusion = await transfusion_repo.get_by_id(db, transfusion_id)
        if not transfusion:
            raise NotFoundException("Transfusion", str(transfusion_id))

        now = datetime.now(timezone.utc)
        existing = await confirmation_repo.get_by_user_and_transfusion(db, user_id, transfusion_id)
        if existing:
            res = await confirmation_repo.update(db, existing.id, {
                "status": ConfirmationStatus.rejected,
                "notes": reason,
                "responded_at": now,
            })
        else:
            res = await confirmation_repo.create(db, {
                "transfusion_id": transfusion_id,
                "user_id": user_id,
                "role": role,
                "status": ConfirmationStatus.rejected,
                "notes": reason,
                "responded_at": now,
            })

        # Update the transfusion's confirmation field to rejected
        from app.models.enums import PatientConfirmation, DonorConfirmation, CoordinatorConfirmation, HospitalConfirmation
        ROLE_REJECTED_VALUE = {
            ConfirmationRole.patient: PatientConfirmation.rejected,
            ConfirmationRole.donor: DonorConfirmation.rejected,
            ConfirmationRole.coordinator: CoordinatorConfirmation.pending,
            ConfirmationRole.hospital: HospitalConfirmation.rejected,
        }
        field = ROLE_FIELD_MAP[role]
        value = ROLE_REJECTED_VALUE[role]
        await transfusion_repo.update(db, transfusion_id, {field: value})

        if role == ConfirmationRole.donor:
            donor = await donor_repo.get_by_user_id(db, user_id)
            if donor:
                from app.services.donor_service import DonorService
                await DonorService().recalculate_reliability(db, donor.id)

        if role == ConfirmationRole.coordinator:
            if transfusion.donor_id:
                donor = await donor_repo.get_by_id(db, transfusion.donor_id)
                if donor:
                    donor_conf = await confirmation_repo.get_by_user_and_transfusion(db, donor.user_id, transfusion_id)
                    if donor_conf:
                        await confirmation_repo.update(db, donor_conf.id, {
                            "status": ConfirmationStatus.rejected,
                            "notes": f"Rejected by coordinator: {reason}",
                            "responded_at": now,
                        })
                    else:
                        await confirmation_repo.create(db, {
                            "transfusion_id": transfusion_id,
                            "user_id": donor.user_id,
                            "role": ConfirmationRole.donor,
                            "status": ConfirmationStatus.rejected,
                            "notes": f"Rejected by coordinator: {reason}",
                            "responded_at": now,
                        })

            await transfusion_repo.update(db, transfusion_id, {
                "donor_id": None,
                "donor_confirmation": DonorConfirmation.pending,
                "coordinator_confirmation": CoordinatorConfirmation.pending,
                "hospital_confirmation": HospitalConfirmation.pending,
            })

            from app.services.scheduling_service import SchedulingService
            try:
                matches = await SchedulingService().get_donor_matches(db, transfusion_id, limit=1)
                if matches:
                    top_match = matches[0]
                    from app.services.transfusion_service import TransfusionService
                    await TransfusionService().assign_donor(db, transfusion_id, top_match.donor_id)
            except Exception:
                pass

        if role == ConfirmationRole.hospital:
            await self._handle_hospital_rejection(db, transfusion_id, transfusion)

        return res

    async def _handle_hospital_rejection(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        t,
    ) -> None:
        from app.services.scheduling_service import SchedulingService
        from app.repositories.hospital_repo import HospitalRepository
        from app.services.notification_service import NotificationService
        from app.models.enums import NotificationType, NotificationPriority
        from sqlalchemy import delete
        
        notif_service = NotificationService()
        
        # Check if alternative hospital was already tried and rejected
        if t.alternate_hospital_id is not None:
            # Second hospital rejected! Coordinator takes manual control.
            # Send notification to coordinators
            from app.repositories.coordinator_repo import CoordinatorRepository
            coords = await CoordinatorRepository().get_all(db, limit=100)
            for c in coords:
                await notif_service.create_notification(
                    db,
                    user_id=c.user_id,
                    type=NotificationType.emergency_alert,
                    title="🚨 Emergency Transfusion Alert",
                    message=f"Alternative hospital rejected transfusion {transfusion_id}. Coordinator manual routing is required.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.emergency
                )
            # Update transfusion notes
            await transfusion_repo.update(db, transfusion_id, {
                "notes": (t.notes or "") + "\n[System] Alternate hospital also rejected. Manual routing required."
            })
            return

        # First rejection: Find alternative hospital
        scheduling_service = SchedulingService()
        alternatives = await scheduling_service.route_alternate_hospital(db, transfusion_id)
        if not alternatives:
            # No alternative hospitals found in the city! Notify coordinators.
            from app.repositories.coordinator_repo import CoordinatorRepository
            coords = await CoordinatorRepository().get_all(db, limit=100)
            for c in coords:
                await notif_service.create_notification(
                    db,
                    user_id=c.user_id,
                    type=NotificationType.emergency_alert,
                    title="🚨 No Alternative Hospitals Found",
                    message=f"Preferred hospital rejected transfusion {transfusion_id}, and no alternative hospitals are available in the city. Coordinator action required.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.emergency
                )
            return
            
        alt_hosp = alternatives[0]
        
        # Update transfusion with alternative hospital and reset status to pending
        from app.models.enums import PatientConfirmation, DonorConfirmation, HospitalConfirmation
        await transfusion_repo.update(db, transfusion_id, {
            "alternate_hospital_id": alt_hosp.id,
            "patient_confirmation": PatientConfirmation.pending,
            "donor_confirmation": DonorConfirmation.pending,
            "hospital_confirmation": HospitalConfirmation.pending,
        })
        
        # Reset confirmations
        await db.execute(
            delete(Confirmation).where(Confirmation.transfusion_id == transfusion_id)
        )
        
        # Recreate pending confirmation requests
        # 1. Patient
        patient = await patient_repo.get_by_id(db, t.patient_id)
        if patient:
            await confirmation_repo.create(db, {
                "transfusion_id": transfusion_id,
                "user_id": patient.user_id,
                "role": ConfirmationRole.patient,
                "status": ConfirmationStatus.pending,
            })
            # Notify patient
            await notif_service.create_notification(
                db,
                user_id=patient.user_id,
                type=NotificationType.confirmation_request,
                title="Alternative Hospital Assigned",
                message=f"Your preferred hospital rejected/had no slots. An alternative hospital ({alt_hosp.name}) has been proposed. Please confirm if this is acceptable.",
                transfusion_id=transfusion_id,
                priority=NotificationPriority.high
            )
            
        # 2. Donor
        if t.donor_id:
            donor = await donor_repo.get_by_id(db, t.donor_id)
            if donor:
                await confirmation_repo.create(db, {
                    "transfusion_id": transfusion_id,
                    "user_id": donor.user_id,
                    "role": ConfirmationRole.donor,
                    "status": ConfirmationStatus.pending,
                })
                # Notify donor
                await notif_service.create_notification(
                    db,
                    user_id=donor.user_id,
                    type=NotificationType.confirmation_request,
                    title="Transfusion Location Updated",
                    message=f"The transfusion has been re-routed to alternative hospital ({alt_hosp.name}). Please re-confirm your availability.",
                    transfusion_id=transfusion_id,
                    priority=NotificationPriority.high
                )
                
        # 3. Hospital
        await confirmation_repo.create(db, {
            "transfusion_id": transfusion_id,
            "user_id": alt_hosp.user_id,
            "role": ConfirmationRole.hospital,
            "status": ConfirmationStatus.pending,
        })
        # Notify alternate hospital
        await notif_service.create_notification(
            db,
            user_id=alt_hosp.user_id,
            type=NotificationType.confirmation_request,
            title="Alternative Capacity Request",
            message=f"Alternative capacity request received for emergency transfusion {transfusion_id}. Please confirm bed/chair availability.",
            transfusion_id=transfusion_id,
            priority=NotificationPriority.high
        )

    async def _check_and_advance_status(self, db: AsyncSession, transfusion_id: UUID) -> None:
        """If all 4 parties confirmed, advance transfusion status to scheduled."""
        t = await transfusion_repo.get_by_id(db, transfusion_id)
        if not t:
            return
        if (
            t.patient_confirmation == PatientConfirmation.confirmed
            and t.donor_confirmation == DonorConfirmation.confirmed
            and t.coordinator_confirmation == CoordinatorConfirmation.confirmed
            and t.hospital_confirmation == HospitalConfirmation.confirmed
        ):
            update_data = {
                "status": TransfusionStatus.scheduled,
            }
            original_hospital_id = t.hospital_id
            if t.alternate_hospital_id:
                update_data["hospital_id"] = t.alternate_hospital_id
                update_data["alternate_hospital_id"] = None
                
            await transfusion_repo.update(db, transfusion_id, update_data)
            
            # Notify the previous hospital
            if t.alternate_hospital_id and original_hospital_id:
                from app.repositories.hospital_repo import HospitalRepository
                from app.services.notification_service import NotificationService
                from app.models.enums import NotificationType
                prev_hosp = await HospitalRepository().get_by_id(db, original_hospital_id)
                if prev_hosp:
                    await NotificationService().create_notification(
                        db,
                        user_id=prev_hosp.user_id,
                        type=NotificationType.system,
                        title="Transfusion Re-routed",
                        message=f"Transfusion request {transfusion_id} which was rejected has been successfully scheduled at an alternative hospital.",
                        transfusion_id=transfusion_id
                    )


    async def get_pending_for_user(
        self, db: AsyncSession, user_id: UUID
    ) -> list[Confirmation]:
        return await confirmation_repo.get_pending_for_user(db, user_id)

    async def get_by_transfusion(
        self, db: AsyncSession, transfusion_id: UUID
    ) -> list[Confirmation]:
        return await confirmation_repo.get_by_transfusion(db, transfusion_id)

    async def get_completion_confirmations(
        self, db: AsyncSession, transfusion_id: UUID
    ) -> list[CompletionConfirmation]:
        from app.models.completion_confirmation import CompletionConfirmation
        from sqlalchemy import select
        result = await db.execute(
            select(CompletionConfirmation)
            .where(CompletionConfirmation.transfusion_id == transfusion_id)
        )
        return list(result.scalars().all())

    async def confirm_completion(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
        user_id: UUID,
        user_role: UserRole,
        notes: str | None = None,
    ) -> list[CompletionConfirmation]:
        from app.models.completion_confirmation import CompletionConfirmation
        from app.models.enums import ConfirmationStatus, ConfirmationRole
        from sqlalchemy import select

        # Find the completion confirmation record for this user
        result = await db.execute(
            select(CompletionConfirmation)
            .where(CompletionConfirmation.transfusion_id == transfusion_id)
            .where(CompletionConfirmation.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            raise NotFoundException("Completion confirmation record not found for this user")

        if existing.status == ConfirmationStatus.confirmed:
            raise BadRequestException("You have already confirmed the completion of this transfusion")

        # Update it to confirmed
        now = datetime.now(timezone.utc)
        from app.repositories.base import BaseRepository
        comp_repo = BaseRepository(CompletionConfirmation)
        await comp_repo.update(db, existing.id, {
            "status": ConfirmationStatus.confirmed,
            "notes": notes,
            "responded_at": now,
        })

        # Send notifications to other stakeholders
        try:
            confirming_name = "A stakeholder"
            transfusion = await transfusion_repo.get_by_id(db, transfusion_id)
            if transfusion:
                patient_name = transfusion.patient.name if transfusion.patient else None
                donor_name = transfusion.donor.name if transfusion.donor else None
                hospital_name = None
                if transfusion.alternate_hospital_id and transfusion.alternate_hospital:
                    hospital_name = transfusion.alternate_hospital.name
                elif transfusion.hospital:
                    hospital_name = transfusion.hospital.name
                coordinator_name = transfusion.coordinator.name if transfusion.coordinator else None

                if user_role == UserRole.patient and patient_name:
                    confirming_name = f"Patient {patient_name}"
                elif user_role == UserRole.donor and donor_name:
                    confirming_name = f"Donor {donor_name}"
                elif user_role == UserRole.hospital:
                    confirming_name = f"Hospital {hospital_name}" if hospital_name else "Hospital"
                elif user_role == UserRole.coordinator and coordinator_name:
                    confirming_name = f"Coordinator {coordinator_name}"

                from app.services.notification_service import NotificationService
                from app.models.enums import NotificationType, NotificationPriority
                notif_service = NotificationService()

                recipients = []
                if transfusion.patient and transfusion.patient.user_id != user_id:
                    recipients.append(transfusion.patient.user_id)
                if transfusion.donor and transfusion.donor.user_id != user_id:
                    recipients.append(transfusion.donor.user_id)

                active_hospital_user_id = transfusion.alternate_hospital.user_id if transfusion.alternate_hospital_id and transfusion.alternate_hospital else transfusion.hospital.user_id if transfusion.hospital else None
                if active_hospital_user_id and active_hospital_user_id != user_id:
                    recipients.append(active_hospital_user_id)
                if transfusion.coordinator and transfusion.coordinator.user_id != user_id:
                    recipients.append(transfusion.coordinator.user_id)

                for recipient_user_id in recipients:
                    await notif_service.create_notification(
                        db,
                        user_id=recipient_user_id,
                        type=NotificationType.system,
                        title="Transfusion Completion Update",
                        message=f"{confirming_name} has confirmed that transfusion Run #{transfusion_id} is completed.",
                        transfusion_id=transfusion_id,
                        priority=NotificationPriority.high if transfusion.is_emergency else NotificationPriority.normal
                    )
        except Exception as err:
            print("Failed to dispatch completion notifications:", err)

        # Check if all completion confirmations for this transfusion are confirmed
        all_confs_res = await db.execute(
            select(CompletionConfirmation)
            .where(CompletionConfirmation.transfusion_id == transfusion_id)
        )
        all_confs = all_confs_res.scalars().all()

        # If all are confirmed
        if all_confs and all(c.status == ConfirmationStatus.confirmed for c in all_confs):
            from app.services.transfusion_service import TransfusionService
            await TransfusionService()._finalise_completion(db, transfusion_id)

        # Return updated list of completion confirmations
        updated_res = await db.execute(
            select(CompletionConfirmation)
            .where(CompletionConfirmation.transfusion_id == transfusion_id)
        )
        return list(updated_res.scalars().all())

    async def get_pending_completion_confirmations_for_user(
        self, db: AsyncSession, user_id: UUID
    ) -> list[dict]:
        from app.models.completion_confirmation import CompletionConfirmation
        from app.models.enums import ConfirmationStatus
        from app.models.transfusion import Transfusion
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(CompletionConfirmation)
            .where(CompletionConfirmation.user_id == user_id)
            .where(CompletionConfirmation.status == ConfirmationStatus.pending)
            .options(
                selectinload(CompletionConfirmation.transfusion).options(
                    selectinload(Transfusion.patient),
                    selectinload(Transfusion.hospital),
                )
            )
        )
        items = result.scalars().all()
        
        output = []
        for item in items:
            t = item.transfusion
            output.append({
                "id": item.id,
                "transfusion_id": item.transfusion_id,
                "role": item.role,
                "status": item.status,
                "patient_name": t.patient.name if t and t.patient else None,
                "hospital_name": t.hospital.name if t and t.hospital else "Hospital",
                "scheduled_date": (t.scheduled_date or t.predicted_date).isoformat() if t and (t.scheduled_date or t.predicted_date) else None,
                "urgency_level": t.urgency_level.value if t else None,
            })
        return output

