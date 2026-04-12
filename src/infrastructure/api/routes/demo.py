"""Demo scenario API routes for the frontend interactive dashboard.

Layer: infrastructure/api/routes
Scenarios stream events via WebSocket for the dashboard. Some routes are
visual demonstrations; the core mechanisms are covered by backend use cases
and integration tests against PostgreSQL and Redis.
"""

from __future__ import annotations

import asyncio
import random
import time

import structlog
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from domain.ticketing.model import Ticket, TicketStatus
from infrastructure.observability.metrics import (
    RESERVATION_DURATION,
    RESERVATIONS_TOTAL,
    STRIPE_CONCURRENT_REQUESTS,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# In-memory counters for the demo metrics endpoint
_demo_counters: dict[str, int] = {
    "requests": 0,
    "conflicts": 0,
}
_latency_samples: list[float] = []


async def _broadcast(
    request: Request, event: dict[str, object]
) -> None:
    """Send event to all WS clients for event_id=1."""
    broadcaster = request.app.state.broadcaster
    conns = list(broadcaster._connections.get(1, set()))
    for ws in conns:
        try:
            await ws.send_json(event)
        except Exception:
            broadcaster._connections[1].discard(ws)


def _saga_step_state(
    steps: list[str],
    current: str,
    status: str,
) -> list[dict[str, str]]:
    """Build SAGA step status list."""
    idx = steps.index(current)
    result: list[dict[str, str]] = []
    for i, s in enumerate(steps):
        if i < idx:
            result.append({"name": s, "status": "success"})
        elif i == idx:
            result.append({"name": s, "status": status})
        else:
            result.append({"name": s, "status": "pending"})
    return result


async def _sem_update(
    request: Request,
    active: int,
    queued: int,
    total: int,
) -> None:
    """Broadcast semaphore state."""
    await _broadcast(request, {
        "type": "semaphore_update",
        "active": active,
        "queued": queued,
        "total": total,
    })


@router.get("/metrics")
async def demo_metrics(request: Request) -> JSONResponse:
    """Return live metrics for the dashboard tiles."""
    conns = request.app.state.broadcaster._connections
    ws_count = len(conns.get(1, set()))
    avg_latency = (
        sum(_latency_samples[-100:])
        / len(_latency_samples[-100:])
        if _latency_samples
        else 0.0
    )
    return JSONResponse({
        "requests": _demo_counters["requests"],
        "conflicts": _demo_counters["conflicts"],
        "ws_clients": ws_count,
        "avg_latency_ms": round(avg_latency, 2),
    })


def _init_seats() -> list[dict[str, object]]:
    """Generate 48 seats (4 rows × 12 cols)."""
    seats: list[dict[str, object]] = []
    for i in range(48):
        row = chr(65 + i // 12)
        col = i % 12 + 1
        seats.append({
            "id": i + 1,
            "seat_number": f"{row}{col}",
            "status": "available",
        })
    return seats


@router.post("/scenarios/race")
async def scenario_race(request: Request) -> JSONResponse:
    """Race condition demo: N concurrent reservations."""
    concurrency = 50
    ticket = Ticket(id=42, event_id=1, seat_number="D7")

    await _broadcast(
        request, {"type": "seats_init", "seats": _init_seats()}
    )
    await _broadcast(request, {
        "type": "log",
        "level": "info",
        "message": f"Race: {concurrency} coroutines → seat #{ticket.id}",
    })
    await _broadcast(
        request, {"type": "layer_active", "layer": "asyncio"}
    )

    successes = 0
    conflicts = 0

    async def attempt(user_id: int) -> None:
        nonlocal successes, conflicts
        start = time.monotonic()
        try:
            if ticket.status == TicketStatus.AVAILABLE:
                ticket.reserve(user_id)
                successes += 1
                _demo_counters["requests"] += 1
                RESERVATIONS_TOTAL.labels(status="success").inc()
                await _broadcast(request, {
                    "type": "seat_update",
                    "seat_id": ticket.id,
                    "status": "reserved",
                })
                await _broadcast(request, {
                    "type": "log",
                    "level": "success",
                    "message": f"User {user_id} reserved #{ticket.id}",
                })
            else:
                conflicts += 1
                _demo_counters["conflicts"] += 1
                RESERVATIONS_TOTAL.labels(status="conflict").inc()
        except Exception:
            conflicts += 1
            _demo_counters["conflicts"] += 1
            RESERVATIONS_TOTAL.labels(status="conflict").inc()
        elapsed = (time.monotonic() - start) * 1000
        _latency_samples.append(elapsed)
        RESERVATION_DURATION.observe(elapsed / 1000)

    await asyncio.gather(
        *[attempt(i) for i in range(concurrency)],
        return_exceptions=True,
    )

    await _broadcast(request, {"type": "layer_idle"})
    await _broadcast(request, {
        "type": "log",
        "level": "info",
        "message": f"Race done: {successes} ok, {conflicts} conflicts",
    })

    return JSONResponse({
        "message": f"{successes} success, {conflicts} conflicts",
        "successes": successes,
        "conflicts": conflicts,
    })


@router.post("/scenarios/saga")
async def scenario_saga(request: Request) -> JSONResponse:
    """SAGA demo: step-by-step with failure at charge."""
    steps = ["validate", "reserve", "charge", "notify"]
    fail_at = "charge"

    await _broadcast(
        request, {"type": "layer_active", "layer": "asyncio"}
    )

    for step in steps:
        state = _saga_step_state(steps, step, "running")
        await _broadcast(
            request, {"type": "saga_update", "steps": state}
        )
        await _broadcast(request, {
            "type": "log",
            "level": "saga",
            "message": f"SAGA step: {step} (running)",
        })
        await asyncio.sleep(0.8)

        if step == fail_at:
            state = _saga_step_state(steps, step, "failed")
            await _broadcast(
                request, {"type": "saga_update", "steps": state}
            )
            await _broadcast(request, {
                "type": "log",
                "level": "error",
                "message": f"SAGA: {step} FAILED — card declined",
            })
            idx = steps.index(step)
            for comp in reversed(steps[:idx]):
                await asyncio.sleep(0.5)
                await _broadcast(request, {
                    "type": "log",
                    "level": "warn",
                    "message": f"SAGA compensating: {comp}",
                })
            await _broadcast(request, {
                "type": "log",
                "level": "info",
                "message": "SAGA rollback complete",
            })
            await _broadcast(request, {"type": "layer_idle"})
            return JSONResponse({
                "message": f"SAGA failed at {fail_at}, compensated",
            })

        state = _saga_step_state(steps, step, "success")
        await _broadcast(
            request, {"type": "saga_update", "steps": state}
        )

    await _broadcast(request, {"type": "layer_idle"})
    return JSONResponse({"message": "SAGA completed"})


@router.post("/scenarios/timeout")
async def scenario_timeout(request: Request) -> JSONResponse:
    """Timeout demo: progress bar, then auto-release."""
    duration_ms = 5000
    num_steps = 20

    await _broadcast(
        request, {"type": "layer_active", "layer": "asyncio"}
    )
    await _broadcast(request, {
        "type": "seat_update",
        "seat_id": 10,
        "status": "reserved",
    })
    await _broadcast(request, {
        "type": "log",
        "level": "info",
        "message": "Timeout: reservation started (5s TTL)",
    })

    for i in range(1, num_steps + 1):
        pct = (i / num_steps) * 100
        await _broadcast(
            request, {"type": "timeout_progress", "percent": pct}
        )
        await asyncio.sleep(duration_ms / num_steps / 1000)

    await _broadcast(request, {"type": "timeout_done"})
    await _broadcast(request, {
        "type": "seat_update",
        "seat_id": 10,
        "status": "available",
    })
    RESERVATIONS_TOTAL.labels(status="timeout").inc()
    await _broadcast(request, {
        "type": "log",
        "level": "warn",
        "message": "Timeout: expired, seat auto-released",
    })
    await _broadcast(request, {"type": "layer_idle"})
    return JSONResponse({"message": "Timeout expired, seat released"})


@router.post("/scenarios/semaphore")
async def scenario_semaphore(request: Request) -> JSONResponse:
    """Semaphore demo: 10-slot gate with queued requests."""
    total_slots = 10
    total_reqs = 20
    sem = asyncio.Semaphore(total_slots)
    active = 0
    queued = 0

    await _broadcast(
        request, {"type": "layer_active", "layer": "asyncio"}
    )

    async def stripe_call(i: int) -> None:
        nonlocal active, queued
        queued += 1
        await _sem_update(request, active, queued, total_slots)
        async with sem:
            queued -= 1
            active += 1
            STRIPE_CONCURRENT_REQUESTS.inc()
            await _sem_update(
                request, active, queued, total_slots
            )
            await _broadcast(request, {
                "type": "log",
                "level": "info",
                "message": f"Stripe #{i} ({active}/{total_slots})",
            })
            await asyncio.sleep(0.5)
            active -= 1
            STRIPE_CONCURRENT_REQUESTS.dec()
            await _sem_update(
                request, active, queued, total_slots
            )

    await asyncio.gather(
        *[stripe_call(i) for i in range(total_reqs)]
    )
    await _sem_update(request, 0, 0, total_slots)
    await _broadcast(request, {
        "type": "log",
        "level": "success",
        "message": f"Semaphore: {total_reqs} calls done",
    })
    await _broadcast(request, {"type": "layer_idle"})
    return JSONResponse({
        "message": f"All {total_reqs} calls processed",
    })


@router.post("/scenarios/broadcast")
async def scenario_broadcast(request: Request) -> JSONResponse:
    """WS broadcast demo: rapid seat updates."""
    await _broadcast(
        request, {"type": "layer_active", "layer": "asyncio"}
    )
    await _broadcast(
        request, {"type": "seats_init", "seats": _init_seats()}
    )
    await _broadcast(request, {
        "type": "log",
        "level": "info",
        "message": "Broadcast: rapid seat updates starting",
    })

    statuses = ["reserved", "confirmed", "available"]
    for _ in range(30):
        seat_id = random.randint(1, 48)
        status = random.choice(statuses)
        await _broadcast(request, {
            "type": "seat_update",
            "seat_id": seat_id,
            "status": status,
        })
        await asyncio.sleep(0.1)

    await _broadcast(request, {
        "type": "log",
        "level": "success",
        "message": "Broadcast: 30 updates sent",
    })
    await _broadcast(request, {"type": "layer_idle"})
    return JSONResponse({"message": "30 seat updates broadcast"})


@router.post("/scenarios/outbox")
async def scenario_outbox(request: Request) -> JSONResponse:
    """Outbox relay demo: transactional outbox pattern."""
    await _broadcast(
        request, {"type": "layer_active", "layer": "asyncio"}
    )

    steps = [
        ("db", "Outbox: BEGIN transaction"),
        ("db", "Outbox: INSERT ticket_events (confirmed)"),
        ("db", "Outbox: INSERT outbox_messages (published=false)"),
        ("db", "Outbox: COMMIT — both writes atomic"),
    ]
    for level, msg in steps:
        await _broadcast(request, {
            "type": "log", "level": level, "message": msg,
        })
        await asyncio.sleep(0.3)

    await asyncio.sleep(0.5)
    relay_steps = [
        ("info", "Relay: polling WHERE published=false"),
        ("info", "Relay: found 1 msg, publishing to Redis"),
        ("success", "Relay: XADD events:ticket.confirmed"),
        ("db", "Relay: UPDATE SET published=true"),
        ("success", "Outbox: relay complete, zero lost"),
    ]
    for level, msg in relay_steps:
        await _broadcast(request, {
            "type": "log", "level": level, "message": msg,
        })
        await asyncio.sleep(0.3)

    await _broadcast(request, {"type": "layer_idle"})
    return JSONResponse({"message": "Outbox relay demo complete"})
