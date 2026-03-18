"""Ticket aggregate repository protocol.

Layer: domain
Cosmic Python rule: repositories only return aggregates, never child entities.
Only one repository per aggregate root — Reservation is accessed through Ticket.

Implemented by: PostgresTicketRepository, MemoryTicketRepository.
"""

from __future__ import annotations

from typing import Protocol

from domain.ticketing.model import Ticket


class TicketRepository(Protocol):
    """Persistence interface for the Ticket aggregate.

    Uses ``add`` / ``get`` naming per Cosmic Python convention.
    """

    async def add(self, ticket: Ticket) -> None: ...

    async def get(self, ticket_id: int) -> Ticket | None: ...

    async def get_for_update(self, ticket_id: int) -> Ticket | None: ...
