import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ServiceStatus


class ServiceBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Human-readable service name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description of the service"
    )


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=100, description="Human-readable service name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description of the service"
    )


class ServiceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: ServiceStatus
    created_at: datetime
    updated_at: datetime

    # from_attributes=True allows Pydantic to read values directly from SQLAlchemy
    # ORM model attributes instead of requiring a plain dict.
    model_config = {"from_attributes": True}


class ServiceListResponse(BaseModel):
    data: list[ServiceResponse]
    meta: dict[str, int]
