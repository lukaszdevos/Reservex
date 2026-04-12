import { useStore } from '../store/useStore'

export function TimeoutBar() {
  const progress = useStore((s) => s.timeoutProgress)
  const active = useStore((s) => s.timeoutActive)
  const runningScenario = useStore((s) => s.runningScenario)
  const lastScenario = useStore((s) => s.lastScenario)
  const isTimeoutScenario = runningScenario === 'timeout' || lastScenario === 'timeout'

  const pct = Math.min(100, Math.max(0, progress))
  const hasProgress = pct > 0
  const barColor =
    pct >= 80 ? 'bg-error shadow-[0_0_8px_rgba(239,68,68,0.5)]'
    : pct >= 50 ? 'bg-warning shadow-[0_0_8px_rgba(245,158,11,0.4)]'
    : 'bg-accent shadow-[0_0_8px_rgba(124,58,237,0.3)]'

  const ttlRemaining = active ? Math.round((1 - pct / 100) * 5) : null

  return (
    <div className={`bg-surface rounded-lg border p-4 transition-all duration-300 ${
      isTimeoutScenario ? 'border-accent/60 shadow-[0_0_16px_rgba(124,58,237,0.15)]' : 'border-border'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Timeout
        </h2>
        <div className="flex items-center gap-2">
          {active && ttlRemaining !== null && (
            <span className={`text-[10px] font-mono ${pct >= 80 ? 'text-error' : 'text-warning'}`}>
              {ttlRemaining}s left
            </span>
          )}
          <span className={`text-xs font-mono ${hasProgress ? (pct >= 80 ? 'text-error' : 'text-accent-light') : 'text-text-dim'}`}>
            {hasProgress ? `${pct.toFixed(0)}%` : 'idle'}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full h-3 bg-surface-alt rounded-full overflow-hidden border border-border/50">
        <div
          className={`h-full rounded-full transition-all duration-300 ${hasProgress ? barColor : 'bg-surface-alt'}`}
          style={{ width: `${hasProgress ? pct : 0}%` }}
        />
      </div>

      {/* Context label */}
      <div className="mt-1.5 text-[10px] font-mono text-text-dim">
        {hasProgress
          ? pct >= 100 && !active
            ? '⏰ TTL expired - asyncio.timeout() fired, seat released'
            : '⏱ asyncio.timeout(5) - reservation TTL counting down'
          : 'asyncio.timeout() context manager - cooperative cancellation'
        }
      </div>
    </div>
  )
}
