"""
Communication Personalization Engine
=====================================
Selects the optimal channel, language, tone, message template, and
send time for each notification to maximize donor response rates.

v1: Rule-based template selection.
v2 upgrade: sklearn classifier on channel open/response outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Optimal send windows (hour ranges in IST)
OPTIMAL_WINDOWS: list[tuple[int, int]] = [(9, 12), (17, 20)]


TEMPLATES: dict[str, dict[str, str]] = {
    "donation_request": {
        "en": (
            "Hello {name}, {patient_name} needs your help on {date}. "
            "Blood group: {blood_group}. Can you donate? Reply YES or NO."
        ),
        "hi": (
            "नमस्ते {name}, {patient_name} को {date} पर आपकी मदद चाहिए। "
            "रक्त समूह: {blood_group}। क्या आप दान कर सकते हैं? YES या NO जवाब दें।"
        ),
    },
    "reminder": {
        "en": "Reminder: Your donation for {patient_name} is scheduled on {date}. Please confirm.",
        "hi": "अनुस्मारक: {patient_name} के लिए आपका दान {date} को है। कृपया पुष्टि करें।",
    },
    "urgent_reminder": {
        "en": "⚠️ URGENT: {patient_name} urgently needs your blood donation on {date}. Please respond now.",
        "hi": "⚠️ जरूरी: {patient_name} को {date} पर आपके रक्तदान की तत्काल जरूरत है। अभी जवाब दें।",
    },
    "emergency_alert": {
        "en": "🚨 EMERGENCY: {patient_name} needs {blood_group} blood IMMEDIATELY. Please call {coordinator_phone} NOW.",
        "hi": "🚨 आपातकाल: {patient_name} को अभी {blood_group} रक्त चाहिए। तुरंत {coordinator_phone} पर कॉल करें।",
    },
    "confirmation_received": {
        "en": "Thank you {name}! Your donation for {patient_name} on {date} is confirmed. We'll send details soon.",
        "hi": "धन्यवाद {name}! {patient_name} के लिए {date} का आपका दान पक्का हो गया।",
    },
    "follow_up": {
        "en": "Thank you for donating, {name}! You've made a real difference. Check your rewards in the app.",
        "hi": "धन्यवाद {name}! आपने वास्तव में फर्क किया। ऐप में अपने पुरस्कार देखें।",
    },
    "reward": {
        "en": "🎉 You earned {points} points for your donation! Total: {total_points}. Keep it up!",
        "hi": "🎉 आपके दान के लिए {points} अंक मिले! कुल: {total_points}। ऐसे ही जारी रखें!",
    },
    "expense_approved": {
        "en": "Your expense of ₹{amount} has been approved and will be credited to your wallet.",
        "hi": "आपका ₹{amount} का खर्च मंजूर हो गया और जल्द वॉलेट में आएगा।",
    },
}

TITLES: dict[str, dict[str, str]] = {
    "donation_request":      {"en": "Blood Donation Request", "hi": "रक्तदान अनुरोध"},
    "reminder":              {"en": "Donation Reminder", "hi": "दान अनुस्मारक"},
    "urgent_reminder":       {"en": "Urgent Reminder", "hi": "जरूरी अनुस्मारक"},
    "emergency_alert":       {"en": "🚨 Emergency Alert", "hi": "🚨 आपातकालीन अलर्ट"},
    "confirmation_received": {"en": "Donation Confirmed", "hi": "दान पक्का"},
    "follow_up":             {"en": "Thank You!", "hi": "धन्यवाद!"},
    "reward":                {"en": "Reward Earned!", "hi": "पुरस्कार मिला!"},
    "expense_approved":      {"en": "Expense Approved", "hi": "खर्च मंजूर"},
}


@dataclass
class PersonalizedMessage:
    channel: str            # "whatsapp" | "sms" | "app"
    language: str           # "en" | "hi"
    title: str
    message: str
    send_at: datetime
    template_key: str
    variables: dict = field(default_factory=dict)
    priority: str = "normal"   # "low" | "normal" | "high" | "emergency"


class CommunicationPersonalizationEngine:
    """Composes personalized notifications optimized for each donor."""

    def compose(
        self,
        donor,
        patient,
        notification_type: str,
        transfusion=None,
        reminder_count: int = 0,
        friendship_score: float = 0.0,
        coordinator_phone: str = "",
        extra_vars: dict | None = None,
    ) -> PersonalizedMessage:
        lang = getattr(getattr(donor, 'language_preference', None), 'value', 'en') or 'en'
        urgency = "routine"
        is_emergency = False
        pred_date = None

        if transfusion:
            urgency = (
                getattr(getattr(transfusion, 'urgency_level', None), 'value', 'routine') or 'routine'
            )
            is_emergency = getattr(transfusion, 'is_emergency', False)
            pred_date = getattr(transfusion, 'predicted_date', None)

        # Resolve template key
        template_key = self._resolve_template_key(
            notification_type, urgency, is_emergency, reminder_count
        )

        # Build variables
        blood_group = (
            patient.blood_group.value
            if hasattr(patient.blood_group, 'value')
            else str(patient.blood_group)
        )
        variables: dict = {
            "name": getattr(donor, 'name', 'Donor'),
            "patient_name": getattr(patient, 'name', 'Patient'),
            "blood_group": blood_group,
            "date": pred_date.strftime("%d %B %Y") if pred_date else "the scheduled date",
            "coordinator_phone": coordinator_phone,
        }
        if extra_vars:
            variables.update(extra_vars)

        template = TEMPLATES.get(template_key, TEMPLATES["donation_request"])
        lang_template = template.get(lang, template.get('en', ''))
        message = lang_template.format_map(variables)

        title = TITLES.get(template_key, TITLES["donation_request"]).get(lang, "VeinConnect")
        priority = (
            "emergency" if is_emergency
            else "high" if urgency == "urgent"
            else "normal"
        )
        channel = self._select_channel(donor)

        return PersonalizedMessage(
            channel=channel,
            language=lang,
            title=title,
            message=message,
            send_at=self._optimal_send_time(donor, urgency, is_emergency),
            template_key=template_key,
            variables=variables,
            priority=priority,
        )

    def _resolve_template_key(
        self,
        notification_type: str,
        urgency: str,
        is_emergency: bool,
        reminder_count: int,
    ) -> str:
        if is_emergency or urgency == "emergency":
            return "emergency_alert"
        if notification_type == "reminder":
            return (
                "urgent_reminder"
                if reminder_count >= 2 or urgency == "urgent"
                else "reminder"
            )
        return notification_type if notification_type in TEMPLATES else "donation_request"

    def _select_channel(self, donor) -> str:
        pref = (
            getattr(getattr(donor, 'communication_preference', None), 'value', 'whatsapp')
            or 'whatsapp'
        )
        return pref  # whatsapp | sms

    def _optimal_send_time(self, donor, urgency: str, is_emergency: bool) -> datetime:
        now = datetime.now(IST)

        # Emergency: send immediately
        if is_emergency or urgency == "emergency":
            return now

        # Use donor's preferred times if set
        preferred = getattr(donor, 'preferred_times', None) or []
        if isinstance(preferred, list) and preferred:
            for t_str in preferred:
                try:
                    h, m = map(int, str(t_str).split(":"))
                    candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    if candidate > now + timedelta(minutes=30):
                        return candidate
                except (ValueError, AttributeError):
                    continue

        # Default: next optimal window
        for start_h, end_h in OPTIMAL_WINDOWS:
            candidate = now.replace(hour=start_h, minute=0, second=0, microsecond=0)
            if now.hour < end_h:
                if now.hour >= start_h:
                    # We're inside a window — send soon
                    return now + timedelta(minutes=5)
                return candidate

        # Default to next morning 9am
        tomorrow_9am = (now + timedelta(days=1)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        return tomorrow_9am

    def batch_compose(
        self,
        recipients: list[tuple],   # [(donor, patient, notification_type, extra_vars)]
        transfusion=None,
        reminder_count: int = 0,
        friendship_scores: dict | None = None,
    ) -> list[PersonalizedMessage]:
        """Compose personalized messages for multiple recipients at once."""
        friendship_scores = friendship_scores or {}
        return [
            self.compose(
                donor=donor,
                patient=patient,
                notification_type=ntype,
                transfusion=transfusion,
                reminder_count=reminder_count,
                friendship_score=friendship_scores.get(getattr(donor, 'id', None), 0.0),
                extra_vars=extra_vars,
            )
            for donor, patient, ntype, extra_vars in recipients
        ]
