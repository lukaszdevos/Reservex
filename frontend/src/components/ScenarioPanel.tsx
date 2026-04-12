import { useCallback } from 'react'
import type { ScenarioName } from '../types'
import { useStore } from '../store/useStore'

interface Scenario {
  name: ScenarioName
  icon: string
  label: string
  description: string
}

const SCENARIOS: Scenario[] = [
  { name: 'race', icon: '\u26A1', label: 'Race Condition', description: 'SELECT FOR UPDATE — 1000 users, 1 ticket' },
  { name: 'saga', icon: '\u21A9', label: 'SAGA Rollback', description: 'Step tracker + compensation on failure' },
  { name: 'timeout', icon: '\u23F1', label: 'Timeout Expiry', description: 'asyncio.timeout() — auto-release' },
  { name: 'semaphore', icon: '\uD83D\uDEE1', label: 'Semaphore Guard', description: 'asyncio.Semaphore(10) — Stripe cap' },
  { name: 'broadcast', icon: '\uD83D\uDCE1', label: 'WS Broadcast', description: 'asyncio.gather() — fan-out to clients' },
  { name: 'outbox', icon: '\uD83D\uDCEC', label: 'Outbox Relay', description: 'Transactional Outbox — DB + relay' },
]

export function ScenarioPanel() {
  const runningScenario = useStore((s) => s.runningScenario)
  const setRunningScenario = useStore((s) => s.setRunningScenario)
  const addLogEntry = useStore((s) => s.addLogEntry)

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

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
        Scenarios
      </h2>
      <div className="flex flex-col gap-2">
        {SCENARIOS.map((s) => (
          <button
            key={s.name}
            onClick={() => runScenario(s.name)}
            disabled={runningScenario !== null}
            className={`
              text-left px-3 py-2.5 rounded-md border transition-all text-sm
              ${
                runningScenario === s.name
                  ? 'border-accent bg-accent/10 text-accent-light animate-pulse-glow'
                  : 'border-border bg-surface-alt hover:border-accent/50 hover:bg-accent/5 text-text'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            <span className="mr-2">{s.icon}</span>
            <span className="font-medium">{s.label}</span>
            <p className="text-[10px] text-text-dim mt-0.5 ml-6">{s.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
