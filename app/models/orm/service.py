from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.orm.incident import Incident

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.orm.base import Base


# SQLAlchemy column defaults must be callables, not values, so that the timestamp
# is evaluated at insert time rather than at module import time.
def utc_now() -> datetime:
    return datetime.now(UTC)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    # selectin loading issues a single IN query to load all related incidents
    # alongside the parent service, avoiding N+1 queries when listing services.
    incidents: Mapped[list[Incident]] = relationship(  # noqa: F821
        "Incident",
        secondary="service_incidents",
        back_populates="services",
        lazy="selectin",
    )
