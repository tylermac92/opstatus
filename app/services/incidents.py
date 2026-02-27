from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.metrics import active_incidents_total
from app.db.repositories.incident_updates import IncidentUpdateRepository
from app.db.repositories.incidents import IncidentRepository
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.orm.incident import Incident
from app.models.schemas.incidents import IncidentResponse, IncidentUpdateResponse


async def _sync_incident_metrics(session: AsyncSession) -> None:
    # Re-query the full incident list and recompute gauges from scratch.
    # This is simpler than tracking incremental changes and guarantees the
    # gauges can never drift out of sync after any create/update/resolve operation.
    repo = IncidentRepository(session)
    all_incidents = await repo.get_all()
    active = [i for i in all_incidents if i.status != IncidentStatus.resolved]

    for severity in IncidentSeverity:
        count = sum(1 for i in active if i.severity == severity)
        active_incidents_total.labels(severity=severity.value).set(count)


# Maps each status to the set of statuses it can legally transition to.
# The lifecycle is strictly forward-only; "resolved" maps to an empty set
# because it is a terminal state — no further transitions are permitted.
VALID_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.investigating: {IncidentStatus.identified},
    IncidentStatus.identified: {IncidentStatus.monitoring},
    IncidentStatus.monitoring: {IncidentStatus.resolved},
    IncidentStatus.resolved: set(),
}


def validate_status_transition(
    current: IncidentStatus,
    new: IncidentStatus,
) -> None:
    if new not in VALID_TRANSITIONS[current]:
        raise ConflictError(
            f"Invalid status transition from '{current}' to '{new}'. "
            f"Valid transitions from '{current}': "
            f"{[s.value for s in VALID_TRANSITIONS[current]] or 'none'}."
        )


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
    await _sync_incident_metrics(session)
    return build_incident_response(incident)


async def get_incident(
    session: AsyncSession,
    incident_id: uuid.UUID,
) -> IncidentResponse:
    repo = IncidentRepository(session)
    incident = await repo.get_by_id(incident_id)
    return build_incident_response(incident)


async def update_incident(
    session: AsyncSession,
    incident_id: uuid.UUID,
    title: str | None = None,
    body: str | None = None,
    severity: IncidentSeverity | None = None,
    status: IncidentStatus | None = None,
) -> IncidentResponse:
    repo = IncidentRepository(session)
    incident = await repo.get_by_id(incident_id)

    if status is not None:
        validate_status_transition(incident.status, status)
        # Resolving via PATCH delegates to the dedicated resolve path so that
        # resolved_at is stamped correctly, even without calling /resolve directly.
        if status == IncidentStatus.resolved:
            incident = await repo.resolve(incident_id)
            return build_incident_response(incident)

    incident = await repo.update(
        incident_id=incident_id,
        title=title,
        body=body,
        severity=severity,
        status=status,
    )
    await _sync_incident_metrics(session)
    return build_incident_response(incident)


async def append_incident_update(
    session: AsyncSession,
    incident_id: uuid.UUID,
    message: str,
    status: IncidentStatus,
) -> IncidentUpdateResponse:
    repo = IncidentUpdateRepository(session)
    update = await repo.create(
        incident_id=incident_id,
        message=message,
        status=status,
    )
    return IncidentUpdateResponse(
        id=update.id,
        incident_id=update.incident_id,
        message=update.message,
        status=update.status,
        created_at=update.created_at,
    )


async def resolve_incident(
    session: AsyncSession,
    incident_id: uuid.UUID,
) -> IncidentResponse:
    # Local import avoids a circular dependency: IncidentUpdate ORM imports Incident
    # which would otherwise create an import cycle at module load time.
    from app.models.orm.incident_update import IncidentUpdate as IncidentUpdateORM

    repo = IncidentRepository(session)
    incident = await repo.get_by_id(incident_id)

    if incident.status == IncidentStatus.resolved:
        raise ConflictError(f"Incident '{incident_id}' is already resolved.")

    incident = await repo.resolve(incident_id)

    final_update = IncidentUpdateORM(
        incident_id=incident_id,
        message="Incident resolved.",
        status=IncidentStatus.resolved,
    )
    session.add(final_update)
    await session.commit()

    await _sync_incident_metrics(session)

    incident = await repo.get_by_id(incident_id)
    return build_incident_response(incident)
