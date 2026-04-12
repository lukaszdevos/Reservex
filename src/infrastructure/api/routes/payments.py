"""Payment API routes.

Layer: infrastructure/api/routes
Endpoints: trigger full SAGA purchase flow, refund a charge.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from infrastructure.api.dependencies import PaymentGatewayDep, SagaDep
from use_cases.saga import SagaContext

router = APIRouter()


class ChargeBody(BaseModel):
    ticket_id: int
    user_id: int
    amount_cents: int
    payment_method: str
    correlation_id: str = ""


@router.post("/charge")
async def charge(body: ChargeBody, saga: SagaDep) -> JSONResponse:
    """Run the full SAGA: validate → reserve → charge → notify."""
    ctx = SagaContext(
        ticket_id=body.ticket_id,
        user_id=body.user_id,
        amount_cents=body.amount_cents,
        payment_method=body.payment_method,
        correlation_id=body.correlation_id or str(uuid.uuid4()),
    )
    result = await saga.execute(ctx)
    status = 200 if result.success else 402
    return JSONResponse(
        {
            "success": result.success,
            "failed_step": result.failed_step,
            "reason": result.reason,
        },
        status_code=status,
    )


@router.post("/refund/{charge_id}")
async def refund(charge_id: str, payment_gateway: PaymentGatewayDep) -> JSONResponse:
    """Refund a previously created charge."""
    await payment_gateway.refund(charge_id)
    return JSONResponse({"success": True, "charge_id": charge_id})
