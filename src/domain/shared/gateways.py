"""Shared gateway protocols used across bounded contexts.

Implemented by: infrastructure adapters (Redis, SMTP, etc.).
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol


class NotificationGateway(Protocol):
    """Send transactional notifications to users.

    Implemented by: SmtpNotificationGateway, StubNotificationGateway.
    """

    async def send_confirmation(self, user_id: int, reservation_id: int) -> None: ...

    async def send_expiry(self, user_id: int, ticket_id: int) -> None: ...


class DistributedLockGateway(Protocol):
    """Acquire distributed locks for critical sections.

    Implemented by: RedisLockGateway.
    """

    def lock(self, resource: str, ttl_ms: int) -> AbstractAsyncContextManager[None]: ...


class UserBlacklistGateway(Protocol):
    """Check whether a user is blacklisted from making reservations.

    Implemented by: RedisUserBlacklistGateway, StubUserBlacklistGateway.
    """

    async def is_blacklisted(self, user_id: int) -> bool: ...
