import type { ConcurrencyLayer } from '../types'
import { useStore } from '../store/useStore'

interface LayerInfo {
  id: ConcurrencyLayer
  label: string
  description: string
  icon: string
}

const LAYERS: LayerInfo[] = [
  { id: 'asyncio', label: 'asyncio', description: 'Event loop, coroutines, TaskGroup', icon: '\u26A1' },
  { id: 'threadpool', label: 'ThreadPool', description: 'SMTP, blocking I/O calls', icon: '\uD83E\uDDF5' },
  { id: 'processpool', label: 'ProcessPool', description: 'PDF generation, CPU-bound', icon: '\u2699' },
]

export function ConcurrencyLayers() {
  const activeLayer = useStore((s) => s.activeLayer)

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
        Concurrency Layers
      </h2>
      <div className="flex gap-2">
        {LAYERS.map((layer) => {
          const isActive = activeLayer === layer.id
          return (
            <div
              key={layer.id}
              className={`
                flex-1 flex flex-col items-center py-4 px-3 rounded-md border transition-all
                ${
                  isActive
                    ? 'border-accent bg-accent/10 text-accent-light shadow-[0_0_12px_rgba(124,58,237,0.3)]'
                    : 'border-border bg-surface-alt text-text-dim'
                }
              `}
            >
              <span className="text-2xl mb-2">{layer.icon}</span>
              <span className="font-mono text-sm font-semibold">{layer.label}</span>
              <span className="text-[10px] mt-1 text-center opacity-70">{layer.description}</span>
              {isActive && (
                <span className="mt-2 text-[10px] font-mono bg-accent/20 px-2 py-0.5 rounded-full">
                  active
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
