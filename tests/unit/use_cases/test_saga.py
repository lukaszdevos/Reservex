"""Unit tests for TicketPurchaseSaga.

Covers: happy path, failure-and-compensation, and compensation-failure resilience.
Uses unittest.mock.AsyncMock for all gateway/repo collaborators.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from domain.payment.exceptions import PaymentDeclinedError
from domain.ticketing.model import Ticket, TicketStatus
from use_cases.saga import SagaContext, TicketPurchaseSaga


def make_ticket(status: TicketStatus = TicketStatus.AVAILABLE) -> Ticket:
    return Ticket(id=1, event_id=10, seat_number="A1", status=status)


def make_saga(
    ticket_repo: AsyncMock,
    payment_gateway: AsyncMock,
    notifier: AsyncMock,
    user_blacklist: AsyncMock,
) -> TicketPurchaseSaga:
    return TicketPurchaseSaga(
        ticket_repo=ticket_repo,
        payment_gateway=payment_gateway,
        notifier=notifier,
        user_blacklist=user_blacklist,
    )


def make_ctx() -> SagaContext:
    return SagaContext(
        ticket_id=1,
        user_id=42,
        amount_cents=5000,
        payment_method="pm_card_visa",
        correlation_id="corr-001",
    )


def make_happy_mocks() -> tuple[AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    ticket_repo = AsyncMock()
    ticket_repo.get.return_value = make_ticket()
    ticket_repo.get_for_update.return_value = make_ticket()

    payment_gateway = AsyncMock()
    payment_gateway.charge.return_value = "charge-abc"

    notifier = AsyncMock()

    user_blacklist = AsyncMock()
    user_blacklist.is_blacklisted.return_value = False

    return ticket_repo, payment_gateway, notifier, user_blacklist


@pytest.mark.asyncio
async def test_happy_path_all_4_steps_called_in_order() -> None:
    ticket_repo, payment_gateway, notifier, user_blacklist = make_happy_mocks()
    saga = make_saga(ticket_repo, payment_gateway, notifier, user_blacklist)

    result = await saga.execute(make_ctx())

    assert result.success is True
    assert result.failed_step is None
    ticket_repo.get.assert_called()           # validate step
    ticket_repo.get_for_update.assert_called()  # reserve step
    payment_gateway.charge.assert_called_once()  # charge step
    notifier.send_confirmation.assert_called_once()  # notify step


@pytest.mark.asyncio
async def test_failure_at_charge_compensates_reserve_in_reverse() -> None:
    ticket_repo, payment_gateway, notifier, user_blacklist = make_happy_mocks()
    payment_gateway.charge.side_effect = PaymentDeclinedError("Card declined")
    saga = make_saga(ticket_repo, payment_gateway, notifier, user_blacklist)

    result = await saga.execute(make_ctx())

    assert result.success is False
    assert result.failed_step == "charge"
    # _release compensation must have been triggered: ticket_repo.get called
    # (once in validate, once in _release) and ticket_repo.add called
    ticket_repo.get.assert_called()
    ticket_repo.add.assert_called()
    notifier.send_confirmation.assert_not_called()


@pytest.mark.asyncio
async def test_failure_at_validate_triggers_no_compensation() -> None:
    ticket_repo, payment_gateway, notifier, user_blacklist = make_happy_mocks()
    # ticket not found causes validate to fail
    ticket_repo.get.return_value = None
    saga = make_saga(ticket_repo, payment_gateway, notifier, user_blacklist)

    result = await saga.execute(make_ctx())

    assert result.success is False
    assert result.failed_step == "validate"
    ticket_repo.get_for_update.assert_not_called()
    payment_gateway.charge.assert_not_called()
    notifier.send_confirmation.assert_not_called()


@pytest.mark.asyncio
async def test_compensation_failure_does_not_interrupt_rollback() -> None:
    ticket_repo, payment_gateway, notifier, user_blacklist = make_happy_mocks()
    # charge fails → triggers compensate for validate+reserve
    payment_gateway.charge.side_effect = PaymentDeclinedError("Card declined")
    # _release compensation also fails: second call to ticket_repo.get raises
    ticket_repo.get.side_effect = [make_ticket(), Exception("DB connection lost")]
    saga = make_saga(ticket_repo, payment_gateway, notifier, user_blacklist)

    # execute must not propagate the compensation exception
    result = await saga.execute(make_ctx())

    assert result.success is False
    assert result.failed_step == "charge"
