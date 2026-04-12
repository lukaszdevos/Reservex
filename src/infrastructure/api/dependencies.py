"""FastAPI dependency injection factory functions.

Layer: infrastructure/api
All stateful resources are read from app.state, which is populated during lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.gateways.mock_payment_gateway import MockPaymentGateway
from adapters.gateways.stub_gateways import (
    StubNotificationGateway,
    StubUserBlacklistGateway,
)
from adapters.repositories.postgres_ticket_repo import PostgresTicketRepository
from use_cases.release_ticket import ReleaseTicketUseCase
from use_cases.reserve_ticket import ReserveTicketUseCase
from use_cases.saga import TicketPurchaseSaga


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession from the app-scoped session factory."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_redis(request: Request) -> aioredis.Redis:
    """Return the app-scoped Redis client."""
    return request.app.state.redis  # type: ignore[no-any-return]


RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]


def get_ticket_repo(session: SessionDep) -> PostgresTicketRepository:
    return PostgresTicketRepository(session)


TicketRepoDep = Annotated[PostgresTicketRepository, Depends(get_ticket_repo)]


def get_reserve_use_case(ticket_repo: TicketRepoDep) -> ReserveTicketUseCase:
    return ReserveTicketUseCase(ticket_repo=ticket_repo)


ReserveUseCaseDep = Annotated[ReserveTicketUseCase, Depends(get_reserve_use_case)]


def get_release_use_case(ticket_repo: TicketRepoDep) -> ReleaseTicketUseCase:
    return ReleaseTicketUseCase(ticket_repo=ticket_repo)


ReleaseUseCaseDep = Annotated[ReleaseTicketUseCase, Depends(get_release_use_case)]


def get_payment_gateway() -> MockPaymentGateway:
    return MockPaymentGateway()


PaymentGatewayDep = Annotated[MockPaymentGateway, Depends(get_payment_gateway)]


def get_saga(
    ticket_repo: TicketRepoDep,
    payment_gateway: PaymentGatewayDep,
) -> TicketPurchaseSaga:
    return TicketPurchaseSaga(
        ticket_repo=ticket_repo,
        payment_gateway=payment_gateway,
        notifier=StubNotificationGateway(),
        user_blacklist=StubUserBlacklistGateway(),
    )


SagaDep = Annotated[TicketPurchaseSaga, Depends(get_saga)]
