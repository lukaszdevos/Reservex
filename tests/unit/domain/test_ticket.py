"""Unit tests for the Ticket aggregate root."""

from __future__ import annotations

import pytest

from domain.ticketing.events import TicketConfirmed, TicketReleased, TicketReserved
from domain.ticketing.exceptions import TicketAlreadyTakenError
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
