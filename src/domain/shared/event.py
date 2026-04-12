"""Base domain event - shared across all bounded contexts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class DomainEvent:
    """Base class for all domain events.

    Every aggregate appends concrete events to its ``events`` list;
    the Unit of Work publishes them after a successful commit.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
