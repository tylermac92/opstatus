from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.error_handlers import (
    conflict_handler,
    not_found_handler,
    service_unavailable_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.core.logging import configure_logging
from app.core.middleware import RequestMiddleware


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

app.add_middleware(RequestMiddleware)

app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(ConflictError, conflict_handler)
app.add_exception_handler(ServiceUnavailableError, service_unavailable_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
