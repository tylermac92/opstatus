from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.db.repositories.base import BaseRepository
from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.orm.incident import Incident


class IncidentRepository(BaseRepository):
    async def get_by_id(self, incident_id: uuid.UUID) -> Incident:
        # Expire all cached ORM state so SQLAlchemy re-fetches from the DB.
        # Without this, stale in-memory data can be returned after a mutation
        # performed earlier in the same session (e.g. resolve then get_by_id).
        self.session.expire_all()
        result = await self.session.execute(
            select(Incident)
            .options(selectinload(Incident.updates), selectinload(Incident.services))
            .where(Incident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident is None:
            raise NotFoundError(f"Incident with id '{incident_id}' does not exist.")
        return incident

    async def get_all(
        self,
        status: IncidentStatus | None = None,
        severity: IncidentSeverity | None = None,
        service_id: uuid.UUID | None = None,
    ) -> list[Incident]:
        query = select(Incident).order_by(Incident.created_at.desc())

        if status is not None:
            query = query.where(Incident.status == status)
        if severity is not None:
            query = query.where(Incident.severity == severity)
        if service_id is not None:
            query = query.where(Incident.services.any(id=service_id))

        result = await self.session.execute(query)
        # .unique() deduplicates rows that can be multiplied by selectinload joins
        # when an incident is linked to multiple services.
        return list(result.scalars().unique().all())

    async def create(
        self,
        title: str,
        severity: IncidentSeverity,
        service_ids: list[uuid.UUID],
        body: str | None = None,
    ) -> Incident:
        # Local import breaks the circular dependency between IncidentRepository
        # and ServiceRepository (both extend BaseRepository in the same package).
        from app.db.repositories.services import ServiceRepository

        service_repo = ServiceRepository(self.session)
        services = [await service_repo.get_by_id(sid) for sid in service_ids]

        incident = Incident(
            title=title,
            severity=severity,
            body=body,
            status=IncidentStatus.investigating,
        )
        incident.services = services
        self.session.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def update(
        self,
        incident_id: uuid.UUID,
        title: str | None = None,
        body: str | None = None,
        severity: IncidentSeverity | None = None,
        status: IncidentStatus | None = None,
    ) -> Incident:
        incident = await self.get_by_id(incident_id)

        if title is not None:
            incident.title = title
        if body is not None:
            incident.body = body
        if severity is not None:
            incident.severity = severity
        if status is not None:
            incident.status = status

        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def resolve(self, incident_id: uuid.UUID) -> Incident:
        incident = await self.get_by_id(incident_id)
        incident.status = IncidentStatus.resolved
        incident.resolved_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident
