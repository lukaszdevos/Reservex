import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from './components/Header'
import { SeatMap } from './components/SeatMap'
import { ScenarioPanel } from './components/ScenarioPanel'
import { SagaVisualizer } from './components/SagaVisualizer'
import { TimeoutBar } from './components/TimeoutBar'
import { SemaphoreGauge } from './components/SemaphoreGauge'
import { EventLog } from './components/EventLog'
import { MetricsDashboard } from './components/MetricsDashboard'
import { ConcurrencyLayers } from './components/ConcurrencyLayers'
import { useWebSocket } from './hooks/useWebSocket'
import { useWsDispatch } from './hooks/useWsDispatch'
import { useStore } from './store/useStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000,
      retry: false,
    },
  },
})

function Dashboard() {
  const { connected, messages } = useWebSocket('/ws/seat-map/1')
  const setWsConnected = useStore((s) => s.setWsConnected)

  useEffect(() => { setWsConnected(connected) }, [connected, setWsConnected])
  useWsDispatch(messages)

  return (
    <div className="flex-1 grid grid-cols-[260px_1fr_280px] gap-4 p-4 min-h-0">
      {/* Left column — Scenarios + controls */}
      <div className="flex flex-col gap-4 overflow-y-auto">
        <ScenarioPanel />
        <SagaVisualizer />
        <TimeoutBar />
        <SemaphoreGauge />
      </div>

      {/* Center — Seat Map + Metrics */}
      <div className="flex flex-col gap-4 overflow-y-auto">
        <SeatMap />
        <ConcurrencyLayers />
        <MetricsDashboard />
      </div>

      {/* Right column — Event Log */}
      <div className="flex flex-col min-h-0">
        <EventLog />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex flex-col h-screen bg-bg text-text">
        <Header />
        <Dashboard />
      </div>
    </QueryClientProvider>
  )
}
