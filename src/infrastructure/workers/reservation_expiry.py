"""Reservation expiry worker.

Layer: infrastructure/workers
Finds expired reservations and releases their tickets through the aggregate.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from domain.ticketing.model import TicketStatus
from infrastructure.database.models import ReservationModel, TicketModel

logger = structlog.get_logger(__name__)


async def release_expired_reservations(
    session_factory: async_sessionmaker[AsyncSession],
    batch_size: int = 100,
) -> int:
    """Release one batch of expired reservations and return the release count."""
    async with session_factory() as session:
        result = await session.execute(
            select(ReservationModel.ticket_id)
            .join(TicketModel, TicketModel.id == ReservationModel.ticket_id)
            .where(TicketModel.status == TicketStatus.RESERVED.value)
            .where(ReservationModel.expires_at <= datetime.now(UTC))
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        ticket_ids = list(result.scalars().all())
        repo = PostgresTicketRepository(session)
        released = 0

        for ticket_id in ticket_ids:
            ticket = await repo.get_for_update(ticket_id)
            if (
                ticket is not None
                and ticket.status == TicketStatus.RESERVED
                and ticket.reservation is not None
                and ticket.reservation.is_expired()
            ):
                ticket.release(reason="timeout")
                await repo.add(ticket)
                released += 1

        await session.commit()
        return released


async def reservation_expiry_worker(
    session_factory: async_sessionmaker[AsyncSession],
    interval_seconds: float = 1.0,
    batch_size: int = 100,
) -> None:
    """Run reservation expiry checks until cancelled."""
    while True:
        try:
            released = await release_expired_reservations(
                session_factory,
                batch_size=batch_size,
            )
            if released:
                logger.info("expired_reservations_released", count=released)
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("reservation_expiry_error", error=str(exc))
            await asyncio.sleep(interval_seconds)
