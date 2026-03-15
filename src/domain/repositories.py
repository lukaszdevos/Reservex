from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from domain.reservation import Reservation
from domain.ticket import Ticket


class TicketRepository(Protocol):
    async def get(self, ticket_id: int) -> Ticket | None: ...

    async def get_for_update(self, ticket_id: int) -> Ticket | None: ...

    async def save(self, ticket: Ticket) -> None: ...

    async def release(self, ticket_id: int) -> None: ...


class ReservationRepository(Protocol):
    async def create(self, reservation: Reservation) -> None: ...

    async def get(self, reservation_id: int) -> Reservation | None: ...

    async def mark_expired(self, reservation_id: int) -> None: ...


class OutboxRepository(Protocol):
    async def save_message(
        self, event_type: str, payload: dict[str, object]
    ) -> None: ...

    async def get_unpublished(self) -> Sequence[dict[str, object]]: ...

    async def mark_published(self, message_id: int) -> None: ...
