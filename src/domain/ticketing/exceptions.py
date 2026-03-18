"""Ticketing-context domain exceptions."""

from __future__ import annotations


class TicketAlreadyTakenError(Exception):
    def __init__(self, ticket_id: int) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} is already taken")


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: int) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} not found")


class InvalidStateTransitionError(Exception):
    """Raised when a state-changing method is called from an invalid status."""

    def __init__(self, ticket_id: int, current: str, expected: str) -> None:
        self.ticket_id = ticket_id
        self.current = current
        self.expected = expected
        super().__init__(
            f"Ticket {ticket_id}: cannot transition from {current!r} "
            f"(expected {expected!r})"
        )


class OptimisticLockConflict(Exception):
    def __init__(self, ticket_id: int, expected_version: int) -> None:
        self.ticket_id = ticket_id
        self.expected_version = expected_version
        super().__init__(
            f"Optimistic lock conflict on ticket {ticket_id}, "
            f"expected version {expected_version}"
        )


class LockNotAcquiredError(Exception):
    def __init__(self, resource: str) -> None:
        self.resource = resource
        super().__init__(f"Could not acquire lock on resource: {resource}")
