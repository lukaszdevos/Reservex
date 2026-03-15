from __future__ import annotations

from datetime import UTC, datetime, timedelta

from domain.reservation import Reservation


def make_reservation(expires_delta: timedelta) -> Reservation:
    now = datetime.now(UTC)
    return Reservation(
        id=1,
        ticket_id=1,
        user_id=42,
        created_at=now,
        expires_at=now + expires_delta,
    )


def test_is_expired_returns_true_after_expires_at() -> None:
    reservation = make_reservation(expires_delta=timedelta(seconds=-1))
    assert reservation.is_expired() is True


def test_is_expired_returns_false_before_expires_at() -> None:
    reservation = make_reservation(expires_delta=timedelta(minutes=5))
    assert reservation.is_expired() is False
