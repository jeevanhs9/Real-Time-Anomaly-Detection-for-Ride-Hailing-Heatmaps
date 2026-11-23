"""
In-process DuckDB connection (read-only) and per-cell ring-buffer cache.

The ring buffer holds the last `ring_buffer_depth` HexMetrics for every
hexagon, giving REST and WebSocket handlers instant O(1) access without
hitting disk on every request.
"""
from __future__ import annotations
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import settings


@dataclass
class HexMetrics:
    """One 15-minute telemetry snapshot for a single hexagon."""
    h3_index: str
    timestamp: datetime
    tick_index: int

    pickup_count: int
    available_drivers: int
    cancellation_rate: float
    surge_multiplier: float
    avg_eta_minutes: float
    is_rainy: bool
    rainfall_mm: float

    # Computed by arbiter
    demand_supply_ratio: float = 0.0
    z_score: float = 0.0
    lgbm_pred: float = 0.0
    residual: float = 0.0
    iso_score: float = 0.0
    anomaly_score: float = 0.0
    severity: str = "NORMAL"
    root_cause: str = "NORMAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "hex":               self.h3_index,
            "timestamp":         self.timestamp.isoformat(),
            "tick_index":        self.tick_index,
            "demand":            self.pickup_count,
            "supply":            self.available_drivers,
            "cancellation_rate": round(self.cancellation_rate, 4),
            "surge":             round(self.surge_multiplier, 3),
            "avg_eta_minutes":   round(self.avg_eta_minutes, 2),
            "is_rainy":          self.is_rainy,
            "rainfall_mm":       round(self.rainfall_mm, 2),
            "dsr":               round(self.demand_supply_ratio, 4),
            "z_score":           round(self.z_score, 4),
            "lgbm_pred":         round(self.lgbm_pred, 2),
            "residual":          round(self.residual, 2),
            "iso_score":         round(self.iso_score, 4),
            "anomaly_score":     round(self.anomaly_score, 2),
            "severity":          self.severity,
            "root_cause":        self.root_cause,
        }


class RingBufferCache:
    """Thread-safe per-hexagon circular history buffer."""

    def __init__(self, depth: int = settings.ring_buffer_depth) -> None:
        self._depth = depth
        self._buffers: dict[str, deque[HexMetrics]] = {}
        self._lock = threading.Lock()

    def push(self, m: HexMetrics) -> None:
        with self._lock:
            self._buffers.setdefault(
                m.h3_index, deque(maxlen=self._depth)
            ).append(m)

    def get_history(self, h3: str) -> list[HexMetrics]:
        with self._lock:
            return list(self._buffers.get(h3, deque()))

    def get_latest(self, h3: str) -> HexMetrics | None:
        with self._lock:
            buf = self._buffers.get(h3)
            return buf[-1] if buf else None

    def get_all_latest(self) -> dict[str, HexMetrics]:
        with self._lock:
            return {h: buf[-1] for h, buf in self._buffers.items() if buf}

    def all_h3_indices(self) -> list[str]:
        with self._lock:
            return list(self._buffers.keys())


# Module-level singleton — shared across all requests
ring_buffer = RingBufferCache()
