import type { CellMetrics } from '../../types/telemetry'

interface Props {
  cell: CellMetrics
}

interface Tile {
  label:   string
  value:   string
  sub?:    string
  alert?:  boolean
}

export default function MarketMetrics({ cell }: Props) {
  const tiles: Tile[] = [
    {
      label: 'DSR',
      value: cell.dsr.toFixed(2),
      sub:   'demand / supply',
      alert: cell.dsr > 2.5,
    },
    {
      label: 'Surge',
      value: `${cell.surge.toFixed(2)}×`,
      sub:   'price multiplier',
      alert: cell.surge > 2.0,
    },
    {
      label: 'Cancellation',
      value: `${(cell.cancellation_rate * 100).toFixed(1)}%`,
      sub:   'of requests',
      alert: cell.cancellation_rate > 0.2,
    },
    {
      label: 'Avg ETA',
      value: `${cell.avg_eta_minutes.toFixed(1)} min`,
      sub:   'estimated arrival',
      alert: cell.avg_eta_minutes > 15,
    },
  ]

  return (
    <div className="market-metrics">
      {tiles.map((t) => (
        <div
          key={t.label}
          className={`market-tile${t.alert ? ' is-alert' : ''}`}
        >
          <div className="market-tile-label">
            {t.label}
          </div>
          <div className="market-tile-value">
            {t.value}
          </div>
          {t.sub && (
            <div className="market-tile-note">{t.sub}</div>
          )}
        </div>
      ))}
    </div>
  )
}
