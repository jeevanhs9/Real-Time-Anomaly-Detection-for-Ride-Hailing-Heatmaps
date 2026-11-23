import { useCallback, useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useH3Registry } from './hooks/useH3Registry'
import Layout from './components/layout/Layout'
import OperationsPanel from './components/layout/OperationsPanel'
import HeatmapView from './components/map/HeatmapView'
import AlertFeed from './components/alerts/AlertFeed'
import SimulationControls from './components/simulation/SimulationControls'
import HexDrillDownDrawer from './components/drilldown/HexDrillDownDrawer'
import { useTelemetryStore } from './store/telemetryStore'

export default function App() {
  useWebSocket()      // live tick stream
  useH3Registry()     // load locality names once
  const [mobileAlertsOpen, setMobileAlertsOpen] = useState(false)
  const activeAnomalyCount = useTelemetryStore((state) => state.summary.active_anomalies_count)
  const closeMobileAlerts = useCallback(() => setMobileAlertsOpen(false), [])

  return (
    <Layout>
      <section className="map-workspace" aria-label="Bengaluru live map">
        <HeatmapView />
        <button
          type="button"
          className="mobile-alert-trigger"
          aria-controls="anomaly-panel"
          aria-expanded={mobileAlertsOpen}
          onClick={() => setMobileAlertsOpen(true)}
        >
          <span>Active anomalies</span>
          <strong>{activeAnomalyCount.toLocaleString()}</strong>
        </button>
        <SimulationControls />
        <HexDrillDownDrawer />
      </section>

      <OperationsPanel />
      <AlertFeed mobileOpen={mobileAlertsOpen} onClose={closeMobileAlerts} />
    </Layout>
  )
}
