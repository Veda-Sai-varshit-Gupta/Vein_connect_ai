import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import ApprovalStatus


class Coordinator(Base, AuditMixin):
    __tablename__ = "coordinators"

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
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus, name="approvalstatus", create_type=False),
        default=ApprovalStatus.pending,
        nullable=False,
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── relationships ──
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="coordinator", foreign_keys=[user_id]
    )
    approver: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[approved_by], lazy="selectin"
    )
    transfusions: Mapped[list["Transfusion"]] = relationship(  # noqa: F821
        back_populates="coordinator", lazy="dynamic"
    )
