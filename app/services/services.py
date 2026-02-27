from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import services_total
from app.db.repositories.services import ServiceRepository
from app.models.enums import IncidentSeverity, IncidentStatus, ServiceStatus
from app.models.orm.incident import Incident
from app.models.orm.service import Service
from app.models.schemas.services import ServiceResponse


def derive_service_status(incidents: list[Incident]) -> ServiceStatus:
    # Only non-resolved incidents affect service health.
    active = [i for i in incidents if i.status != IncidentStatus.resolved]
    if not active:
        return ServiceStatus.operational
    # Outage takes precedence: a single critical or high incident drives the service
    # to "outage" regardless of any lower-severity incidents also being active.
    if any(
        i.severity in (IncidentSeverity.critical, IncidentSeverity.high) for i in active
    ):
        return ServiceStatus.outage
    # Only medium/low incidents remain active at this point.
    return ServiceStatus.degraded


def build_service_response(service: Service) -> ServiceResponse:
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        status=derive_service_status(service.incidents),
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


async def list_services(session: AsyncSession) -> list[ServiceResponse]:
    repo = ServiceRepository(session)
    services = await repo.get_all()
    return [build_service_response(s) for s in services]


async def create_service(
    session: AsyncSession,
    name: str,
    description: str | None = None,
) -> ServiceResponse:
    repo = ServiceRepository(session)
    service = await repo.create(name=name, description=description)
    services_total.inc()
    return build_service_response(service)


async def get_service(
    session: AsyncSession,
    service_id: uuid.UUID,
) -> ServiceResponse:
    repo = ServiceRepository(session)
    service = await repo.get_by_id(service_id)
    return build_service_response(service)


async def update_service(
    session: AsyncSession,
    service_id: uuid.UUID,
    name: str | None = None,
    description: str | None = None,
) -> ServiceResponse:
    repo = ServiceRepository(session)
    service = await repo.update(
        service_id=service_id,
        name=name,
        description=description,
    )
    return build_service_response(service)


async def delete_service(
    session: AsyncSession,
    service_id: uuid.UUID,
) -> None:
    repo = ServiceRepository(session)
    await repo.delete(service_id=service_id)
    services_total.dec()
