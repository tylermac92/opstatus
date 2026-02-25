from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title="opstatus",
    version="0.1.0",
    description="Service Health & Incident Tracking API",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)
