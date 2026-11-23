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
import { IconLayer } from '@deck.gl/layers'
import { Map as MaplibreMap, setWorkerUrl } from 'maplibre-gl'
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { CellMetrics } from '../../types/telemetry'
import { useTelemetryStore } from '../../store/telemetryStore'
import { buildH3Layer } from './H3Layer'
import HoverTooltip, { type TooltipState } from './HoverTooltip'

const MAP_STYLE =
  'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

setWorkerUrl(maplibreWorkerUrl)

const INITIAL_VIEW_STATE = {
  longitude:  77.5946,
  latitude:   12.9716,
  zoom:       11,
  pitch:      45,
  bearing:    0,
  transitionDuration: 0,
}

type MapViewMode = 'map' | 'heatmap' | '3d'

interface VehicleMarker {
  hex: string
  longitude: number
  latitude: number
  supply: number
}

const MAX_VEHICLE_MARKERS = 24
const VEHICLE_ICON = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="32" viewBox="0 0 48 32"><path fill="#143c31" d="M8 12h3l4-7c.8-1.4 2.2-2.2 3.8-2.2h11.4c1.6 0 3 0.8 3.8 2.2l4 7H40a4 4 0 0 1 4 4v7a3 3 0 0 1-3 3h-2a5 5 0 0 1-10 0H19a5 5 0 0 1-10 0H7a3 3 0 0 1-3-3v-7a4 4 0 0 1 4-4Zm10-6-3.2 6h18.4L30 6H18Z"/><circle cx="14" cy="25" r="2.6" fill="#fff"/><circle cx="34" cy="25" r="2.6" fill="#fff"/></svg>',
)} `

const VEHICLE_ICON_DEFINITION = {
  url: VEHICLE_ICON.trim(),
  width: 48,
  height: 32,
  anchorY: 25,
  mask: false,
}

function buildVehicleLayer(markers: VehicleMarker[]) {
  return new IconLayer<VehicleMarker>({
    id: 'representative-driver-markers',
    data: markers,
    getIcon: () => VEHICLE_ICON_DEFINITION,
    getPosition: (marker) => [marker.longitude, marker.latitude],
    getSize: (marker) => 17 + Math.min(marker.supply, 60) * 0.06,
    sizeUnits: 'pixels',
    billboard: true,
    pickable: false,
    transitions: { getPosition: 350 },
  })
}

export default function HeatmapView() {
  const cells          = useTelemetryStore((s) => s.cells)
  const h3Registry     = useTelemetryStore((s) => s.h3Registry)
  const setSelectedHex = useTelemetryStore((s) => s.setSelectedHex)
  const selectedHex    = useTelemetryStore((s) => s.selectedHex)

  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE)
  const [tooltip,   setTooltip]   = useState<TooltipState | null>(null)
  const [viewMode,  setViewMode]  = useState<MapViewMode>('3d')

  // MapLibre container + instance refs
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef          = useRef<MaplibreMap | null>(null)

  const cellsArray = useMemo(() => Array.from(cells.values()), [cells])

  const vehicleMarkers = useMemo(() => {
    const candidates = cellsArray
      .filter((cell) => cell.supply > 0 && h3Registry[cell.hex])
      .map((cell) => ({
        hex: cell.hex,
        supply: cell.supply,
        longitude: h3Registry[cell.hex].lon,
        latitude: h3Registry[cell.hex].lat,
      }))
      .sort((a, b) => b.supply - a.supply || a.hex.localeCompare(b.hex))

    const selected: VehicleMarker[] = []
    for (const candidate of candidates) {
      if (selected.length >= MAX_VEHICLE_MARKERS) break
      const spacedFromExisting = selected.every((marker) =>
        Math.hypot(marker.longitude - candidate.longitude, marker.latitude - candidate.latitude) > 0.008,
      )
      if (spacedFromExisting) selected.push(candidate)
    }

    if (selected.length < MAX_VEHICLE_MARKERS) {
      const selectedHexes = new Set(selected.map((marker) => marker.hex))
      for (const candidate of candidates) {
        if (selected.length >= MAX_VEHICLE_MARKERS) break
        if (!selectedHexes.has(candidate.hex)) selected.push(candidate)
      }
    }

    return selected
  }, [cellsArray, h3Registry])

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
    () => viewMode === 'map'
      ? []
      : [
          buildH3Layer(cellsArray, handleHover, handleClick, viewMode === '3d', selectedHex),
          ...(vehicleMarkers.length > 0 ? [buildVehicleLayer(vehicleMarkers)] : []),
        ],
    [cellsArray, handleHover, handleClick, viewMode, selectedHex, vehicleMarkers],
  )

  function changeViewMode(mode: MapViewMode) {
    setViewMode(mode)
    setTooltip(null)
    setViewState((current) => ({
      ...current,
      pitch: mode === '3d' ? INITIAL_VIEW_STATE.pitch : 0,
    }))
  }

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
          <button type="button" onClick={() => changeViewMode('map')} aria-pressed={viewMode === 'map'}>
            Map
          </button>
          <button type="button" onClick={() => changeViewMode('heatmap')} aria-pressed={viewMode === 'heatmap'}>
            Heatmap
          </button>
          <button type="button" onClick={() => changeViewMode('3d')} aria-pressed={viewMode === '3d'}>
            3D
          </button>
        </div>
      </div>

      {viewMode !== 'map' && (
        <div className="map-legend" aria-label="Anomaly severity legend">
          <span className="legend-label">SEVERITY</span>
          <span><i className="severity-dot severity-dot-normal" />Normal</span>
          <span><i className="severity-dot severity-dot-medium" />Medium</span>
          <span><i className="severity-dot severity-dot-high" />High</span>
          <span><i className="severity-dot severity-dot-critical" />Critical</span>
          <span><i className="vehicle-legend-mark" />Driver activity</span>
        </div>
      )}

      {viewMode !== 'map' && <HoverTooltip tooltip={tooltip} />}
    </div>
  )
}
