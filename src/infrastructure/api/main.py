"""FastAPI application factory with lifespan resource management.

Layer: infrastructure/api
Entry point: uvicorn src.infrastructure.api.main:app --reload
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.responses import FileResponse

from infrastructure.api.middleware.idempotency import IdempotencyMiddleware
from infrastructure.api.middleware.rate_limit import configure_limiter
from infrastructure.api.routes import demo, payments, tickets
from infrastructure.api.websockets.seat_map import SeatMapBroadcaster, ws_router
from infrastructure.observability.logging import configure_structlog
from infrastructure.observability.metrics import configure_metrics
from infrastructure.observability.tracing import configure_otel
from infrastructure.settings import settings
from infrastructure.workers.outbox_relay import outbox_relay_worker
from infrastructure.workers.reservation_expiry import reservation_expiry_worker

STATIC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static"

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and graceful shutdown of all long-lived resources."""
    configure_structlog(settings.log_level)
    configure_metrics()
    configure_otel(settings.otel_exporter_otlp_endpoint, settings.service_name)

    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    redis_client: aioredis.Redis = aioredis.from_url(settings.redis_url)

    process_pool = ProcessPoolExecutor(max_workers=4)
    thread_pool = ThreadPoolExecutor(max_workers=10)
    broadcaster = SeatMapBroadcaster()

    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.redis = redis_client
    app.state.process_pool = process_pool
    app.state.thread_pool = thread_pool
    app.state.broadcaster = broadcaster

    relay_task = asyncio.create_task(
        outbox_relay_worker(session_factory, redis_client),
        name="outbox_relay",
    )
    expiry_task = asyncio.create_task(
        reservation_expiry_worker(
            session_factory,
            interval_seconds=settings.reservation_expiry_interval_seconds,
            batch_size=settings.reservation_expiry_batch_size,
        ),
        name="reservation_expiry",
    )
    _log.info("reservex startup complete environment=%s", settings.environment)

    yield

    relay_task.cancel()
    expiry_task.cancel()
    await asyncio.gather(relay_task, expiry_task, return_exceptions=True)
    process_pool.shutdown(wait=False)
    thread_pool.shutdown(wait=False)
    await redis_client.aclose()
    await engine.dispose()
    _log.info("reservex shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ReserveX",
        description="Distributed reservation and payment platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    configure_limiter(app)
    app.add_middleware(IdempotencyMiddleware)

    app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
    app.include_router(payments.router, prefix="/payments", tags=["payments"])
    app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
    app.include_router(ws_router, prefix="/ws", tags=["websocket"])

    app.mount("/metrics", make_asgi_app())

    if STATIC_DIR.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=STATIC_DIR / "assets"),
            name="static-assets",
        )

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            """Serve frontend SPA — fallback to index.html."""
            file = STATIC_DIR / full_path
            if file.is_file():
                return FileResponse(file)
            return FileResponse(STATIC_DIR / "index.html")

    return app


app: FastAPI = create_app()
