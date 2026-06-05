import enum


class UserRole(str, enum.Enum):
    patient = "patient"
    donor = "donor"
    coordinator = "coordinator"
    hospital = "hospital"
    admin = "admin"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class BloodGroup(str, enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class ThalassemiaType(str, enum.Enum):
    major = "major"
    intermedia = "intermedia"
    minor = "minor"
    hb_e = "hb_e"
    hb_s = "hb_s"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UrgencyLevel(str, enum.Enum):
    routine = "routine"
    urgent = "urgent"
    emergency = "emergency"


class TransfusionStatus(str, enum.Enum):
    predicted = "predicted"
    patient_confirmed = "patient_confirmed"
    matching_donors = "matching_donors"
    donor_confirmed = "donor_confirmed"
    coordinator_confirmed = "coordinator_confirmed"
    hospital_confirmed = "hospital_confirmed"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class ConfirmationRole(str, enum.Enum):
    patient = "patient"
    donor = "donor"
    coordinator = "coordinator"
    hospital = "hospital"


class ConfirmationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    timeout = "timeout"
    overridden = "overridden"


class PatientConfirmation(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    modified = "modified"
    rejected = "rejected"


class DonorConfirmation(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    timeout = "timeout"


class CoordinatorConfirmation(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    overridden = "overridden"


class HospitalConfirmation(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    unavailable = "unavailable"


class DonationStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class CommunicationPreference(str, enum.Enum):
    whatsapp = "whatsapp"
    sms = "sms"


class Language(str, enum.Enum):
    en = "en"
    hi = "hi"


class NotificationType(str, enum.Enum):
    donation_request = "donation_request"
    reminder = "reminder"
    emergency_alert = "emergency_alert"
    confirmation_request = "confirmation_request"
    follow_up = "follow_up"
    system = "system"
    reward = "reward"
    expense = "expense"


class NotificationChannel(str, enum.Enum):
    app = "app"
    whatsapp = "whatsapp"
    sms = "sms"


class NotificationPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    emergency = "emergency"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"
    read = "read"


class RewardType(str, enum.Enum):
    donation = "donation"
    emergency_donation = "emergency_donation"
    consistency_bonus = "consistency_bonus"
    rare_blood_group = "rare_blood_group"
    referral = "referral"
    milestone = "milestone"


class TransactionType(str, enum.Enum):
    credit = "credit"
    debit = "debit"


class TransactionCategory(str, enum.Enum):
    reward_conversion = "reward_conversion"
    reimbursement = "reimbursement"
    expense_payment = "expense_payment"
    assistance = "assistance"
    withdrawal = "withdrawal"
    correction = "correction"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    reversed = "reversed"


class ExpenseStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    flagged = "flagged"
    rejected = "rejected"


class IncidentType(str, enum.Enum):
    matching_failure = "matching_failure"
    prediction_failure = "prediction_failure"
    notification_failure = "notification_failure"
    hospital_sync_failure = "hospital_sync_failure"
    wallet_failure = "wallet_failure"
    system_error = "system_error"
    security = "security"
    escalation = "escalation"


class IncidentSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    closed = "closed"
