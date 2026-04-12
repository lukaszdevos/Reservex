import { useEffect, useRef } from 'react'
import type { WsEvent } from '../types'
import { useStore } from '../store/useStore'

export function getUnprocessedWsEvents(
  messages: WsEvent[],
  lastProcessedId: number,
) {
  return messages.filter((event) => event.id > lastProcessedId)
}

export function useWsDispatch(messages: WsEvent[]) {
  const setSeats = useStore((s) => s.setSeats)
  const updateSeat = useStore((s) => s.updateSeat)
  const setSagaSteps = useStore((s) => s.setSagaSteps)
  const setTimeoutProgress = useStore((s) => s.setTimeoutProgress)
  const setTimeoutActive = useStore((s) => s.setTimeoutActive)
  const setSemaphore = useStore((s) => s.setSemaphore)
  const addLogEntry = useStore((s) => s.addLogEntry)
  const setActiveLayer = useStore((s) => s.setActiveLayer)
  const lastProcessedIdRef = useRef(-1)

  useEffect(() => {
    const unprocessed = getUnprocessedWsEvents(
      messages,
      lastProcessedIdRef.current,
    )

    for (const event of unprocessed) {
      lastProcessedIdRef.current = Math.max(
        lastProcessedIdRef.current,
        event.id,
      )
      const msg = event.message
      switch (msg.type) {
        case 'seats_init':
          setSeats(msg.seats)
          break

        case 'seat_update':
          updateSeat(msg.seat_id, msg.status)
          break

        case 'saga_update':
          setSagaSteps(msg.steps)
          break

        case 'timeout_progress':
          setTimeoutProgress(msg.percent)
          setTimeoutActive(true)
          break

        case 'timeout_done':
          setTimeoutActive(false)
          setTimeoutProgress(100)
          break

        case 'semaphore_update':
          setSemaphore({
            active: msg.active,
            queued: msg.queued,
            total: msg.total ?? 10,
          })
          break

        case 'layer_active':
          setActiveLayer(msg.layer)
          break

        case 'layer_idle':
          setActiveLayer(null)
          break

        case 'log':
          addLogEntry({
            id: crypto.randomUUID(),
            timestamp: new Date().toLocaleTimeString(),
            type: msg.level,
            message: msg.message,
          })
          break
      }
    }
  }, [messages, setSeats, updateSeat, setSagaSteps, setTimeoutProgress, setTimeoutActive, setSemaphore, addLogEntry, setActiveLayer])
}
