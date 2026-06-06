"""
Authentication Service
=======================
Handles signup, login, logout, and token refresh.
Single responsibility: user identity lifecycle.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_token_pair,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.enums import UserRole
from app.repositories.user_repo import UserRepository
from app.repositories.wallet_repo import WalletRepository

# ── IMPORT PROFILE REPOSITORIES ──────────────────────────────────────────────
from app.repositories.patient_repo import PatientRepository
from app.repositories.donor_repo import DonorRepository
from app.repositories.coordinator_repo import CoordinatorRepository
from app.repositories.hospital_repo import HospitalRepository
# ─────────────────────────────────────────────────────────────────────────────

from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse

user_repo = UserRepository()
wallet_repo = WalletRepository()

# ── INITIALIZE REPOSITORIES ──────────────────────────────────────────────────
patient_repo = PatientRepository()
donor_repo = DonorRepository()
coordinator_repo = CoordinatorRepository()
hospital_repo = HospitalRepository()
# ─────────────────────────────────────────────────────────────────────────────


class AuthService:

    async def signup(self, db: AsyncSession, data: SignupRequest) -> TokenResponse:
        """Register a new user. Creates user + wallet + role profile. Returns token pair."""
        # Check email uniqueness
        if await user_repo.get_by_email(db, data.email):
            raise ConflictException(f"An account with email '{data.email}' already exists")

        # Check phone uniqueness
        if await user_repo.get_by_phone(db, data.phone):
            raise ConflictException(f"An account with phone '{data.phone}' already exists")

        # Create user
        user = await user_repo.create(db, {
            "email": data.email,
            "phone": data.phone,
            "password_hash": hash_password(data.password),
            "role": data.role,
            "is_active": True,
            "is_verified": False,
        })

        # Create wallet for all users (patients get assistance credits, donors get reimbursements)
        await wallet_repo.create_wallet(db, user.id)

        # ── AUTOMATIC PROFILE CREATION BASED ON ROLE ─────────────────────────
        profile_data = {
            "user_id": user.id,
            "name": data.email.split("@")[0].capitalize(), # Fallback initial string name
        }

        if data.role == "patient" or data.role == UserRole.patient:
            await patient_repo.create(db, profile_data)
        elif data.role == "donor" or data.role == UserRole.donor:
            await donor_repo.create(db, profile_data)
        elif data.role == "coordinator" or data.role == UserRole.coordinator:
            await coordinator_repo.create(db, {**profile_data, "phone": data.phone})
        elif data.role == "hospital" or data.role == UserRole.hospital:
            await hospital_repo.create(db, profile_data)
        # ─────────────────────────────────────────────────────────────────────

        return create_token_pair(user.id, user.role)

    async def login(self, db: AsyncSession, data: LoginRequest) -> TokenResponse:
        """Authenticate a user. Returns token pair on success."""
        user = await user_repo.get_by_email(db, data.email)

        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Your account has been deactivated. Contact support.")

        await user_repo.update_last_login(db, user.id)
        return create_token_pair(user.id, user.role)

    async def refresh(self, db: AsyncSession, refresh_token: str) -> TokenResponse:
        """Issue a new access token using a valid refresh token."""
        user_id_str = decode_refresh_token(refresh_token)
        user = await user_repo.get_by_id(db, UUID(user_id_str))

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or account deactivated")

        return create_token_pair(user.id, user.role)

    async def get_me(self, db: AsyncSession, user_id: UUID):
        """Fetch the current authenticated user's profile."""
        return await user_repo.get_by_id(db, user_id)
