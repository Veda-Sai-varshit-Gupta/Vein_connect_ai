"""
Confirmation Routes
====================
POST   /confirmations/confirm       current user confirms
POST   /confirmations/reject        current user rejects
GET    /confirmations/pending        user's pending queue
GET    /confirmations/{transfusion_id}/status
"""

from uuid import UUID
from fastapi import APIRouter
from app.dependencies import CurrentUser, DbSession
from app.schemas.confirmation import (
    ConfirmAction,
    ConfirmationResponse,
    PendingConfirmationResponse,
    RejectAction,
    CompletionConfirmationResponse,
    PendingCompletionResponse,
)
from app.services.confirmation_service import ConfirmationService

router = APIRouter()
confirmation_service = ConfirmationService()


@router.post("/confirm", response_model=ConfirmationResponse)
async def confirm_transfusion(data: ConfirmAction, current_user: CurrentUser, db: DbSession):
    """The current user (patient/donor/coordinator/hospital) confirms a transfusion."""
    return await confirmation_service.confirm(
        db,
        transfusion_id=data.transfusion_id,
        user_id=current_user.id,
        user_role=current_user.role,
        notes=data.notes,
    )


@router.post("/reject", response_model=ConfirmationResponse)
async def reject_transfusion(data: RejectAction, current_user: CurrentUser, db: DbSession):
    """The current user rejects/declines a transfusion request."""
    return await confirmation_service.reject(
        db,
        transfusion_id=data.transfusion_id,
        user_id=current_user.id,
        user_role=current_user.role,
        reason=data.reason,
    )


@router.get("/pending", response_model=list[ConfirmationResponse])
async def get_pending_confirmations(current_user: CurrentUser, db: DbSession):
    """Get all pending confirmations waiting for the current user's action."""
    return await confirmation_service.get_pending_for_user(db, current_user.id)


@router.get("/{transfusion_id}/status", response_model=list[ConfirmationResponse])
async def get_transfusion_confirmations(
    transfusion_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all confirmation records for a specific transfusion."""
    return await confirmation_service.get_by_transfusion(db, transfusion_id)


@router.post("/confirm-completion", response_model=list[CompletionConfirmationResponse])
async def confirm_transfusion_completion(
    data: ConfirmAction,
    current_user: CurrentUser,
    db: DbSession,
):
    """The current user confirms the completion of a transfusion."""
    return await confirmation_service.confirm_completion(
        db,
        transfusion_id=data.transfusion_id,
        user_id=current_user.id,
        user_role=current_user.role,
        notes=data.notes,
    )


@router.get("/{transfusion_id}/completion-status", response_model=list[CompletionConfirmationResponse])
async def get_transfusion_completion_status(
    transfusion_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all completion confirmation records for a specific transfusion."""
    return await confirmation_service.get_completion_confirmations(db, transfusion_id)


@router.get("/pending-completions", response_model=list[PendingCompletionResponse])
async def get_pending_completion_confirmations(
    current_user: CurrentUser,
    db: DbSession,
):
    """Get all pending completion confirmations waiting for the current user's action."""
    return await confirmation_service.get_pending_completion_confirmations_for_user(db, current_user.id)

