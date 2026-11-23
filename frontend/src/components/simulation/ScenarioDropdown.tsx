import { useState } from 'react'
import { useTelemetryStore, SCENARIOS, type ScenarioKey } from '../../store/telemetryStore'
import { simInject, simClearScenario } from '../../lib/api'

const SCENARIO_ICONS: Record<ScenarioKey, string> = {
  silk_board_monsoon_flood:   '🌧️',
  cricket_match_exit:         '🏏',
  airport_highway_blockage:   '✈️',
  whitefield_tech_conference: '💼',
}

export default function ScenarioDropdown() {
  const activeScenarios   = useTelemetryStore((s) => s.activeScenarios)
  const setActiveScenarios = useTelemetryStore((s) => s.setActiveScenarios)

  const [loading, setLoading] = useState<ScenarioKey | null>(null)

  async function toggle(key: ScenarioKey) {
    if (loading) return
    setLoading(key)
    try {
      const isActive = activeScenarios.includes(key)
      if (isActive) {
        const res = await simClearScenario(key)
        setActiveScenarios(res.active_scenarios as ScenarioKey[])
      } else {
        const res = await simInject(key)
        setActiveScenarios(res.active_scenarios as ScenarioKey[])
      }
    } catch {
      /* backend may not be running in dev */
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="scenario-control" role="group" aria-label="Anomaly scenarios">
      <span className="dock-label">Scenario</span>
      {(Object.keys(SCENARIOS) as ScenarioKey[]).map((key) => {
        const active  = activeScenarios.includes(key)
        const busy    = loading === key
        return (
          <button
            key={key}
            type="button"
            disabled={busy}
            onClick={() => toggle(key)}
            title={SCENARIOS[key]}
            aria-label={`${active ? 'Clear' : 'Inject'} ${SCENARIOS[key]}`}
            aria-pressed={active}
            className={[
              'scenario-button',
              active ? 'is-active' : '',
            ].join(' ')}
          >
            <span aria-hidden="true">{busy ? '…' : SCENARIO_ICONS[key]}</span>
          </button>
        )
      })}
    </div>
  )
}
