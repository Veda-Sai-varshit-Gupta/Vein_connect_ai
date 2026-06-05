"""
Confirmation Schemas
=====================
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ConfirmationRole, ConfirmationStatus


class ConfirmAction(BaseModel):
    transfusion_id: UUID
    notes: str | None = None


class RejectAction(BaseModel):
    transfusion_id: UUID
    reason: str | None = None


class OverrideAction(BaseModel):
    transfusion_id: UUID
    role: ConfirmationRole
    notes: str


class ReminderRequest(BaseModel):
    transfusion_id: UUID
    user_id: UUID


class ConfirmationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    transfusion_id: UUID
    user_id: UUID
    role: ConfirmationRole
    status: ConfirmationStatus
    notes: str | None
    reminder_count: int
    responded_at: datetime | None
    created_at: datetime


class PendingConfirmationResponse(BaseModel):
    transfusion_id: UUID
    role: ConfirmationRole
    urgency_level: str
    patient_name: str
    predicted_date: str
    hospital_name: str | None


class CompletionConfirmationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    transfusion_id: UUID
    user_id: UUID
    role: ConfirmationRole
    status: ConfirmationStatus
    notes: str | None
    responded_at: datetime | None


class PendingCompletionResponse(BaseModel):
    id: UUID
    transfusion_id: UUID
    role: ConfirmationRole
    status: ConfirmationStatus
    patient_name: str | None
    hospital_name: str | None
    scheduled_date: str | None
    urgency_level: str | None


