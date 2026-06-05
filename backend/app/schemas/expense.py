"""
Expense Request Schemas
========================
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ExpenseStatus


class ExpenseCreate(BaseModel):
    donation_id: UUID
    travel_expense: Decimal = Decimal("0.00")
    other_expense: Decimal = Decimal("0.00")
    description: str | None = None


class ExpenseRejectRequest(BaseModel):
    reason: str


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    donation_id: UUID
    donor_id: UUID
    travel_expense: Decimal
    other_expense: Decimal
    total_amount: Decimal
    description: str | None
    status: ExpenseStatus
    is_flagged_by_ai: bool
    flag_reason: str | None
    reviewed_at: datetime | None
    created_at: datetime
