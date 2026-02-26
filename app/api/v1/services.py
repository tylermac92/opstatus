from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.schemas.services import (
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
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
