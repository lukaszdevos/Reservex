import { create } from 'zustand'
import type {
  ConcurrencyLayer,
  EventLogEntry,
  SagaStep,
  Seat,
  SemaphoreState,
  ThroughputPoint,
} from '../types'

const MAX_LOG_ENTRIES = 60
const MAX_THROUGHPUT_POINTS = 60

const DEFAULT_SAGA_STEPS: SagaStep[] = [
  { name: 'validate', status: 'pending' },
  { name: 'reserve', status: 'pending' },
  { name: 'charge', status: 'pending' },
  { name: 'notify', status: 'pending' },
]

interface AppState {
  // WebSocket
  wsConnected: boolean
  setWsConnected: (connected: boolean) => void

  // Seat map
  seats: Seat[]
  setSeats: (seats: Seat[]) => void
  updateSeat: (seatId: number, status: Seat['status']) => void
  clearSeats: () => void

  // SAGA visualizer
  sagaSteps: SagaStep[]
  setSagaSteps: (steps: SagaStep[]) => void
  resetSagaSteps: () => void

  // Timeout progress
  timeoutProgress: number
  timeoutActive: boolean
  setTimeoutProgress: (pct: number) => void
  setTimeoutActive: (active: boolean) => void

  // Semaphore gauge
  semaphore: SemaphoreState
  setSemaphore: (state: SemaphoreState) => void

  // Event log
  eventLog: EventLogEntry[]
  addLogEntry: (entry: EventLogEntry) => void
  clearLog: () => void

  // Metrics
  throughput: ThroughputPoint[]
  addThroughputPoint: (point: ThroughputPoint) => void

  // Concurrency layers
  activeLayer: ConcurrencyLayer | null
  setActiveLayer: (layer: ConcurrencyLayer | null) => void

  // Scenario running state
  runningScenario: string | null
  setRunningScenario: (name: string | null) => void

  // Reset all transient scenario state back to defaults
  resetScenarioState: () => void
}

export const useStore = create<AppState>((set) => ({
  wsConnected: false,
  setWsConnected: (connected) => set({ wsConnected: connected }),

  seats: [],
  setSeats: (seats) => set({ seats }),
  updateSeat: (seatId, status) =>
    set((state) => ({
      seats: state.seats.map((s) =>
        s.id === seatId ? { ...s, status } : s,
      ),
    })),
  clearSeats: () => set({ seats: [] }),

  sagaSteps: DEFAULT_SAGA_STEPS,
  setSagaSteps: (steps) => set({ sagaSteps: steps }),
  resetSagaSteps: () => set({ sagaSteps: DEFAULT_SAGA_STEPS }),

  timeoutProgress: 0,
  timeoutActive: false,
  setTimeoutProgress: (pct) => set({ timeoutProgress: pct }),
  setTimeoutActive: (active) => set({ timeoutActive: active }),

  semaphore: { active: 0, queued: 0, total: 10 },
  setSemaphore: (semaphore) => set({ semaphore }),

  eventLog: [],
  addLogEntry: (entry) =>
    set((state) => ({
      eventLog: [entry, ...state.eventLog].slice(0, MAX_LOG_ENTRIES),
    })),
  clearLog: () => set({ eventLog: [] }),

  throughput: [],
  addThroughputPoint: (point) =>
    set((state) => ({
      throughput: [...state.throughput, point].slice(-MAX_THROUGHPUT_POINTS),
    })),

  activeLayer: null,
  setActiveLayer: (layer) => set({ activeLayer: layer }),

  runningScenario: null,
  setRunningScenario: (name) => set({ runningScenario: name }),

  resetScenarioState: () =>
    set({
      sagaSteps: DEFAULT_SAGA_STEPS,
      timeoutProgress: 0,
      timeoutActive: false,
      semaphore: { active: 0, queued: 0, total: 10 },
      activeLayer: null,
      // seats keep their last state so user can see result; clear with next scenario
    }),
}))
