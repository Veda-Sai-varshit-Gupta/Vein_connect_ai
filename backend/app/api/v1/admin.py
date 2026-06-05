"""
Admin Routes
=============
GET    /admin/stats              platform-wide KPI stats
GET    /admin/users              all users
PATCH  /admin/users/{id}/deactivate
PATCH  /admin/users/{id}/activate
"""

from uuid import UUID
from fastapi import APIRouter
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.auth import UserResponse
from app.repositories.user_repo import UserRepository
from app.repositories.patient_repo import PatientRepository
from app.repositories.donor_repo import DonorRepository
from app.repositories.hospital_repo import HospitalRepository
from app.repositories.transfusion_repo import TransfusionRepository

router = APIRouter()
user_repo = UserRepository()
patient_repo = PatientRepository()
donor_repo = DonorRepository()
hospital_repo = HospitalRepository()
transfusion_repo = TransfusionRepository()


@router.get("/stats")
async def get_platform_stats(current_user: CurrentUser, db: DbSession):
    """Platform-wide KPI stats for admin dashboard."""
    require_role(current_user, [UserRole.admin])
    from app.models.enums import TransfusionStatus, UrgencyLevel
    
    total_patients = await patient_repo.count(db)
    total_donors = await donor_repo.count(db)
    total_users = await user_repo.count(db)
    total_hospitals = await hospital_repo.count(db)
    
    active_transfusions = await transfusion_repo.count(
        db,
        filters=[
            __import__('app.models.transfusion', fromlist=['Transfusion']).Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
                TransfusionStatus.failed,
            ])
        ]
    )
    
    completed_this_month = await transfusion_repo.count(
        db,
        filters=[
            __import__('app.models.transfusion', fromlist=['Transfusion']).Transfusion.status == TransfusionStatus.completed
        ]
    )
    
    emergencies_today = await transfusion_repo.count(
        db,
        filters=[
            __import__('app.models.transfusion', fromlist=['Transfusion']).Transfusion.urgency_level == UrgencyLevel.emergency,
            __import__('app.models.transfusion', fromlist=['Transfusion']).Transfusion.status.not_in([
                TransfusionStatus.completed,
                TransfusionStatus.cancelled,
                TransfusionStatus.failed,
            ])
        ]
    )
    
    return {
        "total_patients": total_patients,
        "total_donors": total_donors,
        "total_users": total_users,
        "active_transfusions": active_transfusions,
        "total_hospitals": total_hospitals,
        "completed_this_month": completed_this_month,
        "emergencies_today": emergencies_today,
    }


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_all_users(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
):
    require_role(current_user, [UserRole.admin])
    users = await user_repo.get_all(db, skip=pagination.offset, limit=pagination.page_size)
    total = await user_repo.count(db)
    return PaginatedResponse.create(users, total, pagination.page, pagination.page_size)


@router.patch("/users/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.admin])
    await user_repo.set_active(db, user_id, False)
    return MessageResponse(message="User deactivated successfully")


@router.patch("/users/{user_id}/activate", response_model=MessageResponse)
async def activate_user(
    user_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.admin])
    await user_repo.set_active(db, user_id, True)
    return MessageResponse(message="User activated successfully")
