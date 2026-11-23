/**
 * Fetches the H3 spatial registry from the backend once on mount
 * and stores it in the Zustand store so components can look up locality names.
 */
import { useEffect } from 'react'
import { useTelemetryStore } from '../store/telemetryStore'

interface GeoFeatureProps {
  h3_index: string
  locality: string
  lat:      number
  lon:      number
}

export function useH3Registry(): void {
  const setH3Registry = useTelemetryStore((s) => s.setH3Registry)

  useEffect(() => {
    fetch('/api/v1/geo/hexagons')
      .then((r) => r.json())
      .then((fc: { features: { properties: GeoFeatureProps }[] }) => {
        const registry: Record<string, { locality: string; lat: number; lon: number }> = {}
        for (const feat of fc.features) {
          const p = feat.properties
          registry[p.h3_index] = { locality: p.locality, lat: p.lat, lon: p.lon }
        }
        setH3Registry(registry)
      })
      .catch(() => { /* backend not ready yet — harmless */ })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
