"""
Donor Routes
=============
POST   /donors/register
GET    /donors/me
GET    /donors/{donor_id}
PUT    /donors/{donor_id}
PATCH  /donors/{donor_id}/availability
GET    /donors/{donor_id}/scores
GET    /donors/          (coordinator/admin list)
"""

from uuid import UUID
from fastapi import APIRouter, File, UploadFile
import os
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role, require_self_or_role
from app.models.enums import UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.donor import (
    AvailabilityUpdate,
    DonorCreate,
    DonorResponse,
    DonorUpdate,
    DonorScoresResponse,
)
from app.services.donor_service import DonorService

router = APIRouter()
donor_service = DonorService()


@router.post("/register", response_model=DonorResponse, status_code=201)
async def register_donor(data: DonorCreate, current_user: CurrentUser, db: DbSession):
    """Register a donor profile."""
    require_role(current_user, [UserRole.donor])
    return await donor_service.register(db, current_user.id, data)


@router.post("/upload-clearance")
async def upload_medical_clearance(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
):
    """Upload medical clearance certificate (PDF or Image)."""
    require_role(current_user, [UserRole.donor])
    
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    import uuid
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    from app.repositories.donor_repo import DonorRepository
    donor_repo = DonorRepository()
    donor = await donor_repo.get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
        
    from datetime import datetime, timezone
    url = f"/static/uploads/{filename}"
    await donor_repo.update(db, donor.id, {
        "medical_clearance_url": url,
        "medical_clearance_at": datetime.now(timezone.utc),
    })
    
    await donor_service.recalculate_reliability(db, donor.id)
    
    return {
        "medical_clearance_url": url,
        "medical_clearance_at": datetime.now(timezone.utc).isoformat(),
        "message": "Medical clearance certificate uploaded successfully"
    }


@router.get("/me", response_model=DonorResponse | None)
async def get_my_donor_profile(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.donor])
    from app.repositories.donor_repo import DonorRepository
    return await DonorRepository().get_by_user_id(db, current_user.id)


@router.get("/donations", response_model=list)
async def get_my_donations(current_user: CurrentUser, db: DbSession):
    """Get current donor's completed donation history."""
    require_role(current_user, [UserRole.donor])
    from app.repositories.donor_repo import DonorRepository
    from app.repositories.transfusion_repo import TransfusionRepository
    from app.models.enums import TransfusionStatus
    from sqlalchemy import select
    from app.models.transfusion import Transfusion
    from sqlalchemy.orm import selectinload
    donor = await DonorRepository().get_by_user_id(db, current_user.id)
    if not donor:
        return []
    result = await db.execute(
        select(Transfusion)
        .where(Transfusion.donor_id == donor.id)
        .where(Transfusion.status == TransfusionStatus.completed)
        .where(Transfusion.deleted_at.is_(None))
        .options(
            selectinload(Transfusion.patient),
            selectinload(Transfusion.hospital),
        )
        .order_by(Transfusion.actual_date.desc())
        .limit(20)
    )
    items = list(result.scalars().all())
    # Return as dicts for simplicity
    return [
        {
            "id": str(t.id),
            "transfusion_id": str(t.id),
            "patient_id": str(t.patient_id),
            "patient_blood_group": t.patient.blood_group.value if t.patient else None,
            "hospital_id": str(t.hospital_id) if t.hospital_id else None,
            "hospital_name": t.hospital.name if t.hospital else "Hospital",
            "donor_id": str(t.donor_id) if t.donor_id else None,
            "status": t.status.value,
            "urgency_level": t.urgency_level.value,
            "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
            "completed_at": t.actual_date.isoformat() if t.actual_date else None,
            "donated_at": t.actual_date.isoformat() if t.actual_date else None,
            "cancellation_reason": t.notes,
        }
        for t in items
    ]


@router.post("/availability", response_model=DonorResponse)
async def set_my_availability(
    data: AvailabilityUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Set availability without needing donor_id in path (convenience route)."""
    require_role(current_user, [UserRole.donor])
    from app.repositories.donor_repo import DonorRepository
    donor = await DonorRepository().get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
    return await donor_service.toggle_availability(db, donor.id, data, current_user.id)


@router.get("/", response_model=PaginatedResponse[DonorResponse])
async def list_donors(current_user: CurrentUser, db: DbSession, pagination: Pagination):
    """List all donors (coordinator/admin only)."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin])
    donors, total = await donor_service.list_donors(db, skip=pagination.offset, limit=pagination.page_size)
    return PaginatedResponse.create(donors, total, pagination.page, pagination.page_size)


@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(donor_id: UUID, current_user: CurrentUser, db: DbSession):
    donor = await donor_service.get_donor(db, donor_id)
    require_self_or_role(current_user, donor.user_id, [UserRole.coordinator, UserRole.admin])
    return donor


@router.put("/{donor_id}", response_model=DonorResponse)
async def update_donor(donor_id: UUID, data: DonorUpdate, current_user: CurrentUser, db: DbSession):
    return await donor_service.update_profile(db, donor_id, data, current_user.id, current_user.role)


@router.patch("/{donor_id}/availability", response_model=DonorResponse)
async def update_availability(
    donor_id: UUID,
    data: AvailabilityUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    """Toggle donor availability (donor only)."""
    require_role(current_user, [UserRole.donor])
    return await donor_service.toggle_availability(db, donor_id, data, current_user.id)


@router.get("/{donor_id}/scores", response_model=DonorScoresResponse)
async def get_donor_scores(donor_id: UUID, current_user: CurrentUser, db: DbSession):
    """Get AI-computed reliability and friendship scores."""
    require_role(current_user, [UserRole.coordinator, UserRole.admin, UserRole.donor])
    return await donor_service.get_scores(db, donor_id)
