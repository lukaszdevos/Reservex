"""PostgreSQL ticket repository via SQLAlchemy async.

Layer: adapters
Implements: TicketRepository (domain.ticketing.repository)
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.ticketing.exceptions import OptimisticLockConflict
from domain.ticketing.model import Reservation, Ticket, TicketStatus
from infrastructure.database.models import ReservationModel, TicketModel


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


def _update_ticket_model(model: TicketModel, ticket: Ticket) -> None:
    model.status = ticket.status.value
    model.reserved_by = ticket.reserved_by
    model.version = ticket.version
    model.updated_at = datetime.now(UTC)


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
        )
        model = result.scalar_one_or_none()
        return _model_to_ticket(model) if model is not None else None

    async def get_for_update(self, ticket_id: int) -> Ticket | None:
        result = await self._session.execute(
            select(TicketModel)
            .where(TicketModel.id == ticket_id)
            .options(selectinload(TicketModel.reservation))
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return _model_to_ticket(model) if model is not None else None

    async def add(self, ticket: Ticket) -> None:
        result = await self._session.execute(
            select(TicketModel)
            .where(TicketModel.id == ticket.id)
            .options(selectinload(TicketModel.reservation))
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            self._session.add(_ticket_to_new_model(ticket))
            if ticket.reservation is not None:
                self._session.add(
                    ReservationModel(
                        ticket_id=ticket.id,
                        user_id=ticket.reservation.user_id,
                        created_at=ticket.reservation.created_at,
                        expires_at=ticket.reservation.expires_at,
                    )
                )
            return
        if existing.version != ticket.version - 1:
            raise OptimisticLockConflict(ticket.id, ticket.version - 1)
        _update_ticket_model(existing, ticket)
        await self._sync_reservation(existing, ticket)

    async def _sync_reservation(
        self, model: TicketModel, ticket: Ticket
    ) -> None:
        if ticket.reservation is None:
            if model.reservation is not None:
                await self._session.delete(model.reservation)
        elif model.reservation is None:
            self._session.add(
                ReservationModel(
                    ticket_id=ticket.id,
                    user_id=ticket.reservation.user_id,
                    created_at=ticket.reservation.created_at,
                    expires_at=ticket.reservation.expires_at,
                )
            )
        else:
            model.reservation.user_id = ticket.reservation.user_id
            model.reservation.expires_at = ticket.reservation.expires_at
