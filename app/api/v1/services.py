import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.schemas.services import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdate,
)
from app.services import services as service_layer

router = APIRouter(prefix="/services", tags=["Services"])


@router.get(
    "",
    response_model=ServiceListResponse,
    summary="List all services",
    description="Returns all tracked services with their derived health status.",
)
async def list_services(
    session: AsyncSession = Depends(get_session),
) -> ServiceListResponse:
    items = await service_layer.list_services(session)
    return ServiceListResponse(
        data=items,
        meta={"total": len(items)},
    )


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=201,
    summary="Create a service",
    description="Registers a new service for health and incident tracking.",
)
async def create_service(
    payload: ServiceCreate,
    session: AsyncSession = Depends(get_session),
) -> ServiceResponse:
    return await service_layer.create_service(
        session=session,
        name=payload.name,
        description=payload.description,
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get a service by ID",
    description="Returns a single service and its current derived health status.",
)
async def get_service(
    service_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ServiceResponse:
    return await service_layer.get_service(
        session=session,
        service_id=service_id,
    )


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update a service",
    description="Updates a service. Only provided fields are changed.",
)
async def update_service(
    service_id: uuid.UUID,
    payload: ServiceUpdate,
    session: AsyncSession = Depends(get_session),
) -> ServiceResponse:
    return await service_layer.update_service(
        session=session,
        service_id=service_id,
        name=payload.name,
        description=payload.description,
    )


@router.delete(
    "/{service_id}",
    status_code=204,
    summary="Delete a service",
    description="Deletes a service. The service must have no active incidents.",
)
async def delete_service(
    service_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service_layer.delete_service(
        session=session,
        service_id=service_id,
    )
    return Response(status_code=204)
