"""
Friendship Score Engine
========================
Quantifies the relationship quality between a specific patient-donor pair.
High friendship = donor more likely to respond, patient more comfortable.

Tiers:
  0–25:   new
  25–50:  acquaintance
  50–75:  regular
  75–100: champion
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass
class FriendshipScoreResult:
    patient_id: UUID
    donor_id: UUID
    score: float                    # 0.0 – 100.0
    tier: str                       # "new" | "acquaintance" | "regular" | "champion"
    relationship_duration_days: int
    total_donations: int
    positive_interactions: int
    negative_interactions: int
    emergency_responses: int
    score_breakdown: dict


FRIENDSHIP_WEIGHTS: dict[str, float] = {
    "donation_frequency": 0.35,
    "relationship_duration": 0.20,
    "emergency_response": 0.25,
    "positive_interactions": 0.10,
    "no_show_penalty": 0.10,
}

TIER_THRESHOLDS: list[tuple[float, str]] = [
    (75.0, "champion"),
    (50.0, "regular"),
    (25.0, "acquaintance"),
    (0.0,  "new"),
]


def _tier_for_score(score: float) -> str:
    for threshold, label in TIER_THRESHOLDS:
        if score >= threshold:
            return label
    return "new"


class FriendshipScoreEngine:
    """
    Computes the friendship score between a patient and a specific donor.

    Score components:
      Donation frequency      35%  — how often donor has donated for this patient
      Relationship duration   20%  — how long they have been connected
      Emergency response      25%  — responded to emergency requests
      Positive interactions   10%  — confirmations, thanks, follow-ups
      No-show penalty        -10%  — weighted reduction per no-show
    """

    MAX_DONATIONS_FOR_FULL_SCORE: int = 10   # 10+ donations = 100 on frequency
    MAX_DURATION_DAYS: int = 730             # 2 years = 100 on duration

    def compute(
        self,
        patient_id: UUID,
        donor_id: UUID,
        shared_donations: list,           # Donation objects for this patient-donor pair
        relationship_start_date: date | None = None,
        emergency_requests_received: int = 0,
        emergency_requests_honored: int = 0,
        positive_interaction_count: int = 0,
    ) -> FriendshipScoreResult:
        """
        Parameters
        ----------
        shared_donations:
            All Donation ORM objects where donor donated for this patient.
        relationship_start_date:
            Date the donor first connected with or donated for this patient.
        emergency_requests_received:
            Emergency requests sent to this donor for this patient.
        emergency_requests_honored:
            How many emergency requests this donor fulfilled for this patient.
        positive_interaction_count:
            Count of non-donation positive events (messages, confirmations, etc.).
        """
        total = len(shared_donations)
        completed = [d for d in shared_donations if str(getattr(d, 'status', '')) == "completed"]
        no_shows = [d for d in shared_donations if str(getattr(d, 'status', '')) == "no_show"]

        # Donation frequency score
        freq_score = min(100.0, (len(completed) / self.MAX_DONATIONS_FOR_FULL_SCORE) * 100.0)

        # Relationship duration score
        duration_days = 0
        if relationship_start_date:
            duration_days = (date.today() - relationship_start_date).days
        duration_score = min(100.0, (duration_days / self.MAX_DURATION_DAYS) * 100.0)

        # Emergency response score
        if emergency_requests_received > 0:
            emergency_score = (emergency_requests_honored / emergency_requests_received) * 100.0
        else:
            emergency_score = 50.0  # Neutral — never asked

        # Positive interactions score
        positive_score = min(100.0, positive_interaction_count * 10.0)

        # No-show penalty (reduces overall score)
        no_show_rate = len(no_shows) / max(total, 1)
        no_show_penalty = no_show_rate * 100.0

        # Weighted composite
        raw = (
            FRIENDSHIP_WEIGHTS["donation_frequency"] * freq_score
            + FRIENDSHIP_WEIGHTS["relationship_duration"] * duration_score
            + FRIENDSHIP_WEIGHTS["emergency_response"] * emergency_score
            + FRIENDSHIP_WEIGHTS["positive_interactions"] * positive_score
            - FRIENDSHIP_WEIGHTS["no_show_penalty"] * no_show_penalty
        )
        final_score = round(max(0.0, min(100.0, raw)), 2)

        return FriendshipScoreResult(
            patient_id=patient_id,
            donor_id=donor_id,
            score=final_score,
            tier=_tier_for_score(final_score),
            relationship_duration_days=duration_days,
            total_donations=len(completed),
            positive_interactions=positive_interaction_count,
            negative_interactions=len(no_shows),
            emergency_responses=emergency_requests_honored,
            score_breakdown={
                "donation_frequency": round(freq_score, 2),
                "relationship_duration": round(duration_score, 2),
                "emergency_response": round(emergency_score, 2),
                "positive_interactions": round(positive_score, 2),
                "no_show_penalty": round(no_show_penalty, 2),
                "raw_composite": round(raw, 2),
            },
        )

    def batch_compute(
        self,
        patient_id: UUID,
        donor_donation_map: dict,   # {donor_id: list[Donation]}
        relationship_map: dict | None = None,   # {donor_id: start_date}
        emergency_map: dict | None = None,      # {donor_id: (received, honored)}
        interaction_map: dict | None = None,    # {donor_id: int}
    ) -> dict[UUID, FriendshipScoreResult]:
        """Compute friendship scores for all donors for a given patient at once."""
        relationship_map = relationship_map or {}
        emergency_map = emergency_map or {}
        interaction_map = interaction_map or {}

        results: dict[UUID, FriendshipScoreResult] = {}
        for donor_id, donations in donor_donation_map.items():
            er_received, er_honored = emergency_map.get(donor_id, (0, 0))
            results[donor_id] = self.compute(
                patient_id=patient_id,
                donor_id=donor_id,
                shared_donations=donations,
                relationship_start_date=relationship_map.get(donor_id),
                emergency_requests_received=er_received,
                emergency_requests_honored=er_honored,
                positive_interaction_count=interaction_map.get(donor_id, 0),
            )
        return results

    def get_scores_as_dict(
        self, results: dict[UUID, "FriendshipScoreResult"]
    ) -> dict[UUID, float]:
        """Returns a flat {donor_id: score} dict for use in matching engines."""
        return {donor_id: r.score for donor_id, r in results.items()}
