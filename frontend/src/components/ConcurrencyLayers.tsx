import type { ConcurrencyLayer } from '../types'
import { useStore } from '../store/useStore'

interface LayerInfo {
  id: ConcurrencyLayer
  label: string
  description: string
  icon: string
  // Which scenarios activate this layer
  usedBy: string[]
  detail: string
}

const LAYERS: LayerInfo[] = [
  {
    id: 'asyncio',
    label: 'asyncio',
    description: 'Event loop, coroutines, TaskGroup',
    icon: '⚡',
    usedBy: ['race', 'saga', 'timeout', 'semaphore', 'broadcast', 'outbox'],
    detail: 'Native Python coroutines. No threads. Full cooperative multitasking on a single thread.',
  },
  {
    id: 'threadpool',
    label: 'ThreadPool',
    description: 'SMTP, blocking I/O calls',
    icon: '🧵',
    usedBy: ['outbox'],
    detail: 'ThreadPoolExecutor for blocking libs (SMTP). Keeps event loop free during sync I/O.',
  },
  {
    id: 'processpool',
    label: 'ProcessPool',
    description: 'PDF generation, CPU-bound',
    icon: '⚙',
    usedBy: [],
    detail: 'ProcessPoolExecutor for CPU-bound work. Bypasses GIL for true parallelism.',
  },
]

export function ConcurrencyLayers() {
  const activeLayer = useStore((s) => s.activeLayer)
  const runningScenario = useStore((s) => s.runningScenario)

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Concurrency Layers
        </h2>
        {activeLayer && (
          <span className="text-[10px] font-mono text-accent-light animate-pulse-glow">
            {activeLayer} active
          </span>
        )}
      </div>
      <div className="grid grid-cols-3 gap-2">
        {LAYERS.map((layer) => {
          const isActive = activeLayer === layer.id
          const isRelevant = runningScenario ? layer.usedBy.includes(runningScenario) : false

          return (
            <div
              key={layer.id}
              title={layer.detail}
              className={`
                flex flex-col items-center py-3 px-2 rounded-md border transition-all duration-300 cursor-default
                ${isActive
                  ? 'border-accent bg-accent/10 text-accent-light shadow-[0_0_14px_rgba(124,58,237,0.35)]'
                  : isRelevant
                    ? 'border-accent/30 bg-accent/5 text-text'
                    : 'border-border bg-surface-alt text-text-dim'
                }
              `}
            >
              <span className={`text-xl mb-1 transition-all ${isActive ? 'scale-110' : ''}`}>
                {layer.icon}
              </span>
              <span className="font-mono text-xs font-semibold">{layer.label}</span>
              <span className="text-[9px] mt-0.5 text-center opacity-70 leading-tight">{layer.description}</span>
              {isActive && (
                <span className="mt-1.5 text-[9px] font-mono bg-accent/20 px-1.5 py-0.5 rounded-full animate-pulse-glow">
                  ● ACTIVE
                </span>
              )}
              {!isActive && isRelevant && (
                <span className="mt-1.5 text-[9px] font-mono text-accent-light/60">
                  ○ used
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
