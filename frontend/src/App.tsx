import { useWebSocket } from './hooks/useWebSocket'
import { useH3Registry } from './hooks/useH3Registry'
import Layout from './components/layout/Layout'
import HeatmapView from './components/map/HeatmapView'
import AlertFeed from './components/alerts/AlertFeed'
import SimulationControls from './components/simulation/SimulationControls'
import HexDrillDownDrawer from './components/drilldown/HexDrillDownDrawer'

export default function App() {
  useWebSocket()      // live tick stream
  useH3Registry()     // load locality names once

  return (
    <Layout>
      <section className="map-workspace" aria-label="Bengaluru live map">
        <HeatmapView />
        <SimulationControls />
        <HexDrillDownDrawer />
      </section>

      <AlertFeed />
    </Layout>
  )
}
