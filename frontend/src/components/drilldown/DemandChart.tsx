import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts'
import type { CellMetrics } from '../../types/telemetry'

interface Props {
  ticks: CellMetrics[]
}

interface ChartPoint {
  time:      string
  actual:    number
  predicted: number
  upper:     number
  lower:     number
  anomaly:   boolean
}

/** Format ISO timestamp → "HH:mm" in IST */
function toIST(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour:     '2-digit',
      minute:   '2-digit',
    })
  } catch {
    return ''
  }
}

export default function DemandChart({ ticks }: Props) {
  if (ticks.length === 0) {
    return (
      <div className="chart-loading">
        No history yet — waiting for ticks…
      </div>
    )
  }

  // Build chart data from ring-buffer ticks
  // Show at most the last 48 ticks (12 h) so the chart doesn't get too dense
  const slice = ticks.slice(-48)

  // Compute a rough 2-sigma band: ±2 × |residual_std| from predicted.
  // We approximate residual_std per-tick as |residual| since we don't store it
  // globally here.  The band is intentionally indicative, not exact.
  const meanAbsResidual =
    slice.reduce((s, t) => s + Math.abs(t.residual), 0) / slice.length

  const data: ChartPoint[] = slice.map((t) => ({
    time:      toIST(t.timestamp),
    actual:    t.demand,
    predicted: Math.max(0, Math.round(t.lgbm_pred)),
    upper:     Math.round(t.lgbm_pred + 2 * meanAbsResidual),
    lower:     Math.max(0, Math.round(t.lgbm_pred - 2 * meanAbsResidual)),
    anomaly:   t.severity !== 'NORMAL',
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#d9dde1" opacity={0.8} />

        <XAxis
          dataKey="time"
          tick={{ fill: '#72777c', fontSize: 10 }}
          interval="preserveStartEnd"
          tickLine={false}
        />
        <YAxis
          tick={{ fill: '#72777c', fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          width={32}
        />

        <Tooltip
          contentStyle={{
            background: '#ffffff',
            border: '1px solid #dfe3e6',
            borderRadius: 10,
            fontSize: 11,
            color: '#17191c',
            boxShadow: '0 8px 24px rgba(17, 24, 39, 0.12)',
          }}
          labelStyle={{ color: '#72777c' }}
        />

        <Legend
          wrapperStyle={{ fontSize: 10, color: '#72777c' }}
          iconType="line"
        />

        {/* 2-sigma confidence band */}
        <Area
          dataKey="upper"
          stroke="none"
          fill="#5275d8"
          fillOpacity={0.1}
          legendType="none"
          name="upper"
        />
        <Area
          dataKey="lower"
          stroke="none"
          fill="#276ef1"
          fillOpacity={0}
          legendType="none"
          name="lower"
        />

        {/* Predicted demand */}
        <Line
          type="monotone"
          dataKey="predicted"
          stroke="#5275d8"
          strokeWidth={1.5}
          strokeDasharray="4 2"
          dot={false}
          name="Predicted"
        />

        {/* Actual demand */}
        <Line
          type="monotone"
          dataKey="actual"
          stroke="#17191c"
          strokeWidth={2}
          dot={false}
          name="Actual"
          activeDot={{ r: 4, fill: '#da4b3e' }}
        />

        {/* Mark anomaly ticks */}
        {data
          .filter((d) => d.anomaly)
          .map((d) => (
            <ReferenceLine
              key={d.time}
              x={d.time}
              stroke="#da4b3e"
              strokeOpacity={0.4}
              strokeWidth={1}
            />
          ))}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
