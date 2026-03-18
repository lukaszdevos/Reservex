"""Stripe payment gateway implementation.

Layer: adapters
Implements: PaymentGateway (domain.payment.gateway)
"""

import asyncio

import stripe as stripe_lib

from domain.payment.exceptions import PaymentDeclinedError


class StripeGateway:
    """Calls the Stripe API via asyncio.to_thread (stripe SDK is synchronous).

    A semaphore caps concurrent Stripe API calls to avoid rate limiting.
    Implements: PaymentGateway
    """

    def __init__(self, api_key: str, max_concurrency: int = 10) -> None:
        stripe_lib.api_key = api_key
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def charge(
        self, reservation_id: int, amount_cents: int, payment_method: str
    ) -> str:
        async with self._semaphore:
            try:
                intent = await asyncio.to_thread(
                    stripe_lib.PaymentIntent.create,
                    amount=amount_cents,
                    currency="usd",
                    payment_method=payment_method,
                    confirm=True,
                    metadata={"reservation_id": str(reservation_id)},
                )
            except stripe_lib.CardError as exc:
                raise PaymentDeclinedError(str(exc)) from exc
        return str(intent.id)

    async def refund(self, charge_id: str) -> None:
        async with self._semaphore:
            await asyncio.to_thread(
                stripe_lib.Refund.create,
                payment_intent=charge_id,
            )
