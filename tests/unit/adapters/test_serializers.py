"""Unit tests for adapters.serializers and adapters.presenters."""

from datetime import UTC, datetime, timedelta

from adapters.presenters import present_reserve_response
from adapters.serializers import reservation_to_dict, ticket_to_dict
from domain.ticketing.model import Reservation, Ticket, TicketStatus
from use_cases.response_objects import UseCaseResponse


def make_reservation(ticket_id: int = 1, user_id: int = 42) -> Reservation:
    now = datetime.now(UTC)
    return Reservation(
        id=7,
        ticket_id=ticket_id,
        user_id=user_id,
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def make_ticket(with_reservation: bool = False) -> Ticket:
    ticket = Ticket(id=1, event_id=10, seat_number="B2", status=TicketStatus.AVAILABLE)
    if with_reservation:
        ticket.reserve(user_id=42)
    return ticket


def test_reservation_to_dict_round_trip() -> None:
    res = make_reservation()
    d = reservation_to_dict(res)

    assert d["id"] == res.id
    assert d["ticket_id"] == res.ticket_id
    assert d["user_id"] == res.user_id
    assert d["created_at"] == res.created_at.isoformat()
    assert d["expires_at"] == res.expires_at.isoformat()


def test_ticket_to_dict_available() -> None:
    ticket = make_ticket()
    d = ticket_to_dict(ticket)

    assert d["id"] == ticket.id
    assert d["event_id"] == ticket.event_id
    assert d["seat_number"] == ticket.seat_number
    assert d["status"] == "available"
    assert d["reserved_by"] is None
    assert d["reservation"] is None


def test_ticket_to_dict_with_reservation() -> None:
    ticket = make_ticket(with_reservation=True)
    d = ticket_to_dict(ticket)

    assert d["status"] == "reserved"
    assert d["reserved_by"] == 42
    assert isinstance(d["reservation"], dict)
    res_dict = d["reservation"]
    assert isinstance(res_dict, dict)
    assert res_dict["user_id"] == 42


def test_present_reserve_response_success() -> None:
    response = UseCaseResponse(success=True, message="OK", data={"ticket_id": 1})
    d = present_reserve_response(response)

    assert d["success"] is True
    assert d["message"] == "OK"
    assert d["data"] == {"ticket_id": 1}


def test_present_reserve_response_failure_no_data() -> None:
    response = UseCaseResponse(success=False, message="Ticket not available")
    d = present_reserve_response(response)

    assert d["success"] is False
    assert d["message"] == "Ticket not available"
    assert "data" not in d
