"""Main Telemetry Generator for Bengaluru ride-hailing simulation."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import duckdb

from app.core.h3_manager import load_registry_from_geojson
from app.simulation.poi_registry import POIRegistry
from app.simulation.demand_profiles import get_demand_multiplier
from app.simulation.supply_dynamics import get_base_supply, apply_driver_drift
from app.simulation.weather import get_weather, get_weather_modifiers, WeatherState
from app.simulation.scenarios import SCENARIOS, apply_scenario_to_metrics

_REPO_ROOT = Path(__file__).resolve().parents[3]
GEOJSON_PATH = _REPO_ROOT / "data" / "geo" / "bengaluru_h3_res8.json"
PARQUET_OUT = _REPO_ROOT / "data" / "parquet" / "telemetry_60d.parquet"
DUCKDB_OUT = _REPO_ROOT / "data" / "telemetry.duckdb"


class TelemetryGenerator:
    """Generates realistic ride-hailing telemetry for Bengaluru."""

    def __init__(self, seed: int = 42):
        """Initialize with H3 registry and POI mapping."""
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        self.h3_registry = load_registry_from_geojson(GEOJSON_PATH)
        self.poi_registry = POIRegistry(GEOJSON_PATH)
        self.all_cells = sorted([r["h3_index"] for r in self.h3_registry])
        self.h3_neighbors = {r["h3_index"]: r.get("neighbors", []) for r in self.h3_registry}

    def _get_poi_type(self, h3_index: str) -> str:
        """Get POI type for a cell."""
        poi = self.poi_registry.get_poi_by_h3(h3_index)
        return poi.get("poi_type", "DEFAULT") if poi else "DEFAULT"

    def generate_tick(
        self,
        tick_index: int,
        base_date: datetime,
        active_scenarios: dict[str, bool] | None = None,
    ) -> pd.DataFrame:
        """
        Generate one 15-minute tick of telemetry across all cells.

        Returns
        -------
        pd.DataFrame
            Columns: tick_index, timestamp, h3_index, pickup_count, available_drivers,
                     cancellation_rate, surge_multiplier, avg_eta_minutes, is_rainy, scenario_flags
        """
        active_scenarios = active_scenarios or {}
        current_time = base_date + timedelta(minutes=15 * tick_index)
        hour_of_day = current_time.hour + current_time.minute / 60.0
        day_of_year = current_time.timetuple().tm_yday
        is_weekend = current_time.weekday() >= 5
        is_day = 0 < day_of_year <= 365

        weather, rainfall = get_weather(hour_of_day, day_of_year)
        supply_weather_mult, demand_weather_mult = get_weather_modifiers(weather)

        rows = []
        for h3_idx in self.all_cells:
            poi_type = self._get_poi_type(h3_idx)

            # Base demand & supply
            demand_mult = get_demand_multiplier(hour_of_day, is_weekend, weather == WeatherState.HEAVY_RAIN, poi_type)
            base_supply = get_base_supply(poi_type, hour_of_day, is_weekend)

            # Weather modifiers
            demand_final = demand_mult * demand_weather_mult
            supply_final = base_supply * supply_weather_mult

            # Poisson-distributed pickup and dropoff counts
            pickup_count = int(self.np_rng.poisson(max(0.5, demand_final * 15)))  # lambda ~= demand * 15min
            dropoff_count = int(self.np_rng.poisson(max(0.5, pickup_count * 0.9)))

            # Cancellation rate: baseline + weather-driven increases
            cancellation_base = 0.08 + 0.05 * (weather == WeatherState.HEAVY_RAIN)
            cancellation_rate = min(0.5, cancellation_base + 0.02 * (pickup_count - demand_final * 15))

            # ETA: baseline 5-8min, increases with demand and weather
            eta_base = 5.0 + self.rng.uniform(0, 2)
            eta_final = eta_base * (1.0 + 0.1 * max(0, pickup_count - supply_final) / max(1, supply_final))
            if weather == WeatherState.HEAVY_RAIN:
                eta_final *= 1.3
            eta_final = round(eta_final, 2)

            # Surge multiplier: peaks with high demand/supply ratio
            dsr = pickup_count / max(1, supply_final)
            surge_mult = 1.0 + 0.5 * min(3.0, max(0, dsr - 1.0))
            surge_mult = round(surge_mult, 2)

            # Apply scenarios
            scenario_flags = []
            for scn_name, is_active in active_scenarios.items():
                if not is_active:
                    continue
                scn = SCENARIOS.get(scn_name)
                if not scn:
                    continue
                poi = self.poi_registry.get_poi_by_h3(h3_idx)
                if poi and poi.get("locality") in scn.affected_localities:
                    scenario_flags.append(scn_name)
                    metrics = {
                        "pickup_count": pickup_count,
                        "available_drivers": int(supply_final),
                        "cancellation_rate": cancellation_rate,
                        "surge_multiplier": surge_mult,
                        "avg_eta_minutes": eta_final,
                    }
                    modified = apply_scenario_to_metrics(metrics, scn, h3_idx, poi.get("locality", ""), True)
                    pickup_count = modified["pickup_count"]
                    supply_final = modified["available_drivers"]
                    cancellation_rate = modified["cancellation_rate"]
                    surge_mult = modified["surge_multiplier"]
                    eta_final = modified["avg_eta_minutes"]

            rows.append({
                "tick_index": tick_index,
                "timestamp": current_time.isoformat(),
                "h3_index": h3_idx,
                "pickup_count": int(pickup_count),
                "dropoff_count": int(dropoff_count),
                "available_drivers": int(supply_final),
                "cancellation_rate": round(min(0.5, cancellation_rate), 3),
                "surge_multiplier": surge_mult,
                "avg_eta_minutes": eta_final,
                "is_rainy": weather != WeatherState.CLEAR,
                "rainfall_mm": round(rainfall, 2),
                "scenario_flags": json.dumps(scenario_flags),
            })

        return pd.DataFrame(rows)

    def generate_historical_days(
        self,
        num_days: int = 60,
        include_scenarios: bool = True,
        output_path_parquet: Path = PARQUET_OUT,
        output_path_duckdb: Path = DUCKDB_OUT,
    ) -> pd.DataFrame:
        """
        Generate N days of historical telemetry with scenario injection.

        Returns a combined DataFrame and exports to Parquet and DuckDB.
        """
        print(f"\n  Generating {num_days} days of telemetry ({num_days * 96} ticks, {num_days * 96 * len(self.all_cells)} rows total)...")

        base_date = datetime(2026, 9, 1)  # Start from September
        all_rows = []

        # Scenario injection schedule
        scenario_schedule = {}
        if include_scenarios:
            scenario_schedule = {
                10 * 96 + 14 * 4: ("silk_board_monsoon_flood", 4),  # Day 10, 14:00, 4 hours
                20 * 96 + 18 * 4: ("cricket_match_exit", 2),  # Day 20, 18:00, 2 hours
                35 * 96 + 17 * 4 + 2: ("airport_highway_blockage", 3),  # Day 35, 17:30, 3 hours
                45 * 96 + 8 * 4: ("whitefield_tech_conference", 8),  # Day 45, 08:00, 8 hours
            }

        for tick in range(num_days * 96):
            # Determine active scenarios
            active_scenarios = {}
            for scn_name in SCENARIOS.keys():
                active_scenarios[scn_name] = False

            for start_tick, (scn_name, duration_ticks) in scenario_schedule.items():
                if start_tick <= tick < start_tick + duration_ticks:
                    active_scenarios[scn_name] = True

            df_tick = self.generate_tick(tick, base_date, active_scenarios)
            all_rows.append(df_tick)

            if (tick + 1) % (96 * 7) == 0:  # Weekly progress
                print(f"    {tick // 96 + 1}/{num_days} days generated...")

        df_all = pd.concat(all_rows, ignore_index=True)

        # Export to Parquet
        output_path_parquet.parent.mkdir(parents=True, exist_ok=True)
        df_all.to_parquet(output_path_parquet, index=False)
        print(f"  [OK] Parquet written -> {output_path_parquet} ({len(df_all)} rows, {output_path_parquet.stat().st_size / 1024 / 1024:.1f} MB)")

        # Export to DuckDB
        output_path_duckdb.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(output_path_duckdb))
        try:
            con.execute("DROP TABLE IF EXISTS telemetry_15m")
            con.execute("CREATE TABLE telemetry_15m AS SELECT * FROM df_all")
            count = con.execute("SELECT COUNT(*) FROM telemetry_15m").fetchone()[0]
            print(f"  [OK] DuckDB written  -> {output_path_duckdb} ({count} rows)")
        finally:
            con.close()

        return df_all
