from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Exposes application metrics in standard Prometheus text format.",
    response_class=PlainTextResponse,
    include_in_schema=True,
)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
