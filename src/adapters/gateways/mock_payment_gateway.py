"""Mock payment gateway — for tests and local development.

Layer: adapters
Implements: PaymentGateway (domain.payment.gateway)
"""

from domain.payment.exceptions import PaymentDeclinedError


class MockPaymentGateway:
    """Configurable stub that either succeeds or raises PaymentDeclinedError.

    Implements: PaymentGateway
    """

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    async def charge(
        self, reservation_id: int, amount_cents: int, payment_method: str
    ) -> str:
        if self.should_fail:
            raise PaymentDeclinedError("mock: card declined")
        return f"mock_charge_{reservation_id}_{amount_cents}"

    async def refund(self, charge_id: str) -> None:
        if self.should_fail:
            raise PaymentDeclinedError("mock: refund failed")
