"""
Wallet Service
===============
Balance management, transaction history, withdrawal.
"""

from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.enums import TransactionCategory, TransactionStatus, TransactionType
from app.repositories.wallet_repo import WalletRepository

wallet_repo = WalletRepository()

MIN_WITHDRAWAL = Decimal("100.00")


class WalletService:

    async def get_wallet(self, db: AsyncSession, user_id: UUID):
        wallet = await wallet_repo.get_by_user_id(db, user_id)
        if not wallet:
            raise NotFoundException("Wallet not found. Please contact support.")
        return wallet

    async def withdraw(
        self,
        db: AsyncSession,
        user_id: UUID,
        amount: Decimal,
    ) -> dict:
        if amount < MIN_WITHDRAWAL:
            raise BadRequestException(f"Minimum withdrawal amount is ₹{MIN_WITHDRAWAL}")

        wallet = await self.get_wallet(db, user_id)
        success = await wallet_repo.debit(db, wallet.id, amount)

        if not success:
            raise BadRequestException(f"Insufficient balance. Current balance: ₹{wallet.balance}")

        await wallet_repo.create_transaction(db, {
            "wallet_id": wallet.id,
            "type": TransactionType.debit,
            "category": TransactionCategory.withdrawal,
            "amount": amount,
            "description": f"Withdrawal of ₹{amount} to UPI",
            "status": TransactionStatus.completed,
        })

        return {"withdrawn": amount, "new_balance": wallet.balance - amount}

    async def get_transactions(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20):
        wallet = await self.get_wallet(db, user_id)
        return await wallet_repo.get_transactions(db, wallet.id, skip, limit)
