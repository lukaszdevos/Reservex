"""Stub gateway implementations for development and local testing.

Layer: adapters
Implements: NotificationGateway, UserBlacklistGateway (domain.shared.gateways)
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class StubNotificationGateway:
    """No-op gateway that logs notifications instead of sending emails.

    Implements: NotificationGateway
    """

    async def send_confirmation(self, user_id: int, reservation_id: int) -> None:
        logger.info(
            "stub_send_confirmation",
            user_id=user_id,
            reservation_id=reservation_id,
        )

    async def send_expiry(self, user_id: int, ticket_id: int) -> None:
        logger.info("stub_send_expiry", user_id=user_id, ticket_id=ticket_id)


class StubUserBlacklistGateway:
    """Never blacklists any user - always returns False.

    Implements: UserBlacklistGateway
    """

    async def is_blacklisted(self, user_id: int) -> bool:
        return False
