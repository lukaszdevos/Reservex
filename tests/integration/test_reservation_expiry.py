"""Integration tests for the reservation expiry worker."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from domain.ticketing.model import TicketStatus
from infrastructure.database.models import (
    OutboxMessageModel,
    ReservationModel,
    TicketEventModel,
    TicketModel,
)
from infrastructure.workers.reservation_expiry import release_expired_reservations


async def _cleanup_ticket(
    factory_obj: async_sessionmaker[AsyncSession], ticket_id: int
) -> None:
    async with factory_obj() as session:
        await session.execute(
            delete(TicketEventModel).where(TicketEventModel.ticket_id == ticket_id)
        )
        await session.execute(
            delete(OutboxMessageModel).where(
                OutboxMessageModel.payload["ticket_id"].as_integer() == ticket_id
            )
        )
        await session.execute(
            delete(ReservationModel).where(ReservationModel.ticket_id == ticket_id)
        )
        await session.execute(delete(TicketModel).where(TicketModel.id == ticket_id))
        await session.commit()


async def _insert_reserved_ticket(
    factory_obj: async_sessionmaker[AsyncSession],
    ticket_id: int,
    expires_at: datetime,
) -> None:
    now = datetime.now(UTC)
    async with factory_obj() as session:
        session.add(
            TicketModel(
                id=ticket_id,
                event_id=88,
                seat_number=f"E{ticket_id}",
                status="reserved",
                reserved_by=42,
                version=1,
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            ReservationModel(
                ticket_id=ticket_id,
                user_id=42,
                created_at=now - timedelta(minutes=5),
                expires_at=expires_at,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_expiry_worker_releases_expired_reservation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    ticket_id = 6001
    await _cleanup_ticket(session_factory, ticket_id)
    await _insert_reserved_ticket(
        session_factory,
        ticket_id,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    try:
        released = await release_expired_reservations(session_factory)

        assert released == 1
        async with session_factory() as session:
            repo = PostgresTicketRepository(session)
            ticket = await repo.get(ticket_id)
            assert ticket is not None
            assert ticket.status == TicketStatus.AVAILABLE
            assert ticket.reservation is None

            event_result = await session.execute(
                select(TicketEventModel).where(TicketEventModel.ticket_id == ticket_id)
            )
            event = event_result.scalar_one()
            assert event.event_type == "ticket.released"
            assert event.payload["reason"] == "timeout"

            outbox_result = await session.execute(
                select(OutboxMessageModel).where(
                    OutboxMessageModel.event_type == "ticket.released"
                )
            )
            outbox_message = outbox_result.scalar_one()
            assert outbox_message.payload["ticket_id"] == ticket_id
    finally:
        await _cleanup_ticket(session_factory, ticket_id)


@pytest.mark.asyncio
async def test_expiry_worker_leaves_active_reservation_untouched(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    ticket_id = 6002
    await _cleanup_ticket(session_factory, ticket_id)
    await _insert_reserved_ticket(
        session_factory,
        ticket_id,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    try:
        released = await release_expired_reservations(session_factory)

        assert released == 0
        async with session_factory() as session:
            repo = PostgresTicketRepository(session)
            ticket = await repo.get(ticket_id)
            assert ticket is not None
            assert ticket.status == TicketStatus.RESERVED
            assert ticket.reservation is not None
    finally:
        await _cleanup_ticket(session_factory, ticket_id)
