import type { CellMetrics } from '../../types/telemetry'
import { getSeverityHex } from '../../lib/colorRamp'

export interface TooltipState {
  object: CellMetrics
  x:      number
  y:      number
}

export default function HoverTooltip({ tooltip }: { tooltip: TooltipState | null }) {
  if (!tooltip) return null
  const { object: c, x, y } = tooltip

  return (
    <div
      style={{ left: x + 14, top: y - 8, pointerEvents: 'none' }}
      className="map-tooltip"
      role="tooltip"
    >
      <div className="tooltip-heading">
        <span className="tooltip-title">{c.hex.slice(-8)}</span>
        <span
          className={`tooltip-severity severity-${c.severity.toLowerCase()}`}
          style={{ backgroundColor: getSeverityHex(c.severity) }}
        >
          {c.severity}
        </span>
      </div>

      <table className="tooltip-table">
        <tbody>
          {[
            ['Demand',   c.demand,                        ''],
            ['Supply',   c.supply,                        ''],
            ['DSR',      c.dsr.toFixed(2),               ''],
            ['Surge',    `${c.surge.toFixed(2)}×`,        ''],
            ['Z-score',  c.z_score.toFixed(2),            ''],
            ['Score',    c.anomaly_score.toFixed(1),       ''],
            ...(c.is_rainy
              ? [['Rain', `${c.rainfall_mm.toFixed(1)} mm/h`, 'rain']]
              : []),
          ].map(([lbl, val, cls]) => (
            <tr key={String(lbl)}>
              <td className={cls === 'rain' ? 'is-rain' : ''}>
                {lbl}
              </td>
              <td
                className={cls === 'rain' ? 'is-rain' : ''}
              >
                {val}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
