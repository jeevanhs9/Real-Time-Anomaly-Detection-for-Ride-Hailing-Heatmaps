import { useTelemetryStore } from '../../store/telemetryStore'

// ── sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ connected }: { connected: boolean }) {
  return (
    <span className={`connection-status ${connected ? 'is-connected' : 'is-disconnected'}`} role="status">
      <span className="connection-dot" aria-hidden="true" />
      <span>{connected ? 'Live stream' : 'Reconnecting'}</span>
    </span>
  )
}

function KpiItem({
  label,
  value,
  highlight = false,
}: {
  label: string
  value: string | number
  highlight?: boolean
}) {
  const key = label.toLowerCase().replaceAll(' ', '-')
  return (
    <div className={`topbar-kpi kpi-${key}${highlight ? ' is-highlighted' : ''}`}>
      <span className="topbar-kpi-label">{label}</span>
      <span className="topbar-kpi-value">{value}</span>
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────

export default function Header() {
  const isConnected = useTelemetryStore((s) => s.isConnected)
  const simTime = useTelemetryStore((s) => s.simTime)
  const tickIndex = useTelemetryStore((s) => s.tickIndex)
  const summary = useTelemetryStore((s) => s.summary)

  const clock = simTime
    ? new Date(simTime).toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour:     '2-digit',
        minute:   '2-digit',
        day:      '2-digit',
        month:    'short',
        year:     'numeric',
      })
    : 'Waiting for first tick'

  return (
    <header className="topbar">
      <div className="brand-lockup">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /><i /></span>
        <span className="brand-name">Heatmap Pulse</span>
        <span className="brand-divider" aria-hidden="true" />
        <span className="brand-context">Bengaluru operations</span>
      </div>

      <div className="topbar-right">
        <StatusBadge connected={isConnected} />
        <div className="simulation-clock">
          <span className="topbar-kpi-label">Simulation time</span>
          <span className="topbar-kpi-value">{clock}</span>
        </div>
        <KpiItem label="Demand" value={summary.total_demand.toLocaleString()} />
        <KpiItem label="Driver supply" value={summary.total_supply.toLocaleString()} />
        <KpiItem label="Active anomalies" value={summary.active_anomalies_count} highlight={summary.active_anomalies_count > 0} />
        <span className="tick-number">Tick {tickIndex.toLocaleString()}</span>
      </div>
    </header>
  )
}
