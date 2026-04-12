import { useStore } from '../store/useStore'

export function Header() {
  const connected = useStore((s) => s.wsConnected)

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-text tracking-tight">
          ReserveX
        </h1>
        <span className="text-xs text-text-dim font-mono bg-surface-alt px-2 py-0.5 rounded">
          Demo
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm font-mono text-text-dim">
        <StatusDot label="WS" active={connected} />
      </div>
    </header>
  )
}

function StatusDot({ label, active }: { label: string; active: boolean }) {
  return (
    <span className="flex items-center gap-1.5">
      {label}
      <span
        className={`w-2 h-2 rounded-full ${
          active ? 'bg-success' : 'bg-error'
        }`}
      />
    </span>
  )
}
