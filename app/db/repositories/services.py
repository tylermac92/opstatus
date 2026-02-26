from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.db.repositories.base import BaseRepository
from app.models.orm.service import Service


class ServiceRepository(BaseRepository):
    async def get_by_id(self, service_id: uuid.UUID) -> Service:
        result = await self.session.get(Service, service_id)
        if result is None:
            raise NotFoundError(f"Service with id '{service_id}' does not exist.")
        return result

    async def get_all(self) -> list[Service]:
        result = await self.session.execute(select(Service))
        return list(result.scalars().all())

    async def create(self, name: str, description: str | None = None) -> Service:
        service = Service(name=name.strip(), description=description)
        self.session.add(service)
        try:
            await self.session.commit()
            await self.session.refresh(service)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(f"A service with name '{name}' already exists.")
        return service

    async def update(
        self,
        service_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Service:
        service = await self.get_by_id(service_id)
        if name is not None:
            service.name = name.strip()
        if description is not None:
            service.description = description
        try:
            await self.session.commit()
            await self.session.refresh(service)
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(f"A service with name '{name}' already exists.")
        return service

    async def delete(self, service_id: uuid.UUID) -> None:
        service = await self.get_by_id(service_id)
        active_incidents = [i for i in service.incidents if i.status != "resolved"]
        if active_incidents:
            raise ConflictError(
                f"Service '{service.name}' has active incidents and cannot be deleted."
            )
        await self.session.delete(service)
        await self.session.commit()
