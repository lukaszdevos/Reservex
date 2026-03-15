from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from domain.exceptions import TicketAlreadyTakenError


class TicketStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"
    RELEASED = "released"


@dataclass
class Ticket:
    id: int
    event_id: int
    seat_number: str
    status: TicketStatus = field(default=TicketStatus.AVAILABLE)
    reserved_by: int | None = field(default=None)
    version: int = field(default=0)

    def reserve(self, user_id: int) -> None:
        if self.status != TicketStatus.AVAILABLE:
            raise TicketAlreadyTakenError(self.id)
        self.status = TicketStatus.RESERVED
        self.reserved_by = user_id
        self.version += 1

    def release(self) -> None:
        self.status = TicketStatus.AVAILABLE
        self.reserved_by = None
        self.version += 1

    def confirm(self) -> None:
        self.status = TicketStatus.CONFIRMED
        self.version += 1
