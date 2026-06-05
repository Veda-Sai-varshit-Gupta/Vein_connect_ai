"""
Coordinator Routes
===================
POST   /coordinators/register
GET    /coordinators/me
GET    /coordinators/{coordinator_id}
PUT    /coordinators/{coordinator_id}
GET    /coordinators/pending       (admin: pending approvals)
POST   /coordinators/{id}/approve  (admin)
POST   /coordinators/{id}/reject   (admin)
"""

from uuid import UUID
from fastapi import APIRouter
from app.dependencies import CurrentUser, DbSession
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.coordinator import (
    ApprovalAction,
    CoordinatorCreate,
    CoordinatorResponse,
    CoordinatorUpdate,
    DonorOverrideRequest,
    UnresponsiveDonorResponse,
    HospitalOverrideRequest,
    HospitalCapacityDetailResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.transfusion import TransfusionBrief, TransfusionResponse
from app.services.coordinator_service import CoordinatorService
from app.services.scheduling_service import SchedulingService
from app.repositories.transfusion_repo import TransfusionRepository

router = APIRouter()
coordinator_service = CoordinatorService()
scheduling_service = SchedulingService()


@router.post("/register", response_model=CoordinatorResponse, status_code=201)
async def register_coordinator(data: CoordinatorCreate, current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator])
    return await coordinator_service.register(db, current_user.id, data)


@router.get("/me", response_model=CoordinatorResponse | None)
async def get_my_coordinator_profile(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator])
    from app.repositories.coordinator_repo import CoordinatorRepository
    repo = CoordinatorRepository()
    return await repo.get_by_user_id(db, current_user.id)


@router.get("/me/stats")
async def get_coordinator_stats(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator])
    from app.repositories.coordinator_repo import CoordinatorRepository
    from app.repositories.transfusion_repo import TransfusionRepository
    from app.models.enums import TransfusionStatus, UrgencyLevel
    from datetime import date
    from app.models.transfusion import Transfusion
    
    coord = await CoordinatorRepository().get_by_user_id(db, current_user.id)
    if not coord:
        return {
            "active_count": 0,
            "pending_count": 0,
            "done_today": 0,
            "emergency_count": 0,
        }
        
    # Active transfusion count assigned to this coordinator
    active_count = await TransfusionRepository().count(
        db,
        filters=[
            Transfusion.coordinator_id == coord.id,
            Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
                TransfusionStatus.failed,
            ])
        ]
    )
    
    # Pending confirmation count
    pending_count = await TransfusionRepository().count(
        db,
        filters=[
            Transfusion.coordinator_id == coord.id,
            Transfusion.status.in_([
                TransfusionStatus.predicted,
                TransfusionStatus.patient_confirmed,
                TransfusionStatus.matching_donors,
            ])
        ]
    )
    
    # Done today count
    done_today = await TransfusionRepository().count(
        db,
        filters=[
            Transfusion.coordinator_id == coord.id,
            Transfusion.status == TransfusionStatus.completed,
            Transfusion.actual_date == date.today()
        ]
    )
    
    # Emergency count
    emergency_count = await TransfusionRepository().count(
        db,
        filters=[
            Transfusion.coordinator_id == coord.id,
            Transfusion.urgency_level == UrgencyLevel.emergency,
            Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
                TransfusionStatus.failed,
            ])
        ]
    )
    
    return {
        "active_count": active_count,
        "pending_count": pending_count,
        "done_today": done_today,
        "emergency_count": emergency_count,
    }


@router.get("/me/transfusions", response_model=list[TransfusionResponse])
async def get_my_transfusions(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator])
    from app.repositories.coordinator_repo import CoordinatorRepository
    coord = await CoordinatorRepository().get_by_user_id(db, current_user.id)
    if not coord:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Coordinator profile not found")
    return await TransfusionRepository().get_by_coordinator(db, coord.id)


@router.get("/me/unresponsive-donors", response_model=list[UnresponsiveDonorResponse])
async def get_unresponsive_donors(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator])
    return await scheduling_service.get_unresponsive_donors(db)


@router.post("/me/override-donor", response_model=TransfusionResponse)
async def override_donor(
    data: DonorOverrideRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.coordinator])
    return await scheduling_service.override_donor(
        db, data.transfusion_id, data.new_donor_id
    )


@router.post("/me/override-hospital", response_model=TransfusionResponse)
async def override_hospital(
    data: HospitalOverrideRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.coordinator])
    return await scheduling_service.override_hospital(
        db, data.transfusion_id, data.hospital_id
    )


@router.get("/me/hospitals-capacity", response_model=list[HospitalCapacityDetailResponse])
async def get_hospitals_capacity(
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.coordinator])
    from app.repositories.hospital_repo import HospitalRepository
    repo = HospitalRepository()
    hospitals = await repo.get_all(db, limit=100)
    
    results = []
    for h in hospitals:
        capacity = await repo.get_capacity(db, h.id)
        results.append({
            "id": h.id,
            "name": h.name,
            "address": h.address,
            "city": h.city,
            "state": h.state,
            "coordinator_name": h.coordinator_name,
            "coordinator_phone": h.coordinator_phone,
            "coordinator_email": h.coordinator_email,
            "total_transfusion_beds": h.total_transfusion_beds,
            "available_beds": capacity.available_beds if capacity else h.total_transfusion_beds,
            "occupied_beds": capacity.occupied_beds if capacity else 0,
            "total_transfusion_chairs": h.total_transfusion_chairs,
            "available_chairs": capacity.available_chairs if capacity else h.total_transfusion_chairs,
            "occupied_chairs": capacity.occupied_chairs if capacity else 0,
            "emergency_capacity": h.emergency_capacity,
            "emergency_capacity_available": capacity.emergency_capacity_available if capacity else h.emergency_capacity,
        })
    return results




@router.get("/pending", response_model=list[CoordinatorResponse])
async def get_pending_approvals(current_user: CurrentUser, db: DbSession):
    """Get all coordinators awaiting admin approval."""
    require_role(current_user, [UserRole.admin])
    return await coordinator_service.get_pending_approvals(db)


@router.get("/{coordinator_id}", response_model=CoordinatorResponse)
async def get_coordinator(coordinator_id: UUID, current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.admin, UserRole.coordinator])
    return await coordinator_service.get_coordinator(db, coordinator_id)


@router.post("/{coordinator_id}/approve", response_model=CoordinatorResponse)
async def approve_coordinator(
    coordinator_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Approve a coordinator application (admin only)."""
    require_role(current_user, [UserRole.admin])
    return await coordinator_service.approve(db, coordinator_id, current_user.id)


@router.post("/{coordinator_id}/reject", response_model=CoordinatorResponse)
async def reject_coordinator(
    coordinator_id: UUID,
    data: ApprovalAction,
    current_user: CurrentUser,
    db: DbSession,
):
    """Reject a coordinator application (admin only)."""
    require_role(current_user, [UserRole.admin])
    reason = data.reason or "Application rejected by admin"
    return await coordinator_service.reject(db, coordinator_id, reason)
