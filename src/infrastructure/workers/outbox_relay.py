"""Transactional outbox relay worker.

Layer: infrastructure/workers
Polls outbox_messages for unpublished rows and publishes to Redis Streams.
Runs as a long-lived asyncio.Task started in the FastAPI lifespan.
"""

from __future__ import annotations

import asyncio
import json

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure.database.models import OutboxMessageModel
from infrastructure.observability.metrics import OUTBOX_QUEUE_DEPTH

logger = structlog.get_logger(__name__)


class RedisStreamEventBus:
    """Publishes outbox messages to Redis Streams.

    Stream key pattern: ``events:{event_type}``
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def publish(self, message: OutboxMessageModel) -> None:
        await self._redis.xadd(
            f"events:{message.event_type}",
            {"id": str(message.id), "payload": json.dumps(message.payload)},
        )


async def outbox_relay_worker(
    session_factory: async_sessionmaker[AsyncSession],
    redis_client: aioredis.Redis,
) -> None:
    """Poll outbox and publish unpublished messages to Redis Streams.

    Uses WITH FOR UPDATE SKIP LOCKED so multiple app instances are safe.
    Loops forever; exits cleanly on CancelledError.
    """
    event_bus = RedisStreamEventBus(redis_client)
    while True:
        try:
            async with session_factory() as session:
                result = await session.execute(
                    select(OutboxMessageModel)
                    .where(OutboxMessageModel.published == False)  # noqa: E712
                    .limit(100)
                    .with_for_update(skip_locked=True)
                )
                msgs = list(result.scalars().all())
                if not msgs:
                    OUTBOX_QUEUE_DEPTH.set(0)
                    await asyncio.sleep(0.1)
                    continue
                OUTBOX_QUEUE_DEPTH.set(len(msgs))
                await asyncio.gather(*[event_bus.publish(m) for m in msgs])
                for m in msgs:
                    m.published = True
                await session.commit()
                logger.info("outbox_relay_published", count=len(msgs))
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("outbox_relay_error", error=str(exc))
            await asyncio.sleep(1.0)
