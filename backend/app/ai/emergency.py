"""
Emergency Prioritization Engine
================================
Ranks donors and hospitals by emergency readiness.
Overrides normal matching weights — speed and proximity are paramount.

Special rules:
- All response windows halved
- Compatible blood groups included after 15 min if no exact match
- Multi-channel blast (all top donors contacted simultaneously)
- Capacity constraints loosened by 20% for emergency beds
"""

from dataclasses import dataclass, field
from uuid import UUID
from .matcher import haversine_km, blood_group_score, distance_score, COMPATIBILITY

# Emergency-specific weights (blood group and proximity dominate)
EMERGENCY_DONOR_WEIGHTS: dict[str, float] = {
    "blood_group": 0.40,
    "distance": 0.30,
    "availability": 0.20,
    "reliability": 0.10,
}

EMERGENCY_HOSPITAL_WEIGHTS: dict[str, float] = {
    "capacity": 0.50,
    "distance": 0.30,
    "staff": 0.20,
}


@dataclass
class EmergencyDonorRank:
    donor_id: UUID
    donor_name: str
    blood_group: str
    emergency_score: float
    distance_km: float
    reliability_score: float
    is_available: bool
    phone: str
    rank: int


@dataclass
class EmergencyHospitalRank:
    hospital_id: UUID
    hospital_name: str
    emergency_score: float
    distance_km: float
    emergency_beds_available: int
    rank: int


@dataclass
class EmergencyPlan:
    transfusion_id: UUID | None
    alert_level: str                              # "critical" | "urgent" | "high"
    priority_donors: list[EmergencyDonorRank] = field(default_factory=list)
    priority_hospitals: list[EmergencyHospitalRank] = field(default_factory=list)
    fallback_blood_groups: list[str] = field(default_factory=list)
    response_window_hours: int = 12
    blast_all_donors: bool = True
    message: str = ""


class EmergencyPrioritizationEngine:
    """Scores and ranks donors/hospitals for emergency transfusion."""

    EMERGENCY_RESPONSE_WINDOW = {"routine": 24, "urgent": 12, "emergency": 6}

    def rank_donors(
        self,
        candidates: list,
        patient_blood_group: str,
        hospital_lat: float,
        hospital_lng: float,
    ) -> list[EmergencyDonorRank]:
        donor_scores: list[tuple] = []
        for donor in candidates:
            score = self._score_emergency_donor(donor, patient_blood_group, hospital_lat, hospital_lng)
            if score > 0:
                dist = haversine_km(
                    getattr(donor, 'latitude', 0.0) or 0.0,
                    getattr(donor, 'longitude', 0.0) or 0.0,
                    hospital_lat, hospital_lng,
                )
                donor_scores.append((donor, score, dist))

        donor_scores.sort(key=lambda x: x[1], reverse=True)

        return [
            EmergencyDonorRank(
                donor_id=d.id,
                donor_name=getattr(d, 'name', ''),
                blood_group=d.blood_group.value if hasattr(d.blood_group, 'value') else d.blood_group,
                emergency_score=round(s, 2),
                distance_km=round(dist, 2),
                reliability_score=float(getattr(d, 'reliability_score', 50.0)),
                is_available=getattr(d, 'is_available', True),
                phone=d.user.phone if hasattr(d, 'user') and hasattr(d.user, 'phone') else '',
                rank=i + 1,
            )
            for i, (d, s, dist) in enumerate(donor_scores)
        ]

    def prioritize(
        self,
        patient,
        donors: list,
        hospitals: list,
        capacity_map: dict,     # {hospital_id: HospitalCapacity}
        transfusion_id: UUID | None = None,
        patient_lat: float = 0.0,
        patient_lng: float = 0.0,
    ) -> EmergencyPlan:
        patient_bg = (
            patient.blood_group.value
            if hasattr(patient.blood_group, 'value')
            else patient.blood_group
        )

        # Score donors
        donor_scores: list[tuple] = []
        for donor in donors:
            score = self._score_emergency_donor(donor, patient_bg, patient_lat, patient_lng)
            if score > 0:
                dist = haversine_km(
                    getattr(donor, 'latitude', 0.0) or 0.0,
                    getattr(donor, 'longitude', 0.0) or 0.0,
                    patient_lat, patient_lng,
                )
                donor_scores.append((donor, score, dist))

        donor_scores.sort(key=lambda x: x[1], reverse=True)

        # Score hospitals
        hospital_scores: list[tuple] = []
        for hospital in hospitals:
            cap = capacity_map.get(hospital.id)
            score, emerg_beds = self._score_emergency_hospital(hospital, cap, patient_lat, patient_lng)
            if score > 0:
                dist = haversine_km(
                    getattr(hospital, 'latitude', 0.0) or 0.0,
                    getattr(hospital, 'longitude', 0.0) or 0.0,
                    patient_lat, patient_lng,
                )
                hospital_scores.append((hospital, score, dist, emerg_beds))

        hospital_scores.sort(key=lambda x: x[1], reverse=True)

        alert = self._determine_alert(len(donor_scores), len(hospital_scores))
        fallback_bgs = self._get_fallback_blood_groups(patient_bg)

        return EmergencyPlan(
            transfusion_id=transfusion_id,
            alert_level=alert,
            priority_donors=[
                EmergencyDonorRank(
                    donor_id=d.id,
                    donor_name=getattr(d, 'name', ''),
                    blood_group=d.blood_group.value if hasattr(d.blood_group, 'value') else d.blood_group,
                    emergency_score=round(s, 2),
                    distance_km=round(dist, 2),
                    reliability_score=float(getattr(d, 'reliability_score', 50.0)),
                    is_available=getattr(d, 'is_available', True),
                    phone=d.user.phone if hasattr(d, 'user') and hasattr(d.user, 'phone') else '',
                    rank=i + 1,
                )
                for i, (d, s, dist) in enumerate(donor_scores[:15])
            ],
            priority_hospitals=[
                EmergencyHospitalRank(
                    hospital_id=h.id,
                    hospital_name=getattr(h, 'name', ''),
                    emergency_score=round(s, 2),
                    distance_km=round(dist, 2),
                    emergency_beds_available=eb,
                    rank=i + 1,
                )
                for i, (h, s, dist, eb) in enumerate(hospital_scores[:5])
            ],
            fallback_blood_groups=fallback_bgs,
            response_window_hours=6,
            blast_all_donors=True,
            message=self._compose_alert_message(alert, patient_bg),
        )

    def _score_emergency_donor(self, donor, patient_bg: str, lat: float, lng: float) -> float:
        donor_bg = donor.blood_group.value if hasattr(donor.blood_group, 'value') else donor.blood_group
        bg_s = blood_group_score(donor_bg, patient_bg)
        if bg_s == 0:
            return 0.0

        dist = haversine_km(
            getattr(donor, 'latitude', 0.0) or 0.0,
            getattr(donor, 'longitude', 0.0) or 0.0,
            lat, lng,
        )
        dist_s = distance_score(dist, getattr(donor, 'max_travel_distance_km', 25) or 25)
        avail_s = 100.0 if getattr(donor, 'is_available', True) else 0.0
        rel_s = float(getattr(donor, 'reliability_score', 50.0))

        return (
            EMERGENCY_DONOR_WEIGHTS["blood_group"] * bg_s
            + EMERGENCY_DONOR_WEIGHTS["distance"] * dist_s
            + EMERGENCY_DONOR_WEIGHTS["availability"] * avail_s
            + EMERGENCY_DONOR_WEIGHTS["reliability"] * rel_s
        )

    def _score_emergency_hospital(
        self, hospital, capacity, lat: float, lng: float
    ) -> tuple[float, int]:
        if capacity is None:
            return 0.0, 0

        emerg_beds = getattr(capacity, 'emergency_capacity_available', 0) or 0
        # Loosen emergency capacity by 20%
        effective_beds = int(emerg_beds * 1.2)
        if effective_beds <= 0:
            return 0.0, 0

        capacity_s = min(100.0, effective_beds * 20.0)  # 5 beds = 100
        dist = haversine_km(
            getattr(hospital, 'latitude', 0.0) or 0.0,
            getattr(hospital, 'longitude', 0.0) or 0.0,
            lat, lng,
        )
        dist_s = distance_score(dist, 50.0)  # 50km radius for hospitals in emergency
        staff_s = 100.0 if getattr(capacity, 'staff_available', True) else 30.0

        score = (
            EMERGENCY_HOSPITAL_WEIGHTS["capacity"] * capacity_s
            + EMERGENCY_HOSPITAL_WEIGHTS["distance"] * dist_s
            + EMERGENCY_HOSPITAL_WEIGHTS["staff"] * staff_s
        )
        return score, effective_beds

    def _determine_alert(self, donor_count: int, hospital_count: int) -> str:
        if donor_count == 0 or hospital_count == 0:
            return "critical"
        if donor_count < 3:
            return "urgent"
        return "high"

    def _get_fallback_blood_groups(self, patient_bg: str) -> list[str]:
        """Returns donor blood groups that can donate to patient_bg."""
        return [
            donor_bg
            for donor_bg, compatible in COMPATIBILITY.items()
            if patient_bg in compatible and donor_bg != patient_bg
        ]

    def _compose_alert_message(self, alert: str, blood_group: str) -> str:
        messages = {
            "critical": (
                f"CRITICAL: No donors or hospitals available for {blood_group} blood. "
                "Immediate escalation required."
            ),
            "urgent": (
                f"URGENT: Limited donors available for {blood_group} blood. "
                "All contacts being alerted."
            ),
            "high": (
                f"EMERGENCY: {blood_group} blood required immediately. "
                "Top donors and hospitals identified."
            ),
        }
        return messages.get(alert, "Emergency transfusion required.")
