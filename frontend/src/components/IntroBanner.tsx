import { useState } from 'react'

const PILLARS = [
  { icon: '🔀', label: 'asyncio', detail: 'Coroutines, TaskGroup, Semaphore, workers' },
  { icon: '🐘', label: 'PostgreSQL', detail: 'SELECT FOR UPDATE · optimistic version column' },
  { icon: '⚡', label: 'Redis', detail: 'SET NX lock · Streams for outbox relay' },
  { icon: '🧩', label: 'Clean Arch', detail: 'Domain → Use Cases → Adapters → Infra' },
  { icon: '🎯', label: 'SAGA', detail: 'Orchestrated compensation on distributed failure' },
  { icon: '📦', label: 'Outbox', detail: 'Atomic dual-write eliminator, zero lost events' },
]

export function IntroBanner() {
  const [open, setOpen] = useState(false)

  if (!open) {
    return (
      <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-surface/50 flex-shrink-0">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-accent/20 text-accent-light border border-accent/30 tracking-widest uppercase flex-shrink-0">
            Portfolio Demo
          </span>
          <span className="text-xs font-semibold text-text truncate">
            ReserveX - Distributed Reservation Platform
          </span>
          <span className="text-[10px] text-text-dim hidden lg:block truncate">
            Python 3.12 · FastAPI · React · asyncio · PostgreSQL · Redis · Clean Architecture · SAGA · Outbox
          </span>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="text-[10px] font-mono text-text-dim hover:text-accent-light transition-colors whitespace-nowrap flex-shrink-0 underline underline-offset-2"
        >
          about ↓
        </button>
      </div>
    )
  }

  return (
    <div className="flex-shrink-0 mx-4 mt-2 mb-0 bg-surface border border-border rounded-xl p-3 animate-fade-in">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-accent/20 text-accent-light border border-accent/30 tracking-widest uppercase">
              Portfolio Demo
            </span>
            <span className="text-[10px] text-text-dim font-mono">Python 3.12 · FastAPI · React · Railway</span>
          </div>
          <h1 className="text-base font-bold text-text leading-tight">
            ReserveX{' '}
            <span className="text-accent-light font-normal text-sm">
              - Distributed Reservation &amp; Payment Platform
            </span>
          </h1>
          <p className="mt-1 text-xs text-text-dim leading-relaxed max-w-2xl">
            A production-oriented system demonstrating Python concurrency, distributed-systems
            reliability patterns, and Clean Architecture. Demo controls stream live backend events;
            core reservation mechanisms are backed by integration tests against PostgreSQL and Redis.
            Watch the Seat Map, SAGA tracker, and Event Log react in real time via WebSocket.
          </p>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="text-text-dim hover:text-text transition-colors text-base leading-none flex-shrink-0"
          title="Collapse"
        >
          ✕
        </button>
      </div>

      <div className="mt-2 flex flex-wrap gap-1.5">
        {PILLARS.map((p) => (
          <div
            key={p.label}
            title={p.detail}
            className="group flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-alt border border-border hover:border-accent/50 transition-all cursor-default"
          >
            <span className="text-xs">{p.icon}</span>
            <span className="text-[10px] font-mono font-semibold text-text-dim group-hover:text-accent-light transition-colors">
              {p.label}
            </span>
          </div>
        ))}
      </div>

      <p className="mt-2 text-[10px] text-text-dim font-mono leading-relaxed border-t border-border pt-1.5">
        <span className="text-accent-light">Arch:</span>{' '}
        Domain (no deps) → Use Cases → Adapters → Infrastructure.{' '}
        <span className="text-accent-light">Locking:</span>{' '}
        Pessimistic (FOR UPDATE) · Optimistic (version) · Redis SET NX.
      </p>
    </div>
  )
}
