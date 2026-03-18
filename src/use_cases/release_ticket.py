"""ReleaseTicketUseCase — releases a reserved ticket back to AVAILABLE.

Layer: use_cases
Imports: domain + stdlib only
"""

from __future__ import annotations

from domain.ticketing.repository import TicketRepository
from use_cases.request_objects import ReleaseTicketRequest
from use_cases.response_objects import UseCaseResponse


class ReleaseTicketUseCase:
    def __init__(self, ticket_repo: TicketRepository) -> None:
        self._repo = ticket_repo

    async def execute(self, request: ReleaseTicketRequest) -> UseCaseResponse:
        ticket = await self._repo.get(request.ticket_id)
        if ticket is None:
            return UseCaseResponse(
                success=False,
                message=f"Ticket {request.ticket_id} not found",
            )
        ticket.release(reason=request.reason)
        await self._repo.add(ticket)
        return UseCaseResponse(success=True, message="Ticket released successfully")
