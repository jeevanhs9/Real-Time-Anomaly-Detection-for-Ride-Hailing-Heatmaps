from fastapi import APIRouter
from app.db.session import ring_buffer

router = APIRouter()

_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "NORMAL": 3}


@router.get("/anomalies/active")
async def get_active_anomalies() -> dict:
    """Return all cells currently in MEDIUM / HIGH / CRITICAL state, ranked."""
    latest = ring_buffer.get_all_latest()
    anom = [
        m.to_dict()
        for m in latest.values()
        if m.severity in ("MEDIUM", "HIGH", "CRITICAL")
    ]
    anom.sort(key=lambda d: _RANK.get(d["severity"], 9))
    return {"count": len(anom), "anomalies": anom}
