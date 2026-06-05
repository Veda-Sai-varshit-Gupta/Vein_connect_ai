"""
Reliability Engine
==================
Computes a donor's reliability score (0–100) using Exponential Weighted
Moving Average (EWMA) of historical donation behavior.

Default for new donors: 50.0 (neutral)
Updated asynchronously after every donation event.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class ReliabilityResult:
    donor_id: UUID
    score: float            # 0.0 – 100.0
    confidence: str         # "low" | "medium" | "high"
    breakdown: dict
    trend: str              # "improving" | "stable" | "declining"
    total_interactions: int


class ReliabilityEngine:
    """
    Computes reliability score via EWMA over historical interaction outcomes.

    Score components:
      Show-up rate             60%
      No-show penalty          20%
      Response speed           10%
      Emergency willingness    10%
    """

    ALPHA: float = 0.3           # EWMA smoothing factor
    DEFAULT_SCORE: float = 50.0  # New donor default

    def compute(
        self,
        donor_id: UUID,
        donations: list,
        confirmations: list,
        historical_scores: list[float] | None = None,
    ) -> ReliabilityResult:
        if not donations and not confirmations:
            return ReliabilityResult(
                donor_id=donor_id,
                score=self.DEFAULT_SCORE,
                confidence="low",
                breakdown={"note": "No interaction history"},
                trend="stable",
                total_interactions=0,
            )

        def _get_val(val) -> str:
            if hasattr(val, 'value'):
                return str(val.value)
            return str(val)

        total_commitments = len([
            c for c in confirmations
            if hasattr(c, 'status') and _get_val(c.status) != "pending"
        ])

        if total_commitments == 0:
            return ReliabilityResult(
                donor_id=donor_id,
                score=self.DEFAULT_SCORE,
                confidence="low",
                breakdown={"note": "No committed interactions yet"},
                trend="stable",
                total_interactions=len(donations),
            )

        honored = len([d for d in donations if _get_val(getattr(d, 'status', '')) == "completed"])
        no_shows = len([d for d in donations if _get_val(getattr(d, 'status', '')) == "no_show"])

        # Emergency response rate
        emergency_total = len([
            d for d in donations
            if getattr(getattr(d, 'transfusion', None), 'is_emergency', False)
        ])
        emergency_honored = len([
            d for d in donations
            if getattr(getattr(d, 'transfusion', None), 'is_emergency', False)
            and _get_val(getattr(d, 'status', '')) == "completed"
        ])

        # Component scores
        show_rate_score = (honored / total_commitments) * 60
        no_show_penalty = (1 - no_shows / total_commitments) * 20
        response_score = self._response_speed_score(confirmations) * 10
        emergency_score = (emergency_honored / max(emergency_total, 1)) * 10

        base = show_rate_score + no_show_penalty + response_score + emergency_score
        base = min(100.0, max(0.0, base))

        # Apply EWMA
        history = (historical_scores or []) + [base]
        final_score = self._compute_ewma(history, self.ALPHA)
        final_score = round(min(100.0, max(0.0, final_score)), 2)

        # Confidence based on data volume
        confidence = "low" if total_commitments < 3 else "medium" if total_commitments < 10 else "high"

        # Trend: compare last 3 scores
        trend = self._detect_trend(history[-3:] if len(history) >= 3 else history)

        return ReliabilityResult(
            donor_id=donor_id,
            score=final_score,
            confidence=confidence,
            breakdown={
                "show_up_rate": round(show_rate_score, 2),
                "no_show_penalty": round(no_show_penalty, 2),
                "response_speed": round(response_score, 2),
                "emergency_willingness": round(emergency_score, 2),
                "base_score": round(base, 2),
            },
            trend=trend,
            total_interactions=total_commitments,
        )

    def _compute_ewma(self, values: list[float], alpha: float) -> float:
        ewma = values[0]
        for v in values[1:]:
            ewma = alpha * v + (1 - alpha) * ewma
        return ewma

    def _response_speed_score(self, confirmations: list) -> float:
        """Score based on how often the donor responds without needing reminders."""
        if not confirmations:
            return 0.5  # Neutral default
        responded = [c for c in confirmations if getattr(c, 'responded_at', None) is not None]
        if not responded:
            return 0.0
        # Responded on first ask (0 reminders) = best
        fast = [c for c in responded if getattr(c, 'reminder_count', 0) == 0]
        return len(fast) / len(confirmations)

    def _detect_trend(self, scores: list[float]) -> str:
        if len(scores) < 2:
            return "stable"
        diffs = [scores[i + 1] - scores[i] for i in range(len(scores) - 1)]
        if all(d > 1.0 for d in diffs):
            return "improving"
        if all(d < -1.0 for d in diffs):
            return "declining"
        return "stable"
