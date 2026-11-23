from fastapi import APIRouter, HTTPException
from app.db.session import ring_buffer

router = APIRouter()


@router.get("/metrics/snapshot")
async def get_snapshot() -> dict:
    latest = ring_buffer.get_all_latest()
    return {"count": len(latest), "cells": [m.to_dict() for m in latest.values()]}


@router.get("/metrics/history/{h3_index}")
async def get_cell_history(h3_index: str) -> dict:
    history = ring_buffer.get_history(h3_index)
    if not history:
        raise HTTPException(status_code=404, detail=f"No data for {h3_index}")
    return {
        "h3_index": h3_index,
        "count":    len(history),
        "ticks":    [m.to_dict() for m in history],
    }
