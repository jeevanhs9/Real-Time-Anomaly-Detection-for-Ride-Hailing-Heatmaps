import json
from functools import lru_cache
from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@lru_cache(maxsize=1)
def _load_geojson() -> dict:
    with open(settings.geojson_path, encoding="utf-8") as fh:
        return json.load(fh)


@router.get("/geo/hexagons")
async def get_hexagons() -> dict:
    """Return GeoJSON FeatureCollection of all 535 Bengaluru H3 cells."""
    return _load_geojson()
