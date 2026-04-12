import { animated, useSpring } from '@react-spring/web'
import type { SeatStatus } from '../types'
import { useStore } from '../store/useStore'

const STATUS_COLORS: Record<SeatStatus, string> = {
  available: 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400',
  reserved: 'bg-amber-500/20 border-amber-500/40 text-amber-400',
  confirmed: 'bg-blue-500/20 border-blue-500/40 text-blue-400',
  released: 'bg-gray-500/20 border-gray-500/40 text-gray-400',
}

function SeatCell({ id, seat_number, status }: { id: number; seat_number: string; status: SeatStatus }) {
  const spring = useSpring({
    from: { scale: 0.85, opacity: 0.5 },
    to: { scale: 1, opacity: 1 },
    reset: true,
    config: { tension: 300, friction: 20 },
  })

  return (
    <animated.div
      style={{ transform: spring.scale.to((s) => `scale(${s})`), opacity: spring.opacity }}
      className={`
        w-full aspect-square rounded-md border flex flex-col items-center justify-center
        text-[10px] font-mono cursor-default transition-colors
        ${STATUS_COLORS[status]}
      `}
      title={`Seat ${seat_number} (#${id}) — ${status}`}
    >
      <span className="font-semibold">{seat_number}</span>
    </animated.div>
  )
}

export function SeatMap() {
  const seats = useStore((s) => s.seats)

  if (seats.length === 0) {
    return (
      <div className="bg-surface rounded-lg border border-border p-6">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-4">
          Seat Map
        </h2>
        <p className="text-text-dim text-sm">No seats loaded. Run a scenario to populate.</p>
      </div>
    )
  }

  return (
    <div className="bg-surface rounded-lg border border-border p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Seat Map (Live WebSocket)
        </h2>
        <div className="flex flex-wrap gap-3 text-[10px] font-mono text-text-dim">
          <Legend color="emerald" label="available" />
          <Legend color="amber" label="reserved" />
          <Legend color="blue" label="confirmed" />
        </div>
      </div>

      <div className="mb-2 text-center text-[10px] font-mono text-text-dim uppercase tracking-widest">
        Stage
      </div>
      <div className="w-full h-1 bg-accent/30 rounded mb-4" />

      <div className="grid grid-cols-6 sm:grid-cols-8 lg:grid-cols-12 gap-1.5">
        {seats.map((seat) => (
          <SeatCell key={seat.id} {...seat} />
        ))}
      </div>
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  const colorMap: Record<string, string> = {
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    blue: 'bg-blue-500',
  }
  return (
    <span className="flex items-center gap-1">
      <span className={`w-2 h-2 rounded-sm ${colorMap[color]}`} />
      {label}
    </span>
  )
}
