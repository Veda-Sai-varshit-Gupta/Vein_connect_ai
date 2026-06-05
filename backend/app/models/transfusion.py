import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base import Base, AuditMixin
from .enums import (
    CoordinatorConfirmation,
    DonorConfirmation,
    HospitalConfirmation,
    PatientConfirmation,
    TransfusionStatus,
    UrgencyLevel,
)


class Transfusion(Base, AuditMixin):
    __tablename__ = "transfusions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    donor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True,
    )
    hospital_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
    )
    coordinator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("coordinators.id", ondelete="SET NULL"),
        nullable=True,
    )
    predicted_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    urgency_level: Mapped[UrgencyLevel] = mapped_column(
        SAEnum(UrgencyLevel, name="urgencylevel", create_type=False),
        default=UrgencyLevel.routine,
        nullable=False,
    )
    status: Mapped[TransfusionStatus] = mapped_column(
        SAEnum(TransfusionStatus, name="transfusionstatus", create_type=False),
        default=TransfusionStatus.predicted,
        nullable=False,
        index=True,
    )
    patient_confirmation: Mapped[PatientConfirmation] = mapped_column(
        SAEnum(PatientConfirmation, name="patientconfirmation", create_type=False),
        default=PatientConfirmation.pending,
        nullable=False,
    )
    donor_confirmation: Mapped[DonorConfirmation] = mapped_column(
        SAEnum(DonorConfirmation, name="donorconfirmation", create_type=False),
        default=DonorConfirmation.pending,
        nullable=False,
    )
    coordinator_confirmation: Mapped[CoordinatorConfirmation] = mapped_column(
        SAEnum(
            CoordinatorConfirmation,
            name="coordinatorconfirmation",
            create_type=False,
        ),
        default=CoordinatorConfirmation.pending,
        nullable=False,
    )
    hospital_confirmation: Mapped[HospitalConfirmation] = mapped_column(
        SAEnum(
            HospitalConfirmation,
            name="hospitalconfirmation",
            create_type=False,
        ),
        default=HospitalConfirmation.pending,
        nullable=False,
    )
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emergency_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alternate_hospital_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_donor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── relationships ──
    patient: Mapped["Patient"] = relationship(  # noqa: F821
        back_populates="transfusions"
    )
    donor: Mapped["Donor | None"] = relationship(  # noqa: F821
        back_populates="transfusions", foreign_keys=[donor_id]
    )
    hospital: Mapped["Hospital | None"] = relationship(  # noqa: F821
        back_populates="transfusions", foreign_keys=[hospital_id]
    )
    coordinator: Mapped["Coordinator | None"] = relationship(  # noqa: F821
        back_populates="transfusions"
    )
    alternate_hospital: Mapped["Hospital | None"] = relationship(  # noqa: F821
        foreign_keys=[alternate_hospital_id], lazy="selectin"
    )
    previous_donor: Mapped["Donor | None"] = relationship(  # noqa: F821
        foreign_keys=[previous_donor_id], lazy="selectin"
    )
    confirmations: Mapped[list["Confirmation"]] = relationship(  # noqa: F821
        back_populates="transfusion", lazy="dynamic"
    )
    completion_confirmations: Mapped[list["CompletionConfirmation"]] = relationship(  # noqa: F821
        back_populates="transfusion", lazy="dynamic"
    )
    donations: Mapped[list["Donation"]] = relationship(  # noqa: F821
        back_populates="transfusion", lazy="dynamic"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        back_populates="transfusion", lazy="dynamic"
    )
    expense_requests: Mapped[list["ExpenseRequest"]] = relationship(  # noqa: F821
        back_populates="transfusion", lazy="dynamic"
    )
