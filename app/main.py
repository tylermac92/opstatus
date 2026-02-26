from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger = structlog.get_logger()
    await logger.ainfo("Application starting up", env=settings.app_env)
    yield
    await logger.ainfo("Application shutting down")


app = FastAPI(
    title="opstatus",
    version="0.1.0",
    description="Service Health & Incident Tracking API",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)
