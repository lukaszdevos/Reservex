"""Ticketing-context domain events."""

from __future__ import annotations

from dataclasses import dataclass

from domain.shared.event import DomainEvent


@dataclass(kw_only=True)
class TicketReserved(DomainEvent):
    """Emitted when a ticket is successfully reserved."""

    ticket_id: int
    user_id: int


@dataclass(kw_only=True)
class TicketReleased(DomainEvent):
    """Emitted when a reservation is released back to AVAILABLE."""

    ticket_id: int
    reason: str


@dataclass(kw_only=True)
class TicketConfirmed(DomainEvent):
    """Emitted when a ticket is confirmed after successful payment."""

    ticket_id: int
