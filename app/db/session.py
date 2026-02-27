from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

engine = create_async_engine(
    settings.database_url,
    # Log all SQL statements in development to aid debugging.
    echo=settings.app_env == "development",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    # Keep ORM objects accessible after commit without issuing extra SELECT queries.
    # Without this, accessing attributes after commit would trigger lazy loads.
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except SQLAlchemyError as e:
        raise ServiceUnavailableError(f"Database connection error: {str(e)}") from e
