import { useEffect } from 'react'
import { useTelemetryStore } from '../../store/telemetryStore'
import { fetchCellHistory } from '../../lib/api'
import SeverityPill from '../alerts/SeverityPill'
import DemandChart from './DemandChart'
import ModelScores from './ModelScores'
import MarketMetrics from './MarketMetrics'
import { getSeverityHex } from '../../lib/colorRamp'

const ROOT_CAUSE_LABEL: Record<string, string> = {
  DEMAND_SPIKE:       'Demand spike',
  SUPPLY_COLLAPSE:    'Supply collapse',
  MARKET_ANOMALY:     'Market anomaly',
  WEATHER_DISRUPTION: 'Weather disruption',
  NORMAL:             'Normal operation',
}

export default function HexDrillDownDrawer() {
  const selectedHex      = useTelemetryStore((s) => s.selectedHex)
  const cells            = useTelemetryStore((s) => s.cells)
  const cellHistory      = useTelemetryStore((s) => s.cellHistory)
  const historyLoading   = useTelemetryStore((s) => s.historyLoading)
  const setSelectedHex   = useTelemetryStore((s) => s.setSelectedHex)
  const setCellHistory   = useTelemetryStore((s) => s.setCellHistory)
  const setHistoryLoading = useTelemetryStore((s) => s.setHistoryLoading)
  const h3Registry       = useTelemetryStore((s) => s.h3Registry)

  const cell = selectedHex ? cells.get(selectedHex) : null
  const history = selectedHex ? (cellHistory.get(selectedHex) ?? []) : []

  useEffect(() => {
    if (!selectedHex) return
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setSelectedHex(null)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [selectedHex, setSelectedHex])

  // Fetch history whenever selected hex changes
  useEffect(() => {
    if (!selectedHex) return
    setHistoryLoading(true)
    fetchCellHistory(selectedHex)
      .then((res) => setCellHistory(selectedHex, res.ticks))
      .catch(() => setCellHistory(selectedHex, []))
      .finally(() => setHistoryLoading(false))
  }, [selectedHex]) // eslint-disable-line react-hooks/exhaustive-deps

  // Closed state
  if (!selectedHex || !cell) return null

  const locality = h3Registry[selectedHex]?.locality ?? selectedHex
  const severityColor = getSeverityHex(cell.severity)

  return (
    <>
      {/* Backdrop */}
      <button
        type="button"
        aria-label="Close location details"
        className="drawer-backdrop"
        onClick={() => setSelectedHex(null)}
      />

      <aside
        className="detail-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="detail-drawer-title"
      >
        <div className="detail-drawer-header" style={{ borderTopColor: severityColor }}>
          <div className="detail-title-row">
            <div className="detail-title-copy">
              <div className="detail-title-line">
                <h2 id="detail-drawer-title">
                  {locality}
                </h2>
                <SeverityPill severity={cell.severity} />
              </div>
              <p className="detail-hex-id">
                {selectedHex}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedHex(null)}
              className="icon-button drawer-close"
              aria-label="Close location details"
            >
              ×
            </button>
          </div>

          {/* Root cause tag */}
          <div className="root-cause-summary">
            {ROOT_CAUSE_LABEL[cell.root_cause] ?? cell.root_cause}
            <span aria-hidden="true">·</span>
            <strong style={{ color: severityColor }}>
              {cell.anomaly_score.toFixed(0)}/100
            </strong>
          </div>
        </div>

        <div className="detail-drawer-scroll">
          <section className="detail-section">
            <div className="detail-section-heading">
              <h3>Demand vs predicted</h3><span>12 H · 48 ticks</span>
            </div>
            {historyLoading ? (
              <div className="chart-loading" role="status">Loading demand history…</div>
            ) : (
              <DemandChart ticks={history.length > 0 ? history : [cell]} />
            )}
          </section>

          <section className="detail-section">
            <div className="detail-section-heading">
              <h3>Model signals</h3><span>3 detectors</span>
            </div>
            <ModelScores cell={cell} />
          </section>

          <section className="detail-section">
            <div className="detail-section-heading">
              <h3>Market conditions</h3><span>Current</span>
            </div>
            <MarketMetrics cell={cell} />
          </section>

          <section className="detail-section detail-snapshot">
            <div className="detail-section-heading">
              <h3>Cell snapshot</h3><span>Tick {cell.tick_index}</span>
            </div>
            <div className="snapshot-list">
              {[
                ['Demand',  cell.demand],
                ['Supply',  cell.supply],
                ['Rain',    cell.is_rainy ? `${cell.rainfall_mm.toFixed(1)} mm/h` : 'None'],
              ].map(([lbl, val]) => (
                <div key={String(lbl)}>
                  <span>{lbl}</span>
                  <strong>{val}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="detail-drawer-footer">
          <button
            type="button"
            onClick={() => setSelectedHex(null)}
          >
            Close details
          </button>
        </div>
      </aside>
    </>
  )
}
