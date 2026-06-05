from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.enums import IncidentSeverity, IncidentStatus
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self):
        super().__init__(Incident)

    async def get_open(self, db: AsyncSession) -> list[Incident]:
        result = await db.execute(
            select(Incident)
            .where(Incident.status == IncidentStatus.open)
            .where(Incident.deleted_at.is_(None))
            .order_by(Incident.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_severity(self, db: AsyncSession, severity: IncidentSeverity) -> list[Incident]:
        result = await db.execute(
            select(Incident)
            .where(Incident.severity == severity)
            .where(Incident.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def resolve(self, db: AsyncSession, incident_id: UUID, resolver_id: UUID, resolution: str) -> None:
        await db.execute(
            update(Incident)
            .where(Incident.id == incident_id)
            .values(
                status=IncidentStatus.resolved,
                resolution=resolution,
                resolved_by=resolver_id,
                resolved_at=datetime.now(timezone.utc),
            )
        )
        await db.flush()

    async def log(
        self,
        db: AsyncSession,
        type: str,
        severity: str,
        title: str,
        description: str,
        component: str | None = None,
    ) -> Incident:
        from app.models.enums import IncidentType, IncidentSeverity
        incident = Incident(
            type=IncidentType(type),
            severity=IncidentSeverity(severity),
            title=title,
            description=description,
            component=component,
        )
        db.add(incident)
        await db.flush()
        await db.refresh(incident)
        return incident
