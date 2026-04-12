import { useStore } from '../store/useStore'

export function SemaphoreGauge() {
  const { active, queued, total } = useStore((s) => s.semaphore)
  const runningScenario = useStore((s) => s.runningScenario)
  const lastScenario = useStore((s) => s.lastScenario)
  const isSemaphoreScenario =
    runningScenario === 'semaphore' || lastScenario === 'semaphore'

  const fillPct = total > 0 ? Math.round((active / total) * 100) : 0
  const isAtCapacity = active >= total && total > 0
  const isComplete =
    lastScenario === 'semaphore'
    && runningScenario !== 'semaphore'
    && active === 0
    && queued === 0

  return (
    <div className={`bg-surface rounded-lg border p-4 transition-all duration-300 ${
      isSemaphoreScenario ? 'border-accent/60 shadow-[0_0_16px_rgba(124,58,237,0.15)]' : 'border-border'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Semaphore
        </h2>
        <div className="flex items-center gap-2">
          {isAtCapacity && isSemaphoreScenario && (
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-error/20 text-error border border-error/30 animate-pulse-glow">
              AT CAPACITY
            </span>
          )}
          {isComplete && (
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-success/15 text-success border border-success/30">
              COMPLETE
            </span>
          )}
          <span className="text-xs font-mono text-text-dim">
            {active}/{total}
            {queued > 0 && <span className="text-warning ml-1">+{queued} queued</span>}
          </span>
        </div>
      </div>

      {/* Slot grid */}
      <div className="flex gap-1 overflow-x-auto pb-1 hide-scrollbar">
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            title={i < active ? `Slot ${i + 1}: active` : `Slot ${i + 1}: free`}
            className={`
              flex-1 min-w-[18px] h-7 rounded-sm transition-all duration-200 border
              ${i < active
                ? 'bg-accent border-accent/60 shadow-[0_0_6px_rgba(124,58,237,0.5)]'
                : i < active + queued
                  ? 'bg-warning/30 border-warning/40'
                  : 'bg-surface-alt border-border'
              }
            `}
          />
        ))}
      </div>

      {/* Legend + description */}
      <div className="mt-1.5 flex items-center gap-3 text-[10px] font-mono text-text-dim">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-accent inline-block" /> active
        </span>
        {queued > 0 && (
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-warning/50 inline-block" /> queued
          </span>
        )}
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-surface-alt border border-border inline-block" /> free
        </span>
        <span className="ml-auto opacity-60">{fillPct}% used</span>
      </div>

      <div className="mt-1 text-[10px] font-mono text-text-dim opacity-70">
        asyncio.Semaphore({total}) - max {total} concurrent Stripe calls
      </div>
    </div>
  )
}
