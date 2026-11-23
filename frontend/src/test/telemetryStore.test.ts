import { describe, it, expect, beforeEach } from 'vitest'
import { useTelemetryStore } from '../store/telemetryStore'
import type { TickUpdate, CellMetrics, Alert } from '../types/telemetry'

// ── helpers ───────────────────────────────────────────────────────────────────

function makeCell(hex: string): CellMetrics {
  return {
    hex,
    timestamp: '2026-09-01T09:00:00+05:30',
    tick_index: 1,
    demand: 50,
    supply: 40,
    cancellation_rate: 0.08,
    surge: 1.0,
    avg_eta_minutes: 5,
    is_rainy: false,
    rainfall_mm: 0,
    dsr: 1.25,
    z_score: 0.5,
    lgbm_pred: 48,
    residual: 2,
    iso_score: 0.3,
    anomaly_score: 0,
    severity: 'NORMAL',
    root_cause: 'NORMAL',
  }
}

function makeAlert(id: string): Alert {
  return {
    event_id:    id,
    hex:         'hexabc',
    locality:    'Koramangala',
    severity:    'HIGH',
    anomaly_score: 60,
    root_cause:  'DEMAND_SPIKE',
    title:       'HIGH: Demand Spike at Koramangala',
    timestamp:   '2026-09-01T09:00:00+05:30',
  }
}

function makeTick(cells: CellMetrics[], alerts: Alert[] = []): TickUpdate {
  return {
    type:            'TICK_UPDATE',
    simulation_time: '2026-09-01T09:00:00+05:30',
    tick_index:      1,
    summary: {
      total_demand:           cells.reduce((s, c) => s + c.demand, 0),
      total_supply:           cells.reduce((s, c) => s + c.supply, 0),
      active_anomalies_count: 0,
    },
    hex_updates: cells,
    new_alerts:  alerts,
  }
}

// ── tests ─────────────────────────────────────────────────────────────────────

describe('telemetryStore', () => {
  beforeEach(() => {
    useTelemetryStore.setState({
      cells:       new Map(),
      alerts:      [],
      tickIndex:   0,
      simTime:     '',
      selectedHex: null,
      isConnected: false,
    })
  })

  it('applyTick adds cells to the Map', () => {
    useTelemetryStore.getState().applyTick(
      makeTick([makeCell('hex1'), makeCell('hex2')]),
    )
    expect(useTelemetryStore.getState().cells.size).toBe(2)
  })

  it('applyTick updates tickIndex and simTime', () => {
    useTelemetryStore.getState().applyTick(makeTick([makeCell('hex1')]))
    const s = useTelemetryStore.getState()
    expect(s.tickIndex).toBe(1)
    expect(s.simTime).toBeTruthy()
  })

  it('subsequent ticks merge cells (upsert, not replace)', () => {
    useTelemetryStore.getState().applyTick(makeTick([makeCell('hex1')]))
    useTelemetryStore.getState().applyTick(makeTick([makeCell('hex2')]))
    expect(useTelemetryStore.getState().cells.size).toBe(2)
  })

  it('setSelectedHex stores the value', () => {
    useTelemetryStore.getState().setSelectedHex('abc123')
    expect(useTelemetryStore.getState().selectedHex).toBe('abc123')
  })

  it('clearAlerts empties the list', () => {
    useTelemetryStore.getState().applyTick(makeTick([], [makeAlert('1')]))
    useTelemetryStore.getState().clearAlerts()
    expect(useTelemetryStore.getState().alerts).toHaveLength(0)
  })

  it('alerts prepend newest first', () => {
    useTelemetryStore.getState().applyTick(makeTick([], [makeAlert('first')]))
    useTelemetryStore.getState().applyTick(makeTick([], [makeAlert('second')]))
    const alerts = useTelemetryStore.getState().alerts
    expect(alerts[0].event_id).toBe('second')
  })

  it('alerts are capped at 50', () => {
    const batch = Array.from({ length: 60 }, (_, i) => makeAlert(String(i)))
    useTelemetryStore.getState().applyTick(makeTick([], batch))
    expect(useTelemetryStore.getState().alerts.length).toBeLessThanOrEqual(50)
  })

  it('setConnected sets isConnected and clears wsError', () => {
    useTelemetryStore.setState({ wsError: 'previous error' })
    useTelemetryStore.getState().setConnected(true)
    const s = useTelemetryStore.getState()
    expect(s.isConnected).toBe(true)
    expect(s.wsError).toBeNull()
  })
})
