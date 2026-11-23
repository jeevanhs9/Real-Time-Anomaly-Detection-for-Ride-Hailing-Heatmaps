"""
Async simulation tick loop — runs as a background asyncio.Task.

Each tick:
  1. Calls TelemetryGenerator.generate_tick()
  2. Featurizes the resulting DataFrame
  3. Runs the AnomalyArbiter across all cells
  4. Pushes HexMetrics into the ring buffer
  5. Broadcasts a TICK_UPDATE payload to all WebSocket clients
"""
from __future__ import annotations
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta

import pandas as pd

from app.config import settings
from app.db.session import ring_buffer, HexMetrics
from app.state import app_state

logger = logging.getLogger(__name__)

_IST = timezone(timedelta(hours=5, minutes=30))
_SIM_BASE = datetime(2026, 9, 1, 0, 0, 0, tzinfo=_IST)


async def simulation_loop() -> None:
    """Infinite tick loop — cancelled on application shutdown."""
    logger.info("Simulation loop started.")
    while True:
        try:
            if not app_state.paused:
                await _run_tick()
        except asyncio.CancelledError:
            logger.info("Simulation loop cancelled.")
            raise
        except Exception as exc:
            logger.exception("Error in simulation tick: %s", exc)
        await asyncio.sleep(settings.tick_interval_secs)


async def _run_tick() -> None:
    t0 = time.perf_counter()
    tick_i = app_state.tick_index
    sim_time = _SIM_BASE + timedelta(minutes=15 * tick_i)

    # 1. Generate raw telemetry
    df_raw: pd.DataFrame = app_state.generator.generate_tick(
        tick_index=tick_i,
        base_date=_SIM_BASE.replace(tzinfo=None),
        active_scenarios=dict(app_state.active_scenarios),
    )

    # 2. Featurize
    df_feat = app_state.featurizer.fit_transform(df_raw)

    # 3. Score with arbiter
    results = app_state.arbiter.score_batch(df_feat)
    result_map = {r.h3_index: r for r in results}

    hex_updates: list[dict] = []
    new_alerts: list[dict] = []

    for _, row in df_raw.iterrows():
        h3 = str(row["h3_index"])
        ar = result_map.get(h3)
        if ar is None:
            continue

        dsr = float(row["pickup_count"]) / max(float(row["available_drivers"]), 1.0)

        m = HexMetrics(
            h3_index=h3,
            timestamp=sim_time,
            tick_index=tick_i,
            pickup_count=int(row["pickup_count"]),
            available_drivers=int(row["available_drivers"]),
            cancellation_rate=float(row["cancellation_rate"]),
            surge_multiplier=float(row["surge_multiplier"]),
            avg_eta_minutes=float(row["avg_eta_minutes"]),
            is_rainy=bool(row["is_rainy"]),
            rainfall_mm=float(row["rainfall_mm"]),
            demand_supply_ratio=round(dsr, 4),
            z_score=ar.z_score,
            lgbm_pred=ar.lgbm_pred,
            residual=ar.residual,
            iso_score=ar.iso_score,
            anomaly_score=ar.anomaly_score,
            severity=ar.severity,
            root_cause=ar.root_cause,
        )
        ring_buffer.push(m)
        hex_updates.append(m.to_dict())

        if ar.severity in ("HIGH", "CRITICAL"):
            locality = app_state.h3_registry_map.get(h3, {}).get("locality", h3)
            new_alerts.append({
                "event_id":    str(uuid.uuid4()),
                "hex":         h3,
                "locality":    locality,
                "severity":    ar.severity,
                "anomaly_score": ar.anomaly_score,
                "root_cause":  ar.root_cause,
                "title": (
                    f"{ar.severity}: "
                    f"{ar.root_cause.replace('_', ' ').title()} at {locality}"
                ),
                "timestamp":   sim_time.isoformat(),
            })

    # 4. Broadcast
    payload = {
        "type":            "TICK_UPDATE",
        "simulation_time": sim_time.isoformat(),
        "tick_index":      tick_i,
        "summary": {
            "total_demand":  sum(u["demand"] for u in hex_updates),
            "total_supply":  sum(u["supply"] for u in hex_updates),
            "active_anomalies_count": sum(
                1 for u in hex_updates if u["severity"] in ("HIGH", "CRITICAL")
            ),
        },
        "hex_updates": hex_updates,
        "new_alerts":  new_alerts,
    }
    await app_state.ws_manager.broadcast(payload)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    app_state.tick_index += 1
    app_state.last_tick_ms = round(elapsed_ms, 2)

    if tick_i % 10 == 0:
        logger.info(
            "Tick %d | sim=%s | cells=%d | alerts=%d | %.1f ms",
            tick_i, sim_time.strftime("%H:%M"),
            len(hex_updates), len(new_alerts), elapsed_ms,
        )
