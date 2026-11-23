"""
Diurnal Demand Curve Generator for Bengaluru ride-hailing simulation.

Produces hour-by-hour demand multipliers calibrated to realistic Bengaluru
commute patterns (tech-corridor morning rush, evening return, nightlife).
"""

import math
from typing import Literal

ZoneType = Literal["RESIDENTIAL", "TECH_PARK", "COMMERCIAL", "TRANSIT", "EVENT", "DEFAULT"]


def _smooth_peak(hour: float, center: float, width: float, height: float) -> float:
    """Gaussian-like smooth peak centered at *center* hour."""
    return height * math.exp(-((hour - center) ** 2) / (2 * width ** 2))


def get_demand_multiplier(
    hour_of_day: float,
    is_weekend: bool = False,
    is_rainy: bool = False,
    zone_type: ZoneType = "DEFAULT",
) -> float:
    """
    Return a demand multiplier in [0.1, ~3.5] for the given hour and conditions.

    The multiplier represents how much actual demand deviates from the cell's
    base demand weight.  A value of 1.0 means average baseline demand.

    Parameters
    ----------
    hour_of_day : float
        Fractional hour (0.0 = midnight, 9.5 = 09:30, 18.75 = 18:45).
    is_weekend : bool
        Saturday or Sunday.
    is_rainy : bool
        Whether precipitation is active.
    zone_type : str
        POI zone type for fine-tuning curves.

    Returns
    -------
    float
        Non-negative demand multiplier.
    """
    h = hour_of_day

    if is_weekend:
        # Weekend: no morning rush, shifted/flatter evening, extended late-night
        base = 0.30                                # quiet night floor
        base += _smooth_peak(h, 10.5, 2.0, 0.50)  # gentle late-morning rise
        base += _smooth_peak(h, 14.0, 2.5, 0.40)  # afternoon activity
        base += _smooth_peak(h, 20.0, 2.5, 1.60)  # evening peak (later)
        base += _smooth_peak(h, 23.0, 2.0, 1.00)  # late-night sustain
    else:
        # Weekday: strong bi-modal commute pattern
        base = 0.25                                # pre-dawn floor (02:00-05:00)
        base += _smooth_peak(h, 9.5, 1.5, 2.50)   # morning rush peak
        base += _smooth_peak(h, 8.0, 1.2, 1.20)   # early commuters
        base += _smooth_peak(h, 12.5, 2.0, 0.55)  # gentle midday
        base += _smooth_peak(h, 18.5, 1.5, 2.20)  # evening rush peak
        base += _smooth_peak(h, 20.0, 1.5, 0.80)  # post-rush tail
        base += _smooth_peak(h, 22.5, 1.5, 0.40)  # late evening taper

    # Zone-specific adjustments
    if zone_type == "TECH_PARK":
        # Tech parks have sharper commute peaks, dead at night
        if not is_weekend:
            base *= 1.3 if 8.0 <= h <= 11.0 or 17.5 <= h <= 20.0 else 0.6
        else:
            base *= 0.3  # almost no tech park activity on weekends
    elif zone_type == "COMMERCIAL":
        # Nightlife zones sustain demand into late hours
        if 21.0 <= h or h <= 2.0:
            base *= 1.5
        elif 10.0 <= h <= 16.0:
            base *= 1.1
    elif zone_type == "TRANSIT":
        # Transit hubs have spread-out demand (airport: 24/7)
        base = max(base, 0.6)  # floor for transit hubs
    elif zone_type == "EVENT":
        # Events are scenario-driven; baseline is similar to commercial
        pass

    # Rain modifier
    if is_rainy:
        # People avoid 2-wheelers and walking; switch to cabs
        rain_boost = 1.8 + 0.7 * _smooth_peak(h, 18.0, 3.0, 1.0)
        base *= rain_boost

    return max(0.1, round(base, 4))


def get_demand_curve_24h(
    is_weekend: bool = False,
    is_rainy: bool = False,
    zone_type: ZoneType = "DEFAULT",
    resolution_minutes: int = 15,
) -> list[tuple[float, float]]:
    """
    Return a full 24-hour demand curve as [(hour, multiplier), ...].

    Parameters
    ----------
    resolution_minutes : int
        Time step in minutes (default 15).
    """
    steps = int(24 * 60 / resolution_minutes)
    curve = []
    for i in range(steps):
        hour = i * resolution_minutes / 60.0
        m = get_demand_multiplier(hour, is_weekend, is_rainy, zone_type)
        curve.append((round(hour, 4), m))
    return curve
