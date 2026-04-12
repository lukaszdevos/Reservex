export type SeatStatus = 'available' | 'reserved' | 'confirmed' | 'released'

export interface Seat {
  id: number
  seat_number: string
  status: SeatStatus
  reserved_by?: number | null
  version?: number
}

export type SagaStepStatus = 'pending' | 'running' | 'success' | 'failed'

export interface SagaStep {
  name: string
  status: SagaStepStatus
}

export type EventLogType = 'success' | 'error' | 'warn' | 'info' | 'db' | 'saga'

export interface EventLogEntry {
  id: string
  timestamp: string
  type: EventLogType
  message: string
}

export type ScenarioName = 'race' | 'saga' | 'timeout' | 'semaphore' | 'broadcast' | 'outbox'

export interface MetricsData {
  requests: number
  conflicts: number
  ws_clients: number
  avg_latency_ms: number
}

export interface ThroughputPoint {
  time: string
  throughput: number
}

export type ConcurrencyLayer = 'asyncio' | 'threadpool' | 'processpool'

export interface SemaphoreState {
  active: number
  queued: number
  total: number
}

export interface WsMessage {
  type: string
  [key: string]: unknown
}
