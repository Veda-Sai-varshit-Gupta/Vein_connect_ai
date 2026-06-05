import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin


class FriendshipScore(Base, AuditMixin):
    __tablename__ = "friendship_scores"
    __table_args__ = (
        UniqueConstraint("patient_id", "donor_id", name="uq_friendship_patient_donor"),
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_friendship_score_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), nullable=False
    )
    total_donations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationship_duration_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    positive_interactions: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    negative_interactions: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── relationships ──
    patient: Mapped["Patient"] = relationship(  # noqa: F821
        back_populates="friendship_scores"
    )
    donor: Mapped["Donor"] = relationship(  # noqa: F821
        back_populates="friendship_scores"
    )
