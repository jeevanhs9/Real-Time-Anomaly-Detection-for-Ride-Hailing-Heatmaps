/**
 * Phase 6 unit tests — alert feed, store extensions, severity pills.
 * All tests are pure logic (no DOM / rendering) so they run fast in jsdom.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { useTelemetryStore } from '../store/telemetryStore'
import { getSeverityClass, getSeverityHex, getSeverityColor } from '../lib/colorRamp'
import type { Alert, CellMetrics } from '../types/telemetry'

// ── helpers ───────────────────────────────────────────────────────────────────

function makeAlert(id: string, severity: Alert['severity'] = 'HIGH'): Alert {
  return {
    event_id:    id,
    hex:         'hexabc',
    locality:    'Koramangala',
    severity,
    anomaly_score: 72,
    root_cause:  'DEMAND_SPIKE',
    title:       'HIGH: Demand Spike at Koramangala',
    timestamp:   '2026-09-01T09:00:00+05:30',
  }
}

function makeCell(hex: string, severity: CellMetrics['severity'] = 'NORMAL'): CellMetrics {
  return {
    hex, severity,
    timestamp: '2026-09-01T09:00:00+05:30',
    tick_index: 1,
    demand: 50, supply: 40,
    cancellation_rate: 0.08, surge: 1.0,
    avg_eta_minutes: 5, is_rainy: false, rainfall_mm: 0,
    dsr: 1.25, z_score: 0.5, lgbm_pred: 48,
    residual: 2, iso_score: 0.3, anomaly_score: 0,
    root_cause: 'NORMAL',
  }
}

// ── store: simulation state ───────────────────────────────────────────────────

describe('telemetryStore — simulation controls', () => {
  beforeEach(() => {
    useTelemetryStore.setState({
      paused: false, speed: 1, activeScenarios: [],
      cells: new Map(), alerts: [],
    })
  })

  it('setPaused toggles the paused flag', () => {
    useTelemetryStore.getState().setPaused(true)
    expect(useTelemetryStore.getState().paused).toBe(true)
    useTelemetryStore.getState().setPaused(false)
    expect(useTelemetryStore.getState().paused).toBe(false)
  })

  it('setSpeed stores the multiplier', () => {
    useTelemetryStore.getState().setSpeed(60)
    expect(useTelemetryStore.getState().speed).toBe(60)
  })

  it('setActiveScenarios stores keys', () => {
    useTelemetryStore.getState().setActiveScenarios(['silk_board_monsoon_flood'])
    expect(useTelemetryStore.getState().activeScenarios).toContain('silk_board_monsoon_flood')
  })
})

// ── store: h3Registry ─────────────────────────────────────────────────────────

describe('telemetryStore — h3Registry', () => {
  it('setH3Registry stores the registry', () => {
    const reg = { hex1: { locality: 'Koramangala', lat: 12.93, lon: 77.62 } }
    useTelemetryStore.getState().setH3Registry(reg)
    expect(useTelemetryStore.getState().h3Registry['hex1']?.locality).toBe('Koramangala')
  })
})

// ── store: cell history ───────────────────────────────────────────────────────

describe('telemetryStore — cellHistory', () => {
  it('setCellHistory stores ticks for a hex', () => {
    const ticks = [makeCell('hexA'), makeCell('hexA')]
    useTelemetryStore.getState().setCellHistory('hexA', ticks)
    expect(useTelemetryStore.getState().cellHistory.get('hexA')).toHaveLength(2)
  })

  it('setHistoryLoading updates the flag', () => {
    useTelemetryStore.getState().setHistoryLoading(true)
    expect(useTelemetryStore.getState().historyLoading).toBe(true)
    useTelemetryStore.getState().setHistoryLoading(false)
    expect(useTelemetryStore.getState().historyLoading).toBe(false)
  })
})

// ── store: alerts filter ──────────────────────────────────────────────────────

describe('telemetryStore — alert filtering', () => {
  beforeEach(() => {
    useTelemetryStore.setState({ alerts: [], cells: new Map() })
  })

  it('applyTick prepends new alerts', () => {
    useTelemetryStore.getState().applyTick({
      type: 'TICK_UPDATE',
      simulation_time: '2026-09-01T09:00:00+05:30',
      tick_index: 1,
      summary: { total_demand: 100, total_supply: 80, active_anomalies_count: 1 },
      hex_updates: [],
      new_alerts: [makeAlert('a1', 'CRITICAL'), makeAlert('a2', 'HIGH')],
    })
    const alerts = useTelemetryStore.getState().alerts
    expect(alerts[0].event_id).toBe('a1')
    expect(alerts[1].event_id).toBe('a2')
  })

  it('NORMAL alerts are still stored (filtering is in the UI layer)', () => {
    useTelemetryStore.getState().applyTick({
      type: 'TICK_UPDATE',
      simulation_time: '2026-09-01T09:00:00+05:30',
      tick_index: 1,
      summary: { total_demand: 50, total_supply: 40, active_anomalies_count: 0 },
      hex_updates: [],
      new_alerts: [makeAlert('n1', 'NORMAL')],
    })
    expect(useTelemetryStore.getState().alerts).toHaveLength(1)
  })
})

// ── severity color ramp ───────────────────────────────────────────────────────

describe('colorRamp — full coverage', () => {
  it('every severity has a unique RGBA', () => {
    const colors = (['NORMAL', 'MEDIUM', 'HIGH', 'CRITICAL'] as const).map(
      (s) => JSON.stringify(getSeverityColor(s)),
    )
    expect(new Set(colors).size).toBe(4)
  })

  it('every severity has a unique hex', () => {
    const hexes = (['NORMAL', 'MEDIUM', 'HIGH', 'CRITICAL'] as const).map(
      (s) => getSeverityHex(s),
    )
    expect(new Set(hexes).size).toBe(4)
  })

  it('getSeverityClass contains correct bg class for each level', () => {
    expect(getSeverityClass('CRITICAL')).toContain('bg-uber-red')
    expect(getSeverityClass('HIGH')).toContain('bg-uber-orange')
    expect(getSeverityClass('MEDIUM')).toContain('bg-uber-blue')
    expect(getSeverityClass('NORMAL')).toContain('bg-uber-green')
  })
})
