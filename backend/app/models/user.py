import uuid
from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import UserRole


class User(Base, AuditMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole", create_type=False),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @property
    def is_onboarded(self) -> bool:
        if self.role == UserRole.patient:
            return self.patient is not None
        elif self.role == UserRole.donor:
            return self.donor is not None
        elif self.role == UserRole.coordinator:
            return self.coordinator is not None
        elif self.role == UserRole.hospital:
            return self.hospital is not None
        return True

    # ── one-to-one relationships ──
    patient: Mapped["Patient"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, lazy="selectin"
    )
    donor: Mapped["Donor"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, lazy="selectin"
    )
    coordinator: Mapped["Coordinator"] = relationship(  # noqa: F821
        back_populates="user",
        uselist=False,
        lazy="selectin",
        foreign_keys="[Coordinator.user_id]",
    )
    hospital: Mapped["Hospital"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, lazy="selectin"
    )
    wallet: Mapped["Wallet"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, lazy="selectin"
    )

    # ── one-to-many relationships ──
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        back_populates="user", lazy="dynamic"
    )
