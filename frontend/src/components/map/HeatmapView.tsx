 /**
 * HeatmapView — Deck.gl v9 standalone canvas over a MapLibre GL v6 map.
 *
 * Pattern: Both DeckGL and MapLibre share the same container div.
 * MapLibre renders into a ref'd div; DeckGL renders its canvas on top
 * with pointer-events:none so the map still pans/zooms.
 * View state is kept in sync manually via onViewStateChange.
 *
 * This avoids all version-compatibility issues with MapboxOverlay / react-map-gl.
 */
import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import DeckGL from '@deck.gl/react'
import { Map as MaplibreMap } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { CellMetrics } from '../../types/telemetry'
import { useTelemetryStore } from '../../store/telemetryStore'
import { buildH3Layer } from './H3Layer'
import HoverTooltip, { type TooltipState } from './HoverTooltip'

const MAP_STYLE =
  'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

const INITIAL_VIEW_STATE = {
  longitude:  77.5946,
  latitude:   12.9716,
  zoom:       11,
  pitch:      45,
  bearing:    0,
  transitionDuration: 0,
}

export default function HeatmapView() {
  const cells          = useTelemetryStore((s) => s.cells)
  const setSelectedHex = useTelemetryStore((s) => s.setSelectedHex)
  const selectedHex    = useTelemetryStore((s) => s.selectedHex)

  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [tooltip,   setTooltip]   = useState<TooltipState | null>(null)
  const [extruded,  setExtruded]  = useState(true)

  // MapLibre container + instance refs
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef          = useRef<MaplibreMap | null>(null)

  const cellsArray = useMemo(() => Array.from(cells.values()), [cells])

  // ── Initialise MapLibre once ────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    const map = new MaplibreMap({
      container:   mapContainerRef.current,
      style:       MAP_STYLE,
      center:      [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
      zoom:        INITIAL_VIEW_STATE.zoom,
      pitch:       INITIAL_VIEW_STATE.pitch,
      bearing:     INITIAL_VIEW_STATE.bearing,
      interactive: false,   // DeckGL handles all interaction
      attributionControl: false,
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  // ── Keep MapLibre in sync with DeckGL view state ────────────────────────────
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    map.jumpTo({
      center:  [viewState.longitude, viewState.latitude],
      zoom:    viewState.zoom,
      pitch:   viewState.pitch,
      bearing: viewState.bearing,
    })
  }, [viewState])

  // ── Handlers ────────────────────────────────────────────────────────────────
  const handleHover = useCallback(
    (info: { object?: CellMetrics; x: number; y: number }) => {
      setTooltip(info.object ? { object: info.object, x: info.x, y: info.y } : null)
    },
    [],
  )

  const handleClick = useCallback(
    (hex: string) => setSelectedHex(hex),
    [setSelectedHex],
  )

  const layers = useMemo(
    () => [buildH3Layer(cellsArray, handleHover, handleClick, extruded, selectedHex)],
    [cellsArray, handleHover, handleClick, extruded, selectedHex],
  )

  return (
    <div className="map-stage">

      {/* MapLibre base map — rendered beneath DeckGL */}
      <div ref={mapContainerRef} className="map-canvas" />

      {/* DeckGL overlay — transparent background so the map shows through */}
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) =>
          setViewState(vs as typeof INITIAL_VIEW_STATE)
        }
        controller={true}
        layers={layers}
        style={{
          position:  'absolute',
          inset:     '0',
          background: 'transparent',
        }}
      />

      <div className="map-context">
        <span className="eyebrow">LIVE COVERAGE</span>
        <h1>Bengaluru</h1>
        <p>Ride demand and service health across the city</p>
      </div>

      <div className="map-actions">
        <span className="coverage-pill"><span className="coverage-dot" />{cellsArray.length} H3 cells</span>
        <div className="view-switch" role="group" aria-label="Map display mode">
          <button type="button" onClick={() => setExtruded(false)} aria-pressed={!extruded}>
            2D
          </button>
          <button type="button" onClick={() => setExtruded(true)} aria-pressed={extruded}>
            3D
          </button>
        </div>
      </div>

      <div className="map-legend" aria-label="Anomaly severity legend">
        <span className="legend-label">SEVERITY</span>
        <span><i className="severity-dot severity-dot-normal" />Normal</span>
        <span><i className="severity-dot severity-dot-medium" />Medium</span>
        <span><i className="severity-dot severity-dot-high" />High</span>
        <span><i className="severity-dot severity-dot-critical" />Critical</span>
      </div>

      <HoverTooltip tooltip={tooltip} />
    </div>
  )
}
