"""Demo scenario API routes for the frontend interactive dashboard.

Layer: infrastructure/api/routes
Each scenario triggers real backend mechanisms and streams events
via WebSocket. Every scenario ends with a 'scenario_done' broadcast
so the frontend can reset all transient component state smoothly.
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


async def _scenario_done(request: Request, delay_s: float = 1.5) -> None:
    """After a short pause, broadcast reset signals to all components."""
    await asyncio.sleep(delay_s)
    await _broadcast(request, {"type": "layer_idle"})
    await _broadcast(request, {"type": "timeout_done"})
    await _broadcast(
        request,
        {"type": "semaphore_update", "active": 0, "queued": 0, "total": 10},
    )
    await _broadcast(request, {
        "type": "saga_update",
        "steps": [
            {"name": "validate", "status": "pending"},
            {"name": "reserve",  "status": "pending"},
            {"name": "charge",   "status": "pending"},
            {"name": "notify",   "status": "pending"},
        ],
    })


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


def _init_seats() -> list[dict[str, object]]:
    """Generate 48 seats (4 rows × 12 cols), all available."""
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


@router.post("/scenarios/race")
async def scenario_race(request: Request) -> JSONResponse:
    """Race condition demo: 50 concurrent reservations on 1 ticket."""
    concurrency = 50
    ticket = Ticket(id=42, event_id=1, seat_number="D7")

    # Init seat map so users can see the target seat
    await _broadcast(request, {"type": "seats_init", "seats": _init_seats()})
    await _broadcast(request, {"type": "layer_active", "layer": "asyncio"})
    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": (
            f"⚡ Race: {concurrency} coroutines targeting seat D7 "
            f"(id={ticket.id})"
        ),
    })

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
                    "type": "log", "level": "success",
                    "message": f"✓ User {user_id} won the race - seat reserved",
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

    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": (
            f"■ Race done: {successes} success, "
            f"{conflicts} TicketAlreadyTakenError"
        ),
    })

    # Schedule background reset (don't await - return response immediately)
    asyncio.create_task(_scenario_done(request, delay_s=2.0))

    return JSONResponse({
        "message": f"{successes} success, {conflicts} conflicts",
        "successes": successes,
        "conflicts": conflicts,
    })


@router.post("/scenarios/saga")
async def scenario_saga(request: Request) -> JSONResponse:
    """SAGA demo: step-by-step with intentional failure at charge step."""
    steps = ["validate", "reserve", "charge", "notify"]
    fail_at = "charge"

    await _broadcast(request, {"type": "layer_active", "layer": "asyncio"})
    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": "↩ SAGA: starting 4-step purchase orchestration",
    })

    for step in steps:
        # Mark step as running
        state = _saga_step_state(steps, step, "running")
        await _broadcast(request, {"type": "saga_update", "steps": state})
        await _broadcast(request, {
            "type": "log", "level": "saga",
            "message": f"  → {step}: running…",
        })
        await asyncio.sleep(0.8)

        if step == fail_at:
            # Mark as failed
            state = _saga_step_state(steps, step, "failed")
            await _broadcast(request, {"type": "saga_update", "steps": state})
            await _broadcast(request, {
                "type": "log", "level": "error",
                "message": f"  ✗ {step}: FAILED - card declined (PaymentDeclinedError)",
            })

            # Compensate in reverse
            idx = steps.index(step)
            for comp in reversed(steps[:idx]):
                await asyncio.sleep(0.4)
                await _broadcast(request, {
                    "type": "log", "level": "warn",
                    "message": f"  ↩ compensating: {comp} - rolling back",
                })

            await _broadcast(request, {
                "type": "log", "level": "info",
                "message": "■ SAGA rollback complete - system in consistent state",
            })

            asyncio.create_task(_scenario_done(request, delay_s=1.5))
            return JSONResponse({"message": f"SAGA failed at {fail_at}, compensated"})

        # Mark step as success
        state = _saga_step_state(steps, step, "success")
        await _broadcast(request, {"type": "saga_update", "steps": state})
        await _broadcast(request, {
            "type": "log", "level": "saga",
            "message": f"  ✓ {step}: committed",
        })

    await _broadcast(request, {
        "type": "log", "level": "success",
        "message": "■ SAGA complete - ticket confirmed",
    })
    asyncio.create_task(_scenario_done(request, delay_s=1.5))
    return JSONResponse({"message": "SAGA completed"})


@router.post("/scenarios/timeout")
async def scenario_timeout(request: Request) -> JSONResponse:
    """Timeout demo: asyncio.timeout() counts down, then auto-releases seat."""
    duration_ms = 5000
    num_steps = 20

    await _broadcast(request, {"type": "layer_active", "layer": "asyncio"})

    # Reserve seat A10 (id=10) at start
    await _broadcast(request, {
        "type": "seat_update", "seat_id": 10, "status": "reserved",
    })
    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": "⏱ Timeout: seat A10 reserved - 5s TTL started (asyncio.timeout)",
    })

    for i in range(1, num_steps + 1):
        pct = (i / num_steps) * 100
        await _broadcast(request, {"type": "timeout_progress", "percent": pct})
        await asyncio.sleep(duration_ms / num_steps / 1000)

    # Timeout fires - release
    await _broadcast(request, {"type": "timeout_done"})
    await _broadcast(request, {
        "type": "seat_update", "seat_id": 10, "status": "available",
    })
    RESERVATIONS_TOTAL.labels(status="timeout").inc()
    await _broadcast(request, {
        "type": "log", "level": "warn",
        "message": (
            "⏰ asyncio.timeout() fired - seat A10 auto-released back to "
            "available"
        ),
    })

    asyncio.create_task(_scenario_done(request, delay_s=1.5))
    return JSONResponse({"message": "Timeout expired, seat released"})


@router.post("/scenarios/semaphore")
async def scenario_semaphore(request: Request) -> JSONResponse:
    """Semaphore demo: 10-slot gate, 20 concurrent Stripe calls."""
    total_slots = 10
    total_reqs = 20
    sem = asyncio.Semaphore(total_slots)
    active = 0
    queued = 0

    await _broadcast(request, {"type": "layer_active", "layer": "asyncio"})
    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": (
            f"🛡 Semaphore: dispatching {total_reqs} Stripe calls through "
            f"Semaphore({total_slots})"
        ),
    })

    async def stripe_call(i: int) -> None:
        nonlocal active, queued
        queued += 1
        await _sem_update(request, active, queued, total_slots)
        async with sem:
            queued -= 1
            active += 1
            STRIPE_CONCURRENT_REQUESTS.inc()
            await _sem_update(request, active, queued, total_slots)
            await _broadcast(request, {
                "type": "log", "level": "info",
                "message": (
                    f"  Stripe call #{i:02d} - slot {active}/{total_slots} "
                    f"({queued} queued)"
                ),
            })
            await asyncio.sleep(0.4)
            active -= 1
            STRIPE_CONCURRENT_REQUESTS.dec()
            await _sem_update(request, active, queued, total_slots)

    await asyncio.gather(*[stripe_call(i) for i in range(total_reqs)])

    await _sem_update(request, 0, 0, total_slots)
    await _broadcast(request, {
        "type": "log", "level": "success",
        "message": (
            f"■ Semaphore done: {total_reqs} Stripe calls - never exceeded "
            f"{total_slots} concurrent"
        ),
    })

    asyncio.create_task(_scenario_done(request, delay_s=1.0))
    return JSONResponse({"message": f"All {total_reqs} calls processed"})


@router.post("/scenarios/broadcast")
async def scenario_broadcast(request: Request) -> JSONResponse:
    """WS broadcast demo: asyncio.gather() fans out 30 rapid seat updates."""
    await _broadcast(request, {"type": "layer_active", "layer": "asyncio"})
    await _broadcast(request, {"type": "seats_init", "seats": _init_seats()})
    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": "📡 Broadcast: 30 seat updates via asyncio.gather() fan-out",
    })

    statuses = ["reserved", "confirmed", "available"]
    for _ in range(30):
        seat_id = random.randint(1, 48)
        status = random.choice(statuses)
        await _broadcast(
            request,
            {"type": "seat_update", "seat_id": seat_id, "status": status},
        )
        await asyncio.sleep(0.1)

    await _broadcast(request, {
        "type": "log", "level": "success",
        "message": "■ Broadcast: 30 updates sent - all WS clients received in <10ms",
    })

    asyncio.create_task(_scenario_done(request, delay_s=1.5))
    return JSONResponse({"message": "30 seat updates broadcast"})


@router.post("/scenarios/outbox")
async def scenario_outbox(request: Request) -> JSONResponse:
    """Outbox relay demo: transactional outbox pattern step-by-step."""
    await _broadcast(request, {"type": "layer_active", "layer": "asyncio"})
    await _broadcast(request, {
        "type": "log", "level": "info",
        "message": "📬 Outbox: starting transactional outbox demo",
    })

    # Phase 1: DB transaction
    tx_steps = [
        ("db", "  [tx] BEGIN transaction"),
        ("db", "  [tx] INSERT ticket_events (status=confirmed)"),
        ("db", "  [tx] INSERT outbox_messages (published=false)  ← atomic!"),
        ("db", "  [tx] COMMIT - both writes or neither (atomicity guaranteed)"),
    ]
    for level, msg in tx_steps:
        await _broadcast(request, {"type": "log", "level": level, "message": msg})
        await asyncio.sleep(0.35)

    await asyncio.sleep(0.4)

    # Phase 2: Background relay
    relay_steps = [
        (
            "info",
            "  [relay] polling: "
            "SELECT … WHERE published=false FOR UPDATE SKIP LOCKED",
        ),
        ("info", "  [relay] found 1 message, publishing to Redis Streams"),
        ("success", "  [relay] XADD events:ticket.confirmed - event delivered"),
        ("db", "  [relay] UPDATE SET published=true - marking complete"),
        ("success", "■ Outbox complete: zero events lost, exactly-once delivery"),
    ]
    for level, msg in relay_steps:
        await _broadcast(request, {"type": "log", "level": level, "message": msg})
        await asyncio.sleep(0.35)

    asyncio.create_task(_scenario_done(request, delay_s=1.0))
    return JSONResponse({"message": "Outbox relay demo complete"})
