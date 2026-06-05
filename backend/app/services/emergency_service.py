"""
Emergency Service
==================
Emergency transfusion escalation.
Loosens normal matching constraints: all eligible donors are alerted simultaneously.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.enums import TransfusionStatus, UrgencyLevel
from app.repositories.donor_repo import DonorRepository
from app.repositories.hospital_repo import HospitalRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.transfusion_repo import TransfusionRepository
from app.ai.emergency import EmergencyPrioritizationEngine

patient_repo = PatientRepository()
donor_repo = DonorRepository()
hospital_repo = HospitalRepository()
transfusion_repo = TransfusionRepository()
emergency_engine = EmergencyPrioritizationEngine()


class EmergencyService:

    async def create_emergency_transfusion(
        self,
        db: AsyncSession,
        patient_id: UUID,
        reason: str,
        coordinator_id: UUID,
    ):
        """Create an emergency transfusion bypassing normal prediction flow."""
        from datetime import date
        patient = await patient_repo.get_by_id(db, patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))

        return await transfusion_repo.create(db, {
            "patient_id": patient_id,
            "predicted_date": date.today(),
            "urgency_level": UrgencyLevel.emergency,
            "status": TransfusionStatus.patient_confirmed,  # Patient consent implied in emergency
            "is_emergency": True,
            "emergency_reason": reason,
            "coordinator_id": coordinator_id,
        })

    async def get_priority_donors(
        self,
        db: AsyncSession,
        transfusion_id: UUID,
    ) -> list:
        """Get emergency-prioritized donor list (distance > reliability in emergency)."""
        transfusion = await transfusion_repo.get_by_id(db, transfusion_id)
        if not transfusion:
            raise NotFoundException("Transfusion", str(transfusion_id))

        patient = await patient_repo.get_by_id(db, transfusion.patient_id)
        if not patient:
            raise NotFoundException("Patient")

        # Emergency: get ALL eligible donors regardless of availability flag
        candidates = await donor_repo.get_all_available(db, limit=100)

        hospital_lat, hospital_lng = 13.0827, 80.2707
        if transfusion.hospital_id:
            hospital = await hospital_repo.get_by_id(db, transfusion.hospital_id)
            if hospital and hospital.latitude:
                hospital_lat = float(hospital.latitude)
                hospital_lng = float(hospital.longitude)

        results = emergency_engine.rank_donors(
            candidates=candidates,
            patient_blood_group=patient.blood_group.value,
            hospital_lat=hospital_lat,
            hospital_lng=hospital_lng,
        )
        return results
