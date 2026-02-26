from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.schemas.services import ServiceListResponse
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
