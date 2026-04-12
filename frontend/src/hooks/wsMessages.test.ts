import { describe, expect, it } from 'vitest'
import { parseWsMessage, toEventLogType } from './wsMessages'

describe('parseWsMessage', () => {
  it('parses a valid seat update', () => {
    expect(parseWsMessage({
      type: 'seat_update',
      seat_id: 10,
      status: 'reserved',
    })).toEqual({
      type: 'seat_update',
      seat_id: 10,
      status: 'reserved',
    })
  })

  it('rejects malformed seat updates', () => {
    expect(parseWsMessage({
      type: 'seat_update',
      seat_id: '10',
      status: 'reserved',
    })).toBeNull()
  })

  it('parses valid seat initialization messages', () => {
    expect(parseWsMessage({
      type: 'seats_init',
      seats: [{ id: 1, seat_number: 'A1', status: 'available' }],
    })).toEqual({
      type: 'seats_init',
      seats: [{ id: 1, seat_number: 'A1', status: 'available' }],
    })
  })

  it('normalizes unknown log levels to info', () => {
    expect(parseWsMessage({
      type: 'log',
      level: 'verbose',
      message: 'connected',
    })).toEqual({
      type: 'log',
      level: 'info',
      message: 'connected',
    })
  })
})

describe('toEventLogType', () => {
  it('keeps supported log levels', () => {
    expect(toEventLogType('db')).toBe('db')
    expect(toEventLogType('saga')).toBe('saga')
  })

  it('falls back to info', () => {
    expect(toEventLogType('trace')).toBe('info')
  })
})
