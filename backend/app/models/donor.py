import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import BloodGroup, CommunicationPreference, Gender, Language


class Donor(Base, AuditMixin):
    __tablename__ = "donors"
    __table_args__ = (
        CheckConstraint("age IS NULL OR age >= 18", name="ck_donors_age_min_18"),
        CheckConstraint("max_travel_distance_km > 0", name="ck_donors_distance_positive"),
        CheckConstraint(
            "reliability_score >= 0 AND reliability_score <= 100",
            name="ck_donors_reliability_range",
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
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender | None] = mapped_column(
        SAEnum(Gender, name="gender", create_type=False), nullable=True
    )
    blood_group: Mapped[BloodGroup | None] = mapped_column(
        SAEnum(BloodGroup, name="bloodgroup", create_type=False), nullable=True
    )
    last_donation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_donations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preferred_days: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_times: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    max_travel_distance_km: Mapped[int] = mapped_column(
        Integer, default=25, nullable=False
    )
    communication_preference: Mapped[CommunicationPreference | None] = mapped_column(
        SAEnum(
            CommunicationPreference,
            name="communicationpreference",
            create_type=False,
        ),
        nullable=True,
    )
    language_preference: Mapped[Language | None] = mapped_column(
        SAEnum(Language, name="language", create_type=False), nullable=True
    )
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reliability_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("50.00"), nullable=False
    )
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    medical_clearance_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    medical_clearance_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    demanded_reimbursement: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # ── relationships ──
    user: Mapped["User"] = relationship(back_populates="donor")  # noqa: F821
    transfusions: Mapped[list["Transfusion"]] = relationship(  # noqa: F821
        back_populates="donor",
        foreign_keys="[Transfusion.donor_id]",
        lazy="dynamic",
    )
    donations: Mapped[list["Donation"]] = relationship(  # noqa: F821
        back_populates="donor", lazy="dynamic"
    )
    rewards: Mapped[list["Reward"]] = relationship(  # noqa: F821
        back_populates="donor", lazy="dynamic"
    )
    expense_requests: Mapped[list["ExpenseRequest"]] = relationship(  # noqa: F821
        back_populates="donor", lazy="dynamic"
    )
    friendship_scores: Mapped[list["FriendshipScore"]] = relationship(  # noqa: F821
        back_populates="donor", lazy="dynamic"
    )
