"""Weather simulation and rain-driven demand/supply modifiers."""

from enum import Enum
from typing import Literal


class WeatherState(Enum):
    CLEAR = "CLEAR"
    LIGHT_RAIN = "LIGHT_RAIN"
    HEAVY_RAIN = "HEAVY_RAIN"


def get_weather(
    hour_of_day: float,
    day_of_year: int = 1,
    scenario_override: WeatherState | None = None,
) -> tuple[WeatherState, float]:
    """
    Return weather state and rainfall intensity (mm/h).

    Parameters
    ----------
    hour_of_day : float
        Fractional hour [0, 24).
    day_of_year : int
        Day 1-365 (used for seasonal monsoon patterns).
    scenario_override : WeatherState or None
        Force a weather state (used for scenario injection).

    Returns
    -------
    tuple[WeatherState, float]
        (weather_state, rainfall_mm_per_hour)
    """
    if scenario_override is not None:
        if scenario_override == WeatherState.CLEAR:
            return WeatherState.CLEAR, 0.0
        elif scenario_override == WeatherState.LIGHT_RAIN:
            return WeatherState.LIGHT_RAIN, 2.5 + (hour_of_day % 3.0)
        else:  # HEAVY_RAIN
            return WeatherState.HEAVY_RAIN, 15.0 + (hour_of_day % 8.0)

    # Simplified seasonal pattern: monsoon June-September (days 152-274)
    is_monsoon = 152 <= day_of_year <= 274

    # Stochastic rainfall: slightly higher probability during monsoon afternoons
    if is_monsoon and 14.0 <= hour_of_day <= 18.0:
        # ~40% chance of rain during monsoon afternoon
        rain_prob = 0.40
    else:
        # ~10% chance otherwise
        rain_prob = 0.10

    import random

    if random.random() < rain_prob:
        # Rain occurred; determine intensity
        if random.random() < 0.3:
            # Light rain
            return WeatherState.LIGHT_RAIN, 1.5 + random.uniform(0.5, 3.5)
        else:
            # Heavy rain
            return WeatherState.HEAVY_RAIN, 10.0 + random.uniform(3.0, 12.0)
    else:
        return WeatherState.CLEAR, 0.0


def get_weather_modifiers(
    weather: WeatherState,
) -> tuple[float, float]:
    """
    Return (supply_multiplier, demand_multiplier) based on weather.

    Parameters
    ----------
    weather : WeatherState
        Current weather state.

    Returns
    -------
    tuple[float, float]
        (supply_mult, demand_mult)
    """
    if weather == WeatherState.CLEAR:
        return 1.0, 1.0
    elif weather == WeatherState.LIGHT_RAIN:
        return 0.80, 1.40
    else:  # HEAVY_RAIN
        return 0.65, 2.50
