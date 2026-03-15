"""Payment gateway protocol.

Layer: domain
Implemented by: StripeGateway, StubPaymentGateway.
"""

from __future__ import annotations

from typing import Protocol


class PaymentGateway(Protocol):
    """Charge and refund payments via an external processor."""

    async def charge(
        self, reservation_id: int, amount_cents: int, payment_method: str
    ) -> str: ...

    async def refund(self, charge_id: str) -> None: ...
