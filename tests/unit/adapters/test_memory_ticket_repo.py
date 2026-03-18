"""Unit tests for MemoryTicketRepository.

Covers: get, add, and get_for_update blocking semantics.
"""

import asyncio

import pytest

from adapters.repositories.memory_ticket_repo import MemoryTicketRepository
from domain.ticketing.model import Ticket, TicketStatus


def make_ticket(ticket_id: int = 1, status: TicketStatus = TicketStatus.AVAILABLE) -> Ticket:
    return Ticket(id=ticket_id, event_id=10, seat_number="A1", status=status)


@pytest.mark.asyncio
async def test_add_then_get_returns_ticket() -> None:
    repo = MemoryTicketRepository()
    ticket = make_ticket()

    await repo.add(ticket)
    result = await repo.get(ticket.id)

    assert result is not None
    assert result.id == ticket.id
    assert result.status == TicketStatus.AVAILABLE


@pytest.mark.asyncio
async def test_get_unknown_returns_none() -> None:
    repo = MemoryTicketRepository()
    result = await repo.get(999)
    assert result is None


@pytest.mark.asyncio
async def test_get_returns_copy_not_same_object() -> None:
    repo = MemoryTicketRepository()
    ticket = make_ticket()
    await repo.add(ticket)

    first = await repo.get(ticket.id)
    second = await repo.get(ticket.id)

    assert first is not second


@pytest.mark.asyncio
async def test_get_for_update_blocks_second_concurrent_access() -> None:
    """Second get_for_update must wait until add() releases the lock."""
    repo = MemoryTicketRepository()
    ticket = make_ticket()
    await repo.add(ticket)

    acquired_order: list[int] = []

    async def task_a() -> None:
        t = await repo.get_for_update(ticket.id)
        acquired_order.append(1)
        await asyncio.sleep(0.05)  # hold lock briefly
        assert t is not None
        t.version += 1
        await repo.add(t)

    async def task_b() -> None:
        await asyncio.sleep(0.01)  # ensure A acquires first
        await repo.get_for_update(ticket.id)
        acquired_order.append(2)
        await repo.add(ticket)

    await asyncio.gather(task_a(), task_b())

    # A must have acquired before B
    assert acquired_order == [1, 2]


@pytest.mark.asyncio
async def test_add_persists_reserved_state() -> None:
    repo = MemoryTicketRepository()
    ticket = make_ticket()
    await repo.add(ticket)

    locked = await repo.get_for_update(ticket.id)
    assert locked is not None
    locked.reserve(user_id=42)
    await repo.add(locked)

    stored = await repo.get(ticket.id)
    assert stored is not None
    assert stored.status == TicketStatus.RESERVED
    assert stored.reserved_by == 42
