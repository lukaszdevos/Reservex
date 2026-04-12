import { useEffect, useRef } from 'react'
import type { EventLogType } from '../types'
import { useStore } from '../store/useStore'

const TYPE_COLORS: Record<EventLogType, string> = {
  success: 'text-success',
  error: 'text-error',
  warn: 'text-warning',
  info: 'text-info',
  db: 'text-purple-400',
  saga: 'text-accent-light',
}

const TYPE_ICONS: Record<EventLogType, string> = {
  success: '\u2713',
  error: '\u2717',
  warn: '\u26A0',
  info: '\u2139',
  db: '\uD83D\uDDC4',
  saga: '\u21A9',
}

export function EventLog() {
  const entries = useStore((s) => s.eventLog)
  const clearLog = useStore((s) => s.clearLog)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [entries.length])

  return (
    <div className="bg-surface rounded-lg border border-border p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider">
          Event Log
        </h2>
        <button
          onClick={clearLog}
          className="text-[10px] font-mono text-text-dim hover:text-text transition-colors"
        >
          clear
        </button>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-1 min-h-0 max-h-80">
        {entries.length === 0 ? (
          <p className="text-text-dim text-xs">No events yet.</p>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="animate-fade-in flex items-start gap-2 text-xs font-mono"
            >
              <span className="text-text-dim shrink-0 w-16">{entry.timestamp}</span>
              <span className={`shrink-0 w-4 ${TYPE_COLORS[entry.type]}`}>
                {TYPE_ICONS[entry.type]}
              </span>
              <span className={TYPE_COLORS[entry.type]}>{entry.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
