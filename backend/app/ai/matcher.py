"""
Donor Matching Engine
=====================
Ranks candidate donors for a transfusion request using a weighted
9-factor scoring system.

Scoring weights:
  blood_group_match          20%
  eligibility_status         15%
  distance                   15%
  reliability_score          15%
  response_likelihood        10%
  previous_donation_history  10%
  friendship_score            5%
  fair_reimbursement          5%
  emergency_priority          5%
"""

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import UUID


# ── Blood Group Compatibility ────────────────────────────────────────────────
# Key: donor blood group → list of recipient blood groups they can donate to
# Strictly restricted to exact matching only
COMPATIBILITY: dict[str, list[str]] = {
    "O-":  ["O-"],
    "O+":  ["O+"],
    "A-":  ["A-"],
    "A+":  ["A+"],
    "B-":  ["B-"],
    "B+":  ["B+"],
    "AB-": ["AB-"],
    "AB+": ["AB+"],
}

WEIGHTS: dict[str, float] = {
    "blood_group": 0.20,
    "eligibility": 0.15,
    "distance": 0.15,
    "reliability": 0.15,
    "response_likelihood": 0.10,
    "previous_donation_history": 0.10,
    "friendship": 0.05,
    "fair_reimbursement": 0.05,
    "emergency_priority": 0.05,
}

DONATION_COOLDOWN_DAYS: int = 90


@dataclass
class DonorMatchResult:
    donor_id: UUID
    donor_name: str
    blood_group: str
    match_score: float          # 0.0 – 100.0 composite
    blood_group_match: bool
    distance_km: float
    reliability_score: float
    response_likelihood: float
    friendship_score: float
    days_since_last_donation: int
    is_eligible: bool
    rank: int
    score_breakdown: dict[str, float] = field(default_factory=dict)
    reason: str = ""
    demanded_reimbursement: float = 0.0
    medical_clearance_at: Optional[date] = None


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Returns great-circle distance in km between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def blood_group_score(donor_bg: str, patient_bg: str) -> float:
    """100 for exact match, 80 for compatible, 0 for incompatible."""
    if donor_bg == patient_bg:
        return 100.0
    compatible = COMPATIBILITY.get(donor_bg, [])
    if patient_bg in compatible:
        return 80.0
    return 0.0


def distance_score(distance_km: float, max_travel_km: float) -> float:
    """Linear decay from 100 (at origin) to 0 (at max travel distance)."""
    if max_travel_km <= 0:
        return 0.0
    return max(0.0, 100.0 - (distance_km / max_travel_km) * 100.0)


class DonorMatchingEngine:
    """Scores and ranks donors for a given transfusion request."""

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or WEIGHTS

    def _is_eligible(self, donor) -> tuple[bool, int]:
        """Returns (is_eligible, days_since_last_donation)."""
        gender = getattr(donor, "gender", None)
        gender_val = gender.value if hasattr(gender, "value") else str(gender).lower() if gender else "male"
        cooldown_days = 120 if gender_val == "female" else 90

        if donor.last_donation_date is None:
            cooldown_eligible = True
            days = 999
        else:
            days = (date.today() - donor.last_donation_date).days
            cooldown_eligible = days >= cooldown_days

        # Check medical clearance certificate validity (within 6 months / 180 days)
        med_clearance = getattr(donor, "medical_clearance_at", None)
        med_url = getattr(donor, "medical_clearance_url", None)
        if med_clearance is None or not med_url:
            medical_eligible = False
        else:
            clearance_date = med_clearance.date() if hasattr(med_clearance, 'date') else med_clearance
            medical_eligible = (date.today() - clearance_date).days <= 180

        return cooldown_eligible and medical_eligible, days

    def _build_reason(self, breakdown: dict[str, float], is_eligible: bool, donor=None) -> str:
        if not is_eligible:
            reasons = []
            if donor:
                if donor.last_donation_date is not None:
                    gender = getattr(donor, "gender", None)
                    gender_val = gender.value if hasattr(gender, "value") else str(gender).lower() if gender else "male"
                    cooldown_days = 120 if gender_val == "female" else 90
                    days = (date.today() - donor.last_donation_date).days
                    if days < cooldown_days:
                        reasons.append(f"donated {days} days ago (cooldown is {cooldown_days} days for {gender_val})")
                if getattr(donor, "medical_clearance_at", None) is None or not getattr(donor, "medical_clearance_url", None):
                    reasons.append("missing medical clearance")
                else:
                    clearance_date = donor.medical_clearance_at.date() if hasattr(donor.medical_clearance_at, 'date') else donor.medical_clearance_at
                    days_clearance = (date.today() - clearance_date).days
                    if days_clearance > 180:
                        reasons.append(f"medical clearance expired {days_clearance} days ago")
            return "Ineligible: " + (", ".join(reasons) if reasons else "cooldown or clearance issue")

        parts = []
        if breakdown.get("blood_group", 0) == 100:
            parts.append("exact blood group match")
        elif breakdown.get("blood_group", 0) == 80:
            parts.append("compatible blood group")
        else:
            return "Incompatible blood group"
        if breakdown.get("reliability", 0) > 70:
            parts.append("high reliability")
        if breakdown.get("distance", 0) > 70:
            parts.append("close proximity")
        if breakdown.get("friendship", 0) > 70:
            parts.append("strong patient relationship")
        if breakdown.get("previous_donation_history", 0) > 0:
            parts.append("has donated before")
        if breakdown.get("fair_reimbursement", 0) > 70:
            parts.append("fair reimbursement demand")
        return ", ".join(parts) if parts else "standard match"

    def score_donor(
        self,
        donor,
        patient_blood_group: str,
        hospital_lat: float,
        hospital_lng: float,
        response_likelihood: float = 0.5,
        friendship_score: float = 0.0,
        previous_donation_history_count: int = 0,
        is_emergency: bool = False,
        last_donor_id: Optional[UUID] = None,
        learned_gap_days: Optional[float] = None,
    ) -> tuple[float, dict[str, float]]:
        """Returns (composite_score, breakdown_dict)."""
        bg_score = blood_group_score(
            donor.blood_group.value if hasattr(donor.blood_group, 'value') else donor.blood_group,
            patient_blood_group,
        )
        
        cooldown_and_med_eligible, _ = self._is_eligible(donor)
        is_eligible = cooldown_and_med_eligible and (bg_score > 0.0)

        lat = getattr(donor, "latitude", None) or 0.0
        lng = getattr(donor, "longitude", None) or 0.0
        dist_km = haversine_km(lat, lng, hospital_lat, hospital_lng)
        max_travel = getattr(donor, "max_travel_distance_km", 25) or 25

        # Previous donation history score: 50 per donation, max 100
        history_score = min(previous_donation_history_count * 50.0, 100.0)

        # Fair reimbursement score: linear decay (demanded amount / 1000)
        demanded = float(getattr(donor, "demanded_reimbursement", 0.0))
        reimbursement_score = max(0.0, 100.0 - demanded / 10.0)

        # Emergency priority score: 100 if transfusion is emergency and donor is available
        emergency_priority_score = 100.0 if (is_emergency and getattr(donor, "is_available", True)) else 0.0

        breakdown = {
            "blood_group": bg_score,
            "eligibility": 100.0 if is_eligible else 0.0,
            "distance": distance_score(dist_km, max_travel),
            "reliability": float(getattr(donor, "reliability_score", 50.0)),
            "response_likelihood": response_likelihood * 100.0,
            "previous_donation_history": history_score,
            "friendship": float(friendship_score),
            "fair_reimbursement": reimbursement_score,
            "emergency_priority": emergency_priority_score,
        }

        if not is_eligible:
            return 0.0, breakdown

        composite = sum(self.weights[k] * v for k, v in breakdown.items() if k in self.weights)
        
        # Apply custom logic penalties directly to composite score
        if last_donor_id and donor.id == last_donor_id:
            # Rotate donor penalty (prevent back-to-back matches for the same patient)
            composite -= 30.0
            
        if learned_gap_days and getattr(donor, "last_donation_date", None):
            days_since = (date.today() - donor.last_donation_date).days
            if days_since < learned_gap_days:
                # Penalty proportional to how early they are relative to their learned pattern (max 25.0 points)
                freq_penalty = (1.0 - (days_since / learned_gap_days)) * 25.0
                composite -= freq_penalty

        return round(max(0.0, min(100.0, composite)), 2), breakdown

    def rank_donors(
        self,
        candidates: list,
        patient_blood_group: str,
        hospital_lat: float,
        hospital_lng: float,
        response_likelihoods: dict | None = None,
        friendship_scores: dict | None = None,
        previous_donations_counts: dict | None = None,
        is_emergency: bool = False,
        last_donor_id: Optional[UUID] = None,
        learned_gaps: dict | None = None,
    ) -> list[DonorMatchResult]:
        """Scores all candidates and returns ranked DonorMatchResult list."""
        response_likelihoods = response_likelihoods or {}
        friendship_scores = friendship_scores or {}
        previous_donations_counts = previous_donations_counts or {}
        scored: list[tuple] = []

        for donor in candidates:
            bg_score = blood_group_score(
                donor.blood_group.value if hasattr(donor.blood_group, 'value') else donor.blood_group,
                patient_blood_group,
            )
            cooldown_ok, days_since = self._is_eligible(donor)
            is_eligible = cooldown_ok and (bg_score > 0.0)
            
            rl = response_likelihoods.get(donor.id, 0.5)
            fs = friendship_scores.get(donor.id, 0.0)
            pd_count = previous_donations_counts.get(donor.id, 0)
            
            composite, breakdown = self.score_donor(
                donor=donor,
                patient_blood_group=patient_blood_group,
                hospital_lat=hospital_lat,
                hospital_lng=hospital_lng,
                response_likelihood=rl,
                friendship_score=fs,
                previous_donation_history_count=pd_count,
                is_emergency=is_emergency,
                last_donor_id=last_donor_id,
                learned_gap_days=learned_gaps.get(donor.id) if learned_gaps else None,
            )
            bg_val = donor.blood_group.value if hasattr(donor.blood_group, 'value') else donor.blood_group
            dist_km = haversine_km(
                getattr(donor, "latitude", 0.0) or 0.0,
                getattr(donor, "longitude", 0.0) or 0.0,
                hospital_lat, hospital_lng,
            )
            scored.append((
                donor, composite, breakdown, is_eligible, days_since,
                bg_val == patient_blood_group, dist_km, rl, fs,
            ))

        scored.sort(key=lambda x: x[1], reverse=True)

        results: list[DonorMatchResult] = []
        for rank, (donor, score, breakdown, eligible, days, bg_match, dist, rl, fs) in enumerate(scored, 1):
            clearance_date = getattr(donor, "medical_clearance_at", None)
            if clearance_date and hasattr(clearance_date, "date"):
                clearance_date = clearance_date.date()
                
            results.append(DonorMatchResult(
                donor_id=donor.id,
                donor_name=getattr(donor, "name", ""),
                blood_group=donor.blood_group.value if hasattr(donor.blood_group, 'value') else donor.blood_group,
                match_score=score,
                blood_group_match=bg_match,
                distance_km=round(dist, 2),
                reliability_score=float(getattr(donor, "reliability_score", 50.0)),
                response_likelihood=round(rl, 3),
                friendship_score=round(fs, 2),
                days_since_last_donation=days,
                is_eligible=eligible,
                rank=rank,
                score_breakdown=breakdown,
                reason=self._build_reason(breakdown, eligible, donor),
                demanded_reimbursement=float(getattr(donor, "demanded_reimbursement", 0.0)),
                medical_clearance_at=clearance_date,
            ))

        return results
