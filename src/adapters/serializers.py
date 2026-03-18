"""Domain entity → plain dict serializers.

Layer: adapters
Used by presenters and API route handlers.
"""

from domain.ticketing.model import Reservation, Ticket


def reservation_to_dict(res: Reservation) -> dict[str, object]:
    return {
        "id": res.id,
        "ticket_id": res.ticket_id,
        "user_id": res.user_id,
        "created_at": res.created_at.isoformat(),
        "expires_at": res.expires_at.isoformat(),
    }


def ticket_to_dict(ticket: Ticket) -> dict[str, object]:
    return {
        "id": ticket.id,
        "event_id": ticket.event_id,
        "seat_number": ticket.seat_number,
        "status": ticket.status.value,
        "reserved_by": ticket.reserved_by,
        "version": ticket.version,
        "reservation": (
            reservation_to_dict(ticket.reservation)
            if ticket.reservation is not None
            else None
        ),
    }
