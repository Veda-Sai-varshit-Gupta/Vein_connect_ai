import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import DonationStatus


class Donation(Base, AuditMixin):
    __tablename__ = "donations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transfusion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transfusions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    donation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[DonationStatus] = mapped_column(
        SAEnum(DonationStatus, name="donationstatus", create_type=False),
        default=DonationStatus.scheduled,
        nullable=False,
    )
    blood_units: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── relationships ──
    transfusion: Mapped["Transfusion"] = relationship(  # noqa: F821
        back_populates="donations"
    )
    donor: Mapped["Donor"] = relationship(  # noqa: F821
        back_populates="donations"
    )
    hospital: Mapped["Hospital"] = relationship(  # noqa: F821
        back_populates="donations"
    )
    rewards: Mapped[list["Reward"]] = relationship(  # noqa: F821
        back_populates="donation", lazy="selectin"
    )
