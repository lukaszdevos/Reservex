"""Unit tests for the Ticket aggregate root."""

from __future__ import annotations

import pytest

from domain.ticketing.events import TicketConfirmed, TicketReleased, TicketReserved
from domain.ticketing.exceptions import (
    InvalidStateTransitionError,
    TicketAlreadyTakenError,
)
from domain.ticketing.model import Ticket, TicketStatus


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


def test_reserve_creates_reservation_as_child_entity() -> None:
    ticket = make_ticket()
    reservation = ticket.reserve(user_id=42)
    assert reservation is ticket.reservation
    assert reservation.user_id == 42
    assert reservation.ticket_id == ticket.id
    assert not reservation.is_expired()


def test_release_restores_available_and_clears_reservation() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    ticket.release()
    assert ticket.status == TicketStatus.AVAILABLE
    assert ticket.reserved_by is None
    assert ticket.reservation is None


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


def test_reserve_appends_ticket_reserved_event() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=7)
    assert len(ticket.events) == 1
    event = ticket.events[0]
    assert isinstance(event, TicketReserved)
    assert event.ticket_id == ticket.id
    assert event.user_id == 7


def test_release_appends_ticket_released_event() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    ticket.release(reason="expired")
    released = ticket.events[-1]
    assert isinstance(released, TicketReleased)
    assert released.reason == "expired"


def test_confirm_appends_ticket_confirmed_event() -> None:
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    ticket.confirm()
    confirmed = ticket.events[-1]
    assert isinstance(confirmed, TicketConfirmed)
    assert confirmed.ticket_id == ticket.id


def test_confirm_raises_when_not_reserved() -> None:
    """confirm() must only be called on a RESERVED ticket."""
    ticket = make_ticket()  # status = AVAILABLE
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        ticket.confirm()
    assert exc_info.value.ticket_id == ticket.id
    assert exc_info.value.current == TicketStatus.AVAILABLE.value
    assert exc_info.value.expected == TicketStatus.RESERVED.value


def test_reserve_raises_after_confirm() -> None:
    """Once CONFIRMED, a ticket cannot be reserved again."""
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    ticket.confirm()
    with pytest.raises(TicketAlreadyTakenError):
        ticket.reserve(user_id=2)


def test_events_accumulate_across_state_changes() -> None:
    """Full lifecycle produces events in correct order."""
    ticket = make_ticket()
    ticket.reserve(user_id=1)
    ticket.release(reason="timeout")
    ticket.reserve(user_id=2)
    ticket.confirm()
    types = [type(e).__name__ for e in ticket.events]
    expected = ["TicketReserved", "TicketReleased", "TicketReserved", "TicketConfirmed"]
    assert types == expected
