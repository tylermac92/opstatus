import time

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger: structlog.BoundLogger = structlog.get_logger()

router = APIRouter(tags=["Health"])


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Returns 200 if process is running",
    include_in_schema=True,
)
async def liveness() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Returns 200 if db is healthy",
    include_in_schema=True,
)
async def readiness() -> JSONResponse:
    start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "checks": {
                    "database": {
                        "status": "ok",
                        "duration_ms": duration_ms,
                    }
                },
            },
        )
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        await logger.awarning("Readiness check failed - database unreachable")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "checks": {
                    "database": {
                        "status": "error",
                        "duration_ms": duration_ms,
                    }
                },
            },
        )
