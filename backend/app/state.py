"""
Module-level application state singleton.

Populated during FastAPI lifespan startup; read everywhere else.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    # Injected on startup
    generator: Any = None
    featurizer: Any = None
    arbiter: Any = None
    ws_manager: Any = None

    # h3_index → registry dict (locality, lat, lon, …)
    h3_registry_map: dict[str, dict] = field(default_factory=dict)

    # Simulation runtime
    tick_index: int = 0
    paused: bool = False
    speed: int = 1
    active_scenarios: dict[str, bool] = field(default_factory=dict)
    last_tick_ms: float = 0.0

    # Model metadata
    models_loaded: bool = False
    model_metadata: dict[str, Any] = field(default_factory=dict)


app_state = AppState()
