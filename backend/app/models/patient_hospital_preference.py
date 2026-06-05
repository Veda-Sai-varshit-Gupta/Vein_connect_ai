import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin


class PatientHospitalPreference(Base, AuditMixin):
    __tablename__ = "patient_hospital_preferences"
    __table_args__ = (
        UniqueConstraint("patient_id", "preference_order", name="uq_patient_pref_order"),
        UniqueConstraint("patient_id", "hospital_id", name="uq_patient_hospital"),
        CheckConstraint(
            "preference_order >= 1 AND preference_order <= 3",
            name="ck_pref_order_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    preference_order: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── relationships ──
    patient: Mapped["Patient"] = relationship(  # noqa: F821
        back_populates="hospital_preferences"
    )
    hospital: Mapped["Hospital"] = relationship(  # noqa: F821
        back_populates="patient_preferences"
    )
