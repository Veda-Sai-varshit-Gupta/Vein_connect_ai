"""
Hospital Capacity Forecasting Engine
=====================================
Predicts available hospital capacity on a future date using rolling
day-of-week statistics from historical capacity records.

Works with 0 records on Day 1 (returns conservative defaults).
Upgrade path: sklearn Ridge Regression with day-of-week + trend features.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class CapacityForecast:
    hospital_id: UUID
    target_date: date
    predicted_available_beds: int
    predicted_available_chairs: int
    confidence: float               # 0.0 – 1.0
    is_likely_available: bool
    upcoming_bookings: int
    recommendation: str
    data_points_used: int


class CapacityForecaster:
    """
    Forecasts hospital capacity using rolling same-weekday averages.

    Considers:
    - Historical capacity readings (last 90 days)
    - Already-scheduled transfusions for the target date
    - Day-of-week patterns (hospitals busier on weekdays)
    """

    MIN_AVAILABLE_BEDS = 2
    MIN_AVAILABLE_CHAIRS = 2
    LOOKBACK_DAYS = 90

    def forecast(
        self,
        hospital_id: UUID,
        target_date: date,
        capacity_records: list,
        upcoming_bookings: int = 0,
    ) -> CapacityForecast:
        if not capacity_records:
            return self._default_forecast(hospital_id, target_date, upcoming_bookings)

        if PANDAS_AVAILABLE:
            return self._forecast_with_pandas(hospital_id, target_date, capacity_records, upcoming_bookings)
        else:
            return self._forecast_without_pandas(hospital_id, target_date, capacity_records, upcoming_bookings)

    def _forecast_with_pandas(
        self,
        hospital_id: UUID,
        target_date: date,
        capacity_records: list,
        upcoming_bookings: int,
    ) -> CapacityForecast:
        import pandas as pd
        import numpy as np

        records = []
        for r in capacity_records:
            ts = getattr(r, 'last_updated_at', None) or getattr(r, 'created_at', None)
            if ts:
                records.append({
                    "day_of_week": ts.weekday(),
                    "available_beds": getattr(r, 'available_beds', 0),
                    "available_chairs": getattr(r, 'available_chairs', 0),
                })

        if not records:
            return self._default_forecast(hospital_id, target_date, upcoming_bookings)

        df = pd.DataFrame(records)
        target_dow = target_date.weekday()
        same_dow = df[df["day_of_week"] == target_dow]

        if len(same_dow) < 2:
            avg_beds = float(df["available_beds"].mean())
            avg_chairs = float(df["available_chairs"].mean())
            confidence = 0.40
        else:
            avg_beds = float(same_dow["available_beds"].mean())
            avg_chairs = float(same_dow["available_chairs"].mean())
            std_beds = float(same_dow["available_beds"].std())
            confidence = float(max(0.3, min(0.95, 1 - (std_beds / max(avg_beds, 1)))))

        net_beds = max(0, int(avg_beds) - upcoming_bookings)
        net_chairs = max(0, int(avg_chairs) - upcoming_bookings)
        available = (
            net_beds >= self.MIN_AVAILABLE_BEDS
            and net_chairs >= self.MIN_AVAILABLE_CHAIRS
        )

        return CapacityForecast(
            hospital_id=hospital_id,
            target_date=target_date,
            predicted_available_beds=net_beds,
            predicted_available_chairs=net_chairs,
            confidence=round(confidence, 2),
            is_likely_available=available,
            upcoming_bookings=upcoming_bookings,
            recommendation="Use this hospital" if available else "Consider an alternate hospital",
            data_points_used=len(records),
        )

    def _forecast_without_pandas(
        self,
        hospital_id: UUID,
        target_date: date,
        capacity_records: list,
        upcoming_bookings: int,
    ) -> CapacityForecast:
        """Fallback when pandas is unavailable."""
        target_dow = target_date.weekday()
        beds_list: list[int] = []
        chairs_list: list[int] = []

        for r in capacity_records:
            ts = getattr(r, 'last_updated_at', None) or getattr(r, 'created_at', None)
            if ts and ts.weekday() == target_dow:
                beds_list.append(getattr(r, 'available_beds', 0))
                chairs_list.append(getattr(r, 'available_chairs', 0))

        if not beds_list:
            beds_list = [getattr(r, 'available_beds', 5) for r in capacity_records]
            chairs_list = [getattr(r, 'available_chairs', 5) for r in capacity_records]

        avg_beds = sum(beds_list) / len(beds_list)
        avg_chairs = sum(chairs_list) / len(chairs_list)
        net_beds = max(0, int(avg_beds) - upcoming_bookings)
        net_chairs = max(0, int(avg_chairs) - upcoming_bookings)
        available = net_beds >= self.MIN_AVAILABLE_BEDS

        return CapacityForecast(
            hospital_id=hospital_id,
            target_date=target_date,
            predicted_available_beds=net_beds,
            predicted_available_chairs=net_chairs,
            confidence=0.50,
            is_likely_available=available,
            upcoming_bookings=upcoming_bookings,
            recommendation="Use this hospital" if available else "Consider alternate",
            data_points_used=len(capacity_records),
        )

    def _default_forecast(
        self,
        hospital_id: UUID,
        target_date: date,
        upcoming_bookings: int,
    ) -> CapacityForecast:
        """Conservative default when no historical data exists."""
        net_beds = max(0, 5 - upcoming_bookings)
        net_chairs = max(0, 5 - upcoming_bookings)
        return CapacityForecast(
            hospital_id=hospital_id,
            target_date=target_date,
            predicted_available_beds=net_beds,
            predicted_available_chairs=net_chairs,
            confidence=0.30,
            is_likely_available=net_beds >= self.MIN_AVAILABLE_BEDS,
            upcoming_bookings=upcoming_bookings,
            recommendation="Limited data — verify capacity directly with hospital",
            data_points_used=0,
        )

    def bulk_forecast(
        self,
        hospital_capacity_map: dict,   # {hospital_id: (hospital, records, upcoming_count)}
        target_date: date,
    ) -> dict[UUID, CapacityForecast]:
        """Forecast for multiple hospitals at once."""
        return {
            hospital_id: self.forecast(hospital_id, target_date, records, upcoming)
            for hospital_id, (_, records, upcoming) in hospital_capacity_map.items()
        }
