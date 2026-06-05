"""
Response Likelihood Engine
==========================
Predicts the probability (0.0–1.0) that a donor will confirm a specific
donation request. Used during matching to prefer donors likely to respond.

v1: Rule-based adjustments on top of reliability score baseline.
v2 upgrade: sklearn LogisticRegression on confirmations table once 200+ rows.
"""

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass
class ResponseLikelihoodResult:
    donor_id: UUID
    transfusion_id: UUID | None
    probability: float              # 0.0 – 1.0
    key_factors: list[str] = field(default_factory=list)
    confidence: str = "low"        # "low" | "medium" | "high"


class ResponseLikelihoodEngine:
    """
    Rule-based response probability predictor.

    Base probability = reliability_score / 100
    Adjustments:
      +0.15 if day matches preferred_days
      +0.10 if time matches preferred_times
      +0.20 if is_emergency
      +0.10 if friendship_score > 70
      -0.15 if days_since_last_donation < 30
      -0.10 if avg reminders needed > 2
      -0.20 if last response was rejection
    """

    MIN_PROB: float = 0.05
    MAX_PROB: float = 0.98

    def predict(
        self,
        donor,
        transfusion,
        friendship_score: float = 0.0,
        avg_reminders_needed: float = 0.0,
        last_response_rejected: bool = False,
    ) -> ResponseLikelihoodResult:
        base = float(getattr(donor, "reliability_score", 50.0)) / 100.0
        adjustments: list[tuple[float, str]] = []

        # Day of week preference
        if transfusion is not None:
            pred_date = getattr(transfusion, 'predicted_date', None)
            if pred_date:
                requested_day = pred_date.strftime("%A").lower()
                preferred_days = getattr(donor, 'preferred_days', None) or []
                if isinstance(preferred_days, list) and requested_day in [d.lower() for d in preferred_days]:
                    adjustments.append((0.15, "prefers_this_day"))

        # Emergency boost
        if getattr(transfusion, 'is_emergency', False):
            adjustments.append((0.20, "emergency_willingness"))

        # Friendship bonus
        if friendship_score > 70:
            adjustments.append((0.10, "high_friendship_score"))
        elif friendship_score > 50:
            adjustments.append((0.05, "moderate_friendship_score"))

        # Recency penalty
        last_donation = getattr(donor, 'last_donation_date', None)
        if last_donation:
            days_since = (date.today() - last_donation).days
            if days_since < 30:
                adjustments.append((-0.15, "donated_recently"))
            elif days_since < 60:
                adjustments.append((-0.05, "donated_within_60_days"))

        # Reminder history penalty
        if avg_reminders_needed > 2:
            adjustments.append((-0.10, "typically_needs_multiple_reminders"))

        # Last rejection penalty
        if last_response_rejected:
            adjustments.append((-0.20, "last_response_was_rejection"))

        # Availability
        if not getattr(donor, 'is_available', True):
            adjustments.append((-0.30, "marked_unavailable"))

        total_adj = sum(adj for adj, _ in adjustments)
        probability = max(self.MIN_PROB, min(self.MAX_PROB, base + total_adj))

        # Confidence based on reliability score history
        reliability = float(getattr(donor, 'reliability_score', 50.0))
        confidence = "high" if reliability > 70 else "medium" if reliability > 40 else "low"

        tid = getattr(transfusion, 'id', None)
        return ResponseLikelihoodResult(
            donor_id=donor.id,
            transfusion_id=tid,
            probability=round(probability, 4),
            key_factors=[label for _, label in adjustments],
            confidence=confidence,
        )

    def batch_predict(
        self,
        donors: list,
        transfusion,
        friendship_scores: dict | None = None,
    ) -> dict[UUID, float]:
        """Returns {donor_id: probability} for all candidates."""
        friendship_scores = friendship_scores or {}
        return {
            donor.id: self.predict(
                donor, transfusion,
                friendship_score=friendship_scores.get(donor.id, 0.0)
            ).probability
            for donor in donors
        }
