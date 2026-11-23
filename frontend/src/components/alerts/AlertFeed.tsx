import { SCENARIOS, useTelemetryStore, type ScenarioKey } from '../../store/telemetryStore'
import type { Severity } from '../../types/telemetry'
import AlertCard from './AlertCard'

const SEVERITIES: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL']

export default function AlertFeed() {
  const alerts     = useTelemetryStore((s) => s.alerts)
  const cells      = useTelemetryStore((s) => s.cells)
  const activeScenarios = useTelemetryStore((s) => s.activeScenarios)
  const selectedHex = useTelemetryStore((s) => s.selectedHex)
  const clearAlerts = useTelemetryStore((s) => s.clearAlerts)

  const anomalies = alerts.filter((a) => a.severity !== 'NORMAL')
  const counts: Record<Severity, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, NORMAL: 0 }
  cells.forEach((cell) => { counts[cell.severity] += 1 })

  return (
    <aside className="alert-panel" aria-label="Live anomaly feed">
      <div className="alert-panel-header">
        <div>
          <span className="eyebrow">OPERATIONS</span>
          <div className="feed-title-row">
            <h2>Anomaly feed</h2>
            <span className="feed-count" aria-label={`${anomalies.length} recent alerts`}>{anomalies.length}</span>
          </div>
        </div>
        {anomalies.length > 0 && (
          <button
            type="button"
            onClick={clearAlerts}
            className="text-button"
          >
            Clear feed
          </button>
        )}
      </div>

      <div className="severity-summary" aria-label="Current cell counts by severity">
        {SEVERITIES.map((severity) => (
          <div className={`severity-summary-item severity-summary-${severity.toLowerCase()}`} key={severity}>
            <span className="severity-summary-label">{severity}</span>
            <span className="severity-summary-value">{counts[severity].toLocaleString()}</span>
          </div>
        ))}
      </div>

      {activeScenarios.length > 0 && (
        <div className="scenario-banner" role="status" aria-live="polite">
          <span className="scenario-banner-mark" aria-hidden="true">!</span>
          <span><strong>Scenario injected</strong><small>{activeScenarios.map((key) => SCENARIOS[key as ScenarioKey]).join(' · ')}</small></span>
        </div>
      )}

      <div className="feed-section-label">
        <span>Recent events</span>
        <span>{cells.size.toLocaleString()} cells monitored</span>
      </div>

      <div className="feed-list">
        {anomalies.length === 0 ? (
          <div className="feed-empty">
            <span className="empty-indicator" aria-hidden="true">✓</span>
            <strong>No high-severity events</strong>
            <span>New detections will appear here as they arrive.</span>
          </div>
        ) : (
          <div className="feed-card-list">
            {anomalies.map((alert) => (
              <AlertCard
                key={alert.event_id}
                alert={alert}
                isSelected={selectedHex === alert.hex}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
