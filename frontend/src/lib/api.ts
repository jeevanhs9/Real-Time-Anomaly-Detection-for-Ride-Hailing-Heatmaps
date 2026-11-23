/**
 * Thin fetch wrappers for the FastAPI backend.
 * All paths are relative so Vite's proxy (/api → localhost:8000) handles routing.
 */

import type { CellMetrics } from '../types/telemetry'
import type { SimSpeed, ScenarioKey } from '../store/telemetryStore'

const BASE = '/api/v1'

// ── types ─────────────────────────────────────────────────────────────────────

export interface ControlResponse {
  paused:     boolean
  tick_index: number
  speed:      number
}

export interface InjectResponse {
  injected:          string
  active_scenarios:  string[]
}

export interface HistoryResponse {
  h3_index: string
  count:    number
  ticks:    CellMetrics[]
}

// ── helpers ───────────────────────────────────────────────────────────────────

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`POST ${path} → ${r.status}`)
  return r.json() as Promise<T>
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`GET ${path} → ${r.status}`)
  return r.json() as Promise<T>
}

// ── simulation control ────────────────────────────────────────────────────────

export const simControl = (action: string, speed?: SimSpeed) =>
  post<ControlResponse>('/simulation/control', { action, ...(speed ? { speed } : {}) })

export const simInject = (scenario: ScenarioKey) =>
  post<InjectResponse>('/simulation/inject', { scenario })

export const simClearScenario = (scenario: ScenarioKey) =>
  fetch(`${BASE}/simulation/inject/${scenario}`, { method: 'DELETE' }).then(
    (r) => r.json() as Promise<InjectResponse>,
  )

// ── metrics ───────────────────────────────────────────────────────────────────

export const fetchCellHistory = (h3_index: string) =>
  get<HistoryResponse>(`/metrics/history/${h3_index}`)
