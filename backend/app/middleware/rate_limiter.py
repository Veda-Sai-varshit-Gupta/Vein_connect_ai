"""
Simple In-Memory Rate Limiter
==============================
Sliding window rate limiter using in-process dict.
For production: swap to Redis-based implementation.

Limits:
  - Public endpoints:       100 req/min per IP
  - Authenticated endpoints: 300 req/min per user_id
  - Emergency endpoints:     Exempt from rate limiting
"""

import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.core.exceptions import RateLimitException

# Routes exempt from rate limiting
EXEMPT_PATHS = frozenset({
    "/api/v1/emergency/create",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
})


class SlidingWindowCounter:
    """Thread-unsafe (single process) sliding window counter."""

    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self._requests: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str, limit: int) -> bool:
        now = time.time()
        window_start = now - self.window
        timestamps = self._requests[key]

        # Remove expired timestamps
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return False

        timestamps.append(now)
        return True


_counter = SlidingWindowCounter(window_seconds=60)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip exempt paths
        if path in EXEMPT_PATHS or path.startswith("/docs"):
            return await call_next(request)

        # Bypass rate limiting in development mode
        if settings.APP_ENV == "development":
            return await call_next(request)

        # Determine key and limit
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"user:{user_id}"
            limit = settings.RATE_LIMIT_AUTHENTICATED
        else:
            ip = request.client.host if request.client else "unknown"
            key = f"ip:{ip}"
            limit = settings.RATE_LIMIT_PER_MINUTE

        if not _counter.is_allowed(key, limit):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait before retrying."}
            )

        return await call_next(request)
