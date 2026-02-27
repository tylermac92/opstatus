import time

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

logger: structlog.BoundLogger = structlog.get_logger()

router = APIRouter(tags=["Health"])


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Returns 200 if the process is running and responsive.",
)
async def liveness() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Returns 200 only if the database connection pool is healthy.",
)
async def readiness(
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    start = time.perf_counter()
    try:
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
        logger.warning("Readiness check failed - database unreachable")
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
