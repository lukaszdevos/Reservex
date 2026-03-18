"""Unit tests for ReserveTicketUseCase.

Uses an inline fake repo — no database, no Redis.
"""

from __future__ import annotations

import pytest

from domain.ticketing.model import Ticket, TicketStatus
from use_cases.request_objects import ReserveTicketRequest
from use_cases.reserve_ticket import ReserveTicketUseCase


class FakeTicketRepo:
    def __init__(self, ticket: Ticket | None = None) -> None:
        self._store: dict[int, Ticket] = {}
        self.add_call_count: int = 0
        self.get_for_update_call_count: int = 0
        if ticket is not None:
            self._store[ticket.id] = ticket

    async def add(self, ticket: Ticket) -> None:
        self._store[ticket.id] = ticket
        self.add_call_count += 1

    async def get(self, ticket_id: int) -> Ticket | None:
        return self._store.get(ticket_id)

    async def get_for_update(self, ticket_id: int) -> Ticket | None:
        self.get_for_update_call_count += 1
        return self._store.get(ticket_id)


def make_ticket(status: TicketStatus = TicketStatus.AVAILABLE) -> Ticket:
    return Ticket(id=1, event_id=10, seat_number="A1", status=status)


@pytest.mark.asyncio
async def test_happy_path_returns_success() -> None:
    repo = FakeTicketRepo(make_ticket())
    uc = ReserveTicketUseCase(ticket_repo=repo)
    req = ReserveTicketRequest(ticket_id=1, user_id=42, idempotency_key="key-1")

    result = await uc.execute(req)

    assert result.success is True
    assert result.message == "Ticket reserved successfully"
    assert result.data is not None
    assert result.data["ticket_id"] == 1


@pytest.mark.asyncio
async def test_reserve_calls_get_for_update_and_add_once() -> None:
    repo = FakeTicketRepo(make_ticket())
    uc = ReserveTicketUseCase(ticket_repo=repo)
    req = ReserveTicketRequest(ticket_id=1, user_id=42, idempotency_key="key-2")

    await uc.execute(req)

    assert repo.get_for_update_call_count == 1
    assert repo.add_call_count == 1


@pytest.mark.asyncio
async def test_ticket_not_found_returns_failure() -> None:
    repo = FakeTicketRepo(None)
    uc = ReserveTicketUseCase(ticket_repo=repo)
    req = ReserveTicketRequest(ticket_id=99, user_id=42, idempotency_key="key-3")

    result = await uc.execute(req)

    assert result.success is False
    assert "not found" in result.message.lower()


@pytest.mark.asyncio
async def test_already_taken_returns_failure() -> None:
    repo = FakeTicketRepo(make_ticket(status=TicketStatus.RESERVED))
    uc = ReserveTicketUseCase(ticket_repo=repo)
    req = ReserveTicketRequest(ticket_id=1, user_id=42, idempotency_key="key-4")

    result = await uc.execute(req)

    assert result.success is False
    assert result.data is None
