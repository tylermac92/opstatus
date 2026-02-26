import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.schemas.incidents import IncidentListResponse
from app.services import incidents as incident_service

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incidents",
    description="Returns all incidents with optional filtering",
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
