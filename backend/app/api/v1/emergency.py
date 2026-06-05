"""
Emergency Routes
=================
POST   /emergency/create            coordinator creates emergency transfusion
GET    /emergency/active            all active emergencies
GET    /emergency/{id}/donors       priority donor list for this emergency
"""

from uuid import UUID
from fastapi import APIRouter
from pydantic import BaseModel
from app.dependencies import CurrentUser, DbSession
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.transfusion import TransfusionResponse
from app.services.emergency_service import EmergencyService
from app.repositories.coordinator_repo import CoordinatorRepository

router = APIRouter()
emergency_service = EmergencyService()
coordinator_repo = CoordinatorRepository()


class EmergencyCreateRequest(BaseModel):
    patient_id: UUID
    reason: str


@router.post("/create", response_model=TransfusionResponse, status_code=201)
async def create_emergency(
    data: EmergencyCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Coordinator creates an emergency transfusion — bypasses normal prediction flow."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    coordinator = await coordinator_repo.get_by_user_id(db, current_user.id)
    coordinator_id = coordinator.id if coordinator else current_user.id
    return await emergency_service.create_emergency_transfusion(
        db, data.patient_id, data.reason, coordinator_id
    )


@router.get("/active", response_model=list[TransfusionResponse])
async def get_active_emergencies(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.coordinator, UserRole.admin, UserRole.hospital])
    return await emergency_service.get_active_emergencies(db)


@router.get("/{transfusion_id}/donors")
async def get_emergency_donors(
    transfusion_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """AI-prioritized donors for an emergency transfusion."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    return await emergency_service.get_priority_donors(db, transfusion_id)
