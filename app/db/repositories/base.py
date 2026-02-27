from sqlalchemy.ext.asyncio import AsyncSession


# All repositories accept an already-open AsyncSession so that the caller
# (typically a service layer function) controls the transaction boundary.
class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
