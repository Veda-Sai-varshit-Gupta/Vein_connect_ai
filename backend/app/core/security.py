"""
Security Module
================
JWT token creation/decoding and password hashing.
All auth primitives live here — import from here, not from jose directly.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings
from app.core.exceptions import InvalidTokenException
from app.models.enums import UserRole

# ── Password Hashing ─────────────────────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    pwd_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# ── Token Payload ────────────────────────────────────────────────────────────
class TokenPayload(BaseModel):
    sub: str          # user_id as string
    role: UserRole
    type: str         # "access" | "refresh"
    exp: datetime
    iat: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    expires_in: int   # seconds until access token expiry


# ── Token Creation ───────────────────────────────────────────────────────────
def create_access_token(user_id: UUID, role: UserRole) -> str:
    """
    Create a signed JWT access token.
    Payload: { sub, role, type, iat, exp }
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a signed JWT refresh token.
    Payload: { sub, type, iat, exp }  — no role, used only for re-issuance.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Token Decoding ───────────────────────────────────────────────────────────
def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate an access token.
    Raises InvalidTokenException on any failure.
    """
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if raw.get("type") != "access":
            raise InvalidTokenException("Not an access token")
        return TokenPayload(
            sub=raw["sub"],
            role=UserRole(raw["role"]),
            type=raw["type"],
            exp=datetime.fromtimestamp(raw["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(raw["iat"], tz=timezone.utc),
        )
    except JWTError as e:
        raise InvalidTokenException(f"Token decode failed: {e}")


def decode_refresh_token(token: str) -> str:
    """
    Decode and validate a refresh token.
    Returns the user_id string on success.
    Raises InvalidTokenException on failure.
    """
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if raw.get("type") != "refresh":
            raise InvalidTokenException("Not a refresh token")
        return raw["sub"]
    except JWTError as e:
        raise InvalidTokenException(f"Refresh token decode failed: {e}")


def create_token_pair(user_id: UUID, role: UserRole) -> TokenResponse:
    """Convenience: create both access + refresh tokens and return TokenResponse."""
    access_token = create_access_token(user_id, role)
    refresh_token = create_refresh_token(user_id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=role,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
