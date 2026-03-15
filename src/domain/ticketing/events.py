"""Ticketing-context domain events."""

from __future__ import annotations

from dataclasses import dataclass

from domain.shared.event import DomainEvent


@dataclass
class TicketReserved(DomainEvent):
    ticket_id: int = 0
    user_id: int = 0


@dataclass
class TicketReleased(DomainEvent):
    ticket_id: int = 0
    reason: str = ""


@dataclass
class TicketConfirmed(DomainEvent):
    ticket_id: int = 0
