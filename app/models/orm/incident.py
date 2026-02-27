from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.orm.incident_update import IncidentUpdate
    from app.models.orm.service import Service

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.orm.base import Base
from app.models.orm.service import Service


# SQLAlchemy column defaults must be callables so the timestamp is evaluated
# at insert time rather than at module import time.
def utc_now() -> datetime:
    return datetime.now(UTC)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity),
        nullable=False,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus),
        nullable=False,
        # ORM-level default mirrors the service layer rule: all new incidents start
        # in "investigating". This acts as a safety net if the ORM is used directly.
        default=IncidentStatus.investigating,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # selectin loading for both relationships avoids N+1 queries when fetching
    # incidents. Updates are ordered ascending so the timeline reads chronologically.
    services: Mapped[list[Service]] = relationship(  # noqa: F821
        "Service",
        secondary="service_incidents",
        back_populates="incidents",
        lazy="selectin",
    )
    updates: Mapped[list[IncidentUpdate]] = relationship(  # noqa: F821
        "IncidentUpdate",
        back_populates="incident",
        lazy="selectin",
        order_by="IncidentUpdate.created_at",
    )
