"""
Patient Service
================
Registration, profile management, and next transfusion prediction.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.patient_hospital_preference import PatientHospitalPreference
from app.repositories.patient_repo import PatientRepository
from app.repositories.transfusion_repo import TransfusionRepository
from app.schemas.patient import PatientCreate, PatientUpdate
from app.ai.predictor import TransfusionPredictor

patient_repo = PatientRepository()
transfusion_repo = TransfusionRepository()
predictor = TransfusionPredictor()


class PatientService:

    async def register(self, db: AsyncSession, user_id: UUID, data: PatientCreate) -> Patient:
        """Create patient profile linked to user account."""
        if await patient_repo.get_by_user_id(db, user_id):
            raise ConflictException("Patient profile already exists for this account")

        patient = await patient_repo.create(db, {
            "user_id": user_id,
            "name": data.name,
            "age": data.age,
            "gender": data.gender,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "blood_group": data.blood_group,
            "thalassemia_type": data.thalassemia_type,
            "last_transfusion_date": data.last_transfusion_date,
            "avg_transfusion_interval_days": data.avg_transfusion_interval_days,
            "emergency_contact_name": data.emergency_contact_name,
            "emergency_contact_phone": data.emergency_contact_phone,
            "data_sharing_consent": data.data_sharing_consent,
            "emergency_consent": data.emergency_consent,
        })

        # Save hospital preferences
        from app.repositories.hospital_repo import HospitalRepository
        hosp_repo = HospitalRepository()
        for pref in data.hospital_preferences:
            if not await hosp_repo.exists(db, id=pref.hospital_id):
                raise NotFoundException("Hospital", str(pref.hospital_id))
            db.add(PatientHospitalPreference(
                patient_id=patient.id,
                hospital_id=pref.hospital_id,
                preference_order=pref.preference_order,
            ))
        await db.flush()
        return patient

    async def get_patient(self, db: AsyncSession, patient_id: UUID) -> Patient:
        patient = await patient_repo.get_by_id(db, patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))
        return patient

    async def get_my_profile(self, db: AsyncSession, user_id: UUID) -> Patient:
        patient = await patient_repo.get_by_user_id(db, user_id)
        if not patient:
            raise NotFoundException("Patient profile not found. Please complete registration.")
        return patient

    async def update_profile(
        self,
        db: AsyncSession,
        patient_id: UUID,
        data: PatientUpdate,
        requesting_user_id: UUID,
        requesting_role: UserRole,
    ) -> Patient:
        patient = await patient_repo.get_by_id(db, patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))

        # Only the patient themselves or admin/coordinator can update
        if requesting_role == UserRole.patient and patient.user_id != requesting_user_id:
            raise ForbiddenException("You can only update your own profile")

        return await patient_repo.update(db, patient_id, data.model_dump(exclude_none=True))

    async def predict_next_transfusion(self, db: AsyncSession, patient_id: UUID) -> dict:
        """Use AI TransfusionPredictor to estimate next transfusion date."""
        patient = await patient_repo.get_by_id(db, patient_id)
        if not patient:
            raise NotFoundException("Patient", str(patient_id))

        completed = await transfusion_repo.get_completed_for_patient(db, patient_id)
        transfusion_dates = [
            t.actual_date for t in completed if t.actual_date
        ]

        result = predictor.predict(
            patient=patient,
            transfusion_dates=transfusion_dates,
        )
        return result

    async def list_patients(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        city: str | None = None,
    ) -> tuple[list[Patient], int]:
        filters = []
        if city:
            from app.models.patient import Patient as P
            from sqlalchemy import func
            filters.append(P.city.ilike(f"%{city}%"))
        patients = await patient_repo.get_all(db, skip=skip, limit=limit, filters=filters)
        total = await patient_repo.count(db, filters=filters)
        return patients, total
