from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_session
from app.main import app
from app.models.orm import Base

# Tests run against an in-memory SQLite database; no external services are required.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Create a fresh schema for every test and drop it on teardown so tests
    # are fully isolated from one another regardless of execution order.
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Replace the production get_session dependency with one that yields the
    # test session, so all requests in a test share the same transaction scope.
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def broken_db_client() -> AsyncGenerator[AsyncClient, None]:
    # Provides a client wired to a mock session whose execute method always raises,
    # simulating a database connectivity failure for error-path tests.
    from unittest.mock import AsyncMock, MagicMock

    from app.db.session import get_session
    from app.main import app

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(side_effect=Exception("DB connection failed"))

    async def override_broken_session() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session

    app.dependency_overrides[get_session] = override_broken_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
