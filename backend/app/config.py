"""
Application Configuration
==========================
Pydantic Settings reads from environment variables and .env file.
All settings are type-safe and validated at startup.
"""

from functools import lru_cache
from typing import Any
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────────────────────
    APP_NAME: str = "VeinConnect AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-secret-key-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://veinconnect:password@localhost:5432/veinconnect_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False  # Set True to log SQL in dev

    # ── CORS ────────────────────────────────────────────────────────────────
    CORS_ORIGINS: Any = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        return v

    # ── Rate Limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_AUTHENTICATED: int = 300

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str | None = None

    # ── External APIs ────────────────────────────────────────────────────────
    WHATSAPP_API_URL: str | None = None
    WHATSAPP_API_TOKEN: str | None = None
    SMS_API_URL: str | None = None
    SMS_API_KEY: str | None = None

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — import this everywhere."""
    return Settings()


# Convenience alias
settings = get_settings()
