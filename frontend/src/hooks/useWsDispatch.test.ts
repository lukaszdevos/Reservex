import { describe, expect, it } from 'vitest'
import type { WsEvent } from '../types'
import { getUnprocessedWsEvents } from './useWsDispatch'

describe('getUnprocessedWsEvents', () => {
  it('uses monotonic ids when the capped buffer length stays the same', () => {
    const events: WsEvent[] = Array.from({ length: 100 }, (_, index) => ({
      id: index + 2,
      message: { type: 'layer_idle' },
    }))

    expect(getUnprocessedWsEvents(events, 100)).toEqual([
      { id: 101, message: { type: 'layer_idle' } },
    ])
  })
})
