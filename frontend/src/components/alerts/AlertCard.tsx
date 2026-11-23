import type { Alert } from '../../types/telemetry'
import { useTelemetryStore } from '../../store/telemetryStore'
import SeverityPill from './SeverityPill'
import { getSeverityHex } from '../../lib/colorRamp'

const ROOT_CAUSE_LABEL: Record<string, string> = {
  DEMAND_SPIKE:       'Demand spike',
  SUPPLY_COLLAPSE:    'Supply drop',
  MARKET_ANOMALY:     'Market anomaly',
  WEATHER_DISRUPTION: 'Weather disruption',
  NORMAL:             'Normal operation',
}

interface Props {
  alert: Alert
  isSelected: boolean
}

export default function AlertCard({ alert, isSelected }: Props) {
  const setSelectedHex = useTelemetryStore((s) => s.setSelectedHex)

  const time = new Date(alert.timestamp).toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour:     '2-digit',
    minute:   '2-digit',
  })

  const leftBorderColor = getSeverityHex(alert.severity)

  return (
    <button
      type="button"
      onClick={() => setSelectedHex(alert.hex)}
      aria-label={`${alert.severity} alert at ${alert.locality}: ${ROOT_CAUSE_LABEL[alert.root_cause] ?? alert.root_cause}, score ${alert.anomaly_score.toFixed(0)} out of 100`}
      className={[
        'alert-card',
        isSelected
          ? 'is-selected'
          : '',
      ].join(' ')}
      style={{ borderLeftColor: leftBorderColor }}
    >
      {/* Top row: locality + pill */}
      <div className="alert-card-top">
        <span className="alert-locality">{alert.locality}</span>
        <SeverityPill severity={alert.severity} size="xs" />
      </div>

      <div className="alert-card-bottom">
        <span className="alert-cause">
          {ROOT_CAUSE_LABEL[alert.root_cause] ?? alert.root_cause}
        </span>
        <span className="alert-time">
          <strong>{alert.anomaly_score.toFixed(0)}</strong><span>/100</span><i aria-hidden="true">·</i>{time}
        </span>
      </div>
    </button>
  )
}
