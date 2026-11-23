// ── WebSocket payload shapes ──────────────────────────────────────────────────

export type Severity =
  | 'NORMAL'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'

export type RootCause =
  | 'NORMAL'
  | 'DEMAND_SPIKE'
  | 'SUPPLY_COLLAPSE'
  | 'MARKET_ANOMALY'
  | 'WEATHER_DISRUPTION'

export interface CellMetrics {
  hex:               string
  timestamp:         string
  tick_index:        number
  demand:            number
  supply:            number
  cancellation_rate: number
  surge:             number
  avg_eta_minutes:   number
  is_rainy:          boolean
  rainfall_mm:       number
  dsr:               number
  z_score:           number
  lgbm_pred:         number
  residual:          number
  iso_score:         number
  anomaly_score:     number
  severity:          Severity
  root_cause:        RootCause
}

export interface Alert {
  event_id:    string
  hex:         string
  locality:    string
  severity:    Severity
  anomaly_score: number
  root_cause:  RootCause
  title:       string
  timestamp:   string
}

export interface TickSummary {
  total_demand:           number
  total_supply:           number
  active_anomalies_count: number
}

export interface TickUpdate {
  type:            'TICK_UPDATE'
  simulation_time: string
  tick_index:      number
  summary:         TickSummary
  hex_updates:     CellMetrics[]
  new_alerts:      Alert[]
}
