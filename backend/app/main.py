"""
VeinConnect AI — FastAPI Application Entry Point
=================================================
Configures the app, registers middleware, mounts routers,
and sets up lifespan (startup + shutdown) events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import VeinConnectException
from app.middleware.audit_logger import AuditLoggerMiddleware
from app.middleware.error_handler import (
    generic_exception_handler,
    validation_exception_handler,
    veinconnect_exception_handler,
)
from app.middleware.rate_limiter import RateLimiterMiddleware


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    print(f"[VeinConnect AI] Starting up [{settings.APP_ENV}]")
    
    # ── Automated Production DB Initialization ───────────────────────────────
    if not settings.is_production:
        from app.database import create_tables
        try:
            print("[VeinConnect AI] Initializing database tables...")
            await create_tables()
            print("[VeinConnect AI] Database tables initialized successfully!")
        except Exception as e:
            print(f"[VeinConnect AI] CRITICAL: Database initialization failed: {e}")
    # ─────────────────────────────────────────────────────────────────────────

    yield
    print("[VeinConnect AI] Shutting down")


# ── App Instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Recurring Transfusion Coordination Platform for Thalassemia Care",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom Middleware ─────────────────────────────────────────────────────────
# Note: Middleware is applied in REVERSE order of add_middleware calls
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(AuditLoggerMiddleware)

# ── Exception Handlers ───────────────────────────────────────────────────────
app.add_exception_handler(VeinConnectException, veinconnect_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routers ──────────────────────────────────────────────────────────────────
# Import here to avoid circular imports during startup
from app.api.v1.router import api_router  # noqa: E402

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

from fastapi.staticfiles import StaticFiles
import os
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Public health check endpoint. Used by load balancers and monitoring."""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
