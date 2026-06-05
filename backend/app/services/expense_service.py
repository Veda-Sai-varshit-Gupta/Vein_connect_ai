"""
Expense Service
===============
Manages reimbursement claims submitted by donors for travel and other expenses.
Includes automated AI-powered flagging rules and wallet integration on approval.
"""

from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import ExpenseStatus, TransactionType, TransactionCategory, TransactionStatus
from app.models.expense_request import ExpenseRequest
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.donor_repo import DonorRepository
from app.repositories.wallet_repo import WalletRepository
from app.schemas.expense import ExpenseCreate

expense_repo = ExpenseRepository()
donor_repo = DonorRepository()
wallet_repo = WalletRepository()


class ExpenseService:

    async def submit_expense(
        self,
        db: AsyncSession,
        donor_id: UUID,
        data: ExpenseCreate,
    ) -> ExpenseRequest:
        # Verify donor profile exists
        donor = await donor_repo.get_by_id(db, donor_id)
        if not donor:
            raise NotFoundException("Donor profile not found")

        # Total amount calculation
        total_amount = data.travel_expense + data.other_expense
        if total_amount <= 0:
            raise BadRequestException("Total expense amount must be greater than zero")

        # Basic AI / Heuristic rules for flagging suspicious or high claims
        is_flagged = False
        flag_reason = None
        
        # Flag if total amount is unusually high for a single donation (e.g. > ₹5000)
        if total_amount > Decimal("5000.00"):
            is_flagged = True
            flag_reason = "Total claim amount exceeds standard threshold of ₹5000.00"
        # Flag if travel expenses look excessive (e.g. > ₹2000)
        elif data.travel_expense > Decimal("2000.00"):
            is_flagged = True
            flag_reason = "Travel expense claim exceeds standard threshold of ₹2000.00"

        expense = await expense_repo.create(db, {
            "donation_id": data.donation_id,
            "donor_id": donor_id,
            "travel_expense": data.travel_expense,
            "other_expense": data.other_expense,
            "total_amount": total_amount,
            "description": data.description,
            "status": ExpenseStatus.flagged if is_flagged else ExpenseStatus.pending,
            "is_flagged_by_ai": is_flagged,
            "flag_reason": flag_reason,
        })
        return expense

    async def get_expenses_for_donor(
        self,
        db: AsyncSession,
        donor_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ExpenseRequest]:
        return await expense_repo.get_by_donor(db, donor_id, skip, limit)

    async def get_pending_expenses(
        self,
        db: AsyncSession,
        flagged_only: bool = False,
    ) -> list[ExpenseRequest]:
        return await expense_repo.get_pending(db, flagged_only=flagged_only)

    async def approve_expense(
        self,
        db: AsyncSession,
        expense_id: UUID,
        coordinator_id: UUID,
    ) -> ExpenseRequest:
        expense = await expense_repo.get_by_id(db, expense_id)
        if not expense:
            raise NotFoundException("Expense claim not found")

        if expense.status in [ExpenseStatus.approved, ExpenseStatus.rejected]:
            raise BadRequestException(f"Cannot approve expense with status: {expense.status.value}")

        # Retrieve donor profile to find the user_id associated with the wallet
        donor = await donor_repo.get_by_id(db, expense.donor_id)
        if not donor:
            raise NotFoundException("Associated donor profile not found")

        # Get or create the donor's wallet
        wallet = await wallet_repo.get_by_user_id(db, donor.user_id)
        if not wallet:
            wallet = await wallet_repo.create_wallet(db, donor.user_id)

        # Credit the total approved amount to the wallet
        await wallet_repo.credit(db, wallet.id, expense.total_amount)
        await wallet_repo.create_transaction(db, {
            "wallet_id": wallet.id,
            "type": TransactionType.credit,
            "category": TransactionCategory.reimbursement,
            "amount": expense.total_amount,
            "description": f"Approved reimbursement for expense claim: {expense.id}",
            "status": TransactionStatus.completed,
        })

        # Update the expense status
        now = datetime.now(timezone.utc)
        updated = await expense_repo.update(db, expense_id, {
            "status": ExpenseStatus.approved,
            "reviewed_by": coordinator_id,
            "reviewed_at": now,
        })
        return updated

    async def reject_expense(
        self,
        db: AsyncSession,
        expense_id: UUID,
        reason: str,
    ) -> ExpenseRequest:
        expense = await expense_repo.get_by_id(db, expense_id)
        if not expense:
            raise NotFoundException("Expense claim not found")

        if expense.status in [ExpenseStatus.approved, ExpenseStatus.rejected]:
            raise BadRequestException(f"Cannot reject expense with status: {expense.status.value}")

        now = datetime.now(timezone.utc)
        updated = await expense_repo.update(db, expense_id, {
            "status": ExpenseStatus.rejected,
            "flag_reason": f"Rejected by coordinator: {reason}",
            "reviewed_at": now,
        })
        return updated
