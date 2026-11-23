import { create } from 'zustand'
import type { CellMetrics, Alert, TickUpdate, TickSummary } from '../types/telemetry'

const MAX_ALERTS = 50

// ── Simulation control types ──────────────────────────────────────────────────

export type SimSpeed = 1 | 10 | 60 | 300

export const SCENARIOS = {
  silk_board_monsoon_flood:   'Silk Board Monsoon Flood',
  cricket_match_exit:         'Cricket Match Exit Surge',
  airport_highway_blockage:   'Airport Highway Blockage',
  whitefield_tech_conference: 'Whitefield Tech Conference',
} as const

export type ScenarioKey = keyof typeof SCENARIOS

// ── Store interface ───────────────────────────────────────────────────────────

export interface TelemetryState {
  // Connection
  isConnected: boolean
  wsError:     string | null

  // Live data
  cells:     Map<string, CellMetrics>
  alerts:    Alert[]
  simTime:   string
  tickIndex: number
  summary:   TickSummary

  // Per-cell drill-down history (fetched on demand from REST)
  cellHistory: Map<string, CellMetrics[]>
  historyLoading: boolean

  // Static H3 registry: hex → { locality, lat, lon, ... }  (loaded once from REST)
  h3Registry: Record<string, { locality: string; lat: number; lon: number }>

  // UI selection
  selectedHex: string | null

  // Simulation control state (mirrors backend)
  paused:          boolean
  speed:           SimSpeed
  activeScenarios: ScenarioKey[]

  // Actions — data
  setConnected:    (v: boolean) => void
  setWsError:      (e: string | null) => void
  applyTick:       (tick: TickUpdate) => void
  clearAlerts:     () => void

  // Actions — UI
  setSelectedHex:  (h: string | null) => void
  setCellHistory:  (hex: string, ticks: CellMetrics[]) => void
  setHistoryLoading: (v: boolean) => void
  setH3Registry: (r: Record<string, { locality: string; lat: number; lon: number }>) => void

  // Actions — simulation (call API then update local state)
  setPaused:          (v: boolean) => void
  setSpeed:           (s: SimSpeed) => void
  setActiveScenarios: (keys: ScenarioKey[]) => void
}

// ── Default summary ───────────────────────────────────────────────────────────

const DEFAULT_SUMMARY: TickSummary = {
  total_demand: 0,
  total_supply: 0,
  active_anomalies_count: 0,
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useTelemetryStore = create<TelemetryState>((set) => ({
  isConnected:     false,
  wsError:         null,
  cells:           new Map(),
  alerts:          [],
  simTime:         '',
  tickIndex:       0,
  summary:         DEFAULT_SUMMARY,
  cellHistory:     new Map(),
  historyLoading:  false,
  h3Registry:      {},
  selectedHex:     null,
  paused:          false,
  speed:           1,
  activeScenarios: [],

  // ── data actions ─────────────────────────────────────────────────────────
  setConnected: (v) =>
    set({ isConnected: v, ...(v ? { wsError: null } : {}) }),

  setWsError: (e) => set({ wsError: e }),

  applyTick: (tick) =>
    set((state) => {
      const cells = new Map(state.cells)
      for (const c of tick.hex_updates) cells.set(c.hex, c)
      const alerts = [...tick.new_alerts, ...state.alerts].slice(0, MAX_ALERTS)
      return { cells, alerts, simTime: tick.simulation_time, tickIndex: tick.tick_index, summary: tick.summary }
    }),

  clearAlerts: () => set({ alerts: [] }),

  // ── UI actions ────────────────────────────────────────────────────────────
  setSelectedHex: (h) => set({ selectedHex: h }),

  setCellHistory: (hex, ticks) =>
    set((state) => {
      const cellHistory = new Map(state.cellHistory)
      cellHistory.set(hex, ticks)
      return { cellHistory }
    }),

  setHistoryLoading: (v) => set({ historyLoading: v }),

  setH3Registry: (r) => set({ h3Registry: r }),

  // ── simulation actions ────────────────────────────────────────────────────
  setPaused:          (v)    => set({ paused: v }),
  setSpeed:           (s)    => set({ speed: s }),
  setActiveScenarios: (keys) => set({ activeScenarios: keys }),
}))
