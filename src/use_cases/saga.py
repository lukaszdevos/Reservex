"""TicketPurchaseSaga — orchestrates the full ticket purchase flow.

Steps: validate → reserve → charge → notify
On failure: compensates completed steps in reverse order (best-effort).

Layer: use_cases
Imports: domain + stdlib only
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from domain.payment.gateway import PaymentGateway
from domain.shared.gateways import NotificationGateway, UserBlacklistGateway
from domain.ticketing.exceptions import TicketNotFoundError
from domain.ticketing.repository import TicketRepository
from use_cases.validators import (
    validate_payment_method,
    validate_ticket_available,
    validate_user_not_blacklisted,
)

logger = logging.getLogger(__name__)


@dataclass
class SagaContext:
    ticket_id: int
    user_id: int
    amount_cents: int
    payment_method: str
    correlation_id: str
    reservation_id: int = field(default=0)
    charge_id: str | None = field(default=None)


@dataclass
class SagaResult:
    success: bool
    failed_step: str | None = field(default=None)
    reason: str | None = field(default=None)


@dataclass
class SagaStep:
    name: str
    action: Callable[[SagaContext], Awaitable[None]]
    compensation: Callable[[SagaContext], Awaitable[None]] | None


class TicketPurchaseSaga:
    def __init__(
        self,
        ticket_repo: TicketRepository,
        payment_gateway: PaymentGateway,
        notifier: NotificationGateway,
        user_blacklist: UserBlacklistGateway,
    ) -> None:
        self._ticket_repo = ticket_repo
        self._payment_gateway = payment_gateway
        self._notifier = notifier
        self._user_blacklist = user_blacklist
        self._steps: list[SagaStep] = [
            SagaStep("validate", self._validate, None),
            SagaStep("reserve", self._reserve, self._release),
            SagaStep("charge", self._charge, self._refund),
            SagaStep("notify", self._notify, None),
        ]

    async def execute(self, ctx: SagaContext) -> SagaResult:
        executed: list[SagaStep] = []
        for step in self._steps:
            try:
                await step.action(ctx)
                executed.append(step)
            except Exception as exc:
                await self._compensate(ctx, executed)
                return SagaResult(success=False, failed_step=step.name, reason=str(exc))
        return SagaResult(success=True)

    async def _compensate(self, ctx: SagaContext, executed: list[SagaStep]) -> None:
        for step in reversed(executed):
            if step.compensation is not None:
                try:
                    await step.compensation(ctx)
                except Exception as exc:
                    logger.critical(
                        "compensation_failed step=%s error=%s", step.name, str(exc)
                    )

    async def _validate(self, ctx: SagaContext) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(validate_ticket_available(ctx.ticket_id, self._ticket_repo))
            tg.create_task(
                validate_user_not_blacklisted(ctx.user_id, self._user_blacklist)
            )
            tg.create_task(
                validate_payment_method(ctx.payment_method, self._payment_gateway)
            )

    async def _reserve(self, ctx: SagaContext) -> None:
        ticket = await self._ticket_repo.get_for_update(ctx.ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ctx.ticket_id)
        reservation = ticket.reserve(ctx.user_id)
        await self._ticket_repo.add(ticket)
        ctx.reservation_id = reservation.id

    async def _charge(self, ctx: SagaContext) -> None:
        charge_id = await self._payment_gateway.charge(
            ctx.reservation_id, ctx.amount_cents, ctx.payment_method
        )
        ctx.charge_id = charge_id

    async def _release(self, ctx: SagaContext) -> None:
        ticket = await self._ticket_repo.get(ctx.ticket_id)
        if ticket is not None:
            ticket.release(reason="saga_compensation")
            await self._ticket_repo.add(ticket)

    async def _refund(self, ctx: SagaContext) -> None:
        if ctx.charge_id is not None:
            await self._payment_gateway.refund(ctx.charge_id)

    async def _notify(self, ctx: SagaContext) -> None:
        await self._notifier.send_confirmation(ctx.user_id, ctx.reservation_id)
