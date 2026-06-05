"""
Reward Schemas
===============
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import RewardType


class RewardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    donor_id: UUID
    donation_id: UUID | None
    type: RewardType
    points: int
    description: str | None
    created_at: datetime


class RewardSummaryResponse(BaseModel):
    donor_id: UUID
    total_points: int
    tier: str
    tier_level: int
    points_to_next_tier: int
    next_tier: str | None
    breakdown: dict[str, int]


class ConvertPointsRequest(BaseModel):
    points: int


class ManualAwardRequest(BaseModel):
    donor_id: UUID
    type: RewardType
    points: int
    description: str


class LeaderboardEntry(BaseModel):
    rank: int
    donor_id: UUID
    donor_name: str
    total_points: int
    tier: str
    total_donations: int
