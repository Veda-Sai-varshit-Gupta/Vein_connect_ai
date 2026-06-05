import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import ExpenseStatus


class ExpenseRequest(Base, AuditMixin):
    __tablename__ = "expense_requests"
    __table_args__ = (
        CheckConstraint(
            "travel_expense >= 0", name="ck_expense_travel_non_negative"
        ),
        CheckConstraint(
            "other_expense >= 0", name="ck_expense_other_non_negative"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donation_id: Mapped[uuid.UUID] = mapped_column(
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
    travel_expense: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    other_expense: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        SAEnum(ExpenseStatus, name="expensestatus", create_type=False),
        default=ExpenseStatus.pending,
        nullable=False,
    )
    is_flagged_by_ai: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    flag_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── relationships ──
    transfusion: Mapped["Transfusion"] = relationship(  # noqa: F821
        back_populates="expense_requests",
        foreign_keys=[donation_id],
    )
    donor: Mapped["Donor"] = relationship(  # noqa: F821
        back_populates="expense_requests"
    )
    reviewer: Mapped["User | None"] = relationship(lazy="selectin")  # noqa: F821
