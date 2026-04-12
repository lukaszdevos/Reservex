"""Ticket management API routes.

Layer: infrastructure/api/routes
Endpoints: list seats, reserve, release, get status.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select
from starlette.responses import JSONResponse

from adapters.presenters import present_reserve_response
from adapters.serializers import ticket_to_dict
from infrastructure.api.dependencies import (
    ReleaseUseCaseDep,
    ReserveUseCaseDep,
    SessionDep,
    TicketRepoDep,
)
from infrastructure.api.middleware.rate_limit import limiter
from infrastructure.database.models import TicketModel
from use_cases.request_objects import ReleaseTicketRequest, ReserveTicketRequest

router = APIRouter()


class ReserveBody(BaseModel):
    user_id: int
    idempotency_key: str = ""


class ReleaseBody(BaseModel):
    reason: str = "user_request"


@router.get("/{event_id}")
async def list_tickets(event_id: int, session: SessionDep) -> JSONResponse:
    """List all seats for an event with their current status."""
    result = await session.execute(
        select(TicketModel).where(TicketModel.event_id == event_id)
    )
    models = result.scalars().all()
    tickets = [
        {"id": m.id, "seat_number": m.seat_number, "status": m.status}
        for m in models
    ]
    return JSONResponse({"event_id": event_id, "tickets": tickets})


@router.post("/{ticket_id}/reserve")
@limiter.limit("100/minute")
async def reserve_ticket(
    ticket_id: int,
    body: ReserveBody,
    request: Request,
    use_case: ReserveUseCaseDep,
) -> JSONResponse:
    """Reserve a ticket for a user; expiry is handled by a background worker."""
    req = ReserveTicketRequest(
        ticket_id=ticket_id,
        user_id=body.user_id,
        idempotency_key=body.idempotency_key,
    )
    response = await use_case.execute(req)
    status = 200 if response.success else 409
    return JSONResponse(present_reserve_response(response), status_code=status)


@router.post("/{ticket_id}/release")
async def release_ticket(
    ticket_id: int,
    body: ReleaseBody,
    use_case: ReleaseUseCaseDep,
) -> JSONResponse:
    """Release a reserved ticket back to AVAILABLE."""
    req = ReleaseTicketRequest(ticket_id=ticket_id, reason=body.reason)
    response = await use_case.execute(req)
    return JSONResponse({"success": response.success, "message": response.message})


@router.get("/{ticket_id}/status")
async def ticket_status(ticket_id: int, ticket_repo: TicketRepoDep) -> JSONResponse:
    """Return the current status of a single ticket."""
    ticket = await ticket_repo.get(ticket_id)
    if ticket is None:
        return JSONResponse({"error": "Ticket not found"}, status_code=404)
    return JSONResponse(ticket_to_dict(ticket))
