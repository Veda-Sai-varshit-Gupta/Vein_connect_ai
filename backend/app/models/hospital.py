import uuid
from datetime import time

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin


class Hospital(Base, AuditMixin):
    __tablename__ = "hospitals"
    __table_args__ = (
        CheckConstraint(
            "total_transfusion_beds >= 0", name="ck_hospitals_beds_non_negative"
        ),
        CheckConstraint(
            "total_transfusion_chairs >= 0", name="ck_hospitals_chairs_non_negative"
        ),
        CheckConstraint(
            "emergency_capacity >= 0", name="ck_hospitals_emergency_non_negative"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_transfusion_beds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_transfusion_chairs: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    emergency_capacity: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    coordinator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coordinator_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coordinator_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    operating_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    operating_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── relationships ──
    user: Mapped["User"] = relationship(back_populates="hospital")  # noqa: F821
    capacity: Mapped["HospitalCapacity"] = relationship(  # noqa: F821
        back_populates="hospital", uselist=False, lazy="selectin"
    )
    transfusions: Mapped[list["Transfusion"]] = relationship(  # noqa: F821
        back_populates="hospital",
        foreign_keys="[Transfusion.hospital_id]",
        lazy="dynamic",
    )
    donations: Mapped[list["Donation"]] = relationship(  # noqa: F821
        back_populates="hospital", lazy="dynamic"
    )
    patient_preferences: Mapped[list["PatientHospitalPreference"]] = relationship(  # noqa: F821
        back_populates="hospital", lazy="dynamic"
    )
