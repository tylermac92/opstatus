from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.orm.incident import Incident

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.enums import IncidentStatus
from app.models.orm.base import Base


# SQLAlchemy column defaults must be callables so the timestamp is evaluated
# at insert time rather than at module import time.
def utc_now() -> datetime:
    return datetime.now(UTC)


# Incident updates are append-only: there are no API endpoints to edit or delete them.
# This preserves an accurate audit trail of the incident response timeline.
class IncidentUpdate(Base):
    __tablename__ = "incident_updates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    # CASCADE so updates are removed automatically when the parent incident is deleted.
    incident_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    incident: Mapped[Incident] = relationship(  # noqa: F821
        "Incident",
        back_populates="updates",
    )
