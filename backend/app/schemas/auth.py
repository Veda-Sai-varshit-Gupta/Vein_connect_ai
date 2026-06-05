"""
Authentication Schemas
========================
Request/response shapes for signup, login, token refresh.
"""

import re
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    phone: str
    password: str
    role: UserRole

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Accept Indian phone numbers: +91XXXXXXXXXX or 10 digits
        cleaned = re.sub(r"[\s\-()]", "", v)
        if not re.match(r"^(\+91)?[6-9]\d{9}$", cleaned):
            raise ValueError("Invalid phone number format. Use 10-digit Indian mobile number.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    phone: str
    role: UserRole
    is_active: bool
    is_verified: bool
    is_onboarded: bool
    created_at: datetime
