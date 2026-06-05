"""
Transfusion Routes
===================
POST   /transfusions/                    create (patient)
GET    /transfusions/                    list
GET    /transfusions/upcoming            upcoming window
GET    /transfusions/emergency           active emergencies
GET    /transfusions/{id}
GET    /transfusions/{id}/consensus      4-party status
POST   /transfusions/{id}/patient-confirm
POST   /transfusions/{id}/assign-donor   (coordinator)
POST   /transfusions/{id}/cancel
POST   /transfusions/{id}/complete       (coordinator)
GET    /transfusions/{id}/donor-matches  AI ranked donors
"""

from uuid import UUID
from fastapi import APIRouter, Query
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import TransfusionStatus, UrgencyLevel, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.transfusion import (
    AssignDonorRequest,
    ConsensusStatusResponse,
    TransfusionBrief,
    TransfusionCancel,
    TransfusionComplete,
    TransfusionCreate,
    TransfusionResponse,
    TransfusionUpdate,
)
from app.schemas.donor import DonorMatchResult
from app.services.transfusion_service import TransfusionService
from app.services.scheduling_service import SchedulingService

router = APIRouter()
transfusion_service = TransfusionService()
scheduling_service = SchedulingService()


@router.post("/", response_model=TransfusionResponse, status_code=201)
async def create_transfusion(
    data: TransfusionCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Patient initiates a new transfusion record."""
    require_role(current_user, [UserRole.patient, UserRole.coordinator])
    # Get patient_id from the current user's patient profile
    from app.repositories.patient_repo import PatientRepository
    patient_repo = PatientRepository()
    patient = await patient_repo.get_by_user_id(db, current_user.id)
    if not patient:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Patient profile not found")
    return await transfusion_service.create_transfusion(db, patient.id, data)


@router.get("/upcoming", response_model=list[TransfusionResponse])
async def get_upcoming_transfusions(
    current_user: CurrentUser,
    db: DbSession,
    days: int = Query(default=14, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=50),
    urgency: UrgencyLevel | None = Query(None),
):
    """Get upcoming transfusions. Patients see only their own; coordinators/admin see all."""
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.transfusion import Transfusion
    if current_user.role == UserRole.patient:
        from app.repositories.patient_repo import PatientRepository
        patient = await PatientRepository().get_by_user_id(db, current_user.id)
        if not patient:
            return []
        
        stmt = (
            select(Transfusion)
            .where(Transfusion.patient_id == patient.id)
            .where(Transfusion.deleted_at.is_(None))
            .options(
                selectinload(Transfusion.donor),
                selectinload(Transfusion.hospital),
                selectinload(Transfusion.coordinator),
            )
        )
        result = await db.execute(stmt.order_by(Transfusion.predicted_date.desc()).limit(limit))
        items = list(result.scalars().all())
        
        # Filter to non-completed, non-cancelled within the upcoming window
        from datetime import date, timedelta
        future_cutoff = date.today() + timedelta(days=days)
        upcoming_statuses = {
            "predicted", "patient_confirmed", "matching_donors",
            "donor_confirmed", "coordinator_confirmed", "hospital_confirmed",
            "scheduled", "in_progress",
        }
        res_items = [
            t for t in items
            if t.status.value in upcoming_statuses
        ][:limit]
        for t in res_items:
            score = None
            if t.patient_id and t.donor_id:
                from app.models.friendship_score import FriendshipScore
                fs_res = await db.execute(
                    select(FriendshipScore)
                    .where(FriendshipScore.patient_id == t.patient_id)
                    .where(FriendshipScore.donor_id == t.donor_id)
                )
                fs = fs_res.scalar_one_or_none()
                if fs:
                    score = float(fs.score)
            t.friendship_score = score
        return res_items
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    return await scheduling_service.get_upcoming_transfusions(db, days=days, urgency=urgency)


@router.get("/history", response_model=list[TransfusionBrief])
async def get_transfusion_history(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
):
    """Get completed transfusion history. Patients see only their own; coordinators/admin see all."""
    if current_user.role == UserRole.patient:
        from app.repositories.patient_repo import PatientRepository
        from app.repositories.transfusion_repo import TransfusionRepository as _TRepo
        patient = await PatientRepository().get_by_user_id(db, current_user.id)
        if not patient:
            return []
        items = await _TRepo().get_by_patient(
            db, patient.id, skip=0, limit=limit, status=TransfusionStatus.completed
        )
        return items
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    from app.repositories.transfusion_repo import TransfusionRepository
    items = await TransfusionRepository().get_by_status(
        db, TransfusionStatus.completed, skip=0, limit=limit
    )
    return items


@router.get("/pending-donor", response_model=list[TransfusionResponse])
async def get_pending_donor_transfusions(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
):
    """Get transfusions assigned to the current donor that need their response."""
    require_role(current_user, [UserRole.donor])
    from app.repositories.donor_repo import DonorRepository
    from sqlalchemy import select
    from app.models.transfusion import Transfusion
    from app.models.enums import DonorConfirmation
    donor = await DonorRepository().get_by_user_id(db, current_user.id)
    if not donor:
        return []
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Transfusion)
        .where(Transfusion.donor_id == donor.id)
        .where(Transfusion.donor_confirmation == DonorConfirmation.pending)
        .where(Transfusion.deleted_at.is_(None))
        .where(Transfusion.status.not_in([
            TransfusionStatus.completed,
            TransfusionStatus.cancelled,
            TransfusionStatus.failed,
        ]))
        .options(
            selectinload(Transfusion.patient),
            selectinload(Transfusion.donor),
            selectinload(Transfusion.hospital),
            selectinload(Transfusion.coordinator),
        )
        .order_by(Transfusion.scheduled_date.asc())
        .limit(limit)
    )
    items = list(result.scalars().all())
    for t in items:
        score = None
        if t.patient_id and t.donor_id:
            from app.models.friendship_score import FriendshipScore
            res = await db.execute(
                select(FriendshipScore)
                .where(FriendshipScore.patient_id == t.patient_id)
                .where(FriendshipScore.donor_id == t.donor_id)
            )
            fs = res.scalar_one_or_none()
            if fs:
                score = float(fs.score)
        t.friendship_score = score
    return items


@router.get("/emergency", response_model=list[TransfusionResponse])
async def get_emergency_transfusions(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    from app.repositories.transfusion_repo import TransfusionRepository
    return await TransfusionRepository().get_emergency(db)


@router.get("/", response_model=PaginatedResponse[TransfusionBrief])
async def list_transfusions(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
    status: str | None = Query(None),
):
    from app.repositories.patient_repo import PatientRepository
    from app.repositories.coordinator_repo import CoordinatorRepository
    patient_id = None
    coordinator_id = None
    if current_user.role == UserRole.patient:
        p = await PatientRepository().get_by_user_id(db, current_user.id)
        patient_id = p.id if p else None
    elif current_user.role == UserRole.coordinator:
        c = await CoordinatorRepository().get_by_user_id(db, current_user.id)
        coordinator_id = c.id if c else None
    items, total = await transfusion_service.list_transfusions(
        db, patient_id=patient_id, coordinator_id=coordinator_id,
        status=status, skip=pagination.offset, limit=pagination.page_size
    )
    return PaginatedResponse.create(items, total, pagination.page, pagination.page_size)


@router.get("/{transfusion_id}", response_model=TransfusionResponse)
async def get_transfusion(transfusion_id: UUID, current_user: CurrentUser, db: DbSession):
    t = await transfusion_service.get_transfusion(db, transfusion_id)
    score = None
    if t.patient_id and t.donor_id:
        from sqlalchemy import select
        from app.models.friendship_score import FriendshipScore
        res = await db.execute(
            select(FriendshipScore)
            .where(FriendshipScore.patient_id == t.patient_id)
            .where(FriendshipScore.donor_id == t.donor_id)
        )
        fs = res.scalar_one_or_none()
        if fs:
            score = float(fs.score)
    t.friendship_score = score
    return t


@router.put("/{transfusion_id}", response_model=TransfusionResponse)
async def update_transfusion(
    transfusion_id: UUID,
    data: TransfusionUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Coordinator or Admin updates transfusion details."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    return await transfusion_service.update_transfusion(db, transfusion_id, data)


@router.get("/{transfusion_id}/consensus", response_model=ConsensusStatusResponse)
async def get_consensus_status(transfusion_id: UUID, current_user: CurrentUser, db: DbSession):
    return await transfusion_service.get_consensus_status(db, transfusion_id)


@router.post("/{transfusion_id}/patient-confirm", response_model=TransfusionResponse)
async def patient_confirm(
    transfusion_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Patient confirms they want the scheduled transfusion."""
    require_role(current_user, [UserRole.patient])
    return await transfusion_service.patient_confirm(db, transfusion_id, current_user.id)


@router.post("/{transfusion_id}/assign-donor", response_model=TransfusionResponse)
async def assign_donor(
    transfusion_id: UUID,
    data: AssignDonorRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Coordinator selects a donor from AI recommendations."""
    require_role(current_user, [UserRole.coordinator])
    return await transfusion_service.assign_donor(db, transfusion_id, data.donor_id)


@router.post("/{transfusion_id}/cancel", response_model=TransfusionResponse)
async def cancel_transfusion(
    transfusion_id: UUID,
    data: TransfusionCancel,
    current_user: CurrentUser,
    db: DbSession,
):
    if current_user.role == UserRole.coordinator:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Coordinators are not permitted to cancel transfusion runs")
    return await transfusion_service.cancel_transfusion(
        db, transfusion_id, data.reason, current_user.role
    )


@router.post("/{transfusion_id}/complete", response_model=TransfusionResponse)
async def complete_transfusion(
    transfusion_id: UUID,
    data: TransfusionComplete,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.hospital, UserRole.admin])
    return await transfusion_service.mark_completed(db, transfusion_id, data)


@router.get("/{transfusion_id}/donor-matches", response_model=list[DonorMatchResult])
async def get_donor_matches(
    transfusion_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(default=10, ge=1, le=50),
):
    """AI-ranked donor candidates for this transfusion (coordinator view)."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    return await scheduling_service.get_donor_matches(db, transfusion_id, limit=limit)
