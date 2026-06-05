"""
Transfusion & Scheduling Schemas
=================================
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    CoordinatorConfirmation,
    DonorConfirmation,
    HospitalConfirmation,
    PatientConfirmation,
    TransfusionStatus,
    UrgencyLevel,
)
from app.schemas.donor import DonorBrief
from app.schemas.patient import PatientBrief
from app.schemas.hospital import HospitalBrief
from app.schemas.coordinator import CoordinatorBrief, CoordinatorResponse


class TransfusionCreate(BaseModel):
    predicted_date: date
    urgency_level: UrgencyLevel = UrgencyLevel.routine
    hospital_id: UUID | None = None
    is_emergency: bool = False
    emergency_reason: str | None = None
    notes: str | None = None


class TransfusionUpdate(BaseModel):
    scheduled_date: date | None = None
    hospital_id: UUID | None = None
    coordinator_id: UUID | None = None
    notes: str | None = None


class TransfusionComplete(BaseModel):
    actual_date: date
    notes: str | None = None


class TransfusionCancel(BaseModel):
    reason: str


class ConfirmationState(BaseModel):
    status: str
    confirmed_at: datetime | None = None


class ConsensusStatusResponse(BaseModel):
    transfusion_id: UUID
    patient: ConfirmationState
    donor: ConfirmationState
    coordinator: ConfirmationState
    hospital: ConfirmationState
    all_confirmed: bool
    pending_count: int


class TransfusionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: TransfusionStatus
    urgency_level: UrgencyLevel
    predicted_date: date
    scheduled_date: date | None
    is_emergency: bool


class TransfusionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    donor_id: UUID | None
    hospital_id: UUID | None
    coordinator_id: UUID | None
    predicted_date: date
    scheduled_date: date | None
    actual_date: date | None
    urgency_level: UrgencyLevel
    status: TransfusionStatus
    patient_confirmation: PatientConfirmation
    donor_confirmation: DonorConfirmation
    coordinator_confirmation: CoordinatorConfirmation
    hospital_confirmation: HospitalConfirmation
    is_emergency: bool
    emergency_reason: str | None
    alternate_hospital_id: UUID | None = None
    previous_donor_id: UUID | None = None
    friendship_score: float | None = None
    patient: PatientBrief | None = None
    donor: DonorBrief | None = None
    hospital: HospitalBrief | None = None
    coordinator: CoordinatorResponse | None = None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AssignDonorRequest(BaseModel):
    donor_id: UUID


class SchedulingInitiateRequest(BaseModel):
    transfusion_id: UUID


class DonorRequestPayload(BaseModel):
    transfusion_id: UUID
    donor_id: UUID


class AlternateHospitalRequest(BaseModel):
    transfusion_id: UUID
