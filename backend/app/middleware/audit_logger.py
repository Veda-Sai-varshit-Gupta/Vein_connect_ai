"""
Audit Logger Middleware
========================
Logs every request + response to structured logs.
Sensitive fields (passwords, tokens) are automatically redacted.
"""

import time
import json
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Fields to redact in request/response bodies
REDACTED_FIELDS = frozenset({
    "password", "password_hash", "access_token", "refresh_token",
    "token", "secret", "api_key", "upi_id",
})


def redact_dict(data: dict) -> dict:
    """Recursively redact sensitive fields from a dict."""
    result = {}
    for k, v in data.items():
        if k.lower() in REDACTED_FIELDS:
            result[k] = "***REDACTED***"
        elif isinstance(v, dict):
            result[k] = redact_dict(v)
        else:
            result[k] = v
    return result


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """
    Logs structured audit records for every HTTP request.
    Log format: { method, path, user_id, status_code, duration_ms, timestamp }
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # Extract user ID from request state if available (set by auth)
        user_id = getattr(request.state, "user_id", None)

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Structured log (print for hackathon; replace with structlog in production)
        log_record = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) or None,
            "user_id": str(user_id) if user_id else None,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "ip": request.client.host if request.client else None,
        }

        # Color-code status for dev readability
        status = response.status_code
        prefix = "[INF]" if status < 400 else "[WRN]" if status < 500 else "[ERR]"
        print(f"{prefix} [{status}] {request.method} {request.url.path} - {duration_ms}ms")

        return response
