"""Use-case request DTOs.

Layer: use_cases
Imports: stdlib only
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReserveTicketRequest:
    ticket_id: int
    user_id: int
    idempotency_key: str


@dataclass
class ReleaseTicketRequest:
    ticket_id: int
    reason: str


@dataclass
class ProcessPaymentRequest:
    reservation_id: int
    amount_cents: int
    payment_method: str
