"""Application settings — resolved from environment with safe defaults."""
from __future__ import annotations
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class _Base(BaseSettings):
        model_config = SettingsConfigDict(env_prefix="HEATMAP_", case_sensitive=False)
except ImportError:
    from pydantic import BaseSettings  # type: ignore[no-redef]

    class _Base(BaseSettings):  # type: ignore[no-redef]
        class Config:
            env_prefix = "HEATMAP_"


_ROOT = Path(__file__).resolve().parents[2]


class Settings(_Base):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Simulation
    tick_interval_secs: float = 2.0
    simulation_speed: int = 1
    simulation_paused: bool = False

    # Paths
    geojson_path: Path = _ROOT / "data" / "geo" / "bengaluru_h3_res8.json"
    parquet_path: Path = _ROOT / "data" / "parquet" / "telemetry_60d.parquet"
    duckdb_path: Path = _ROOT / "data" / "telemetry.duckdb"

    zscore_model_path: Path = (
        _ROOT / "data" / "models" / "zscore_baseline.joblib"
    )
    lgbm_model_path: Path = (
        _ROOT / "data" / "models" / "lightgbm_demand.joblib"
    )
    isoforest_model_path: Path = (
        _ROOT / "data" / "models" / "isoforest_market.joblib"
    )

    # Arbiter thresholds
    zscore_threshold: float = 3.0
    residual_sigma_k: float = 3.0
    isoforest_threshold: float = 0.65

    # Ring-buffer depth (96 × 15 min = 24 h)
    ring_buffer_depth: int = 96


settings = Settings()
