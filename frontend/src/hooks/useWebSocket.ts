import { useEffect, useRef } from 'react'
import { useTelemetryStore } from '../store/telemetryStore'
import type { TickUpdate } from '../types/telemetry'

const WS_URL   = 'ws://localhost:8000/ws/telemetry'
const BACKOFFS  = [1_000, 2_000, 5_000, 10_000] // ms

export function useWebSocket(): void {
  const setConnected  = useTelemetryStore((s) => s.setConnected)
  const setWsError    = useTelemetryStore((s) => s.setWsError)
  const applyTick     = useTelemetryStore((s) => s.applyTick)
  const retryRef      = useRef(0)
  const wsRef         = useRef<WebSocket | null>(null)
  const mountedRef    = useRef(true)

  useEffect(() => {
    mountedRef.current = true

    function connect() {
      if (!mountedRef.current) return

      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        retryRef.current = 0
        setConnected(true)
      }

      ws.onmessage = (ev: MessageEvent<string>) => {
        try {
          const payload = JSON.parse(ev.data) as TickUpdate
          if (payload.type === 'TICK_UPDATE') {
            applyTick(payload)
          }
        } catch {
          /* ignore malformed frames */
        }
      }

      ws.onerror = () => {
        setWsError('WebSocket error')
      }

      ws.onclose = () => {
        setConnected(false)
        if (!mountedRef.current) return
        const delay = BACKOFFS[Math.min(retryRef.current, BACKOFFS.length - 1)]
        retryRef.current += 1
        setTimeout(connect, delay)
      }
    }

    connect()

    return () => {
      mountedRef.current = false
      wsRef.current?.close()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
