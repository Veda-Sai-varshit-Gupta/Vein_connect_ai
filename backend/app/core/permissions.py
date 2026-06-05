"""
Role-Based Access Control
==========================
Simple, explicit permission checks.
No magic decorators — every route explicitly declares required roles.
"""

from uuid import UUID
from fastapi import Depends

from app.core.exceptions import ForbiddenException
from app.models.enums import UserRole
from app.models.user import User


def require_role(user: User, allowed_roles: list[UserRole]) -> None:
    """
    Raise ForbiddenException if user's role is not in allowed_roles.
    Call this at the start of any route handler that needs role restriction.
    """
    if user.role not in allowed_roles:
        raise ForbiddenException(
            detail=f"Role '{user.role.value}' is not authorized for this resource. "
                   f"Required: {[r.value for r in allowed_roles]}"
        )


def require_self_or_role(
    user: User,
    resource_user_id: UUID,
    allowed_roles: list[UserRole],
) -> None:
    """
    Allow access if:
    - user is accessing their own data (user.id == resource_user_id), OR
    - user has one of the allowed_roles (admin, coordinator, etc.)
    """
    if user.id == resource_user_id:
        return  # Owner access
    require_role(user, allowed_roles)


def is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN


def is_coordinator(user: User) -> bool:
    return user.role == UserRole.COORDINATOR


def is_patient(user: User) -> bool:
    return user.role == UserRole.PATIENT


def is_donor(user: User) -> bool:
    return user.role == UserRole.DONOR


def is_hospital(user: User) -> bool:
    return user.role == UserRole.HOSPITAL
