import { useMemo, useState } from 'react'
import { useTelemetryStore } from '../../store/telemetryStore'
import ScenarioDropdown from '../simulation/ScenarioDropdown'

const formatNumber = new Intl.NumberFormat('en-IN')

export default function OperationsPanel() {
  const cells = useTelemetryStore((state) => state.cells)
  const summary = useTelemetryStore((state) => state.summary)
  const h3Registry = useTelemetryStore((state) => state.h3Registry)
  const setSelectedHex = useTelemetryStore((state) => state.setSelectedHex)
  const [query, setQuery] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)

  const suggestions = useMemo(() => {
    const value = query.trim().toLocaleLowerCase()
    if (value.length < 2) return []

    return Object.entries(h3Registry)
      .filter(([, location]) => location.locality.toLocaleLowerCase().includes(value))
      .sort((a, b) => a[1].locality.localeCompare(b[1].locality))
      .slice(0, 5)
  }, [h3Registry, query])

  function selectLocation(hex: string, locality: string) {
    setSelectedHex(hex)
    setQuery(locality)
    setSearchOpen(false)
  }

  return (
    <aside className="operations-panel" aria-labelledby="operations-title">
      <header className="operations-panel-heading">
        <span className="eyebrow">CITY OPERATIONS</span>
        <h1 id="operations-title">Bengaluru Operations</h1>
        <p>Real-time ride-hailing intelligence</p>
      </header>

      <div className="location-search-wrap">
        <label className="visually-hidden" htmlFor="location-search">Search Bengaluru location</label>
        <svg aria-hidden="true" viewBox="0 0 20 20" className="search-icon">
          <circle cx="8.5" cy="8.5" r="5.5" />
          <path d="m13 13 4 4" />
        </svg>
        <input
          id="location-search"
          type="search"
          placeholder="Search Bengaluru location"
          value={query}
          onFocus={() => setSearchOpen(true)}
          onChange={(event) => {
            setQuery(event.target.value)
            setSearchOpen(true)
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') setSearchOpen(false)
            if (event.key === 'Enter' && suggestions[0]) {
              event.preventDefault()
              selectLocation(suggestions[0][0], suggestions[0][1].locality)
            }
          }}
          autoComplete="off"
          aria-autocomplete="list"
          aria-controls="location-suggestions"
          aria-expanded={searchOpen && suggestions.length > 0}
        />
        {searchOpen && suggestions.length > 0 && (
          <div id="location-suggestions" className="location-suggestions" role="listbox" aria-label="Bengaluru locations">
            {suggestions.map(([hex, location]) => (
              <button
                type="button"
                role="option"
                aria-selected={false}
                className="location-suggestion"
                key={hex}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => selectLocation(hex, location.locality)}
              >
                <span>{location.locality}</span>
                <small>{hex.slice(-6)}</small>
              </button>
            ))}
          </div>
        )}
      </div>

      <section className="operations-kpis" aria-label="Live city metrics">
        <article className="operations-kpi">
          <span className="operations-kpi-value">{formatNumber.format(cells.size)}</span>
          <span className="operations-kpi-label">H3 cells</span>
        </article>
        <article className="operations-kpi">
          <span className="operations-kpi-value">{formatNumber.format(summary.total_demand)}</span>
          <span className="operations-kpi-label">Demand</span>
        </article>
        <article className="operations-kpi">
          <span className="operations-kpi-value">{formatNumber.format(summary.total_supply)}</span>
          <span className="operations-kpi-label">Driver supply</span>
        </article>
        <article className="operations-kpi operations-kpi-alerts">
          <span className="operations-kpi-value">{formatNumber.format(summary.active_anomalies_count)}</span>
          <span className="operations-kpi-label">Active anomalies</span>
        </article>
      </section>

      <section className="operations-scenarios" aria-label="Simulation scenarios">
        <div className="operations-section-heading">
          <h2>Scenarios</h2>
          <span>TEST CONDITIONS</span>
        </div>
        <ScenarioDropdown />
      </section>

      <p className="operations-footnote">Vehicle markers summarize live supply by H3 area.</p>
    </aside>
  )
}
