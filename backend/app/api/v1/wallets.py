"""
Wallet Routes
==============
GET    /wallets/me                  current user's wallet balance
GET    /wallets/me/transactions     transaction history
POST   /wallets/me/withdraw         withdraw to UPI
POST   /wallets/admin/credit        (admin) manual credit
"""

from fastapi import APIRouter
from decimal import Decimal
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import UserRole
from app.schemas.wallet import (
    ManualCreditRequest,
    TransactionResponse,
    WalletResponse,
    WithdrawRequest,
)
from app.services.wallet_service import WalletService
from app.repositories.wallet_repo import WalletRepository

router = APIRouter()
wallet_service = WalletService()
wallet_repo = WalletRepository()


@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(current_user: CurrentUser, db: DbSession):
    return await wallet_service.get_wallet(db, current_user.id)


@router.get("/me/transactions", response_model=list[TransactionResponse])
async def get_my_transactions(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
):
    return await wallet_service.get_transactions(
        db, current_user.id, pagination.offset, pagination.page_size
    )


@router.post("/me/withdraw")
async def withdraw(
    data: WithdrawRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Withdraw wallet balance to registered UPI ID."""
    require_role(current_user, [UserRole.donor])
    return await wallet_service.withdraw(db, current_user.id, data.amount)


@router.post("/admin/credit")
async def admin_credit(
    data: ManualCreditRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Admin manually credits a user's wallet (e.g., for corrections)."""
    require_role(current_user, [UserRole.admin])
    wallet = await wallet_repo.get_by_user_id(db, data.user_id)
    if not wallet:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Wallet", str(data.user_id))
    from app.models.enums import TransactionType, TransactionCategory, TransactionStatus
    await wallet_repo.credit(db, wallet.id, data.amount)
    await wallet_repo.create_transaction(db, {
        "wallet_id": wallet.id,
        "type": TransactionType.credit,
        "category": TransactionCategory.correction,
        "amount": data.amount,
        "description": data.description,
        "status": TransactionStatus.completed,
    })
    return {"message": f"₹{data.amount} credited successfully"}
