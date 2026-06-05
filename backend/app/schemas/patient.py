"""
Patient Schemas
================
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.enums import BloodGroup, Gender, ThalassemiaType


class HospitalPreferenceCreate(BaseModel):
    hospital_id: UUID
    preference_order: int  # 1, 2, or 3

    @field_validator("preference_order")
    @classmethod
    def validate_order(cls, v: int) -> int:
        if v not in (1, 2, 3):
            raise ValueError("preference_order must be 1, 2, or 3")
        return v


class HospitalPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    hospital_id: UUID
    preference_order: int
    preference_rank: int | None = None
    hospital_name: str | None = None
    city: str | None = None
    state: str | None = None
    opening_time: str | None = None
    closing_time: str | None = None
    contact_phone: str | None = None

    @model_validator(mode="before")
    @classmethod
    def flatten_hospital_fields(cls, data):
        if isinstance(data, dict):
            return data
        
        h = getattr(data, "hospital", None)
        res = {
            "id": getattr(data, "id", None),
            "hospital_id": getattr(data, "hospital_id", None),
            "preference_order": getattr(data, "preference_order", None),
            "preference_rank": getattr(data, "preference_order", None),
        }
        if h:
            res.update({
                "hospital_name": getattr(h, "name", None),
                "city": getattr(h, "city", None),
                "state": getattr(h, "state", None),
                "opening_time": str(getattr(h, "operating_hours_start")) if getattr(h, "operating_hours_start", None) else None,
                "closing_time": str(getattr(h, "operating_hours_end")) if getattr(h, "operating_hours_end", None) else None,
                "contact_phone": getattr(h, "coordinator_phone", None),
            })
        return res


class PatientCreate(BaseModel):
    name: str
    age: int
    gender: Gender
    address: str
    city: str
    state: str
    blood_group: BloodGroup
    thalassemia_type: ThalassemiaType
    last_transfusion_date: date | None = None
    avg_transfusion_interval_days: int = 21
    emergency_contact_name: str
    emergency_contact_phone: str
    data_sharing_consent: bool
    emergency_consent: bool
    hospital_preferences: list[HospitalPreferenceCreate] = []

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Age must be greater than 0")
        return v

    @field_validator("avg_transfusion_interval_days")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if not 7 <= v <= 90:
            raise ValueError("Transfusion interval must be between 7 and 90 days")
        return v


class PatientUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    last_transfusion_date: date | None = None
    avg_transfusion_interval_days: int | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    blood_group: BloodGroup
    city: str
    thalassemia_type: ThalassemiaType


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    name: str
    age: int
    gender: Gender
    address: str
    city: str
    state: str
    blood_group: BloodGroup
    thalassemia_type: ThalassemiaType
    last_transfusion_date: date | None
    avg_transfusion_interval_days: int
    emergency_contact_name: str
    emergency_contact_phone: str
    data_sharing_consent: bool
    emergency_consent: bool
    created_at: datetime
    updated_at: datetime


class PredictionResponse(BaseModel):
    patient_id: UUID
    predicted_date: date
    confidence_interval_days: int
    based_on_n_transfusions: int
    interval_trend: str
    average_interval_days: float
    alert: str | None = None
