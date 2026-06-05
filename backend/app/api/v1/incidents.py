"""
Incident Routes
================
GET    /incidents/             list all (admin)
GET    /incidents/open         open incidents
GET    /incidents/stats        summary stats
GET    /incidents/{id}
POST   /incidents/{id}/resolve
"""

from uuid import UUID
from fastapi import APIRouter, Query
from app.dependencies import CurrentUser, DbSession, Pagination
from app.core.permissions import require_role
from app.models.enums import IncidentSeverity, UserRole
from app.schemas.incident import IncidentResponse, IncidentStatsResponse, ResolveIncidentRequest
from app.services.incident_service import IncidentService

router = APIRouter()
incident_service = IncidentService()


@router.get("/open", response_model=list[IncidentResponse])
async def get_open_incidents(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.admin, UserRole.coordinator])
    return await incident_service.get_open_incidents(db)


@router.get("/stats", response_model=IncidentStatsResponse)
async def get_incident_stats(current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.admin])
    return await incident_service.get_stats(db)


@router.get("/", response_model=list[IncidentResponse])
async def list_incidents(
    current_user: CurrentUser,
    db: DbSession,
    pagination: Pagination,
    severity: IncidentSeverity | None = Query(None),
):
    require_role(current_user, [UserRole.admin])
    return await incident_service.list_incidents(
        db, skip=pagination.offset, limit=pagination.page_size, severity=severity
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, current_user: CurrentUser, db: DbSession):
    require_role(current_user, [UserRole.admin])
    from app.repositories.incident_repo import IncidentRepository
    incident = await IncidentRepository().get_by_id(db, incident_id)
    if not incident:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Incident", str(incident_id))
    return incident


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: UUID,
    data: ResolveIncidentRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    require_role(current_user, [UserRole.admin])
    return await incident_service.resolve_incident(db, incident_id, current_user.id, data.resolution)
