"""
Transfusion Predictor
=====================
Predicts the next transfusion date for a patient using a recency-weighted
moving average of historical transfusion intervals.

Works with 0 transfusions on Day 1 (uses thalassemia-type defaults).
Upgrade path: sklearn BayesianRidge for uncertainty bands.
"""

import numpy as np
from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID


# Typical transfusion intervals by thalassemia type (days)
DEFAULT_INTERVALS: dict[str, int] = {
    "major":      21,
    "intermedia": 28,
    "minor":      42,
    "hb_e":       28,
    "hb_s":       21,
}


@dataclass
class TransfusionPrediction:
    patient_id: UUID
    predicted_date: date
    confidence_interval_days: int       # ± this many days
    based_on_n_transfusions: int
    interval_trend: str                 # "stable" | "shortening" | "lengthening"
    average_interval_days: float
    alert: str | None = None            # Clinical warning if trend detected


class TransfusionPredictor:
    """Predicts next transfusion date using recency-weighted interval average."""

    def predict(
        self,
        patient,
        transfusion_dates: list[date],
    ) -> TransfusionPrediction:
        thal_type = getattr(patient.thalassemia_type, 'value', str(patient.thalassemia_type))
        default_interval = DEFAULT_INTERVALS.get(thal_type, patient.avg_transfusion_interval_days)

        # No history: use type default
        if len(transfusion_dates) < 1:
            predicted = date.today() + timedelta(days=default_interval)
            return TransfusionPrediction(
                patient_id=patient.id,
                predicted_date=predicted,
                confidence_interval_days=7,
                based_on_n_transfusions=0,
                interval_trend="stable",
                average_interval_days=float(default_interval),
            )

        dates_sorted = sorted(transfusion_dates)
        last_date = dates_sorted[-1]

        # Only 1 date: use default interval
        if len(dates_sorted) < 2:
            predicted = last_date + timedelta(days=default_interval)
            return TransfusionPrediction(
                patient_id=patient.id,
                predicted_date=predicted,
                confidence_interval_days=5,
                based_on_n_transfusions=1,
                interval_trend="stable",
                average_interval_days=float(default_interval),
            )

        # Compute intervals
        intervals = [
            (dates_sorted[i + 1] - dates_sorted[i]).days
            for i in range(len(dates_sorted) - 1)
        ]

        # Recency-weighted average
        weights = list(range(1, len(intervals) + 1))
        weighted_avg = float(np.average(intervals, weights=weights))
        std_dev = float(np.std(intervals)) if len(intervals) > 1 else 3.0

        predicted = last_date + timedelta(days=int(round(weighted_avg)))
        confidence = max(2, min(14, int(std_dev)))  # Cap between 2 and 14 days

        # Trend detection using last 3 intervals
        recent = intervals[-3:] if len(intervals) >= 3 else intervals
        trend = self._detect_trend(recent)

        # Clinical alert on trend change
        alert: str | None = None
        if trend == "shortening":
            alert = (
                f"Transfusion interval is shortening (avg {weighted_avg:.0f} days). "
                "Medical review recommended."
            )
        elif trend == "lengthening":
            alert = (
                f"Transfusion interval is lengthening (avg {weighted_avg:.0f} days). "
                "Patient is stabilizing — verify with physician."
            )

        return TransfusionPrediction(
            patient_id=patient.id,
            predicted_date=predicted,
            confidence_interval_days=confidence,
            based_on_n_transfusions=len(transfusion_dates),
            interval_trend=trend,
            average_interval_days=round(weighted_avg, 1),
            alert=alert,
        )

    def _detect_trend(self, intervals: list[int]) -> str:
        if len(intervals) < 2:
            return "stable"
        diffs = [intervals[i + 1] - intervals[i] for i in range(len(intervals) - 1)]
        if all(d < -1 for d in diffs):
            return "shortening"
        if all(d > 1 for d in diffs):
            return "lengthening"
        return "stable"

    def bulk_predict(
        self,
        patients: list,
        patient_transfusion_map: dict,
    ) -> list[TransfusionPrediction]:
        """Predict for multiple patients at once."""
        return [
            self.predict(patient, patient_transfusion_map.get(patient.id, []))
            for patient in patients
        ]
