"""In-memory ticket repository - for unit tests and local development.

Layer: adapters
Implements: TicketRepository (domain.ticketing.repository)
"""

import asyncio
import copy

from domain.ticketing.model import Ticket, TicketStatus


class MemoryTicketRepository:
    """Thread-safe in-memory store for Ticket aggregates.

    Uses one asyncio.Lock per ticket_id to simulate SELECT FOR UPDATE.
    Implements: TicketRepository
    """

    def __init__(self) -> None:
        self._store: dict[int, Ticket] = {}
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock_for(self, ticket_id: int) -> asyncio.Lock:
        if ticket_id not in self._locks:
            self._locks[ticket_id] = asyncio.Lock()
        return self._locks[ticket_id]

    async def get(self, ticket_id: int) -> Ticket | None:
        ticket = self._store.get(ticket_id)
        return copy.deepcopy(ticket) if ticket is not None else None

    async def get_for_update(self, ticket_id: int) -> Ticket | None:
        lock = self._lock_for(ticket_id)
        await lock.acquire()
        ticket = self._store.get(ticket_id)
        if ticket is None:
            lock.release()
            return None
        if ticket.status != TicketStatus.AVAILABLE:
            lock.release()
        return copy.deepcopy(ticket)

    async def add(self, ticket: Ticket) -> None:
        self._store[ticket.id] = copy.deepcopy(ticket)
        lock = self._lock_for(ticket.id)
        if lock.locked():
            lock.release()
