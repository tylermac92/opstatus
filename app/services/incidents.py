from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.incidents import IncidentRepository
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.orm.incident import Incident
from app.models.schemas.incidents import IncidentResponse, IncidentUpdateResponse


def build_incident_response(incident: Incident) -> IncidentResponse:
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        body=incident.body,
        severity=incident.severity,
        status=incident.status,
        service_ids=[s.id for s in incident.services],
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        resolved_at=incident.resolved_at,
        updates=[
            IncidentUpdateResponse(
                id=u.id,
                incident_id=u.incident_id,
                message=u.message,
                status=u.status,
                created_at=u.created_at,
            )
            for u in incident.updates
        ],
    )


async def list_incidents(
    session: AsyncSession,
    status: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    service_id: uuid.UUID | None = None,
) -> list[IncidentResponse]:
    repo = IncidentRepository(session)
    incidents = await repo.get_all(
        status=status,
        severity=severity,
        service_id=service_id,
    )
    return [build_incident_response(i) for i in incidents]


async def create_incident(
    session: AsyncSession,
    title: str,
    severity: IncidentSeverity,
    service_ids: list[uuid.UUID],
    body: str | None = None,
) -> IncidentResponse:
    repo = IncidentRepository(session)
    incident = await repo.create(
        title=title,
        severity=severity,
        service_ids=service_ids,
        body=body,
    )
    return build_incident_response(incident)
