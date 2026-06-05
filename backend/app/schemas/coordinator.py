"""
Coordinator Schemas
====================
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStatus


class CoordinatorCreate(BaseModel):
    name: str
    phone: str
    organization: str
    assigned_region: str


class CoordinatorUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    organization: str | None = None
    assigned_region: str | None = None


class CoordinatorBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    assigned_region: str
    approval_status: ApprovalStatus


class CoordinatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    name: str
    phone: str
    organization: str
    assigned_region: str
    approval_status: ApprovalStatus
    rejection_reason: str | None
    created_at: datetime


class ApprovalAction(BaseModel):
    reason: str | None = None  # Required for rejection


class DonorOverrideRequest(BaseModel):
    transfusion_id: UUID
    new_donor_id: UUID


class UnresponsiveDonorResponse(BaseModel):
    transfusion_id: UUID
    scheduled_date: str | None = None
    urgency_level: str
    patient_name: str
    hospital_name: str
    donor_id: UUID
    donor_name: str
    donor_phone: str
    donor_upi: str | None = None
    donor_email: str
    reminder_count: int
    created_at: str


class HospitalOverrideRequest(BaseModel):
    transfusion_id: UUID
    hospital_id: UUID


class HospitalCapacityDetailResponse(BaseModel):
    id: UUID
    name: str
    address: str
    city: str
    state: str
    coordinator_name: str | None = None
    coordinator_phone: str | None = None
    coordinator_email: str | None = None
    total_transfusion_beds: int
    available_beds: int
    occupied_beds: int
    total_transfusion_chairs: int
    available_chairs: int
    occupied_chairs: int
    emergency_capacity: int
    emergency_capacity_available: int


