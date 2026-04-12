"""PostgreSQL ticket repository via SQLAlchemy async.

Layer: adapters
Implements: TicketRepository (domain.ticketing.repository)
"""

from dataclasses import asdict
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy import update as sqla_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.shared.event import DomainEvent
from domain.ticketing.events import TicketConfirmed, TicketReleased, TicketReserved
from domain.ticketing.exceptions import OptimisticLockConflict
from domain.ticketing.model import Reservation, Ticket, TicketStatus
from infrastructure.database.models import (
    OutboxMessageModel,
    ReservationModel,
    TicketEventModel,
    TicketModel,
)

_EVENT_TYPES: dict[type[DomainEvent], str] = {
    TicketReserved: "ticket.reserved",
    TicketReleased: "ticket.released",
    TicketConfirmed: "ticket.confirmed",
}


def _model_to_reservation(model: ReservationModel) -> Reservation:
    return Reservation(
        id=model.id,
        ticket_id=model.ticket_id,
        user_id=model.user_id,
        created_at=model.created_at,
        expires_at=model.expires_at,
    )


def _model_to_ticket(model: TicketModel) -> Ticket:
    reservation = (
        _model_to_reservation(model.reservation)
        if model.reservation is not None
        else None
    )
    return Ticket(
        id=model.id,
        event_id=model.event_id,
        seat_number=model.seat_number,
        status=TicketStatus(model.status),
        reserved_by=model.reserved_by,
        version=model.version,
        reservation=reservation,
    )


def _ticket_to_new_model(ticket: Ticket) -> TicketModel:
    now = datetime.now(UTC)
    return TicketModel(
        id=ticket.id,
        event_id=ticket.event_id,
        seat_number=ticket.seat_number,
        status=ticket.status.value,
        reserved_by=ticket.reserved_by,
        version=ticket.version,
        created_at=now,
        updated_at=now,
    )


def _event_type(event: DomainEvent) -> str:
    return _EVENT_TYPES.get(type(event), type(event).__name__)


def _event_payload(event: DomainEvent) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in asdict(event).items():
        payload[key] = value.isoformat() if isinstance(value, datetime) else value
    return payload


class PostgresTicketRepository:
    """PostgreSQL-backed repository for the Ticket aggregate.

    Uses optimistic locking via the ``version`` column.
    Implements: TicketRepository
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, ticket_id: int) -> Ticket | None:
        result = await self._session.execute(
            select(TicketModel)
            .where(TicketModel.id == ticket_id)
            .options(selectinload(TicketModel.reservation))
            .execution_options(populate_existing=True)
        )
        model = result.scalar_one_or_none()
        return _model_to_ticket(model) if model is not None else None

    async def get_for_update(self, ticket_id: int) -> Ticket | None:
        result = await self._session.execute(
            select(TicketModel)
            .where(TicketModel.id == ticket_id)
            .options(selectinload(TicketModel.reservation))
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        model = result.scalar_one_or_none()
        return _model_to_ticket(model) if model is not None else None

    async def add(self, ticket: Ticket) -> None:
        # populate_existing=True forces SQLAlchemy to reload from DB even if
        # the object is already in the identity map, preventing stale-cache bugs
        # when compensation logic re-reads a ticket loaded earlier in the saga.
        result = await self._session.execute(
            select(TicketModel)
            .where(TicketModel.id == ticket.id)
            .options(selectinload(TicketModel.reservation))
            .execution_options(populate_existing=True)
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            self._session.add(_ticket_to_new_model(ticket))
            if ticket.reservation is not None:
                reservation_model = ReservationModel(
                    ticket_id=ticket.id,
                    user_id=ticket.reservation.user_id,
                    created_at=ticket.reservation.created_at,
                    expires_at=ticket.reservation.expires_at,
                )
                self._session.add(reservation_model)
                await self._session.flush()
                ticket.reservation.id = reservation_model.id
            await self._persist_events(ticket)
            await self._session.flush()
            ticket.events.clear()
            return

        # Atomic optimistic-lock check: the UPDATE only succeeds when the row's
        # version still matches the pre-increment value.  An application-level
        # SELECT+compare is not atomic under concurrent sessions.
        update_result = await self._session.execute(
            sqla_update(TicketModel)
            .where(TicketModel.id == ticket.id)
            .where(TicketModel.version == ticket.version - 1)
            .values(
                status=ticket.status.value,
                reserved_by=ticket.reserved_by,
                version=ticket.version,
                updated_at=datetime.now(UTC),
            )
            .returning(TicketModel.id)
        )
        if update_result.scalar_one_or_none() is None:
            raise OptimisticLockConflict(ticket.id, ticket.version - 1)

        await self._sync_reservation(ticket)
        await self._persist_events(ticket)
        await self._session.flush()
        ticket.events.clear()

    async def _sync_reservation(self, ticket: Ticket) -> None:
        result = await self._session.execute(
            select(ReservationModel)
            .where(ReservationModel.ticket_id == ticket.id)
            .execution_options(populate_existing=True)
        )
        reservation_model = result.scalar_one_or_none()
        if ticket.reservation is None:
            if reservation_model is not None:
                await self._session.execute(
                    delete(ReservationModel).where(
                        ReservationModel.ticket_id == ticket.id
                    )
                )
        elif reservation_model is None:
            new_reservation_model = ReservationModel(
                ticket_id=ticket.id,
                user_id=ticket.reservation.user_id,
                created_at=ticket.reservation.created_at,
                expires_at=ticket.reservation.expires_at,
            )
            self._session.add(new_reservation_model)
            await self._session.flush()
            ticket.reservation.id = new_reservation_model.id
        else:
            reservation_model.user_id = ticket.reservation.user_id
            reservation_model.expires_at = ticket.reservation.expires_at
            ticket.reservation.id = reservation_model.id

    async def _persist_events(self, ticket: Ticket) -> None:
        for event in ticket.events:
            payload = _event_payload(event)
            ticket_id = payload.get("ticket_id")
            self._session.add(
                TicketEventModel(
                    ticket_id=ticket_id if isinstance(ticket_id, int) else ticket.id,
                    event_type=_event_type(event),
                    payload=payload,
                    occurred_at=event.occurred_at,
                    correlation_id=event.correlation_id,
                )
            )
            self._session.add(
                OutboxMessageModel(
                    event_type=_event_type(event),
                    payload=payload,
                    published=False,
                    created_at=datetime.now(UTC),
                )
            )
