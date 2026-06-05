"""
Wallet Schemas
===============
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import TransactionCategory, TransactionStatus, TransactionType


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    balance: Decimal
    total_earned: Decimal
    total_spent: Decimal
    currency: str


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    wallet_id: UUID
    type: TransactionType
    category: TransactionCategory
    amount: Decimal
    description: str | None
    status: TransactionStatus
    created_at: datetime


class WithdrawRequest(BaseModel):
    amount: Decimal


class ManualCreditRequest(BaseModel):
    user_id: UUID
    amount: Decimal
    description: str
