import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import IncidentSeverity, IncidentStatus


class IncidentUpdateResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    message: str
    status: IncidentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: str | None
    severity: IncidentSeverity
    status: IncidentStatus
    service_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    updates: list[IncidentUpdateResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Brief description of the incident",
    )
    body: str | None = Field(
        None, description="Detailed incident description, supports Markdown"
    )
    severity: IncidentSeverity = Field(..., description="Incident severity level")
    service_ids: list[uuid.UUID] = Field(
        ..., min_length=1, description="One or more affected service IDs"
    )


class IncidentUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    body: str | None = Field(None)
    severity: IncidentSeverity | None = Field(None)
    status: IncidentStatus | None = Field(None)


class IncidentAppendUpdate(BaseModel):
    message: str = Field(..., min_length=1, description="Status update message")
    status: IncidentStatus = Field(
        ..., description="The incident status at time of this update"
    )


class IncidentListResponse(BaseModel):
    data: list[IncidentResponse]
    meta: dict[str, int]
