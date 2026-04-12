"""Integration test fixtures.

Starts real Postgres and Redis containers once per session via testcontainers.
Each test gets a fresh AsyncSession wrapped in a transaction that is rolled
back after the test — no data bleeds between tests.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from typing import Any

import factory
import pytest
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from domain.ticketing.model import Ticket, TicketStatus
from infrastructure.database.models import Base, TicketModel

# ---------------------------------------------------------------------------
# Containers — started once per session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16") as container:
        yield container


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:7") as container:
        yield container


@pytest.fixture(scope="session")
def pg_url(postgres_container: PostgresContainer) -> str:
    return postgres_container.get_connection_url(driver="asyncpg")


@pytest.fixture(scope="session")
def redis_url(redis_container: RedisContainer) -> str:
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


# ---------------------------------------------------------------------------
# Schema setup — run once per session via asyncio.run() in a sync fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _setup_db(pg_url: str) -> Generator[None, None, None]:
    """Create all tables using Base.metadata.create_all (faster than Alembic)."""

    async def _create() -> None:
        engine = create_async_engine(pg_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_create())
    yield

    async def _drop() -> None:
        engine = create_async_engine(pg_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_drop())


# ---------------------------------------------------------------------------
# Per-test session — wrapped in a rolled-back transaction
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session(
    pg_url: str, _setup_db: None
) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession in a transaction rolled back after each test."""
    engine = create_async_engine(pg_url)
    async with engine.connect() as conn:
        await conn.begin()
        async with AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint"
        ) as session:
            yield session
            await session.rollback()
    await engine.dispose()


@pytest.fixture
async def session_factory(
    pg_url: str, _setup_db: None
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Yield a sessionmaker for tests that need independent concurrent sessions."""
    engine = create_async_engine(pg_url)
    factory_obj: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )
    yield factory_obj
    await engine.dispose()


# ---------------------------------------------------------------------------
# Redis client — flushed after each test
# ---------------------------------------------------------------------------


@pytest.fixture
async def redis_client(redis_url: str) -> AsyncGenerator[aioredis.Redis, None]:  # type: ignore[type-arg]
    client: aioredis.Redis = aioredis.from_url(redis_url)  # type: ignore[type-arg]
    yield client
    await client.flushdb()
    await client.aclose()


# ---------------------------------------------------------------------------
# ticket_factory — inserts Ticket rows, respects the rollback session
# ---------------------------------------------------------------------------


class TicketFactory(factory.Factory):
    """factory-boy factory for the Ticket domain object."""

    class Meta:
        model = Ticket

    id = factory.Sequence(lambda n: n + 1)
    event_id = 1
    seat_number = factory.Sequence(lambda n: f"A{n}")
    status = TicketStatus.AVAILABLE
    version = 0
    reserved_by = None
    reservation = None


@pytest.fixture
def ticket_factory(db_session: AsyncSession) -> Any:
    """Return an async callable that inserts a Ticket into the test DB."""

    async def _create(**kwargs: Any) -> Ticket:
        ticket: Ticket = TicketFactory.build(**kwargs)
        model = TicketModel(
            id=ticket.id,
            event_id=ticket.event_id,
            seat_number=ticket.seat_number,
            status=ticket.status.value,
            version=ticket.version,
            reserved_by=ticket.reserved_by,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(model)
        await db_session.flush()
        return ticket

    return _create
