import { useStore } from '../store/useStore'

export function SemaphoreGauge() {
  const { active, queued, total } = useStore((s) => s.semaphore)

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Semaphore
        </h2>
        <span className="text-xs font-mono text-text-dim">
          {active}/{total} active &middot; {queued} queued
        </span>
      </div>
      <div className="flex gap-1.5 overflow-x-auto pb-1 hide-scrollbar">
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            className={`
              flex-1 h-6 w-5 shrink-0 rounded-sm transition-colors duration-200
              ${i < active ? 'bg-accent shadow-[0_0_8px_rgba(124,58,237,0.4)]' : 'bg-surface-alt border border-border'}
            `}
          />
        ))}
      </div>
    </div>
  )
}
