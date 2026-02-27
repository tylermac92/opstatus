import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.schemas.incidents import (
    IncidentAppendUpdate,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
    IncidentUpdateResponse,
)
from app.services import incidents as incident_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incidents",
    description=(
        "Returns all incidents with optional filtering by status, severity, or service."
    ),
)
async def list_incidents(
    status: IncidentStatus | None = Query(
        None, description="Filter by incident status"
    ),
    severity: IncidentSeverity | None = Query(
        None, description="Filter by incident severity"
    ),
    service_id: uuid.UUID | None = Query(
        None, description="Filter by affected service ID"
    ),
    session: AsyncSession = Depends(get_session),
) -> IncidentListResponse:
    items = await incident_service.list_incidents(
        session=session,
        status=status,
        severity=severity,
        service_id=service_id,
    )
    return IncidentListResponse(
        data=items,
        meta={"total": len(items)},
    )


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=201,
    summary="Create an incident",
    description=(
        "Opens a new incident against one or more services. "
        "Initial status is always investigating."
    ),
)
async def create_incident(
    payload: IncidentCreate,
    session: AsyncSession = Depends(get_session),
) -> IncidentResponse:
    return await incident_service.create_incident(
        session=session,
        title=payload.title,
        severity=payload.severity,
        service_ids=payload.service_ids,
        body=payload.body,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get an incident by ID",
    description="Returns a single incident with its full update timeline.",
)
async def get_incident(
    incident_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> IncidentResponse:
    return await incident_service.get_incident(
        session=session,
        incident_id=incident_id,
    )


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update an incident",
    description="Updates incident fields or advances its status through the lifecycle.",
)
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    session: AsyncSession = Depends(get_session),
) -> IncidentResponse:
    return await incident_service.update_incident(
        session=session,
        incident_id=incident_id,
        title=payload.title,
        body=payload.body,
        severity=payload.severity,
        status=payload.status,
    )


@router.post(
    "/{incident_id}/updates",
    response_model=IncidentUpdateResponse,
    status_code=201,
    summary="Append an incident update",
    description=(
        "Appends a new status update to the incident timeline. "
        "Cannot be edited or deleted."
    ),
)
async def append_incident_update(
    incident_id: uuid.UUID,
    payload: IncidentAppendUpdate,
    session: AsyncSession = Depends(get_session),
) -> IncidentUpdateResponse:
    return await incident_service.append_incident_update(
        session=session,
        incident_id=incident_id,
        message=payload.message,
        status=payload.status,
    )


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
    summary="Resolve an incident",
    description=(
        "Resolves the incident, sets resolved_at timestamp, "
        "and appends a final update to the timeline."
    ),
)
async def resolve_incident(
    incident_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> IncidentResponse:
    return await incident_service.resolve_incident(
        session=session,
        incident_id=incident_id,
    )
