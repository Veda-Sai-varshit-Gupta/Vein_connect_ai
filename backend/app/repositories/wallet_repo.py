from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.enums import TransactionStatus


class WalletRepository:
    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Wallet | None:
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_wallet(self, db: AsyncSession, user_id: UUID) -> Wallet:
        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        await db.flush()
        await db.refresh(wallet)
        return wallet

    async def credit(self, db: AsyncSession, wallet_id: UUID, amount: Decimal) -> None:
        await db.execute(
            update(Wallet).where(Wallet.id == wallet_id).values(
                balance=Wallet.balance + amount,
                total_earned=Wallet.total_earned + amount,
            )
        )
        await db.flush()

    async def debit(self, db: AsyncSession, wallet_id: UUID, amount: Decimal) -> bool:
        # Check balance first
        wallet = await db.get(Wallet, wallet_id)
        if not wallet or wallet.balance < amount:
            return False
        await db.execute(
            update(Wallet).where(Wallet.id == wallet_id).values(
                balance=Wallet.balance - amount,
                total_spent=Wallet.total_spent + amount,
            )
        )
        await db.flush()
        return True

    async def get_transactions(
        self,
        db: AsyncSession,
        wallet_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[WalletTransaction]:
        result = await db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet_id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create_transaction(self, db: AsyncSession, data: dict) -> WalletTransaction:
        txn = WalletTransaction(**data)
        db.add(txn)
        await db.flush()
        await db.refresh(txn)
        return txn
