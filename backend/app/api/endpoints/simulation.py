from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.state import app_state
from app.simulation.scenarios import SCENARIOS

router = APIRouter()


class ControlRequest(BaseModel):
    action: str
    speed: int | None = None


class InjectRequest(BaseModel):
    scenario: str


@router.post("/simulation/control")
async def simulation_control(req: ControlRequest) -> dict:
    action = req.action.lower()
    if action == "play":
        app_state.paused = False
    elif action == "pause":
        app_state.paused = True
    elif action == "reset":
        app_state.tick_index = 0
        app_state.paused = False
        app_state.active_scenarios = {}
    elif action == "step":
        # Fire one tick even if paused (loop checks paused flag)
        app_state.paused = False
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action!r}")

    if req.speed is not None:
        if req.speed not in (1, 10, 60, 300):
            raise HTTPException(
                status_code=400, detail="Speed must be 1, 10, 60, or 300"
            )
        app_state.speed = req.speed

    return {
        "paused":     app_state.paused,
        "tick_index": app_state.tick_index,
        "speed":      app_state.speed,
    }


@router.post("/simulation/inject")
async def inject_scenario(req: InjectRequest) -> dict:
    if req.scenario not in SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown scenario {req.scenario!r}. "
                f"Available: {list(SCENARIOS.keys())}"
            ),
        )
    app_state.active_scenarios[req.scenario] = True
    return {
        "injected":         req.scenario,
        "active_scenarios": list(app_state.active_scenarios.keys()),
    }


@router.delete("/simulation/inject/{scenario}")
async def clear_scenario(scenario: str) -> dict:
    app_state.active_scenarios.pop(scenario, None)
    return {
        "cleared":          scenario,
        "active_scenarios": list(app_state.active_scenarios.keys()),
    }


@router.get("/models/summary")
async def models_summary() -> dict:
    return {
        "models_loaded": app_state.models_loaded,
        "metadata":      app_state.model_metadata,
    }
