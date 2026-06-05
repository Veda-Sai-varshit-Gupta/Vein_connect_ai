"""
Expense Routes
===============
POST   /expenses/submit             donor submits expense claim
GET    /expenses/me                  donor's expense history
GET    /expenses/pending             coordinator: pending queue
POST   /expenses/{id}/approve       coordinator approves
POST   /expenses/{id}/reject        coordinator rejects
"""

from uuid import UUID
from fastapi import APIRouter
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.expense import ExpenseCreate, ExpenseRejectRequest, ExpenseResponse
from app.services.expense_service import ExpenseService
from app.repositories.donor_repo import DonorRepository

router = APIRouter()
expense_service = ExpenseService()
donor_repo = DonorRepository()


@router.post("/submit", response_model=ExpenseResponse, status_code=201)
async def submit_expense(
    data: ExpenseCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.donor])
    donor = await donor_repo.get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
    return await expense_service.submit_expense(db, donor.id, data)


@router.get("/me", response_model=list[ExpenseResponse])
async def get_my_expenses(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
):
    require_role(current_user, [UserRole.donor])
    donor = await donor_repo.get_by_user_id(db, current_user.id)
    if not donor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Donor profile not found")
    return await expense_service.get_expenses_for_donor(
        db, donor.id, pagination.offset, pagination.page_size
    )


@router.get("/pending", response_model=list[ExpenseResponse])
async def get_pending_expenses(
    current_user: CurrentUser,
    db: DbSession,
    flagged_only: bool = False,
):
    require_role(current_user, [UserRole.coordinator, UserRole.admin, UserRole.patient])
    return await expense_service.get_pending_expenses(db, flagged_only=flagged_only)


@router.post("/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.coordinator, UserRole.admin, UserRole.patient])
    return await expense_service.approve_expense(db, expense_id, current_user.id)


@router.post("/{expense_id}/reject", response_model=ExpenseResponse)
async def reject_expense(
    expense_id: UUID,
    data: ExpenseRejectRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.coordinator, UserRole.admin, UserRole.patient])
    return await expense_service.reject_expense(db, expense_id, data.reason)


@router.get("/donation/{donation_id}", response_model=ExpenseResponse | None)
async def get_expense_by_donation(
    donation_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    from sqlalchemy import select
    from app.models.expense_request import ExpenseRequest
    
    result = await db.execute(
        select(ExpenseRequest)
        .where(ExpenseRequest.donation_id == donation_id)
        .where(ExpenseRequest.deleted_at.is_(None))
    )
    expense = result.scalar_one_or_none()
    return expense


@router.post("/{expense_id}/patient-approve", response_model=ExpenseResponse)
async def patient_approve_expense(
    expense_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.patient])
    return await expense_service.approve_expense(db, expense_id, current_user.id)
