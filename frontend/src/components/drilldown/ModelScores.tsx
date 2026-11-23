import type { CellMetrics } from '../../types/telemetry'

interface Props {
  cell: CellMetrics
}

interface ScoreRow {
  label:    string
  value:    number
  max:      number
  color:    string
  note:     string
}

export default function ModelScores({ cell }: Props) {
  const rows: ScoreRow[] = [
    {
      label: 'Z-Score',
      value: Math.abs(cell.z_score),
      max:   6,
      color: Math.abs(cell.z_score) >= 3 ? '#f43b00' : '#276ef1',
      note:  `${cell.z_score >= 0 ? '+' : ''}${cell.z_score.toFixed(2)}  (flag ≥ 3.0)`,
    },
    {
      label: 'Residual / σ',
      value: Math.abs(cell.residual),
      max:   Math.abs(cell.residual) > 0 ? Math.abs(cell.residual) * 2 : 10,
      color: Math.abs(cell.residual) > 2 ? '#fc993c' : '#276ef1',
      note:  `Δ${cell.residual >= 0 ? '+' : ''}${cell.residual.toFixed(1)}  (actual − pred)`,
    },
    {
      label: 'IsoForest',
      value: cell.iso_score,
      max:   1,
      color: cell.iso_score >= 0.65 ? '#f43b00' : '#276ef1',
      note:  `${(cell.iso_score * 100).toFixed(0)}%  (flag ≥ 65%)`,
    },
  ]

  return (
    <div className="model-scores">
      {rows.map((row) => {
        const pct = Math.min((row.value / row.max) * 100, 100)
        return (
          <div className="model-score-row" key={row.label}>
            <div className="model-score-heading">
              <span>{row.label}</span>
              <span>{row.note}</span>
            </div>
            <div className="model-score-track">
              <div
                className="model-score-fill"
                style={{ width: `${pct}%`, backgroundColor: row.color }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
