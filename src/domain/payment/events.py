"""Payment-context domain events."""

from __future__ import annotations

from dataclasses import dataclass

from domain.shared.event import DomainEvent


@dataclass(kw_only=True)
class PaymentCompleted(DomainEvent):
    """Emitted when a payment is successfully charged."""

    reservation_id: int
    amount_cents: int


@dataclass(kw_only=True)
class PaymentFailed(DomainEvent):
    """Emitted when a payment charge fails."""

    reservation_id: int
    error: str
