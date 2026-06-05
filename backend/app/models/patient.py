import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import BloodGroup, Gender, ThalassemiaType


class Patient(Base, AuditMixin):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint("age > 0", name="ck_patients_age_positive"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[Gender] = mapped_column(
        SAEnum(Gender, name="gender", create_type=False), nullable=False
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blood_group: Mapped[BloodGroup] = mapped_column(
        SAEnum(BloodGroup, name="bloodgroup", create_type=False), nullable=False
    )
    thalassemia_type: Mapped[ThalassemiaType] = mapped_column(
        SAEnum(ThalassemiaType, name="thalassemiatype", create_type=False),
        nullable=False,
    )
    last_transfusion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    avg_transfusion_interval_days: Mapped[int] = mapped_column(
        Integer, default=21, nullable=False
    )
    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    emergency_contact_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    data_sharing_consent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    emergency_consent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── relationships ──
    user: Mapped["User"] = relationship(back_populates="patient")  # noqa: F821
    transfusions: Mapped[list["Transfusion"]] = relationship(  # noqa: F821
        back_populates="patient", lazy="dynamic"
    )
    hospital_preferences: Mapped[list["PatientHospitalPreference"]] = relationship(  # noqa: F821
        back_populates="patient", lazy="selectin"
    )
    friendship_scores: Mapped[list["FriendshipScore"]] = relationship(  # noqa: F821
        back_populates="patient", lazy="dynamic"
    )
