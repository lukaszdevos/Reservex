"""ReserveTicketUseCase — reserves a ticket for a user.

Includes execute_with_timeout() which automatically releases and notifies
when the reservation window expires.

Layer: use_cases
Imports: domain + stdlib only
"""

from __future__ import annotations

import asyncio

from domain.shared.gateways import NotificationGateway
from domain.ticketing.exceptions import TicketAlreadyTakenError
from domain.ticketing.repository import TicketRepository
from use_cases.release_ticket import ReleaseTicketUseCase
from use_cases.request_objects import ReleaseTicketRequest, ReserveTicketRequest
from use_cases.response_objects import UseCaseResponse


class ReserveTicketUseCase:
    def __init__(
        self,
        ticket_repo: TicketRepository,
        notifier: NotificationGateway | None = None,
    ) -> None:
        self._repo = ticket_repo
        self._notifier = notifier

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

    async def execute_with_timeout(
        self,
        request: ReserveTicketRequest,
        timeout_seconds: int = 300,
    ) -> UseCaseResponse:
        try:
            async with asyncio.timeout(timeout_seconds):
                return await self.execute(request)
        except TimeoutError:
            release_uc = ReleaseTicketUseCase(self._repo)
            await release_uc.execute(
                ReleaseTicketRequest(ticket_id=request.ticket_id, reason="timeout")
            )
            if self._notifier is not None:
                await self._notifier.send_expiry(request.user_id, request.ticket_id)
            return UseCaseResponse(success=False, message="Reservation timed out")
