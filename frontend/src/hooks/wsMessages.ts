import type {
  ConcurrencyLayer,
  EventLogType,
  SagaStep,
  Seat,
  SeatStatus,
  WsMessage,
} from '../types'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isSeatStatus(value: unknown): value is SeatStatus {
  return (
    value === 'available'
    || value === 'reserved'
    || value === 'confirmed'
    || value === 'released'
  )
}

function isConcurrencyLayer(value: unknown): value is ConcurrencyLayer {
  return value === 'asyncio' || value === 'threadpool' || value === 'processpool'
}

function isSeat(value: unknown): value is Seat {
  return (
    isRecord(value)
    && typeof value.id === 'number'
    && typeof value.seat_number === 'string'
    && isSeatStatus(value.status)
  )
}

function isSagaStep(value: unknown): value is SagaStep {
  return (
    isRecord(value)
    && typeof value.name === 'string'
    && (
      value.status === 'pending'
      || value.status === 'running'
      || value.status === 'success'
      || value.status === 'failed'
    )
  )
}

export function toEventLogType(value: unknown): EventLogType {
  if (
    value === 'success'
    || value === 'error'
    || value === 'warn'
    || value === 'info'
    || value === 'db'
    || value === 'saga'
  ) {
    return value
  }
  return 'info'
}

export function parseWsMessage(value: unknown): WsMessage | null {
  if (!isRecord(value) || typeof value.type !== 'string') return null

  switch (value.type) {
    case 'seats_init':
      return Array.isArray(value.seats) && value.seats.every(isSeat)
        ? { type: 'seats_init', seats: value.seats }
        : null

    case 'seat_update':
      return typeof value.seat_id === 'number' && isSeatStatus(value.status)
        ? { type: 'seat_update', seat_id: value.seat_id, status: value.status }
        : null

    case 'saga_update':
      return Array.isArray(value.steps) && value.steps.every(isSagaStep)
        ? { type: 'saga_update', steps: value.steps }
        : null

    case 'timeout_progress':
      return typeof value.percent === 'number'
        ? { type: 'timeout_progress', percent: value.percent }
        : null

    case 'timeout_done':
      return { type: 'timeout_done' }

    case 'semaphore_update':
      return typeof value.active === 'number' && typeof value.queued === 'number'
        ? {
            type: 'semaphore_update',
            active: value.active,
            queued: value.queued,
            total: typeof value.total === 'number' ? value.total : undefined,
          }
        : null

    case 'layer_active':
      return isConcurrencyLayer(value.layer)
        ? { type: 'layer_active', layer: value.layer }
        : null

    case 'layer_idle':
      return { type: 'layer_idle' }

    case 'log':
      return typeof value.message === 'string'
        ? { type: 'log', level: toEventLogType(value.level), message: value.message }
        : null

    default:
      return null
  }
}
