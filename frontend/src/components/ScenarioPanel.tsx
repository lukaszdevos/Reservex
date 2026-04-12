import { useCallback, useState } from 'react'
import type { ScenarioName } from '../types'
import { useStore } from '../store/useStore'

interface Scenario {
  name: ScenarioName
  icon: string
  label: string
  tagline: string
  tooltip: {
    mechanism: string
    what: string
    why: string
    code: string
  }
}

const SCENARIOS: Scenario[] = [
  {
    name: 'race',
    icon: '⚡',
    label: 'Race Condition',
    tagline: 'SELECT FOR UPDATE — 1 ticket, 50 users',
    tooltip: {
      mechanism: 'asyncio + PostgreSQL FOR UPDATE',
      what: '50 coroutines race to reserve the same seat simultaneously.',
      why: 'Demonstrates pessimistic locking: the DB row is locked at read-time, so only one transaction can proceed. All others block until the winner commits, then receive TicketAlreadyTakenError.',
      code: 'SELECT … WHERE id=? FOR UPDATE',
    },
  },
  {
    name: 'saga',
    icon: '↩',
    label: 'SAGA Rollback',
    tagline: 'SAGA orchestrator + compensating transactions',
    tooltip: {
      mechanism: 'TicketPurchaseSaga — 4-step orchestrator',
      what: 'Runs validate → reserve → charge → notify. Fails at "charge" (card declined).',
      why: 'SAGA pattern avoids distributed transactions by executing local steps and compensating in reverse on failure. The seat is auto-released when the payment fails, leaving the system in a consistent state.',
      code: '_compensate(ctx, reversed(executed))',
    },
  },
  {
    name: 'timeout',
    icon: '⏱',
    label: 'Timeout Expiry',
    tagline: 'asyncio.timeout() — cooperative cancellation',
    tooltip: {
      mechanism: 'asyncio.timeout(5) context manager',
      what: 'Reserves a seat with a 5-second TTL. When time runs out, the seat is auto-released.',
      why: 'asyncio.timeout() uses cooperative cancellation — no polling threads. The CancelledError propagates up, the cleanup code runs in the except block, and the event loop stays fully free.',
      code: 'async with asyncio.timeout(300): …',
    },
  },
  {
    name: 'semaphore',
    icon: '🛡',
    label: 'Semaphore Guard',
    tagline: 'asyncio.Semaphore(10) — Stripe rate cap',
    tooltip: {
      mechanism: 'asyncio.Semaphore with 10 permits',
      what: '20 concurrent Stripe calls dispatched; at most 10 run simultaneously.',
      why: 'Stripe\'s API has rate limits. A Semaphore in the gateway layer enforces a hard cap without a thread pool or external queue. Callers await the semaphore — no busy-wait, no dropped requests.',
      code: 'async with self._semaphore: await stripe.charge(…)',
    },
  },
  {
    name: 'broadcast',
    icon: '📡',
    label: 'WS Broadcast',
    tagline: 'asyncio.gather() — fan-out to all clients',
    tooltip: {
      mechanism: 'asyncio.gather(return_exceptions=True)',
      what: '30 rapid seat updates fan-out to every connected WebSocket client in parallel.',
      why: 'gather() sends all frames concurrently in the same event loop tick. return_exceptions=True ensures one dead client never stalls the broadcast — dead sockets are pruned after each round.',
      code: 'await asyncio.gather(*[ws.send_json(p) for ws in conns], return_exceptions=True)',
    },
  },
  {
    name: 'outbox',
    icon: '📬',
    label: 'Outbox Relay',
    tagline: 'Transactional Outbox — dual-write eliminator',
    tooltip: {
      mechanism: 'Transactional Outbox + background relay worker',
      what: 'Ticket confirmation and outbox message are committed in a single DB transaction. A background asyncio task polls and publishes to Redis Streams.',
      why: 'Solves the dual-write problem: without an outbox, a crash between the DB write and event publish silently loses the event. Here, both writes are atomic — the relay always has a record to publish.',
      code: 'session.add(OutboxMessage(…))  # same tx as ticket update',
    },
  },
]

function Tooltip({ scenario }: { scenario: Scenario }) {
  return (
    <div className="animate-slide-down overflow-hidden">
      <div className="mt-2 ml-6 p-3 rounded-md bg-bg border border-border/80 text-[11px] space-y-2">
        {/* Mechanism badge */}
        <div className="flex items-center gap-1.5">
          <span className="px-1.5 py-0.5 rounded bg-accent/20 text-accent-light font-mono text-[10px] font-semibold tracking-wide">
            {scenario.tooltip.mechanism}
          </span>
        </div>

        {/* What */}
        <div>
          <span className="text-text-dim font-semibold uppercase tracking-wider text-[9px]">WHAT HAPPENS</span>
          <p className="text-text mt-0.5 leading-relaxed">{scenario.tooltip.what}</p>
        </div>

        {/* Why */}
        <div>
          <span className="text-text-dim font-semibold uppercase tracking-wider text-[9px]">WHY IT MATTERS</span>
          <p className="text-text mt-0.5 leading-relaxed">{scenario.tooltip.why}</p>
        </div>

        {/* Code snippet */}
        <div className="font-mono bg-surface-alt rounded px-2 py-1.5 text-accent-light text-[10px] break-all leading-snug border border-border/50">
          {scenario.tooltip.code}
        </div>
      </div>
    </div>
  )
}

export function ScenarioPanel() {
  const runningScenario = useStore((s) => s.runningScenario)
  const setRunningScenario = useStore((s) => s.setRunningScenario)
  const addLogEntry = useStore((s) => s.addLogEntry)
  const [expandedTooltip, setExpandedTooltip] = useState<ScenarioName | null>(null)

  const runScenario = useCallback(
    async (name: ScenarioName) => {
      if (runningScenario) return
      setRunningScenario(name)
      addLogEntry({
        id: crypto.randomUUID(),
        timestamp: new Date().toLocaleTimeString(),
        type: 'info',
        message: `Starting scenario: ${name}`,
      })
      try {
        const res = await fetch(`/api/demo/scenarios/${name}`, { method: 'POST' })
        const data = await res.json()
        addLogEntry({
          id: crypto.randomUUID(),
          timestamp: new Date().toLocaleTimeString(),
          type: res.ok ? 'success' : 'error',
          message: `Scenario ${name}: ${data.message ?? (res.ok ? 'completed' : 'failed')}`,
        })
      } catch (err) {
        addLogEntry({
          id: crypto.randomUUID(),
          timestamp: new Date().toLocaleTimeString(),
          type: 'error',
          message: `Scenario ${name} failed: ${err instanceof Error ? err.message : 'unknown error'}`,
        })
      } finally {
        setRunningScenario(null)
      }
    },
    [runningScenario, setRunningScenario, addLogEntry],
  )

  const toggleTooltip = (name: ScenarioName, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpandedTooltip((prev) => (prev === name ? null : name))
  }

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
        Scenarios
      </h2>
      <div className="flex flex-col gap-2">
        {SCENARIOS.map((s) => {
          const isRunning = runningScenario === s.name
          const isExpanded = expandedTooltip === s.name

          return (
            <div key={s.name}>
              <div className="flex items-stretch gap-1.5">
                {/* Main run button */}
                <button
                  onClick={() => runScenario(s.name)}
                  disabled={runningScenario !== null}
                  className={`
                    flex-1 text-left px-3 py-2 rounded-md border transition-all text-sm
                    ${isRunning
                      ? 'border-accent bg-accent/10 text-accent-light animate-pulse-glow'
                      : 'border-border bg-surface-alt hover:border-accent/50 hover:bg-accent/5 text-text'
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  <div className="flex items-center gap-2">
                    <span>{s.icon}</span>
                    <span className="font-medium text-sm">{s.label}</span>
                  </div>
                  <p className="text-[10px] text-text-dim mt-0.5 ml-6 leading-snug">{s.tagline}</p>
                </button>

                {/* Info toggle button */}
                <button
                  onClick={(e) => toggleTooltip(s.name, e)}
                  title="Show technical details"
                  className={`
                    px-2 rounded-md border transition-all text-[11px] font-mono font-bold
                    ${isExpanded
                      ? 'border-accent/60 bg-accent/10 text-accent-light'
                      : 'border-border bg-surface-alt text-text-dim hover:border-accent/40 hover:text-accent-light'
                    }
                  `}
                >
                  {isExpanded ? '✕' : 'ℹ'}
                </button>
              </div>

              {/* Expandable tooltip */}
              {isExpanded && <Tooltip scenario={s} />}
            </div>
          )
        })}
      </div>
    </div>
  )
}
