"""
Phase 4 integration tests — requires trained model artefacts on disk.
Run from project root with:
    $env:PYTHONPATH="backend"
    pytest backend/tests/test_phase4.py -v
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    # Entering TestClient runs the app lifespan, which loads the models and
    # initializes the simulation and WebSocket manager used by these tests.
    with TestClient(app) as test_client:
        yield test_client


def test_health_ok(client: TestClient):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["models_loaded"] is True


def test_health_has_tick_index(client: TestClient):
    r = client.get("/api/v1/health")
    assert "tick_index" in r.json()


def test_geo_hexagons_at_least_400(client: TestClient):
    r = client.get("/api/v1/geo/hexagons")
    assert r.status_code == 200
    assert len(r.json()["features"]) >= 400


def test_geo_hexagons_required_props(client: TestClient):
    r = client.get("/api/v1/geo/hexagons")
    prop = r.json()["features"][0]["properties"]
    for key in ("h3_index", "locality", "lat", "lon"):
        assert key in prop


def test_metrics_snapshot(client: TestClient):
    time.sleep(3)   # allow at least one tick
    r = client.get("/api/v1/metrics/snapshot")
    assert r.status_code == 200
    assert "cells" in r.json()


def test_metrics_history_404_for_unknown(client: TestClient):
    r = client.get("/api/v1/metrics/history/0000000000000000")
    assert r.status_code == 404


def test_anomalies_active_returns_list(client: TestClient):
    r = client.get("/api/v1/anomalies/active")
    assert r.status_code == 200
    assert isinstance(r.json()["anomalies"], list)


def test_simulation_pause(client: TestClient):
    r = client.post("/api/v1/simulation/control", json={"action": "pause"})
    assert r.status_code == 200
    assert r.json()["paused"] is True


def test_simulation_play(client: TestClient):
    r = client.post("/api/v1/simulation/control", json={"action": "play"})
    assert r.status_code == 200
    assert r.json()["paused"] is False


def test_simulation_invalid_action(client: TestClient):
    r = client.post("/api/v1/simulation/control", json={"action": "kaboom"})
    assert r.status_code == 400


def test_inject_silk_board(client: TestClient):
    r = client.post(
        "/api/v1/simulation/inject",
        json={"scenario": "silk_board_monsoon_flood"},
    )
    assert r.status_code == 200
    assert "silk_board_monsoon_flood" in r.json()["active_scenarios"]


def test_inject_unknown_404(client: TestClient):
    r = client.post("/api/v1/simulation/inject", json={"scenario": "nope"})
    assert r.status_code == 404


def test_models_summary_has_three_keys(client: TestClient):
    r = client.get("/api/v1/models/summary")
    assert r.status_code == 200
    meta = r.json()["metadata"]
    for key in ("zscore", "lgbm", "isoforest"):
        assert key in meta


def test_websocket_connect_does_not_raise(client: TestClient):
    with client.websocket_connect("/ws/telemetry"):
        pass
