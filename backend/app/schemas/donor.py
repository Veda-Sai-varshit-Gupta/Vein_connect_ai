"""
Donor Schemas
==============
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import BloodGroup, CommunicationPreference, Gender, Language


class DonorCreate(BaseModel):
    name: str
    age: int
    gender: Gender
    blood_group: BloodGroup
    last_donation_date: date | None = None
    preferred_days: list[str] = []
    preferred_times: list[str] = []
    max_travel_distance_km: int = 25
    communication_preference: CommunicationPreference = CommunicationPreference.whatsapp
    language_preference: Language = Language.en
    upi_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    medical_clearance_url: str | None = None
    medical_clearance_at: datetime | None = None
    demanded_reimbursement: float = 0.0

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 18:
            raise ValueError("Donor must be at least 18 years old")
        return v

    @field_validator("max_travel_distance_km")
    @classmethod
    def validate_distance(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Max travel distance must be greater than 0")
        return v


class DonorUpdate(BaseModel):
    name: str | None = None
    preferred_days: list[str] | None = None
    preferred_times: list[str] | None = None
    max_travel_distance_km: int | None = None
    communication_preference: CommunicationPreference | None = None
    language_preference: Language | None = None
    upi_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    medical_clearance_url: str | None = None
    medical_clearance_at: datetime | None = None
    demanded_reimbursement: float | None = None


class AvailabilityUpdate(BaseModel):
    is_available: bool


class DonorBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    blood_group: BloodGroup
    reliability_score: float
    is_available: bool
    demanded_reimbursement: float


class DonorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    name: str
    age: int
    gender: Gender
    blood_group: BloodGroup
    last_donation_date: date | None
    total_donations: int
    preferred_days: list | None
    preferred_times: list | None
    max_travel_distance_km: int
    communication_preference: CommunicationPreference
    language_preference: Language
    reliability_score: float
    is_available: bool
    medical_clearance_url: str | None
    medical_clearance_at: datetime | None
    demanded_reimbursement: float
    created_at: datetime


class DonorMatchResult(BaseModel):
    donor_id: UUID
    donor_name: str
    blood_group: BloodGroup
    match_score: float
    blood_group_match: bool
    distance_km: float
    reliability_score: float
    response_likelihood: float
    friendship_score: float
    days_since_last_donation: int
    is_eligible: bool
    rank: int
    reason: str
    demanded_reimbursement: float = 0.0
    medical_clearance_at: datetime | None = None


class DonorScoresResponse(BaseModel):
    donor_id: UUID
    reliability_score: float
    reliability_trend: str
    total_friendship_pairs: int
