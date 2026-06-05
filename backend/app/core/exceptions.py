"""
Custom Exception Hierarchy
===========================
All exceptions produce a consistent JSON error body:
  { detail, status_code, error_code, timestamp }
"""

from datetime import datetime, timezone
from fastapi import HTTPException, status


class VeinConnectException(HTTPException):
    """Base exception. All custom exceptions inherit from this."""

    error_code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str, status_code: int = 500, error_code: str | None = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code or self.__class__.error_code
        self.timestamp = datetime.now(timezone.utc).isoformat()


# ── 400 Bad Request ──────────────────────────────────────────────────────────
class BadRequestException(VeinConnectException):
    error_code = "BAD_REQUEST"

    def __init__(self, detail: str = "Bad request", error_code: str | None = None):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST, error_code)


# ── 401 Unauthorized ─────────────────────────────────────────────────────────
class UnauthorizedException(VeinConnectException):
    error_code = "UNAUTHORIZED"

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED")


# ── 403 Forbidden ────────────────────────────────────────────────────────────
class ForbiddenException(VeinConnectException):
    error_code = "FORBIDDEN"

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


# ── 404 Not Found ────────────────────────────────────────────────────────────
class NotFoundException(VeinConnectException):
    error_code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        detail = f"{resource} not found" if not resource_id else f"{resource} '{resource_id}' not found"
        super().__init__(detail, status.HTTP_404_NOT_FOUND, "NOT_FOUND")


# ── 409 Conflict ─────────────────────────────────────────────────────────────
class ConflictException(VeinConnectException):
    error_code = "CONFLICT"

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail, status.HTTP_409_CONFLICT, "CONFLICT")


# ── 422 Validation Error ─────────────────────────────────────────────────────
class ValidationException(VeinConnectException):
    error_code = "VALIDATION_ERROR"

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")


# ── 429 Rate Limit ───────────────────────────────────────────────────────────
class RateLimitException(VeinConnectException):
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, detail: str = "Too many requests. Please wait before retrying."):
        super().__init__(detail, status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED")


# ── 503 Service Unavailable ──────────────────────────────────────────────────
class ServiceUnavailableException(VeinConnectException):
    error_code = "SERVICE_UNAVAILABLE"

    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(detail, status.HTTP_503_SERVICE_UNAVAILABLE, "SERVICE_UNAVAILABLE")


# ── Domain-specific ──────────────────────────────────────────────────────────
class IneligibleDonorException(BadRequestException):
    """Raised when a donor attempts to donate within the 90-day cooldown."""
    def __init__(self, days_remaining: int):
        super().__init__(
            f"Donor is not eligible. {days_remaining} days remaining in cooldown period.",
            error_code="DONOR_INELIGIBLE",
        )


class IncompatibleBloodGroupException(BadRequestException):
    def __init__(self, donor_group: str, patient_group: str):
        super().__init__(
            f"Blood group {donor_group} is incompatible with patient's {patient_group}.",
            error_code="BLOOD_GROUP_INCOMPATIBLE",
        )


class TransfusionStateException(BadRequestException):
    def __init__(self, current_status: str, attempted_action: str):
        super().__init__(
            f"Cannot perform '{attempted_action}' on transfusion with status '{current_status}'.",
            error_code="INVALID_TRANSFUSION_STATE",
        )


class InvalidTokenException(UnauthorizedException):
    def __init__(self, detail: str = "Token is invalid or has expired"):
        super().__init__(detail)
        self.error_code = "INVALID_TOKEN"
