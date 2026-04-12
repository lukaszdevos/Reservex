import { useStore } from '../store/useStore'

export function TimeoutBar() {
  const progress = useStore((s) => s.timeoutProgress)
  const active = useStore((s) => s.timeoutActive)

  const pct = Math.min(100, Math.max(0, progress))
  const barColor =
    pct >= 80
      ? 'bg-error'
      : pct >= 50
        ? 'bg-warning'
        : 'bg-accent'

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Timeout
        </h2>
        <span className="text-xs font-mono text-text-dim">
          {active ? `${pct.toFixed(0)}%` : 'idle'}
        </span>
      </div>
      <div className="w-full h-3 bg-surface-alt rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${active ? pct : 0}%` }}
        />
      </div>
    </div>
  )
}
