"""
Hospital Routes
================
POST   /hospitals/register
GET    /hospitals/me
GET    /hospitals/me/capacity
PUT    /hospitals/me/capacity
GET    /hospitals/me/transfusions
GET    /hospitals/{hospital_id}
PUT    /hospitals/{hospital_id}
GET    /hospitals/{hospital_id}/capacity
PUT    /hospitals/{hospital_id}/capacity
GET    /hospitals/                        (list with city filter)
"""

from uuid import UUID
from fastapi import APIRouter, Query
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.hospital import (
    CapacityResponse,
    CapacityUpdate,
    HospitalCreate,
    HospitalResponse,
    HospitalUpdate,
)
from app.services.hospital_service import HospitalService
from app.repositories.hospital_repo import HospitalRepository

router = APIRouter()
hospital_service = HospitalService()
hospital_repo = HospitalRepository()


@router.post("/register", response_model=HospitalResponse, status_code=201)
async def register_hospital(data: HospitalCreate, current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.hospital])
    return await hospital_service.register(db, current_user.id, data)


@router.get("/me", response_model=HospitalResponse | None)
async def get_my_hospital_profile(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.hospital])
    return await hospital_repo.get_by_user_id(db, current_user.id)


@router.get("/me/capacity", response_model=CapacityResponse | None)
async def get_my_hospital_capacity(current_user: CurrentUser, db: DbSession):
    """Get the current hospital's capacity record."""
    require_role(current_user, [UserRole.hospital])
    hospital = await hospital_repo.get_by_user_id(db, current_user.id)
    if not hospital:
        return None
    return await hospital_service.get_capacity(db, hospital.id)


@router.put("/me/capacity", response_model=CapacityResponse)
async def update_my_hospital_capacity(
    data: CapacityUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update the current hospital's capacity."""
    require_role(current_user, [UserRole.hospital])
    hospital = await hospital_repo.get_by_user_id(db, current_user.id)
    if not hospital:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Hospital profile not found")
    return await hospital_service.update_capacity(db, hospital.id, data)


@router.get("/me/transfusions", response_model=list)
async def get_my_hospital_transfusions(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
):
    """Get scheduled transfusions for the current hospital (paginated)."""
    require_role(current_user, [UserRole.hospital])
    hospital = await hospital_repo.get_by_user_id(db, current_user.id)
    if not hospital:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Hospital profile not found")
    from sqlalchemy import select
    from app.models.transfusion import Transfusion
    from app.models.enums import TransfusionStatus
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Transfusion)
        .where(Transfusion.hospital_id == hospital.id)
        .where(Transfusion.deleted_at.is_(None))
        .where(Transfusion.status.not_in([
            TransfusionStatus.cancelled,
            TransfusionStatus.failed,
        ]))
        .options(
            selectinload(Transfusion.patient),
            selectinload(Transfusion.donor),
            selectinload(Transfusion.coordinator),
        )
        .order_by(Transfusion.scheduled_date.asc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    items = list(result.scalars().all())
    
    from app.models.completion_confirmation import CompletionConfirmation
    comp_res = await db.execute(
        select(CompletionConfirmation.transfusion_id)
        .where(CompletionConfirmation.transfusion_id.in_([t.id for t in items]))
    )
    initiated_ids = set(comp_res.scalars().all())

    return [
        {
            "id": str(t.id),
            "patient_id": str(t.patient_id),
            "patient_name": t.patient.name if t.patient else "Patient",
            "patient_blood_group": t.patient.blood_group.value if t.patient else None,
            "hospital_id": str(t.hospital_id) if t.hospital_id else None,
            "donor_id": str(t.donor_id) if t.donor_id else None,
            "donor_name": t.donor.name if t.donor else None,
            "donor_medical_clearance_url": t.donor.medical_clearance_url if t.donor and t.donor.medical_clearance_url else None,
            "status": t.status.value,
            "urgency_level": t.urgency_level.value,
            "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else t.predicted_date.isoformat() if t.predicted_date else None,
            "completed_at": t.actual_date.isoformat() if t.actual_date else None,
            "is_completion_initiated": t.id in initiated_ids,
            "notes": t.notes,
            "coordinator": {
                "id": str(t.coordinator.id),
                "name": t.coordinator.name,
                "phone": t.coordinator.phone,
                "organization": t.coordinator.organization,
                "assigned_region": t.coordinator.assigned_region,
            } if t.coordinator else None,
        }
        for t in items
    ]


@router.get("/", response_model=PaginatedResponse[HospitalResponse])
async def list_hospitals(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
    city: str | None = Query(None),
):
    hospitals, total = await hospital_service.list_hospitals(
        db, city=city, skip=pagination.offset, limit=pagination.page_size
    )
    return PaginatedResponse.create(hospitals, total, pagination.page, pagination.page_size)


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: UUID, current_user: CurrentUser, db: DbSession):
    return await hospital_service.get_hospital(db, hospital_id)


@router.get("/{hospital_id}/capacity", response_model=CapacityResponse)
async def get_capacity(hospital_id: UUID, current_user: CurrentUser, db: DbSession):
    return await hospital_service.get_capacity(db, hospital_id)


@router.put("/{hospital_id}/capacity", response_model=CapacityResponse)
async def update_capacity(
    hospital_id: UUID,
    data: CapacityUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Update hospital capacity (hospital or coordinator)."""
    require_role(current_user, [UserRole.hospital, UserRole.coordinator, UserRole.admin])
    return await hospital_service.update_capacity(db, hospital_id, data)


@router.get("/{hospital_id}/schedule", response_model=list)
async def get_hospital_schedule(hospital_id: UUID, current_user: CurrentUser, db: DbSession):
    """Get today's transfusion schedule for a hospital."""
    from sqlalchemy import select
    from app.models.transfusion import Transfusion
    from app.models.enums import TransfusionStatus
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Transfusion)
        .where(Transfusion.hospital_id == hospital_id)
        .where(Transfusion.deleted_at.is_(None))
        .where(Transfusion.status.not_in([
            TransfusionStatus.cancelled,
            TransfusionStatus.failed,
        ]))
        .options(
            selectinload(Transfusion.patient),
            selectinload(Transfusion.donor),
            selectinload(Transfusion.coordinator),
        )
        .order_by(Transfusion.scheduled_date.asc())
        .limit(50)
    )
    items = list(result.scalars().all())
    
    from app.models.completion_confirmation import CompletionConfirmation
    comp_res = await db.execute(
        select(CompletionConfirmation.transfusion_id)
        .where(CompletionConfirmation.transfusion_id.in_([t.id for t in items]))
    )
    initiated_ids = set(comp_res.scalars().all())

    return [
        {
            "id": str(t.id),
            "patient_id": str(t.patient_id),
            "patient_name": t.patient.name if t.patient else "Patient",
            "patient_blood_group": t.patient.blood_group.value if t.patient else None,
            "hospital_id": str(t.hospital_id) if t.hospital_id else None,
            "donor_id": str(t.donor_id) if t.donor_id else None,
            "donor_name": t.donor.name if t.donor else "TBD",
            "donor_medical_clearance_url": t.donor.medical_clearance_url if t.donor and t.donor.medical_clearance_url else None,
            "status": t.status.value,
            "urgency_level": t.urgency_level.value,
            "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else t.predicted_date.isoformat() if t.predicted_date else None,
            "completed_at": t.actual_date.isoformat() if t.actual_date else None,
            "is_completion_initiated": t.id in initiated_ids,
            "cancellation_reason": t.notes,
            "coordinator": {
                "id": str(t.coordinator.id),
                "name": t.coordinator.name,
                "phone": t.coordinator.phone,
                "organization": t.coordinator.organization,
                "assigned_region": t.coordinator.assigned_region,
            } if t.coordinator else None,
        }
        for t in items
    ]


@router.get("/{hospital_id}/pending-slots", response_model=list)
async def get_pending_slots(hospital_id: UUID, current_user: CurrentUser, db: DbSession):
    """Get transfusions pending hospital slot confirmation."""
    from sqlalchemy import select
    from app.models.transfusion import Transfusion
    from app.models.enums import TransfusionStatus, HospitalConfirmation
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Transfusion)
        .where(Transfusion.hospital_id == hospital_id)
        .where(Transfusion.hospital_confirmation == HospitalConfirmation.pending)
        .where(Transfusion.deleted_at.is_(None))
        .where(Transfusion.status.not_in([
            TransfusionStatus.completed,
            TransfusionStatus.cancelled,
            TransfusionStatus.failed,
        ]))
        .options(
            selectinload(Transfusion.patient),
            selectinload(Transfusion.donor),
            selectinload(Transfusion.coordinator),
        )
        .order_by(Transfusion.scheduled_date.asc())
        .limit(20)
    )
    items = list(result.scalars().all())
    return [
        {
            "id": str(t.id),
            "patient_id": str(t.patient_id),
            "patient_name": t.patient.name if t.patient else "Patient",
            "patient_blood_group": t.patient.blood_group.value if t.patient else None,
            "hospital_id": str(t.hospital_id) if t.hospital_id else None,
            "donor_id": str(t.donor_id) if t.donor_id else None,
            "donor_name": t.donor.name if t.donor else "TBD",
            "donor_medical_clearance_url": t.donor.medical_clearance_url if t.donor and t.donor.medical_clearance_url else None,
            "status": t.status.value,
            "urgency_level": t.urgency_level.value,
            "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else t.predicted_date.isoformat() if t.predicted_date else None,
            "completed_at": t.actual_date.isoformat() if t.actual_date else None,
            "cancellation_reason": t.notes,
            "coordinator": {
                "id": str(t.coordinator.id),
                "name": t.coordinator.name,
                "phone": t.coordinator.phone,
                "organization": t.coordinator.organization,
                "assigned_region": t.coordinator.assigned_region,
            } if t.coordinator else None,
        }
        for t in items
    ]
