"""Payment-context domain events."""

from __future__ import annotations

from dataclasses import dataclass

from domain.shared.event import DomainEvent


@dataclass
class PaymentCompleted(DomainEvent):
    reservation_id: int = 0
    amount_cents: int = 0


@dataclass
class PaymentFailed(DomainEvent):
    reservation_id: int = 0
    error: str = ""
