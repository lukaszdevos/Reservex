"""SQLAlchemy async session factory and dependency.

Layer: infrastructure
Usage: inject get_session() into FastAPI routes via Depends().
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from infrastructure.database.url import make_async_database_url

_DATABASE_URL: str = make_async_database_url(os.environ.get("DATABASE_URL", ""))

_engine = create_async_engine(_DATABASE_URL, echo=False) if _DATABASE_URL else None

async_session_factory: async_sessionmaker[AsyncSession] | None = (
    async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    if _engine is not None
    else None
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession; caller is responsible for commit/rollback."""
    if async_session_factory is None:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    async with async_session_factory() as session:
        yield session
