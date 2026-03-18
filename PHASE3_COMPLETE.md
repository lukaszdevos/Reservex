# Reservex — Phase 3 Complete: Adapters Layer

**Date completed:** 2026-03-18
**Branch:** `claude/phase-3-implementation-qmIBv`
**Repo:** `lukaszdevos/Reservex`

---

## What Was Built

Phase 3 is the adapters layer — **concrete implementations of all domain Protocols**,
plus database models, migrations, and serializers. First layer that imports third-party
libraries (SQLAlchemy, Redis, Stripe).

Clean Architecture rule: `adapters/` may import `domain/`, `use_cases/`, and third-party
libs. `infrastructure/` is still empty (Phase 4).

---

## Adapters Structure

```
src/
├── adapters/
│   ├── repositories/
│   │   ├── memory_ticket_repo.py    # MemoryTicketRepository — asyncio.Lock per ticket
│   │   └── postgres_ticket_repo.py  # PostgresTicketRepository — SELECT FOR UPDATE + optimistic lock
│   ├── gateways/
│   │   ├── redis_lock_gateway.py    # RedisDistributedLockGateway — SET NX + Lua CAS release
│   │   ├── stripe_gateway.py        # StripeGateway — Semaphore(10) + asyncio.to_thread
│   │   └── mock_payment_gateway.py  # MockPaymentGateway — configurable should_fail
│   ├── serializers.py               # ticket_to_dict, reservation_to_dict
│   └── presenters.py                # present_reserve_response
│
└── infrastructure/
    └── database/
        ├── models.py                # TicketModel, ReservationModel, OutboxMessageModel, TicketEventModel
        ├── session.py               # async_session_factory, get_session()
        └── migrations/
            ├── env.py               # Alembic async env with DATABASE_URL override
            └── versions/
                ├── 001_create_tickets.py
                ├── 002_create_reservations.py
                ├── 003_create_outbox.py
                └── 004_create_ticket_events.py
```

---

## Key Design Decisions

### 1. MemoryTicketRepository — one asyncio.Lock per ticket_id

`get_for_update()` acquires a per-ticket `asyncio.Lock`. The lock is held until
`add()` is called, which writes to `_store` then releases it. `get()` always returns
`copy.deepcopy()` to prevent callers mutating the store directly.

This faithfully mimics PostgreSQL's `SELECT FOR UPDATE` semantics in-process —
a second coroutine calling `get_for_update(same_id)` will suspend until the first
calls `add()`.

### 2. PostgresTicketRepository — two locking modes

- `get_for_update()` → `SELECT ... WITH FOR UPDATE` — pessimistic DB lock
- `add()` version check: `existing.version != ticket.version - 1` → raises
  `OptimisticLockConflict` — second line of defence for the non-locked read path

`_sync_reservation()` handles add / update / delete of the `ReservationModel`
child based on aggregate state, keeping the DB consistent with the domain model.

### 3. RedisDistributedLockGateway — Lua CAS release

Acquire: `SET key token NX PX ttl_ms` — atomic, returns `None` on contention.
Release: Lua script checks `GET key == token` before `DEL key` — guarantees we
never delete another owner's lock even if our TTL expired mid-execution.
`secrets.token_hex(16)` generates a cryptographically-random fencing token.

Method name is `lock()` to match the `DistributedLockGateway` Protocol exactly.

### 4. StripeGateway — asyncio.Semaphore(10) + asyncio.to_thread

The official Stripe Python SDK is synchronous. Rather than introducing a separate
async client, `asyncio.to_thread()` offloads each call to a thread pool.
`asyncio.Semaphore(10)` caps concurrent Stripe requests to avoid rate limiting.

### 5. Alembic async env.py

`env.py` uses `async_engine_from_config` + `asyncio.run()` to support the
`asyncpg` driver. `DATABASE_URL` env var overrides the `alembic.ini` default,
so the same config file works in CI, Railway, and local dev without edits.

### 6. Serializers are pure functions, not methods

`ticket_to_dict` and `reservation_to_dict` are module-level functions in
`adapters/serializers.py`. No class, no state. The presenter `present_reserve_response`
sits separately in `presenters.py` to keep HTTP shaping concerns isolated.

---

## Quality Checks

```
uv run ruff check .    → ✅ 0 errors
uv run mypy src/       → ✅ 0 errors (48 files, strict mode)
uv run pytest tests/unit -v  → ✅ 31/31 passed
```

### New Tests (10 added, 21 pre-existing)

#### test_memory_ticket_repo.py (5 tests)

| Test | Status |
|------|--------|
| `add()` then `get()` returns ticket with correct state | ✅ |
| `get()` unknown ticket_id returns `None` | ✅ |
| `get()` returns a copy, not the same object | ✅ |
| `get_for_update()` blocks second concurrent coroutine until `add()` releases | ✅ |
| `add()` after `get_for_update()` persists reserved state | ✅ |

#### test_serializers.py (5 tests)

| Test | Status |
|------|--------|
| `reservation_to_dict` round-trip: all fields match | ✅ |
| `ticket_to_dict` for AVAILABLE ticket: no reservation | ✅ |
| `ticket_to_dict` for RESERVED ticket: nested reservation dict | ✅ |
| `present_reserve_response` success includes data | ✅ |
| `present_reserve_response` failure omits `data` key | ✅ |

---

## Clean Architecture Import Verification

| Layer | Allowed | Actual |
|-------|---------|--------|
| `domain/` | stdlib only | ✅ unchanged |
| `use_cases/` | domain + stdlib | ✅ unchanged |
| `adapters/` | domain + use_cases + third-party | ✅ SQLAlchemy, Redis, Stripe |
| `infrastructure/database/` | everything | ✅ SQLAlchemy async engine |

---

## What Does NOT Exist Yet

- No FastAPI app factory or lifespan — Phase 4
- No dependency injection wiring — Phase 4
- No API routes (tickets, payments) — Phase 4
- No idempotency middleware — Phase 4
- No WebSocket broadcaster — Phase 4
- No outbox relay worker — Phase 4
- No integration tests (Testcontainers) — Phase 5

---

## Starting Phase 4

```
Phase 3 is complete. See PHASE3_COMPLETE.md for context.
Now implement Phase 4: Infrastructure Layer.
Start with P4.1 — FastAPI app factory with lifespan.
```
