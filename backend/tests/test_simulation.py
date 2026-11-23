"""Tests for Phase 2 telemetry simulation engine."""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.simulation.demand_profiles import get_demand_multiplier
from app.simulation.supply_dynamics import get_base_supply
from app.simulation.scenarios import SCENARIOS
from app.simulation.generator import TelemetryGenerator


def test_demand_multiplier_morning_peak():
    """Verify morning rush peak on weekday."""
    m_morning = get_demand_multiplier(9.5, is_weekend=False)
    m_midnight = get_demand_multiplier(3.0, is_weekend=False)
    assert m_morning > 2.0, f"Morning peak {m_morning} should be > 2.0"
    assert m_morning > m_midnight, "Morning should exceed midnight"


def test_demand_multiplier_weekend_shift():
    """Weekend demand should lack sharp morning rush."""
    m_wk_morning = get_demand_multiplier(9.5, is_weekend=False)
    m_we_morning = get_demand_multiplier(9.5, is_weekend=True)
    assert m_wk_morning > m_we_morning * 1.5, "Weekday morning should dominate"


def test_supply_tech_park_vs_residential():
    """Tech parks should have higher daytime supply than residential."""
    s_tech = get_base_supply("TECH_PARK", hour_of_day=10.0, is_weekend=False)
    s_res = get_base_supply("RESIDENTIAL", hour_of_day=10.0, is_weekend=False)
    assert s_tech > s_res * 2, f"Tech supply {s_tech} should exceed residential {s_res} * 2"


def test_scenario_silk_board_exists():
    """Verify Silk Board scenario is defined."""
    scn = SCENARIOS.get("silk_board_monsoon_flood")
    assert scn is not None
    assert scn.supply_multiplier < 0.5
    assert scn.demand_multiplier > 2.0


def test_telemetry_generator_initialization():
    """Verify generator initializes correctly."""
    gen = TelemetryGenerator(seed=42)
    assert len(gen.all_cells) > 400
    assert len(gen.all_cells) < 600


def test_telemetry_generator_tick():
    """Verify single tick generation produces valid data."""
    from datetime import datetime
    gen = TelemetryGenerator(seed=42)
    df = gen.generate_tick(0, datetime(2026, 9, 1), {})
    assert len(df) == len(gen.all_cells)
    assert "pickup_count" in df.columns
    assert "available_drivers" in df.columns
    assert df["pickup_count"].sum() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
