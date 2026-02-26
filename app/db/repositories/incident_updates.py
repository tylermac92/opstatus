from __future__ import annotations

import uuid
from datetime import UTC

from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError
from app.db.repositories.base import BaseRepository
from app.models.enums import IncidentStatus
from app.models.orm.incident import Incident
from app.models.orm.incident_update import IncidentUpdate


class IncidentUpdateRepository(BaseRepository):
    async def get_by_incident_id(self, incident_id: uuid.UUID) -> list[IncidentUpdate]:
        result = await self.session.execute(
            select(IncidentUpdate)
            .where(IncidentUpdate.incident_id == incident_id)
            .order_by(IncidentUpdate.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        incident_id: uuid.UUID,
        message: str,
        status: IncidentStatus,
    ) -> IncidentUpdate:
        incident = await self.session.get(Incident, incident_id)
        if incident is None:
            raise NotFoundError(f"Incident with id '{incident_id}' does not exist.")
        if incident.status == IncidentStatus.resolved:
            raise ConflictError(
                f"Incident '{incident_id}' is already resolved and cannot be updated."
            )

        update = IncidentUpdate(
            incident_id=incident_id,
            message=message,
            status=status,
        )
        self.session.add(update)

        # Refresh the parent incident's updated_at timestamp
        from datetime import datetime

        incident.updated_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(update)
        return update
