from fastapi import APIRouter
from app.state import app_state
from app.db.session import ring_buffer

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {
        "status":        "ok",
        "models_loaded": app_state.models_loaded,
        "tick_index":    app_state.tick_index,
        "last_tick_ms":  app_state.last_tick_ms,
        "ws_connections": (
            app_state.ws_manager.connection_count
            if app_state.ws_manager else 0
        ),
        "paused":        app_state.paused,
        "speed":         app_state.speed,
        "tracked_cells": len(ring_buffer.all_h3_indices()),
    }
