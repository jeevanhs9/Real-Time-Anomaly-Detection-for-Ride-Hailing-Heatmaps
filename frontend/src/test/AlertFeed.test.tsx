import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { useTelemetryStore } from '../store/telemetryStore'
import AlertFeed from '../components/alerts/AlertFeed'

describe('AlertFeed', () => {
  afterEach(() => { vi.restoreAllMocks() })

  beforeEach(() => {
    useTelemetryStore.setState({
      alerts: [{
        event_id: 'event-1',
        hex: 'hex-1',
        locality: 'Koramangala',
        severity: 'CRITICAL',
        anomaly_score: 82,
        root_cause: 'DEMAND_SPIKE',
        title: 'CRITICAL: Demand spike at Koramangala',
        timestamp: '2026-09-01T09:00:00+05:30',
      }],
      cells: new Map([['hex-1', {
        hex: 'hex-1',
        timestamp: '2026-09-01T09:00:00+05:30',
        tick_index: 1,
        demand: 120,
        supply: 30,
        cancellation_rate: 0.24,
        surge: 2.1,
        avg_eta_minutes: 14,
        is_rainy: false,
        rainfall_mm: 0,
        dsr: 4,
        z_score: 3.8,
        lgbm_pred: 60,
        residual: 60,
        iso_score: 0.8,
        anomaly_score: 82,
        severity: 'CRITICAL',
        root_cause: 'DEMAND_SPIKE',
      }]]),
      activeScenarios: ['silk_board_monsoon_flood'],
      selectedHex: null,
    })
  })

  it('shows the injected scenario and opens the selected cell from an alert', () => {
    render(<AlertFeed />)

    expect(screen.getByText('Scenario injected')).toBeTruthy()
    expect(screen.getByText('Silk Board Monsoon Flood')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', {
      name: /critical alert at Koramangala/i,
    }))
    expect(useTelemetryStore.getState().selectedHex).toBe('hex-1')
  })

  it('uses unique React keys when an event appears more than once in the feed', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
    const duplicate = useTelemetryStore.getState().alerts[0]
    useTelemetryStore.setState({ alerts: [duplicate, duplicate] })

    render(<AlertFeed />)

    expect(screen.getAllByRole('button', { name: /critical alert at Koramangala/i })).toHaveLength(2)
    expect(consoleError.mock.calls.some((call) => String(call[0]).includes('same key'))).toBe(false)
  })
})
