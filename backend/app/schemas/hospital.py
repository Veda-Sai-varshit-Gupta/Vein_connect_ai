"""
Hospital Schemas
=================
"""

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class HospitalCreate(BaseModel):
    name: str
    registration_number: str
    address: str
    city: str
    state: str
    total_transfusion_beds: int
    total_transfusion_chairs: int
    emergency_capacity: int
    coordinator_name: str
    coordinator_email: str
    coordinator_phone: str
    operating_hours_start: time | None = None
    operating_hours_end: time | None = None
    latitude: float | None = None
    longitude: float | None = None


class HospitalUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    coordinator_name: str | None = None
    coordinator_email: str | None = None
    coordinator_phone: str | None = None
    operating_hours_start: time | None = None
    operating_hours_end: time | None = None
    latitude: float | None = None
    longitude: float | None = None


class CapacityUpdate(BaseModel):
    available_beds: int
    occupied_beds: int
    available_chairs: int
    occupied_chairs: int
    staff_available: bool = True
    emergency_capacity_available: int = 0

    @model_validator(mode="after")
    def validate_capacity_bounds(self) -> "CapacityUpdate":
        total_beds = self.available_beds + self.occupied_beds
        total_chairs = self.available_chairs + self.occupied_chairs
        if total_beds > 0 and self.occupied_beds >= total_beds:
            raise ValueError("Occupied beds must be less than total beds")
        if total_chairs > 0 and self.occupied_chairs >= total_chairs:
            raise ValueError("Occupied chairs must be less than total chairs")
        return self


class HospitalBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    city: str
    is_active: bool


class HospitalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    name: str
    registration_number: str
    address: str
    city: str
    state: str
    total_transfusion_beds: int
    total_transfusion_chairs: int
    emergency_capacity: int
    coordinator_name: str
    coordinator_email: str
    coordinator_phone: str
    is_active: bool
    created_at: datetime


class CapacityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hospital_id: UUID
    available_beds: int
    occupied_beds: int
    available_chairs: int
    occupied_chairs: int
    staff_available: bool
    emergency_capacity_available: int
    last_updated_at: datetime | None


class HospitalWithDistanceResponse(BaseModel):
    hospital: HospitalBrief
    distance_km: float
    is_likely_available: bool
