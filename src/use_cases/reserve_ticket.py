"""ReserveTicketUseCase — reserves a ticket for a user.

Layer: use_cases
Imports: domain + stdlib only
"""

from __future__ import annotations

from domain.ticketing.exceptions import TicketAlreadyTakenError
from domain.ticketing.repository import TicketRepository
from use_cases.request_objects import ReserveTicketRequest
from use_cases.response_objects import UseCaseResponse


class ReserveTicketUseCase:
    def __init__(self, ticket_repo: TicketRepository) -> None:
        self._repo = ticket_repo

    async def execute(self, request: ReserveTicketRequest) -> UseCaseResponse:
        ticket = await self._repo.get_for_update(request.ticket_id)
        if ticket is None:
            return UseCaseResponse(
                success=False,
                message=f"Ticket {request.ticket_id} not found",
            )
        try:
            reservation = ticket.reserve(request.user_id)
            await self._repo.add(ticket)
            return UseCaseResponse(
                success=True,
                message="Ticket reserved successfully",
                data={
                    "ticket_id": ticket.id,
                    "reservation_id": reservation.id,
                    "expires_at": reservation.expires_at.isoformat(),
                },
            )
        except TicketAlreadyTakenError as exc:
            return UseCaseResponse(success=False, message=str(exc))
