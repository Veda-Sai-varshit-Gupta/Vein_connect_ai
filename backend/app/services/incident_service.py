"""
Incident Service
================
Manages system anomalies, alerts, and operational incidents.
"""

from uuid import UUID
from datetime import datetime, timezone, time
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.repositories.incident_repo import IncidentRepository

incident_repo = IncidentRepository()


class IncidentService:

    async def get_open_incidents(self, db: AsyncSession) -> list[Incident]:
        return await incident_repo.get_open(db)

    async def get_stats(self, db: AsyncSession) -> dict:
        total = await incident_repo.count(db)
        open_count = await incident_repo.count(db, filters=[Incident.status == IncidentStatus.open])
        
        # Count open critical incidents
        critical_count = await incident_repo.count(db, filters=[
            Incident.severity == IncidentSeverity.critical,
            Incident.status == IncidentStatus.open
        ])
        
        # Count incidents resolved today in UTC time
        today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(tzinfo=timezone.utc)
        resolved_today = await incident_repo.count(db, filters=[
            Incident.status == IncidentStatus.resolved,
            Incident.resolved_at >= today_start
        ])
        
        return {
            "total": total,
            "open_count": open_count,
            "critical_count": critical_count,
            "resolved_today": resolved_today,
        }

    async def list_incidents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        severity: IncidentSeverity | None = None,
    ) -> list[Incident]:
        filters = []
        if severity:
            filters.append(Incident.severity == severity)
        return await incident_repo.get_all(db, skip=skip, limit=limit, filters=filters)

    async def resolve_incident(
        self,
        db: AsyncSession,
        incident_id: UUID,
        resolver_user_id: UUID,
        resolution: str,
    ) -> Incident:
        incident = await incident_repo.get_by_id(db, incident_id)
        if not incident:
            raise NotFoundException("Incident not found")
            
        if incident.status == IncidentStatus.resolved:
            raise BadRequestException("Incident is already resolved")

        await incident_repo.resolve(db, incident_id, resolver_user_id, resolution)
        
        # Retrieve the updated incident with relations loaded
        updated = await incident_repo.get_by_id(db, incident_id)
        return updated
