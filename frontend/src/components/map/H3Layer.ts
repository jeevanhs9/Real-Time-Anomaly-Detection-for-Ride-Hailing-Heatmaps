import { H3HexagonLayer } from '@deck.gl/geo-layers'
import type { PickingInfo } from '@deck.gl/core'
import type { CellMetrics } from '../../types/telemetry'
import { getSeverityColor } from '../../lib/colorRamp'

const MAX_DEMAND    = 300
const MAX_ELEVATION = 1_500

export function buildH3Layer(
  cells:       CellMetrics[],
  onHover:     (info: { object?: CellMetrics; x: number; y: number }) => void,
  onClickCell: (hex: string) => void,
  extruded:    boolean,
  selectedHex: string | null,
): H3HexagonLayer<CellMetrics> {
  return new H3HexagonLayer<CellMetrics>({
    id:               'h3-bengaluru',
    data:             cells,
    pickable:         true,
    extruded,
    elevationScale:   1,

    getHexagon:   (d) => d.hex,
    getFillColor: (d) => getSeverityColor(d.severity),
    getElevation: (d) =>
      Math.min(d.demand / MAX_DEMAND, 1) * MAX_ELEVATION,

    getLineColor:       (d) => d.hex === selectedHex ? [16, 24, 32, 255] : [255, 255, 255, 45],
    lineWidthMinPixels: 1,

    transitions: {
      getFillColor: 300,
      getElevation: 300,
    },
    updateTriggers: {
      getFillColor: cells,
      getElevation: cells,
      getLineColor: selectedHex,
    },

    onHover: (info: PickingInfo<CellMetrics>) => {
      onHover({
        object: info.object ?? undefined,
        x: info.x,
        y: info.y,
      })
    },

    onClick: (info: PickingInfo<CellMetrics>) => {
      if (info.object) onClickCell(info.object.hex)
    },
  })
}
