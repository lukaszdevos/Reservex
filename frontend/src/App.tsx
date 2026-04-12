import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Header } from './components/Header'
import { IntroBanner } from './components/IntroBanner'
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
    <div className="flex-1 grid grid-cols-1 xl:grid-cols-[280px_minmax(0,1fr)_300px] gap-4 p-3 sm:p-4 min-h-0 overflow-y-auto xl:overflow-hidden">
      <div className="flex flex-col gap-4 min-w-0 xl:overflow-y-auto hide-scrollbar">
        <ScenarioPanel />
        <SagaVisualizer />
        <TimeoutBar />
        <SemaphoreGauge />
      </div>

      <div className="flex flex-col gap-4 min-w-0 xl:overflow-y-auto hide-scrollbar">
        <SeatMap />
        <ConcurrencyLayers />
        <MetricsDashboard />
      </div>

      <div className="flex flex-col min-h-0 min-w-0">
        <EventLog />
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex flex-col min-h-screen xl:h-screen bg-bg text-text overflow-x-hidden xl:overflow-hidden">
        <Header />
        <div className="flex-shrink-0">
          <IntroBanner />
        </div>
        <Dashboard />
      </div>
    </QueryClientProvider>
  )
}
