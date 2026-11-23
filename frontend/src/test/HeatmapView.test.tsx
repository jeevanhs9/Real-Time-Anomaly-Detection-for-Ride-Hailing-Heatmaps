import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import HeatmapView from '../components/map/HeatmapView'
import { useTelemetryStore } from '../store/telemetryStore'
import type { CellMetrics } from '../types/telemetry'

vi.mock('@deck.gl/react', () => ({
  default: ({ layers }: { layers: Array<{ id: string; extruded?: boolean }> }) => (
    <div
      data-testid="deckgl"
      data-layer-count={layers.length}
      data-layer-ids={layers.map((layer) => layer.id).join(',')}
      data-extruded={String(layers[0]?.extruded ?? false)}
    />
  ),
}))

vi.mock('@deck.gl/layers', () => ({
  IconLayer: class {
    id: string

    constructor(props: { id: string }) {
      this.id = props.id
    }
  },
}))

vi.mock('maplibre-gl', () => ({
  setWorkerUrl: vi.fn(),
  Map: class {
    jumpTo() {}
    remove() {}
  },
}))

vi.mock('../components/map/H3Layer', () => ({
  buildH3Layer: (_cells: unknown, _hover: unknown, _click: unknown, extruded: boolean) => ({
    id: 'h3-bengaluru',
    extruded,
  }),
}))

const cell: CellMetrics = {
  hex: 'hex-1',
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

describe('HeatmapView display modes', () => {
  beforeEach(() => {
    useTelemetryStore.setState({
      cells: new Map([[cell.hex, cell]]),
      h3Registry: { [cell.hex]: { locality: 'Koramangala', lat: 12.93, lon: 77.62 } },
      selectedHex: null,
    })
  })

  it('switches between a clean basemap, flat heatmap, and existing 3D layer', () => {
    const { container } = render(<HeatmapView />)
    const deckgl = () => screen.getByTestId('deckgl')

    expect(deckgl().getAttribute('data-layer-count')).toBe('2')
    expect(deckgl().getAttribute('data-layer-ids')).toBe('h3-bengaluru,representative-driver-markers')
    expect(deckgl().getAttribute('data-extruded')).toBe('true')
    expect(container.querySelector('.map-canvas')).not.toBeNull()

    fireEvent.click(screen.getByRole('button', { name: 'Map' }))
    expect(deckgl().getAttribute('data-layer-count')).toBe('0')
    expect(screen.getByRole('button', { name: 'Map' }).getAttribute('aria-pressed')).toBe('true')
    expect(container.querySelector('.map-canvas')).not.toBeNull()
    expect(screen.queryByLabelText('Anomaly severity legend')).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: 'Heatmap' }))
    expect(deckgl().getAttribute('data-layer-count')).toBe('2')
    expect(deckgl().getAttribute('data-layer-ids')).toBe('h3-bengaluru,representative-driver-markers')
    expect(deckgl().getAttribute('data-extruded')).toBe('false')
    expect(screen.getByLabelText('Anomaly severity legend')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: '3D' }))
    expect(deckgl().getAttribute('data-layer-count')).toBe('2')
    expect(deckgl().getAttribute('data-extruded')).toBe('true')
  })
})
