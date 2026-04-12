"""Ticketing bounded context - domain model.

Layer: domain
Aggregate root: Ticket
Child entity: Reservation (accessed only through Ticket)

Cosmic Python rule: the only way to modify objects inside an aggregate
is to load the whole thing and call methods on the aggregate root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum

from domain.shared.event import DomainEvent
from domain.ticketing.events import TicketConfirmed, TicketReleased, TicketReserved
from domain.ticketing.exceptions import (
    InvalidStateTransitionError,
    TicketAlreadyTakenError,
)

RESERVATION_TTL: timedelta = timedelta(minutes=5)


class TicketStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    RELEASED = "released"  # terminal: permanently deactivated / event cancelled


@dataclass
class Reservation:
    """Child entity of the Ticket aggregate.

    Never instantiate directly - created by Ticket.reserve().
    """

    ticket_id: int
    user_id: int
    created_at: datetime
    expires_at: datetime
    id: int = field(default=0)

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at


@dataclass
class Ticket:
    """Aggregate root for the ticketing context.

    All state changes go through this class. Domain events are collected
    in ``events`` and published by the Unit of Work after commit.
    """

    id: int
    event_id: int
    seat_number: str
    status: TicketStatus = field(default=TicketStatus.AVAILABLE)
    reserved_by: int | None = field(default=None)
    version: int = field(default=0)
    reservation: Reservation | None = field(default=None)
    events: list[DomainEvent] = field(default_factory=list)

    def reserve(self, user_id: int) -> Reservation:
        """Reserve this ticket for a user.

        Creates a Reservation child entity (TTL = RESERVATION_TTL),
        bumps version, and appends TicketReserved to events.

        Raises: TicketAlreadyTakenError if status != AVAILABLE.
        """
        if self.status != TicketStatus.AVAILABLE:
            raise TicketAlreadyTakenError(self.id)
        now = datetime.now(UTC)
        self.status = TicketStatus.RESERVED
        self.reserved_by = user_id
        self.version += 1
        self.reservation = Reservation(
            ticket_id=self.id,
            user_id=user_id,
            created_at=now,
            expires_at=now + RESERVATION_TTL,
        )
        self.events.append(TicketReserved(ticket_id=self.id, user_id=user_id))
        return self.reservation

    def release(self, reason: str = "released") -> None:
        """Release ticket back to AVAILABLE and clear the reservation."""
        self.status = TicketStatus.AVAILABLE
        self.reserved_by = None
        self.reservation = None
        self.version += 1
        self.events.append(TicketReleased(ticket_id=self.id, reason=reason))

    def confirm(self) -> None:
        """Confirm ticket after successful payment.

        Raises: InvalidStateTransitionError if status != RESERVED.
        """
        if self.status != TicketStatus.RESERVED:
            raise InvalidStateTransitionError(
                self.id, self.status.value, TicketStatus.RESERVED.value
            )
        self.status = TicketStatus.CONFIRMED
        self.version += 1
        self.events.append(TicketConfirmed(ticket_id=self.id))
