"""
Patient Routes
===============
POST   /patients/register
GET    /patients/me
GET    /patients/me/transfusions
GET    /patients/me/hospitals
PUT    /patients/me/hospitals
GET    /patients/me/prediction
GET    /patients/{patient_id}
PUT    /patients/{patient_id}
GET    /patients/{patient_id}/prediction
GET    /patients/{patient_id}/transfusions
GET    /patients/                (coordinator/admin list)
"""

from uuid import UUID
from fastapi import APIRouter, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.models.patient_hospital_preference import PatientHospitalPreference
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.patient import (
    HospitalPreferenceCreate,
    HospitalPreferenceResponse,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
    PredictionResponse,
)
from app.schemas.transfusion import TransfusionBrief
from app.repositories.transfusion_repo import TransfusionRepository
from app.repositories.patient_repo import PatientRepository
from app.services.patient_service import PatientService

router = APIRouter()
patient_service = PatientService()
transfusion_repo = TransfusionRepository()
patient_repo = PatientRepository()


@router.post("/register", response_model=PatientResponse, status_code=201)
async def register_patient(
    data: PatientCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Register a patient profile for the authenticated user."""
    require_role(current_user, [UserRole.patient])
    return await patient_service.register(db, current_user.id, data)


@router.get("/me", response_model=PatientResponse | None)
async def get_my_patient_profile(current_user: CurrentUser, db: DbSession):
    """Get my patient profile."""
    require_role(current_user, [UserRole.patient])
    return await patient_repo.get_by_user_id(db, current_user.id)


@router.get("/me/transfusions", response_model=PaginatedResponse[TransfusionBrief])
async def get_my_transfusions(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
):
    """Get paginated list of current patient's own transfusions."""
    require_role(current_user, [UserRole.patient])
    patient = await patient_service.get_my_profile(db, current_user.id)
    items = await transfusion_repo.get_by_patient(
        db,
        patient_id=patient.id,
        skip=pagination.offset,
        limit=pagination.page_size,
    )
    from sqlalchemy import select, func
    from app.models.transfusion import Transfusion
    count_result = await db.execute(
        select(func.count()).select_from(Transfusion)
        .where(Transfusion.patient_id == patient.id)
        .where(Transfusion.deleted_at.is_(None))
    )
    total = count_result.scalar_one()
    return PaginatedResponse.create(items, total, pagination.page, pagination.page_size)


@router.get("/me/hospitals", response_model=list[HospitalPreferenceResponse])
async def get_my_hospital_preferences(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get the current patient's hospital preferences."""
    require_role(current_user, [UserRole.patient])
    patient = await patient_repo.get_by_user_id(db, current_user.id)
    if not patient:
        return []
    result = await db.execute(
        select(PatientHospitalPreference)
        .where(PatientHospitalPreference.patient_id == patient.id)
        .options(selectinload(PatientHospitalPreference.hospital))
        .order_by(PatientHospitalPreference.preference_order.asc())
    )
    return list(result.scalars().all())


@router.put("/me/hospitals", response_model=list[HospitalPreferenceResponse])
async def update_my_hospital_preferences(
    data: list[HospitalPreferenceCreate],
    current_user: CurrentUser,
    db: DbSession,
):
    """Replace the current patient's hospital preferences."""
    require_role(current_user, [UserRole.patient])
    patient = await patient_service.get_my_profile(db, current_user.id)
    # Delete existing preferences
    await db.execute(
        delete(PatientHospitalPreference)
        .where(PatientHospitalPreference.patient_id == patient.id)
    )
    await db.flush()
    # Insert new preferences
    for pref in data:
        db.add(PatientHospitalPreference(
            patient_id=patient.id,
            hospital_id=pref.hospital_id,
            preference_order=pref.preference_order,
        ))
    await db.flush()
    # Query with selectinload to return fresh preferences with hospital details
    result = await db.execute(
        select(PatientHospitalPreference)
        .where(PatientHospitalPreference.patient_id == patient.id)
        .options(selectinload(PatientHospitalPreference.hospital))
        .order_by(PatientHospitalPreference.preference_order.asc())
    )
    return list(result.scalars().all())


@router.get("/me/prediction", response_model=PredictionResponse)
async def get_my_prediction(
    current_user: CurrentUser,
    db: DbSession,
):
    """AI-powered prediction of next transfusion date for the logged-in patient."""
    require_role(current_user, [UserRole.patient])
    patient = await patient_service.get_my_profile(db, current_user.id)
    return await patient_service.predict_next_transfusion(db, patient.id)



@router.get("/", response_model=PaginatedResponse[PatientResponse])
async def list_patients(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
    city: str | None = Query(None),
):
    """List all patients (coordinator/admin only)."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    patients, total = await patient_service.list_patients(
        db, skip=pagination.offset, limit=pagination.page_size, city=city
    )
    return PaginatedResponse.create(patients, total, pagination.page, pagination.page_size)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get patient by ID (coordinator/admin or the patient themselves)."""
    from app.core.permissions import require_self_or_role
    patient = await patient_service.get_patient(db, patient_id)
    require_self_or_role(current_user, patient.user_id, [UserRole.coordinator, UserRole.admin])
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    data: PatientUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update patient profile."""
    return await patient_service.update_profile(
        db, patient_id, data, current_user.id, current_user.role
    )


@router.get("/{patient_id}/prediction", response_model=PredictionResponse)
async def predict_next_transfusion(
    patient_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """AI-powered prediction of next transfusion date."""
    require_role(current_user, [UserRole.patient, UserRole.coordinator, UserRole.admin])
    return await patient_service.predict_next_transfusion(db, patient_id)
