import { useState } from 'react'
import { useTelemetryStore, type SimSpeed } from '../../store/telemetryStore'
import { simControl } from '../../lib/api'
import ScenarioDropdown from './ScenarioDropdown'

const SPEEDS: SimSpeed[] = [1, 10, 60, 300]

export default function SimulationControls() {
  const paused   = useTelemetryStore((s) => s.paused)
  const speed    = useTelemetryStore((s) => s.speed)
  const setPaused = useTelemetryStore((s) => s.setPaused)
  const setSpeed  = useTelemetryStore((s) => s.setSpeed)

  const [busy, setBusy] = useState(false)

  async function handleControl(action: string, newSpeed?: SimSpeed) {
    if (busy) return
    setBusy(true)
    try {
      const res = await simControl(action, newSpeed)
      setPaused(res.paused)
      if (newSpeed) setSpeed(newSpeed)
    } catch {
      /* silently ignore — backend may not be running in dev */
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="simulation-dock" role="group" aria-label="Simulation controls">
      <button
        type="button"
        disabled={busy}
        onClick={() => handleControl(paused ? 'play' : 'pause')}
        className="control-primary"
        title={paused ? 'Resume simulation' : 'Pause simulation'}
        aria-label={paused ? 'Resume simulation' : 'Pause simulation'}
      >
        <span aria-hidden="true">{paused ? '▶' : 'Ⅱ'}</span>{paused ? 'Play' : 'Pause'}
      </button>

      <button
        type="button"
        disabled={busy}
        onClick={() => handleControl('step')}
        className="control-secondary"
        title="Advance one 15-min tick"
        aria-label="Advance one simulation tick"
      >
        <span aria-hidden="true">›</span>Step
      </button>

      <span className="dock-divider" aria-hidden="true" />

      <div className="speed-control" role="group" aria-label="Simulation speed">
        <span className="dock-label">Speed</span>
        <div className="speed-options">
        {SPEEDS.map((s) => (
          <button
            key={s}
            type="button"
            disabled={busy}
            onClick={() => handleControl('play', s)}
            aria-pressed={speed === s}
            aria-label={`Set simulation speed to ${s} times`}
            className={[
              'speed-option',
              speed === s ? 'is-active' : '',
            ].join(' ')}
          >
            {s}×
          </button>
        ))}
        </div>
      </div>

      <span className="dock-divider" aria-hidden="true" />

      <ScenarioDropdown />

      <span className={`simulation-state ${paused ? 'is-paused' : 'is-running'}`}>
        <i aria-hidden="true" />{paused ? 'Paused' : 'Running'}
      </span>
    </div>
  )
}
