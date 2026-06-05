import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base
from .enums import ConfirmationRole, ConfirmationStatus


class CompletionConfirmation(Base):
    __tablename__ = "completion_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transfusion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transfusions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ConfirmationRole] = mapped_column(
        SAEnum(ConfirmationRole, name="confirmationrole", create_type=False),
        nullable=False,
    )
    status: Mapped[ConfirmationStatus] = mapped_column(
        SAEnum(ConfirmationStatus, name="confirmationstatus", create_type=False),
        default=ConfirmationStatus.pending,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(
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
    transfusion: Mapped["Transfusion"] = relationship(  # noqa: F821
        back_populates="completion_confirmations"
    )
    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
