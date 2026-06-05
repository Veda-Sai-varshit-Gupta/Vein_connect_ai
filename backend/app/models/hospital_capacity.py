import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class HospitalCapacity(Base):
    __tablename__ = "hospital_capacities"
    __table_args__ = (
        CheckConstraint(
            "available_beds >= 0", name="ck_hospital_cap_avail_beds_non_neg"
        ),
        CheckConstraint(
            "occupied_beds >= 0", name="ck_hospital_cap_occ_beds_non_neg"
        ),
        CheckConstraint(
            "available_chairs >= 0", name="ck_hospital_cap_avail_chairs_non_neg"
        ),
        CheckConstraint(
            "occupied_chairs >= 0", name="ck_hospital_cap_occ_chairs_non_neg"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    available_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_chairs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occupied_chairs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    staff_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upcoming_appointments: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    emergency_capacity_available: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    last_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── relationships ──
    hospital: Mapped["Hospital"] = relationship(  # noqa: F821
        back_populates="capacity"
    )
