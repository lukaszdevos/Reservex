from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reservation:
    id: int
    ticket_id: int
    user_id: int
    created_at: datetime
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
