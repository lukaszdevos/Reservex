"""Alembic environment - async mode with DATABASE_URL override."""

import asyncio
import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_engine_from_config

from infrastructure.database.models import Base
from infrastructure.database.url import make_async_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")
_CONNECT_ATTEMPTS = int(os.environ.get("MIGRATION_DB_CONNECT_ATTEMPTS", "6"))
_CONNECT_RETRY_SECONDS = float(
    os.environ.get("MIGRATION_DB_CONNECT_RETRY_SECONDS", "5")
)
_CONNECT_TIMEOUT_SECONDS = float(
    os.environ.get("MIGRATION_DB_CONNECT_TIMEOUT_SECONDS", "10")
)

# Override URL from environment variable when present
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    config.set_main_option("sqlalchemy.url", make_async_database_url(_db_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
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
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"timeout": _CONNECT_TIMEOUT_SECONDS},
    )
    try:
        for attempt in range(1, _CONNECT_ATTEMPTS + 1):
            try:
                async with connectable.connect() as connection:
                    await connection.run_sync(do_run_migrations)
                return
            except (OSError, OperationalError, TimeoutError) as exc:
                if attempt == _CONNECT_ATTEMPTS:
                    raise
                logger.warning(
                    "database unavailable for migrations; retrying "
                    "attempt=%s max_attempts=%s error=%s",
                    attempt,
                    _CONNECT_ATTEMPTS,
                    type(exc).__name__,
                )
                await asyncio.sleep(_CONNECT_RETRY_SECONDS)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
