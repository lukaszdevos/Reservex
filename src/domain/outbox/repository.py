"""Transactional outbox repository protocol.

Layer: domain
Implemented by: PostgresOutboxRepository.

The outbox pattern guarantees at-least-once delivery of domain events
by writing them to the same DB transaction as the aggregate change.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class OutboxRepository(Protocol):
    """Persist and retrieve unpublished outbox messages."""

    async def save_message(
        self, event_type: str, payload: dict[str, object]
    ) -> None: ...

    async def get_unpublished(self) -> Sequence[dict[str, object]]: ...

    async def mark_published(self, message_id: int) -> None: ...
