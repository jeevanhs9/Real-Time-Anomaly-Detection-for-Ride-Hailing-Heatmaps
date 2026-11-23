import type { Severity } from '../../types/telemetry'

interface Props {
  severity: Severity
  size?: 'sm' | 'xs'
}

export default function SeverityPill({ severity, size = 'sm' }: Props) {
  return (
    <span className={`severity-pill severity-${severity.toLowerCase()} severity-pill-${size}`}>
      {severity}
    </span>
  )
}
