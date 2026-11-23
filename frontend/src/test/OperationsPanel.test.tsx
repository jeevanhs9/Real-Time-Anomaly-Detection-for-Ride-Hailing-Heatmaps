import { beforeEach, describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import OperationsPanel from '../components/layout/OperationsPanel'
import { useTelemetryStore } from '../store/telemetryStore'
import type { CellMetrics } from '../types/telemetry'

const cell: CellMetrics = {
  hex: '8860145841fffff',
  timestamp: '2026-09-01T09:00:00+05:30',
  tick_index: 1,
  demand: 50,
  supply: 40,
  cancellation_rate: 0.08,
  surge: 1,
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

describe('OperationsPanel', () => {
  beforeEach(() => {
    useTelemetryStore.setState({
      cells: new Map([[cell.hex, cell]]),
      summary: { total_demand: 2419, total_supply: 10307, active_anomalies_count: 3 },
      h3Registry: {
        [cell.hex]: { locality: 'Koramangala', lat: 12.93, lon: 77.62 },
        '8860145845fffff': { locality: 'Whitefield', lat: 12.97, lon: 77.75 },
      },
      selectedHex: null,
    })
  })

  it('shows KPIs from live store state and selects a searched H3 locality', () => {
    const { container } = render(<OperationsPanel />)

    expect(container.querySelector('.operations-kpi-value')?.textContent).toBe('1')
    expect(screen.getByText('2,419')).toBeTruthy()
    expect(screen.getByText('10,307')).toBeTruthy()
    expect(screen.getByText('3', { exact: true })).toBeTruthy()

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search Bengaluru location' }), {
      target: { value: 'Whitefield' },
    })
    fireEvent.click(screen.getByRole('option', { name: /Whitefield/ }))

    expect(useTelemetryStore.getState().selectedHex).toBe('8860145845fffff')
    expect(screen.getByRole('searchbox', { name: 'Search Bengaluru location' }).getAttribute('value')).toBe('Whitefield')
  })
})
