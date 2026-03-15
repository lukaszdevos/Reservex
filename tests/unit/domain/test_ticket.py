from __future__ import annotations

import pytest

from domain.exceptions import TicketAlreadyTakenError
from domain.ticket import Ticket, TicketStatus


def make_ticket(**kwargs: object) -> Ticket:
    defaults: dict[str, object] = {"id": 1, "event_id": 10, "seat_number": "A1"}
    return Ticket(**{**defaults, **kwargs})  # type: ignore[arg-type]


def test_reserve_changes_status_to_reserved() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=42)
    assert ticket.status == TicketStatus.RESERVED
    assert ticket.reserved_by == 42


def test_reserve_raises_when_not_available() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    with pytest.raises(TicketAlreadyTakenError):
        ticket.reserve(user_id=2)


def test_release_restores_available_and_clears_reserved_by() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    ticket.release()
    assert ticket.status == TicketStatus.AVAILABLE
    assert ticket.reserved_by is None


def test_version_increments_on_every_state_change() -> None:
    ticket = make_ticket()
    assert ticket.version == 0
    ticket.reserve(user_id=1)
    assert ticket.version == 1
    ticket.release()
    assert ticket.version == 2
    ticket.reserve(user_id=1)
    ticket.confirm()
    assert ticket.version == 4
