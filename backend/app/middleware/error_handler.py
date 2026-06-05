"""
Global Error Handler Middleware
================================
Catches all exceptions and returns a consistent JSON error structure.
This prevents stack traces from leaking to the client in production.
"""

import traceback
from datetime import datetime, timezone

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.exceptions import VeinConnectException


def error_response(status_code: int, detail: str, error_code: str = "ERROR") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": detail,
            "status_code": status_code,
            "error_code": error_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def veinconnect_exception_handler(request: Request, exc: VeinConnectException):
    """Handle all custom VeinConnect exceptions."""
    return error_response(
        status_code=exc.status_code,
        detail=exc.detail,
        error_code=getattr(exc, "error_code", "ERROR"),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors from request bodies."""
    errors = exc.errors()
    # Format validation errors cleanly
    messages = []
    for err in errors:
        field = " → ".join(str(loc) for loc in err["loc"][1:])  # Skip 'body'
        messages.append(f"{field}: {err['msg']}")
    detail = "; ".join(messages) if messages else "Validation failed"
    print(f"[VALIDATION ERROR] Request body validation failed: {detail}")
    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail,
        error_code="VALIDATION_ERROR",
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected exceptions."""
    if settings.DEBUG:
        detail = f"{type(exc).__name__}: {str(exc)}"
    else:
        detail = "An unexpected error occurred. Please try again."

    # Always log the full traceback server-side
    traceback.print_exc()

    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
        error_code="INTERNAL_SERVER_ERROR",
    )
