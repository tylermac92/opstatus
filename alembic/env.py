import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.core.config import settings
from app.models.orm import Base

config = context.config
# Override the URL from alembic.ini at runtime so that the same DATABASE_URL
# environment variable used by the application is also used for migrations.
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at the application's ORM metadata so autogenerate can diff
# the schema against the current database state.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # Offline mode generates SQL scripts without a live DB connection,
    # useful for reviewing or applying migrations manually.
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    # Synchronous callback passed to run_sync; Alembic's context.configure
    # requires a sync connection, so the async driver hands off here.
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
