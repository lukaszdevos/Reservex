from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol


class PaymentGateway(Protocol):
    async def charge(
        self, reservation_id: int, amount_cents: int, payment_method: str
    ) -> str: ...

    async def refund(self, charge_id: str) -> None: ...


class NotificationGateway(Protocol):
    async def send_confirmation(self, user_id: int, reservation_id: int) -> None: ...

    async def send_expiry(self, user_id: int, ticket_id: int) -> None: ...


class DistributedLockGateway(Protocol):
    def lock(self, resource: str, ttl_ms: int) -> AbstractAsyncContextManager[None]: ...
