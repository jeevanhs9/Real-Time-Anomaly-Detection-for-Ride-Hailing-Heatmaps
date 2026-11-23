"""Predefined anomaly injection scenarios for Bengaluru ride-hailing simulation."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class AnomalyScenario:
    """Definition of an injectable anomaly event."""
    name: str
    description: str
    affected_localities: list[str]
    supply_multiplier: float
    demand_multiplier: float
    eta_multiplier: float
    start_hour: float
    duration_hours: float
    cancellation_rate_delta: float


SCENARIOS = {
    "silk_board_monsoon_flood": AnomalyScenario(
        name="Silk Board Monsoon Flood",
        description="Heavy rain + traffic stoppage at Silk Board junction",
        affected_localities=["Silk Board Junction", "BTM Layout", "HSR Layout"],
        supply_multiplier=0.30,
        demand_multiplier=2.50,
        eta_multiplier=3.00,
        start_hour=14.0,
        duration_hours=4.0,
        cancellation_rate_delta=0.20,
    ),
    "cricket_match_exit": AnomalyScenario(
        name="Cricket Match Exit Surge",
        description="Sharp spatial demand surge post-match at Chinnaswamy Stadium",
        affected_localities=["MG Road / CBD", "Koramangala", "Indiranagar"],
        supply_multiplier=0.85,
        demand_multiplier=4.00,
        eta_multiplier=2.50,
        start_hour=18.0,
        duration_hours=2.0,
        cancellation_rate_delta=0.15,
    ),
    "airport_highway_blockage": AnomalyScenario(
        name="Airport Highway Blockage",
        description="NH7 / HSR Layout road closure due to accident",
        affected_localities=["Kempegowda Airport (BLR)", "Yelahanka", "Yeshwanthpur"],
        supply_multiplier=0.40,
        demand_multiplier=1.80,
        eta_multiplier=3.50,
        start_hour=17.5,
        duration_hours=3.0,
        cancellation_rate_delta=0.25,
    ),
    "whitefield_tech_conference": AnomalyScenario(
        name="Whitefield Tech Conference",
        description="Large enterprise event: sustained demand surge 8 hours",
        affected_localities=["Whitefield", "Marathahalli", "ITPL", "Manyata Tech Park / Hebbal"],
        supply_multiplier=0.95,
        demand_multiplier=2.00,
        eta_multiplier=1.50,
        start_hour=8.0,
        duration_hours=8.0,
        cancellation_rate_delta=0.05,
    ),
}


def get_scenario(scenario_name: str) -> AnomalyScenario | None:
    """Return scenario by name, or None if not found."""
    return SCENARIOS.get(scenario_name)


def apply_scenario_to_metrics(
    metrics_dict: dict,
    scenario: AnomalyScenario,
    h3_index: str,
    locality_name: str,
    is_affected: bool,
) -> dict:
    """
    Modify a single cell's metrics if it falls within an anomaly scenario.

    Parameters
    ----------
    metrics_dict : dict
        Current metrics: {pickup_count, available_drivers, cancellation_rate, surge, eta}
    scenario : AnomalyScenario
        Anomaly to apply.
    h3_index : str
        Cell H3 index (for logging).
    locality_name : str
        Cell locality name.
    is_affected : bool
        Whether this cell is in the scenario's affected zone.

    Returns
    -------
    dict
        Modified metrics if affected, else original.
    """
    if not is_affected:
        return metrics_dict

    return {
        **metrics_dict,
        "pickup_count": int(metrics_dict.get("pickup_count", 0) * scenario.demand_multiplier),
        "available_drivers": max(0, int(metrics_dict.get("available_drivers", 0) * scenario.supply_multiplier)),
        "cancellation_rate": min(0.5, metrics_dict.get("cancellation_rate", 0.0) + scenario.cancellation_rate_delta),
        "surge_multiplier": metrics_dict.get("surge_multiplier", 1.0) * (scenario.demand_multiplier / scenario.supply_multiplier),
        "avg_eta_minutes": metrics_dict.get("avg_eta_minutes", 5.0) * scenario.eta_multiplier,
    }
