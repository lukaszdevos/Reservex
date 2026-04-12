"""Integration tests - SAGA rollback against real Postgres (P5.4).

Happy path: ticket ends RESERVED after SAGA completes.
Failure path: card decline triggers compensation - ticket returns to AVAILABLE.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.gateways.mock_payment_gateway import MockPaymentGateway
from adapters.gateways.stub_gateways import (
    StubNotificationGateway,
    StubUserBlacklistGateway,
)
from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from domain.ticketing.model import TicketStatus
from use_cases.saga import SagaContext, TicketPurchaseSaga


def _make_saga(
    db_session: AsyncSession, should_fail: bool = False
) -> TicketPurchaseSaga:
    return TicketPurchaseSaga(
        ticket_repo=PostgresTicketRepository(db_session),
        payment_gateway=MockPaymentGateway(should_fail=should_fail),
        notifier=StubNotificationGateway(),
        user_blacklist=StubUserBlacklistGateway(),
    )


def _make_ctx(ticket_id: int) -> SagaContext:
    return SagaContext(
        ticket_id=ticket_id,
        user_id=1,
        amount_cents=5000,
        payment_method="pm_card_visa",
        correlation_id="integ-test",
    )


@pytest.mark.asyncio
async def test_saga_happy_path_ticket_reserved(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """All 4 steps succeed - ticket is RESERVED in DB."""
    await ticket_factory(id=10, event_id=1, seat_number="S1")

    saga = _make_saga(db_session)
    result = await saga.execute(_make_ctx(ticket_id=10))

    assert result.success is True
    assert result.failed_step is None

    repo = PostgresTicketRepository(db_session)
    ticket = await repo.get(10)
    assert ticket is not None
    assert ticket.status == TicketStatus.RESERVED
    assert ticket.reservation is not None


@pytest.mark.asyncio
async def test_saga_payment_failure_releases_ticket(
    db_session: AsyncSession, ticket_factory: Any
) -> None:
    """Card decline at charge step → compensation releases ticket back to AVAILABLE."""
    await ticket_factory(id=11, event_id=1, seat_number="S2")

    saga = _make_saga(db_session, should_fail=True)
    result = await saga.execute(_make_ctx(ticket_id=11))

    assert result.success is False
    assert result.failed_step == "charge"

    repo = PostgresTicketRepository(db_session)
    ticket = await repo.get(11)
    assert ticket is not None
    assert ticket.status == TicketStatus.AVAILABLE
    assert ticket.reservation is None


@pytest.mark.asyncio
async def test_saga_ticket_not_found_returns_failure(
    db_session: AsyncSession,
) -> None:
    """SAGA fails at validate when ticket does not exist."""
    saga = _make_saga(db_session)
    result = await saga.execute(_make_ctx(ticket_id=9999))

    assert result.success is False
    assert result.failed_step == "validate"
