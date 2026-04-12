"""Load-oriented smoke tests for reservation concurrency.

These tests are deterministic enough for CI and complement the Locust HTTP
profile in this directory.
"""

from __future__ import annotations

import asyncio

import pytest

from adapters.repositories.memory_ticket_repo import MemoryTicketRepository
from domain.ticketing.model import Ticket
from use_cases.request_objects import ReserveTicketRequest
from use_cases.reserve_ticket import ReserveTicketUseCase


@pytest.mark.asyncio
async def test_hot_seat_load_allows_exactly_one_winner() -> None:
    repo = MemoryTicketRepository()
    await repo.add(Ticket(id=1, event_id=1, seat_number="A1"))
    use_case = ReserveTicketUseCase(repo)

    async def reserve(user_id: int) -> bool:
        result = await use_case.execute(
            ReserveTicketRequest(
                ticket_id=1,
                user_id=user_id,
                idempotency_key=f"hot-seat-{user_id}",
            )
        )
        return result.success

    results = await asyncio.gather(*[reserve(user_id) for user_id in range(300)])

    assert results.count(True) == 1
    assert results.count(False) == 299


@pytest.mark.asyncio
async def test_many_distinct_reservations_complete_successfully() -> None:
    repo = MemoryTicketRepository()
    total = 300
    for ticket_id in range(1, total + 1):
        await repo.add(Ticket(id=ticket_id, event_id=1, seat_number=f"L{ticket_id}"))

    use_case = ReserveTicketUseCase(repo)

    async def reserve(ticket_id: int) -> bool:
        result = await use_case.execute(
            ReserveTicketRequest(
                ticket_id=ticket_id,
                user_id=ticket_id + 1_000,
                idempotency_key=f"distinct-{ticket_id}",
            )
        )
        return result.success

    results = await asyncio.gather(
        *[reserve(ticket_id) for ticket_id in range(1, total + 1)]
    )

    assert all(results)
