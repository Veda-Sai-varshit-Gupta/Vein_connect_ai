"""
Incident Schemas
=================
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import IncidentSeverity, IncidentStatus, IncidentType


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    component: str | None
    status: IncidentStatus
    resolution: str | None
    resolved_at: datetime | None
    created_at: datetime


class ResolveIncidentRequest(BaseModel):
    resolution: str


class IncidentStatsResponse(BaseModel):
    total: int
    open_count: int
    critical_count: int
    resolved_today: int
