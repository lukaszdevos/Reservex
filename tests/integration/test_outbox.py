"""Integration tests - transactional outbox relay (P5.5).

Inserts an unpublished outbox message, starts the relay worker as a task,
then asserts the message was published to Redis Streams and marked published.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

import pytest
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure.database.models import OutboxMessageModel
from infrastructure.workers.outbox_relay import outbox_relay_worker


@pytest.mark.asyncio
async def test_relay_publishes_message_to_redis_streams(
    session_factory: async_sessionmaker[AsyncSession],
    redis_client: aioredis.Redis,  # type: ignore[type-arg]
) -> None:
    """Relay picks up an unpublished message and writes it to a Redis Stream."""
    # Insert an unpublished outbox message
    async with session_factory() as session:
        session.add(
            OutboxMessageModel(
                event_type="ticket.reserved",
                payload={"ticket_id": 1, "user_id": 42},
                published=False,
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()

    # Start the relay worker and give it time to process
    task = asyncio.create_task(outbox_relay_worker(session_factory, redis_client))
    await asyncio.sleep(0.5)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    # Assert: message published to Redis Stream
    messages = await redis_client.xrange("events:ticket.reserved", "-", "+")
    assert len(messages) >= 1
    _, fields = messages[0]
    payload = json.loads(fields[b"payload"])
    assert payload["ticket_id"] == 1

    # Assert: marked published=True in DB
    async with session_factory() as session:
        result = await session.execute(
            select(OutboxMessageModel).where(
                OutboxMessageModel.event_type == "ticket.reserved"
            )
        )
        msg = result.scalar_one()
    assert msg.published is True


@pytest.mark.asyncio
async def test_relay_processes_multiple_messages(
    session_factory: async_sessionmaker[AsyncSession],
    redis_client: aioredis.Redis,  # type: ignore[type-arg]
) -> None:
    """Relay processes all unpublished messages in one batch."""
    async with session_factory() as session:
        for i in range(5):
            session.add(
                OutboxMessageModel(
                    event_type="ticket.confirmed",
                    payload={"ticket_id": i},
                    published=False,
                    created_at=datetime.now(UTC),
                )
            )
        await session.commit()

    task = asyncio.create_task(outbox_relay_worker(session_factory, redis_client))
    await asyncio.sleep(0.5)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    messages = await redis_client.xrange("events:ticket.confirmed", "-", "+")
    assert len(messages) == 5

    async with session_factory() as session:
        result = await session.execute(
            select(OutboxMessageModel).where(
                OutboxMessageModel.event_type == "ticket.confirmed"
            )
        )
        all_msgs = result.scalars().all()
    assert all(m.published for m in all_msgs)
