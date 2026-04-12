"""Integration tests - reservation happy path (P5.2).

Tests run against a real Postgres container. Each test is wrapped in a
transaction that rolls back automatically after the test.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from domain.ticketing.model import TicketStatus
from infrastructure.database.models import OutboxMessageModel, TicketEventModel
from use_cases.request_objects import ReserveTicketRequest
from use_cases.reserve_ticket import ReserveTicketUseCase


@pytest.mark.asyncio
async def test_reserve_ticket_happy_path(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """Reserve an available ticket - status becomes RESERVED in DB."""
    await ticket_factory(id=1, event_id=1, seat_number="A1")

    repo = PostgresTicketRepository(db_session)
    uc = ReserveTicketUseCase(ticket_repo=repo)
    req = ReserveTicketRequest(ticket_id=1, user_id=42, idempotency_key="key-1")

    response = await uc.execute(req)

    assert response.success is True
    assert response.data is not None
    assert response.data["ticket_id"] == 1
    assert response.data["reservation_id"] != 0


@pytest.mark.asyncio
async def test_version_increments_after_reserve(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """Version bumps from 0 to 1 after a successful reserve."""
    await ticket_factory(id=2, event_id=1, seat_number="A2")

    repo = PostgresTicketRepository(db_session)
    uc = ReserveTicketUseCase(ticket_repo=repo)
    await uc.execute(ReserveTicketRequest(ticket_id=2, user_id=1, idempotency_key="k2"))

    ticket = await repo.get(2)
    assert ticket is not None
    assert ticket.version == 1
    assert ticket.status == TicketStatus.RESERVED


@pytest.mark.asyncio
async def test_reservation_expires_at_set_to_5_minutes(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """expires_at is approximately now + 5 minutes."""
    await ticket_factory(id=3, event_id=1, seat_number="A3")

    repo = PostgresTicketRepository(db_session)
    uc = ReserveTicketUseCase(ticket_repo=repo)
    await uc.execute(ReserveTicketRequest(ticket_id=3, user_id=1, idempotency_key="k3"))

    ticket = await repo.get(3)
    assert ticket is not None
    assert ticket.reservation is not None

    expected = datetime.now(UTC) + timedelta(minutes=5)
    delta = abs(ticket.reservation.expires_at - expected)
    assert delta < timedelta(seconds=5), f"expires_at off by {delta}"


@pytest.mark.asyncio
async def test_second_reserve_on_same_ticket_fails(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """A second reservation on an already-reserved ticket returns success=False."""
    await ticket_factory(id=4, event_id=1, seat_number="A4")

    repo = PostgresTicketRepository(db_session)
    uc = ReserveTicketUseCase(ticket_repo=repo)

    first = await uc.execute(
        ReserveTicketRequest(ticket_id=4, user_id=1, idempotency_key="k4a")
    )
    second = await uc.execute(
        ReserveTicketRequest(ticket_id=4, user_id=2, idempotency_key="k4b")
    )

    assert first.success is True
    assert second.success is False


@pytest.mark.asyncio
async def test_reserve_persists_ticket_event_and_outbox_message(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """Saving a reserved ticket writes the event log and outbox in one transaction."""
    await ticket_factory(id=5, event_id=1, seat_number="A5")

    repo = PostgresTicketRepository(db_session)
    uc = ReserveTicketUseCase(ticket_repo=repo)
    response = await uc.execute(
        ReserveTicketRequest(ticket_id=5, user_id=42, idempotency_key="k5")
    )

    assert response.success is True

    event_result = await db_session.execute(
        select(TicketEventModel).where(TicketEventModel.ticket_id == 5)
    )
    ticket_event = event_result.scalar_one()
    assert ticket_event.event_type == "ticket.reserved"
    assert ticket_event.payload["ticket_id"] == 5
    assert ticket_event.payload["user_id"] == 42

    outbox_result = await db_session.execute(
        select(OutboxMessageModel).where(
            OutboxMessageModel.event_type == "ticket.reserved",
            OutboxMessageModel.payload["ticket_id"].as_integer() == 5,
        )
    )
    outbox_message = outbox_result.scalar_one()
    assert outbox_message.published is False
    assert outbox_message.payload["ticket_id"] == 5
