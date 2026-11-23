"""Supply dynamics and driver repositioning for Bengaluru ride-hailing simulation."""

import random
from typing import Literal

ZoneType = Literal["RESIDENTIAL", "TECH_PARK", "COMMERCIAL", "TRANSIT", "EVENT"]


def get_base_supply(
    zone_type: ZoneType,
    hour_of_day: float,
    is_weekend: bool = False,
    cell_demand_level: float = 1.0,
) -> float:
    """
    Return base driver supply (count) for a cell given zone and time.

    Parameters
    ----------
    zone_type : str
        POI type: RESIDENTIAL, TECH_PARK, COMMERCIAL, TRANSIT, EVENT.
    hour_of_day : float
        Fractional hour [0, 24).
    is_weekend : bool
        Weekend day.
    cell_demand_level : float
        Current cell demand (used for dynamic supply attraction).

    Returns
    -------
    float
        Estimated active drivers in this hexagon.
    """
    h = hour_of_day

    if zone_type == "TECH_PARK":
        # High daytime (office hours), low at night
        if 7.5 <= h <= 19.0 and not is_weekend:
            supply = 80 + 40 * (1.0 if 9.0 <= h <= 18.0 else 0.3)
        else:
            supply = 15
    elif zone_type == "RESIDENTIAL":
        # Low daytime (people commuting out), high evening return
        if is_weekend:
            supply = 25 if 8.0 <= h <= 22.0 else 10
        else:
            if 7.0 <= h <= 10.0:
                supply = 8  # outbound rush
            elif 17.0 <= h <= 22.0:
                supply = 45 + 10 * (1.0 if 18.0 <= h <= 20.0 else 0.0)  # return + evening
            else:
                supply = 15
    elif zone_type == "COMMERCIAL":
        # Low daytime, high late-night (nightlife)
        if 9.0 <= h <= 17.0:
            supply = 20
        elif 18.0 <= h <= 2.0:
            supply = 50 + 30 * (1.0 if 20.0 <= h <= 23.0 else 0.3)
        else:
            supply = 10
    elif zone_type == "TRANSIT":
        # Steady, moderate (airport is 24/7)
        supply = 35 + 15 * random.uniform(-0.2, 0.2)
    else:  # EVENT
        supply = 25

    # Slight dynamic attraction: drivers move toward high demand
    supply *= 0.95 + 0.1 * min(cell_demand_level / 3.0, 1.0)

    return max(0.0, supply)


def apply_driver_drift(
    supply_by_h3: dict[str, float],
    h3_neighbors: dict[str, list[str]],
    drift_rate: float = 0.10,
    rng: random.Random | None = None,
) -> dict[str, float]:
    """
    Simulate driver repositioning: 5-15% drift toward neighboring high-demand cells.

    Parameters
    ----------
    supply_by_h3 : dict
        {h3_index: driver_count, ...}
    h3_neighbors : dict
        {h3_index: [neighbor_h3_indices, ...], ...}
    drift_rate : float
        Fraction of drivers (5-15%) who reposition per tick.
    rng : random.Random
        Random state (default: global random).

    Returns
    -------
    dict
        Updated supply_by_h3 after repositioning.
    """
    if rng is None:
        rng = random

    updated = dict(supply_by_h3)
    for h3_idx, supply in supply_by_h3.items():
        neighbors = h3_neighbors.get(h3_idx, [])
        if not neighbors:
            continue

        # Randomly select 5-15% of drivers to reposition
        drift_count = int(supply * rng.uniform(0.05, 0.15))
        if drift_count < 1:
            continue

        # Move to a random neighbor
        target = rng.choice(neighbors)
        updated[h3_idx] -= drift_count
        updated[target] = updated.get(target, 0) + drift_count

    return updated
