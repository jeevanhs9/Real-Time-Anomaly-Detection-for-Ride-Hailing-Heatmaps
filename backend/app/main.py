"""
FastAPI application entry point.

Lifespan:
  startup  — load model artefacts, build H3 registry map, initialise
             ConnectionManager, TelemetryGenerator, Featurizer, Arbiter,
             start background simulation loop.
  shutdown — cancel simulation task.
"""
from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.state import app_state

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

_sim_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _sim_task

    logger.info("=== STARTUP ===")

    # Lazy imports keep module-level import order clean
    from app.ml.zscore_baseline import SeasonalZScoreModel
    from app.ml.lightgbm_model import LightGBMRegressorModel
    from app.ml.isolation_forest import IsoForestAnomalyModel
    from app.ml.arbiter import AnomalyArbiter
    from app.core.featurizer import TelemetryFeaturizer
    from app.core.h3_manager import load_registry_from_geojson
    from app.simulation.generator import TelemetryGenerator
    from app.api.websockets.telemetry_hub import ConnectionManager

    # --- Load model artefacts ---
    zm = SeasonalZScoreModel()
    zm.load(settings.zscore_model_path)

    ld = joblib.load(settings.lgbm_model_path)
    lm = LightGBMRegressorModel()
    lm.model_ = ld["model"]
    lm.feature_names_ = ld["feature_names"]
    lm.residual_std_ = ld["residual_std"]

    im = IsoForestAnomalyModel()
    im.load(settings.isoforest_model_path)

    logger.info("Models loaded.")

    # --- H3 registry ---
    registry = load_registry_from_geojson(settings.geojson_path)
    app_state.h3_registry_map = {r["h3_index"]: r for r in registry}
    logger.info("H3 registry: %d cells.", len(app_state.h3_registry_map))

    # --- Wire up components ---
    app_state.ws_manager = ConnectionManager()
    app_state.featurizer = TelemetryFeaturizer(settings.geojson_path)
    app_state.generator = TelemetryGenerator(seed=42)
    app_state.arbiter = AnomalyArbiter(zm, lm, im)
    app_state.models_loaded = True
    app_state.model_metadata = {
        "zscore":    {"threshold":    settings.zscore_threshold},
        "lgbm":      {"residual_std": lm.residual_std_,
                      "k":            settings.residual_sigma_k},
        "isoforest": {"threshold":    settings.isoforest_threshold},
    }

    # --- Start background simulation ---
    from app.simulation.runner import simulation_loop
    _sim_task = asyncio.create_task(simulation_loop(), name="sim_loop")
    logger.info("Simulation loop started.")

    yield  # ← app is running

    # --- Shutdown ---
    logger.info("=== SHUTDOWN ===")
    if _sim_task and not _sim_task.done():
        _sim_task.cancel()
        try:
            await asyncio.wait_for(_sim_task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass


app = FastAPI(
    title="Heatmap Pulse — Bengaluru Anomaly Detection",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
from app.api.endpoints.health import router as health_router
from app.api.endpoints.geo import router as geo_router
from app.api.endpoints.metrics import router as metrics_router
from app.api.endpoints.anomalies import router as anomalies_router
from app.api.endpoints.simulation import router as simulation_router

P = "/api/v1"
app.include_router(health_router,     prefix=P)
app.include_router(geo_router,        prefix=P)
app.include_router(metrics_router,    prefix=P)
app.include_router(anomalies_router,  prefix=P)
app.include_router(simulation_router, prefix=P)


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket) -> None:
    manager = app_state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
