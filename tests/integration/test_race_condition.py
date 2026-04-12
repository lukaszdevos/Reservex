"""Integration tests - race condition with pessimistic and optimistic locking (P5.3).

50 concurrent coroutines try to reserve the same ticket.
Exactly one must win; all others must fail.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from domain.ticketing.exceptions import OptimisticLockConflict
from domain.ticketing.model import TicketStatus
from infrastructure.database.models import ReservationModel, TicketModel
from use_cases.request_objects import ReserveTicketRequest
from use_cases.reserve_ticket import ReserveTicketUseCase


async def _insert_available_ticket(
    factory_obj: async_sessionmaker[AsyncSession], ticket_id: int
) -> None:
    """Insert a committed, available ticket (outside any rollback transaction)."""
    async with factory_obj() as session:
        session.add(
            TicketModel(
                id=ticket_id,
                event_id=99,
                seat_number=f"R{ticket_id}",
                status="available",
                version=0,
                reserved_by=None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        await session.commit()


async def _cleanup_ticket(
    factory_obj: async_sessionmaker[AsyncSession], ticket_id: int
) -> None:
    async with factory_obj() as session:
        await session.execute(
            delete(ReservationModel).where(ReservationModel.ticket_id == ticket_id)
        )
        await session.execute(
            delete(TicketModel).where(TicketModel.id == ticket_id)
        )
        await session.commit()


async def _try_reserve(
    factory_obj: async_sessionmaker[AsyncSession],
    ticket_id: int,
    user_id: int,
) -> Any:
    """Single reservation attempt in its own session and transaction."""
    async with factory_obj() as session:
        repo = PostgresTicketRepository(session)
        uc = ReserveTicketUseCase(ticket_repo=repo)
        result = await uc.execute(
            ReserveTicketRequest(
                ticket_id=ticket_id,
                user_id=user_id,
                idempotency_key=str(user_id),
            )
        )
        if result.success:
            await session.commit()
        return result


@pytest.mark.asyncio
async def test_pessimistic_lock_only_one_wins(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """SELECT FOR UPDATE ensures exactly 1 of 50 concurrent reservations succeeds."""
    ticket_id = 1001
    await _insert_available_ticket(session_factory, ticket_id)

    try:
        results = await asyncio.gather(
            *[_try_reserve(session_factory, ticket_id, i) for i in range(50)],
            return_exceptions=True,
        )

        successes = [r for r in results if hasattr(r, "success") and r.success]
        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"

        # Verify DB state: exactly one reservation row
        async with session_factory() as session:
            repo = PostgresTicketRepository(session)
            ticket = await repo.get(ticket_id)
        assert ticket is not None
        assert ticket.status == TicketStatus.RESERVED
        assert ticket.reservation is not None
    finally:
        await _cleanup_ticket(session_factory, ticket_id)


@pytest.mark.asyncio
async def test_optimistic_lock_only_one_wins(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Optimistic locking (get + add with version check) allows exactly 1 winner."""
    ticket_id = 1002
    await _insert_available_ticket(session_factory, ticket_id)

    async def _try_optimistic(user_id: int) -> Any:
        async with session_factory() as session:
            repo = PostgresTicketRepository(session)
            # non-locking read
            ticket = await repo.get(ticket_id)
            if ticket is None or ticket.status != TicketStatus.AVAILABLE:
                return None
            try:
                ticket.reserve(user_id)
                await repo.add(ticket)
                await session.commit()
                return True
            except OptimisticLockConflict:
                return None

    try:
        results = await asyncio.gather(
            *[_try_optimistic(i) for i in range(50)],
            return_exceptions=True,
        )

        wins = [r for r in results if r is True]
        assert len(wins) == 1, f"Expected 1 win, got {len(wins)}"

        async with session_factory() as session:
            repo = PostgresTicketRepository(session)
            ticket = await repo.get(ticket_id)
        assert ticket is not None
        assert ticket.status == TicketStatus.RESERVED
    finally:
        await _cleanup_ticket(session_factory, ticket_id)
