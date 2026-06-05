"""
Authentication Routes
======================
POST /auth/signup
POST /auth/login
POST /auth/refresh
GET  /auth/me
POST /auth/logout  (client-side token discard)
"""

from fastapi import APIRouter
from app.dependencies import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, SignupRequest, RefreshRequest, TokenResponse, UserResponse
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(data: SignupRequest, db: DbSession):
    """Register a new user account and return JWT tokens."""
    return await auth_service.signup(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DbSession):
    """Authenticate with email/password. Returns JWT token pair."""
    return await auth_service.login(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DbSession):
    """Exchange a refresh token for a new access token."""
    return await auth_service.refresh(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser, db: DbSession):
    """Get the currently authenticated user's profile."""
    return await auth_service.get_me(db, current_user.id)


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: CurrentUser):
    """Logout (client should discard tokens; no server-side session)."""
    return MessageResponse(message="Logged out successfully", detail="Discard your access and refresh tokens.")
