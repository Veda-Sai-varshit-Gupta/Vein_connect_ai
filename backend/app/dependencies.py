"""
FastAPI Dependency Injection
=============================
All shared dependencies (db session, current user, pagination) live here.
Use these with FastAPI's Depends() system.
"""

from uuid import UUID
from typing import Annotated

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

# ── Database ─────────────────────────────────────────────────────────────────
DbSession = Annotated[AsyncSession, Depends(get_db)]

# ── Auth Bearer ──────────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)


async def get_current_user(
    db: DbSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """
    Extract and validate JWT Bearer token from Authorization header.
    Returns the authenticated User ORM object.
    Raises 401 if token is missing or invalid.
    """
    if not credentials:
        raise UnauthorizedException("Authorization header missing")

    payload = decode_access_token(credentials.credentials)

    # Import here to avoid circular imports
    from app.repositories.user_repo import UserRepository
    user_repo = UserRepository()
    user = await user_repo.get_by_id(db, UUID(payload.sub))

    if not user:
        raise UnauthorizedException("User account not found")
    if not user.is_active:
        raise UnauthorizedException("User account is deactivated")

    return user


# ── Typed dependency aliases ─────────────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]


# ── Pagination ───────────────────────────────────────────────────────────────
class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


Pagination = Annotated[PaginationParams, Depends(PaginationParams)]
