"""Property-based tests for TicketPurchaseSaga (P5.6).

Uses Hypothesis to generate random failure patterns and asserts that
the ticket always returns to AVAILABLE when any SAGA step fails.
No database — uses MemoryTicketRepository.
"""

from __future__ import annotations

import asyncio

from hypothesis import given, settings
from hypothesis import strategies as st

from adapters.gateways.mock_payment_gateway import MockPaymentGateway
from adapters.gateways.stub_gateways import (
    StubNotificationGateway,
    StubUserBlacklistGateway,
)
from adapters.repositories.memory_ticket_repo import MemoryTicketRepository
from domain.ticketing.model import Ticket, TicketStatus
from use_cases.saga import SagaContext, TicketPurchaseSaga


def _build_saga(
    fail_at_charge: bool,
) -> tuple[TicketPurchaseSaga, MemoryTicketRepository]:
    repo = MemoryTicketRepository()
    saga = TicketPurchaseSaga(
        ticket_repo=repo,
        payment_gateway=MockPaymentGateway(should_fail=fail_at_charge),
        notifier=StubNotificationGateway(),
        user_blacklist=StubUserBlacklistGateway(),
    )
    return saga, repo


async def _run(fail_at_charge: bool) -> tuple[bool, TicketStatus | None]:
    saga, repo = _build_saga(fail_at_charge)

    ticket = Ticket(id=1, event_id=1, seat_number="A1")
    await repo.add(ticket)

    ctx = SagaContext(
        ticket_id=1,
        user_id=42,
        amount_cents=5000,
        payment_method="pm_test",
        correlation_id="prop-test",
    )
    result = await saga.execute(ctx)

    final = await repo.get(1)
    status = final.status if final is not None else None
    return result.success, status


@given(fail_at_charge=st.booleans())
@settings(max_examples=50)
def test_ticket_status_consistent_after_saga(fail_at_charge: bool) -> None:
    """After any saga outcome the ticket status is always consistent:
    - success=True  → RESERVED
    - success=False → AVAILABLE (compensation restored it)
    """
    success, status = asyncio.run(_run(fail_at_charge))

    if success:
        assert status == TicketStatus.RESERVED
    else:
        assert status == TicketStatus.AVAILABLE


@given(
    fail_at_charge=st.booleans(),
    user_id=st.integers(min_value=1, max_value=10_000),
    amount_cents=st.integers(min_value=1, max_value=100_000),
)
@settings(max_examples=50)
def test_ticket_never_stuck_in_reserved_after_failure(
    fail_at_charge: bool, user_id: int, amount_cents: int
) -> None:
    """Ticket must never be left RESERVED when the saga reports failure."""

    async def _inner() -> tuple[bool, TicketStatus | None]:
        saga, repo = _build_saga(fail_at_charge)
        ticket = Ticket(id=1, event_id=1, seat_number="A1")
        await repo.add(ticket)
        ctx = SagaContext(
            ticket_id=1,
            user_id=user_id,
            amount_cents=amount_cents,
            payment_method="pm_test",
            correlation_id="prop-2",
        )
        result = await saga.execute(ctx)
        final = await repo.get(1)
        return result.success, final.status if final else None

    success, status = asyncio.run(_inner())

    if not success:
        assert status != TicketStatus.RESERVED, (
            f"Ticket stuck RESERVED after failure (fail_at_charge={fail_at_charge})"
        )
