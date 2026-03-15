from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class TicketReserved(DomainEvent):
    ticket_id: int = 0
    user_id: int = 0


@dataclass
class TicketReleased(DomainEvent):
    ticket_id: int = 0
    reason: str = ""


@dataclass
class PaymentCompleted(DomainEvent):
    reservation_id: int = 0
    amount_cents: int = 0


@dataclass
class PaymentFailed(DomainEvent):
    reservation_id: int = 0
    error: str = ""


@dataclass
class TicketConfirmed(DomainEvent):
    ticket_id: int = 0
