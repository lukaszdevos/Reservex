"""Standalone validator coroutines used by the SAGA _validate step.

All three are meant to run concurrently via asyncio.TaskGroup so that the
first failure immediately cancels the remaining checks.

Layer: use_cases
Imports: domain + stdlib only
"""

from __future__ import annotations

from domain.payment.gateway import PaymentGateway
from domain.shared.gateways import UserBlacklistGateway
from domain.ticketing.exceptions import TicketAlreadyTakenError, TicketNotFoundError
from domain.ticketing.model import TicketStatus
from domain.ticketing.repository import TicketRepository


async def validate_ticket_available(ticket_id: int, repo: TicketRepository) -> None:
    """Raise if the ticket does not exist or is not AVAILABLE."""
    ticket = await repo.get(ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    if ticket.status != TicketStatus.AVAILABLE:
        raise TicketAlreadyTakenError(ticket_id)


async def validate_user_not_blacklisted(
    user_id: int, gateway: UserBlacklistGateway
) -> None:
    """Raise if the user is on the blacklist."""
    if await gateway.is_blacklisted(user_id):
        raise ValueError(f"User {user_id} is blacklisted and cannot make reservations")


async def validate_payment_method(method_id: str, gateway: PaymentGateway) -> None:
    """Raise if the payment method ID is blank."""
    if not method_id.strip():
        raise ValueError("Payment method ID cannot be empty")
