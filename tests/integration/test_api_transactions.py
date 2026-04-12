"""Integration tests for API transaction dependency behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from infrastructure.api.dependencies import get_session
from infrastructure.database.models import ReservationModel, TicketModel


def _request(session_factory: async_sessionmaker[AsyncSession]) -> Any:
    return SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(session_factory=session_factory),
        )
    )


async def _cleanup_ticket(
    session_factory: async_sessionmaker[AsyncSession],
    ticket_id: int,
) -> None:
    async with session_factory() as session:
        await session.execute(
            delete(ReservationModel).where(ReservationModel.ticket_id == ticket_id)
        )
        await session.execute(delete(TicketModel).where(TicketModel.id == ticket_id))
        await session.commit()


async def _ticket_exists(
    session_factory: async_sessionmaker[AsyncSession],
    ticket_id: int,
) -> bool:
    async with session_factory() as session:
        result = await session.execute(
            select(TicketModel.id).where(TicketModel.id == ticket_id)
        )
        return result.scalar_one_or_none() is not None


def _ticket_model(ticket_id: int) -> TicketModel:
    now = datetime.now(UTC)
    return TicketModel(
        id=ticket_id,
        event_id=777,
        seat_number=f"T{ticket_id}",
        status="available",
        version=0,
        reserved_by=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_get_session_commits_on_success(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    ticket_id = 5101
    await _cleanup_ticket(session_factory, ticket_id)
    session_gen = get_session(_request(session_factory))

    try:
        session = await session_gen.__anext__()
        session.add(_ticket_model(ticket_id))
        with pytest.raises(StopAsyncIteration):
            await session_gen.__anext__()

        assert await _ticket_exists(session_factory, ticket_id)
    finally:
        await session_gen.aclose()
        await _cleanup_ticket(session_factory, ticket_id)


@pytest.mark.asyncio
async def test_get_session_rolls_back_on_exception(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    ticket_id = 5102
    await _cleanup_ticket(session_factory, ticket_id)
    session_gen = get_session(_request(session_factory))

    try:
        session = await session_gen.__anext__()
        session.add(_ticket_model(ticket_id))
        with pytest.raises(RuntimeError):
            await session_gen.athrow(RuntimeError("route failed"))

        assert not await _ticket_exists(session_factory, ticket_id)
    finally:
        await session_gen.aclose()
        await _cleanup_ticket(session_factory, ticket_id)
