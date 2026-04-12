import { useState } from 'react'

const PILLARS = [
  { icon: '🔀', label: 'asyncio', detail: 'Native coroutines, TaskGroup, Semaphore, timeout' },
  { icon: '🐘', label: 'PostgreSQL', detail: 'SELECT FOR UPDATE · optimistic version column' },
  { icon: '⚡', label: 'Redis', detail: 'Distributed Redlock · Streams for outbox relay' },
  { icon: '🧩', label: 'Clean Arch', detail: 'Domain → Use Cases → Adapters → Infrastructure' },
  { icon: '🎯', label: 'SAGA', detail: 'Orchestrated compensation on distributed failure' },
  { icon: '📦', label: 'Outbox', detail: 'Atomic dual-write eliminator, zero lost events' },
]

export function IntroBanner() {
  const [open, setOpen] = useState(true)

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="mx-4 mt-3 mb-0 text-[11px] font-mono text-text-dim hover:text-accent-light transition-colors underline underline-offset-2 self-start"
      >
        ▶ show app description
      </button>
    )
  }

  return (
    <div className="mx-4 mt-3 bg-surface border border-border rounded-xl p-4 animate-fade-in">
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-accent/20 text-accent-light border border-accent/30 tracking-widest uppercase">
              Portfolio Demo
            </span>
            <span className="text-[10px] text-text-dim font-mono">Python 3.12 · FastAPI · React · Railway</span>
          </div>
          <h1 className="text-xl font-bold text-text leading-tight">
            ReserveX{' '}
            <span className="text-accent-light font-normal text-base">
              — Distributed Reservation &amp; Payment Platform
            </span>
          </h1>
          <p className="mt-1.5 text-sm text-text-dim leading-relaxed max-w-2xl">
            A production-grade system built to demonstrate advanced Python concurrency,
            distributed-systems reliability patterns, and Clean Architecture (Cosmic Python).
            Every button below triggers{' '}
            <span className="text-text font-medium">real backend mechanisms</span> — no mocks.
            Watch the Seat Map, SAGA tracker, and Event Log react in real time via WebSocket.
          </p>
        </div>
        <button
          onClick={() => setOpen(false)}
          className="text-text-dim hover:text-text transition-colors text-lg leading-none mt-0.5 flex-shrink-0"
          title="Collapse"
        >
          ✕
        </button>
      </div>

      {/* Pillars */}
      <div className="mt-3 flex flex-wrap gap-2">
        {PILLARS.map((p) => (
          <div
            key={p.label}
            title={p.detail}
            className="group flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-alt border border-border hover:border-accent/50 transition-all cursor-default"
          >
            <span className="text-sm">{p.icon}</span>
            <span className="text-[11px] font-mono font-semibold text-text-dim group-hover:text-accent-light transition-colors">
              {p.label}
            </span>
            <span className="hidden group-hover:block text-[10px] text-text-dim ml-1 whitespace-nowrap animate-fade-in">
              — {p.detail}
            </span>
          </div>
        ))}
      </div>

      {/* Architecture note */}
      <p className="mt-3 text-[10px] text-text-dim font-mono leading-relaxed border-t border-border pt-2">
        <span className="text-accent-light">Architecture:</span>{' '}
        Domain (zero deps) → Use Cases (domain only) → Adapters (repos, gateways) → Infrastructure (FastAPI, SQLAlchemy, Redis).
        {' '}<span className="text-accent-light">Locking:</span>{' '}
        Pessimistic (FOR UPDATE) · Optimistic (version column) · Distributed (Redis Redlock) — switchable per scenario.
      </p>
    </div>
  )
}
