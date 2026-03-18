# Reservex — Phase 2 Complete: Use Cases Layer

**Date completed:** 2026-03-18
**Branch:** `claude/start-phase-2-jxiOP`
**Repo:** `lukaszdevos/Reservex`

---

## What Was Built

Phase 2 is the use cases layer — **pure business logic, zero framework imports**.
It follows Clean Architecture Layer 2 rules: imports only `domain/` and Python stdlib.

All orchestration of the ticket purchase flow lives here — use cases, SAGA, validators,
request/response DTOs — with no knowledge of SQLAlchemy, Redis, FastAPI, or Stripe.

---

## Use Cases Structure

```
src/use_cases/
├── request_objects.py   # Input DTOs: ReserveTicketRequest, ReleaseTicketRequest, ProcessPaymentRequest
├── response_objects.py  # Output DTO: UseCaseResponse(success, message, data)
├── reserve_ticket.py    # ReserveTicketUseCase + execute_with_timeout()
├── release_ticket.py    # ReleaseTicketUseCase
├── validators.py        # Three standalone async validator coroutines
└── saga.py              # TicketPurchaseSaga orchestrator + SagaContext, SagaResult, SagaStep
```

Also extended:

```
src/domain/shared/gateways.py  # + UserBlacklistGateway(Protocol)
```

---

## Key Design Decisions

### 1. Request / Response DTOs as plain dataclasses

`ReserveTicketRequest`, `ReleaseTicketRequest`, `ProcessPaymentRequest` are stdlib
`@dataclass` — no Pydantic, no validation. Validation is the SAGA's job.

`UseCaseResponse(success, message, data)` is the single return type for all use cases.
`data` carries structured output on success; `None` on failure. Callers pattern-match on `success`.

### 2. ReserveTicketUseCase — wraps the aggregate

`execute()` delegates to the domain aggregate:

```python
ticket = await self._repo.get_for_update(request.ticket_id)
reservation = ticket.reserve(request.user_id)   # aggregate changes state + emits event
await self._repo.add(ticket)                     # saves Ticket + its Reservation child
```

The use case never constructs `Reservation` directly — the aggregate owns that.

### 3. execute_with_timeout() — asyncio.timeout()

```python
async with asyncio.timeout(timeout_seconds):
    return await self.execute(request)
# On TimeoutError:
await ReleaseTicketUseCase(self._repo).execute(...)  # release the seat
await self._notifier.send_expiry(...)                # notify the user
```

Uses Python 3.11+ `asyncio.timeout()` (not `wait_for`). Cooperative cancellation —
no polling, no background thread.

### 4. SAGA Orchestrator — orchestrator style

`TicketPurchaseSaga` is the single coordinator for the full purchase flow:

```
HAPPY PATH:
  1. validate   ✓  (no compensation)
  2. reserve    ✓  (compensation: _release → ticket back to AVAILABLE)
  3. charge     ✓  (compensation: _refund  → Stripe refund)
  4. notify     ✓  (no compensation)

FAILURE AT STEP 3 (card declined):
  → _compensate([validate, reserve]) reversed: reserve → validate
  → _release runs: ticket returns to AVAILABLE
  → System in consistent state
```

Each compensation is wrapped in `try/except`. A compensation failure is logged at
CRITICAL level and the loop continues — rollback of remaining steps is never interrupted.

### 5. asyncio.TaskGroup — fail-fast parallel validation

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(validate_ticket_available(...))
    tg.create_task(validate_user_not_blacklisted(...))
    tg.create_task(validate_payment_method(...))
```

All three run concurrently. On the first failure, `TaskGroup` cancels the peers and
raises `ExceptionGroup`. The SAGA catches it as `Exception` at the step boundary.
Fail-fast: no waiting for remaining validators after one fails.

### 6. UserBlacklistGateway added to domain/shared

The validators require a user blacklist check. Rather than coupling the `use_cases/`
layer to a concrete implementation, a `UserBlacklistGateway(Protocol)` was added to
`domain/shared/gateways.py`. The SAGA receives it via constructor injection.

### 7. SagaContext carries mutable flow state

`SagaContext` is a mutable dataclass that steps write to as they complete:

| Field | Set by |
|-------|--------|
| `ticket_id`, `user_id`, `amount_cents`, `payment_method`, `correlation_id` | caller |
| `reservation_id` | `_reserve` step (after `ticket.reserve()`) |
| `charge_id` | `_charge` step (Stripe charge ID, needed by `_refund`) |

---

## Quality Checks

```
uv run ruff check .    → ✅ 0 errors
uv run mypy src/       → ✅ 0 errors (34 files, strict mode)
uv run pytest tests/unit -v  → ✅ 21/21 passed
```

### Tests

#### test_reserve_ticket.py (4 tests)

| Test | Status |
|------|--------|
| Happy path returns `success=True` with data payload | ✅ |
| `get_for_update()` called once, `add()` called once | ✅ |
| `get_for_update()` returns `None` → `success=False` | ✅ |
| `TicketAlreadyTakenError` → `success=False`, `data=None` | ✅ |

#### test_saga.py (4 tests)

| Test | Status |
|------|--------|
| Happy path: all 4 steps called in order | ✅ |
| Failure at charge (step 3) → `_release` compensation called, notify skipped | ✅ |
| Failure at validate (step 1) → no compensation, no reserve, no charge | ✅ |
| Compensation failure → rollback continues, `execute()` does not raise | ✅ |

---

## Clean Architecture Import Verification

| Layer | Allowed | Actual |
|-------|---------|--------|
| `domain/` | stdlib only | ✅ unchanged |
| `use_cases/` | domain + stdlib | ✅ no third-party imports |
| `adapters/` | domain + use_cases + third-party | (Phase 3) |
| `infrastructure/` | everything | (Phase 4) |

---

## What Does NOT Exist Yet

- No repository implementations — only Protocols — Phase 3
- No SQLAlchemy models or Alembic migrations — Phase 3
- No Redis lock gateway implementation — Phase 3
- No Stripe gateway implementation — Phase 3
- No FastAPI app factory or routes — Phase 4
- No integration tests — Phase 5

---

## Starting Phase 3

```
Phase 2 is complete. See PHASE2_COMPLETE.md for context.
Now implement Phase 3: Adapters Layer.
Start with P3.1 — MemoryTicketRepository (for tests).
```
