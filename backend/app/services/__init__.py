"""
Services package for VeinConnect AI.

Exports all service classes for use in API routers.
"""

from app.services.auth_service import AuthService
from app.services.patient_service import PatientService
from app.services.donor_service import DonorService
from app.services.hospital_service import HospitalService
from app.services.coordinator_service import CoordinatorService
from app.services.transfusion_service import TransfusionService
from app.services.scheduling_service import SchedulingService
from app.services.confirmation_service import ConfirmationService
from app.services.notification_service import NotificationService
from app.services.reward_service import RewardService
from app.services.wallet_service import WalletService
from app.services.emergency_service import EmergencyService
from app.services.expense_service import ExpenseService
from app.services.incident_service import IncidentService

__all__ = [
    "AuthService",
    "PatientService",
    "DonorService",
    "HospitalService",
    "CoordinatorService",
    "TransfusionService",
    "SchedulingService",
    "ConfirmationService",
    "NotificationService",
    "RewardService",
    "WalletService",
    "EmergencyService",
    "ExpenseService",
    "IncidentService",
]
