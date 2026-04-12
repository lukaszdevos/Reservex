import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import type { MetricsData } from '../types'
import { useStore } from '../store/useStore'

async function fetchMetrics(): Promise<MetricsData> {
  const res = await fetch('/api/demo/metrics')
  if (!res.ok) {
    return { requests: 0, conflicts: 0, ws_clients: 0, avg_latency_ms: 0 }
  }
  return res.json()
}

function Tile({ label, value, unit }: { label: string; value: number; unit?: string }) {
  return (
    <div className="bg-surface-alt rounded-md border border-border p-3 text-center">
      <div className="text-lg font-bold font-mono text-text">
        {value.toLocaleString()}{unit && <span className="text-xs text-text-dim ml-0.5">{unit}</span>}
      </div>
      <div className="text-[10px] text-text-dim uppercase tracking-wider mt-1">{label}</div>
    </div>
  )
}

export function MetricsDashboard() {
  const throughput = useStore((s) => s.throughput)
  const addThroughputPoint = useStore((s) => s.addThroughputPoint)

  const { data } = useQuery({
    queryKey: ['metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 1000,
  })

  const metrics = data ?? { requests: 0, conflicts: 0, ws_clients: 0, avg_latency_ms: 0 }

  // Track throughput
  useQuery({
    queryKey: ['throughput-tracker'],
    queryFn: async () => {
      addThroughputPoint({
        time: new Date().toLocaleTimeString(),
        throughput: metrics.requests,
      })
      return null
    },
    refetchInterval: 1000,
  })

  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wider mb-3">
        Metrics
      </h2>
      <div className="grid grid-cols-4 gap-2 mb-4">
        <Tile label="Requests" value={metrics.requests} />
        <Tile label="Conflicts" value={metrics.conflicts} />
        <Tile label="WS Clients" value={metrics.ws_clients} />
        <Tile label="Avg Latency" value={metrics.avg_latency_ms} unit="ms" />
      </div>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={throughput}>
            <XAxis dataKey="time" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                background: '#1a1d27',
                border: '1px solid #2e3347',
                borderRadius: '6px',
                fontSize: '11px',
              }}
            />
            <Line
              type="monotone"
              dataKey="throughput"
              stroke="#7c3aed"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
