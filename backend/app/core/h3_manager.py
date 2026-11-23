"""
Bengaluru H3 Hexagonal Spatial Registry Manager.

Partitions the urban extent of Bengaluru (BBMP metropolitan core and the
Kempegowda International Airport northern corridor) into a deterministic set
of H3 Resolution-8 hexagons.  For every cell the module computes:
  - Centroid coordinates (lat, lon)
  - GeoJSON polygon boundary coordinates ([lon, lat] ring, closed)
  - k=1 ring neighbours
  - Human-readable locality label, commercial / tech-hub / transit-hub flags

Compatible with h3-py v4 (`latlng_to_cell`, `cell_to_latlng`,
`polygon_to_cells`, `grid_disk`) only.  The older v3 API names
(geo_to_h3, polyfill …) are NOT present in h3≥4.0.

Output artefacts
----------------
data/geo/bengaluru_h3_res8.json      - GeoJSON FeatureCollection
data/geo/bengaluru_hex_registry.duckdb   - Persistent DuckDB analytical table
"""

import math
import json
import logging
from pathlib import Path
from typing import Any

import h3
import duckdb

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project-root-relative output paths
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]  # …/backend/app/core → root
GEO_DIR = _REPO_ROOT / "data" / "geo"
GEOJSON_OUT = GEO_DIR / "bengaluru_h3_res8.json"
DUCKDB_OUT = GEO_DIR / "bengaluru_hex_registry.duckdb"

# ---------------------------------------------------------------------------
# H3 resolution
# ---------------------------------------------------------------------------
RESOLUTION = 8

# ---------------------------------------------------------------------------
# Bengaluru BBMP urban boundary polygon
# -----------------------------------------------------------------------
# Vertices ordered counter-clockwise, forming a concave hull that covers:
#   - BBMP core metro (Whitefield, ORR corridor, Electronic City)
#   - Airport northern corridor (Yelahanka → Devanahalli)
# Coordinates are (lat, lon) as h3.LatLngPoly expects.
# ---------------------------------------------------------------------------
BENGALURU_BOUNDARY_COORDS: list[tuple[float, float]] = [
    (12.845, 77.655),   # A: Electronic City South
    (12.855, 77.685),   # B: Electronic City Phase 1 East
    (12.905, 77.695),   # C: Bellandur / Sarjapur ORR junction
    (12.955, 77.745),   # D: Whitefield South Corridor
    (12.995, 77.745),   # E: ITPL / Kadugodi
    (13.025, 77.695),   # F: KR Puram / Mahadevapura
    (13.050, 77.630),   # G: Manyata Tech Park / Nagavara
    (13.100, 77.605),   # H: Yelahanka New Town
    (13.200, 77.710),   # I: Kempegowda Int'l Airport – North-East
    (13.200, 77.690),   # J: Kempegowda Int'l Airport – North-West
    (13.075, 77.585),   # K: Hebbal Flyover
    (13.035, 77.535),   # L: Yeshwanthpur / Peenya junction
    (12.980, 77.525),   # M: Rajajinagar / Nagarbhavi
    (12.925, 77.545),   # N: Jayanagar South / Uttarahalli
    (12.875, 77.595),   # O: BTM Layout / Bannerghatta Road south
    (12.845, 77.655),   # A′: ring closed
]

# ---------------------------------------------------------------------------
# Landmark catalogue
# (name, lat, lon, is_commercial, is_tech_hub, is_transit_hub)
# Each cell is tagged to the *closest* landmark by Haversine distance.
# ---------------------------------------------------------------------------
LANDMARKS: list[tuple[str, float, float, bool, bool, bool]] = [
    ("Koramangala",               12.9352, 77.6245, True,  False, False),
    ("Indiranagar",               12.9784, 77.6408, True,  False, False),
    ("Whitefield",                12.9698, 77.7500, True,  True,  False),
    ("Electronic City",           12.8452, 77.6602, False, True,  False),
    ("HSR Layout",                12.9121, 77.6446, True,  False, False),
    ("Bellandur / ORR",           12.9250, 77.6780, False, True,  False),
    ("Marathahalli",              12.9591, 77.7011, True,  True,  False),
    ("MG Road / CBD",             12.9756, 77.6066, True,  False, True),
    ("Kempegowda Airport (BLR)", 13.1986, 77.7066, False, False, True),
    ("Manyata Tech Park / Hebbal",13.0450, 77.6200, False, True,  False),
    ("Jayanagar / JP Nagar",      12.9250, 77.5850, True,  False, False),
    ("Silk Board Junction",       12.9176, 77.6238, True,  False, True),
    ("Majestic / KSR Station",    12.9780, 77.5695, True,  False, True),
    ("Yeshwanthpur",              13.0280, 77.5410, True,  True,  True),
    ("BTM Layout",                12.9166, 77.6101, True,  False, False),
    ("Domlur / EGL",              12.9610, 77.6387, True,  True,  False),
    ("Yelahanka",                 13.1007, 77.5963, False, False, True),
    ("KR Puram",                  13.0075, 77.6959, False, False, True),
    ("Rajajinagar",               12.9982, 77.5530, True,  False, False),
    ("Malleshwaram",              13.0031, 77.5643, True,  False, False),
]


# ---------------------------------------------------------------------------
# Utility: Haversine great-circle distance (km)
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


# ---------------------------------------------------------------------------
# Core spatial functions
# ---------------------------------------------------------------------------

def get_bengaluru_boundary_polygon() -> h3.LatLngPoly:
    """Return the h3.LatLngPoly covering the Bengaluru BBMP urban extent."""
    return h3.LatLngPoly(BENGALURU_BOUNDARY_COORDS)


def get_all_bengaluru_cells(resolution: int = RESOLUTION) -> list[str]:
    """
    Return a sorted list of all H3 cell indices at *resolution* that fall
    within the Bengaluru boundary polygon.

    Parameters
    ----------
    resolution:
        H3 resolution (default 8, ~0.74 km² per cell).
    """
    poly = get_bengaluru_boundary_polygon()
    cells = h3.polygon_to_cells(poly, resolution)
    logger.info("Covered %d H3 res-%d hexagons inside the Bengaluru boundary.",
                len(cells), resolution)
    return sorted(cells)


def get_cell_centroid(cell: str) -> tuple[float, float]:
    """Return (lat, lon) centroid for *cell*."""
    lat, lon = h3.cell_to_latlng(cell)
    return lat, lon


def get_cell_boundary_geojson(cell: str) -> list[list[float]]:
    """
    Return the closed GeoJSON polygon ring for *cell* as [[lon, lat], …].
    The ring has 7 points (6 hexagon vertices + closing repeat of the first).
    """
    boundary = h3.cell_to_boundary(cell)   # returns tuple of (lat, lon) pairs
    ring = [[lon, lat] for lat, lon in boundary]
    ring.append(ring[0])                   # close the ring
    return ring


def get_cell_neighbors(cell: str) -> list[str]:
    """Return the six k=1 ring neighbours of *cell* (the centre excluded)."""
    disk = h3.grid_disk(cell, 1)
    return sorted(n for n in disk if n != cell)


def tag_cell(cell_lat: float, cell_lon: float) -> dict[str, Any]:
    """
    Find the closest landmark to (cell_lat, cell_lon) and return a tag dict::

        {
            "locality":         str,
            "is_commercial":    bool,
            "is_tech_hub":      bool,
            "is_transit_hub":   bool,
        }
    """
    best_name, best_comm, best_tech, best_transit = LANDMARKS[0][:4]
    min_dist = float("inf")

    for name, lat, lon, comm, tech, transit in LANDMARKS:
        dist = _haversine_km(cell_lat, cell_lon, lat, lon)
        if dist < min_dist:
            min_dist = dist
            best_name = name
            best_comm = comm
            best_tech = tech
            best_transit = transit

    return {
        "locality":      best_name,
        "is_commercial": best_comm,
        "is_tech_hub":   best_tech,
        "is_transit_hub": best_transit,
    }


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------

def build_registry() -> list[dict[str, Any]]:
    """
    Generate the full Bengaluru hexagonal cell registry.

    Returns a list of dicts, one per cell, with keys:
        h3_index, locality, is_commercial, is_tech_hub, is_transit_hub,
        lat, lon, neighbors, geojson_boundary
    """
    cells = get_all_bengaluru_cells()
    registry: list[dict[str, Any]] = []

    for cell in cells:
        lat, lon = get_cell_centroid(cell)
        boundary = get_cell_boundary_geojson(cell)
        neighbors = get_cell_neighbors(cell)
        tag = tag_cell(lat, lon)

        registry.append({
            "h3_index":        cell,
            "lat":             lat,
            "lon":             lon,
            "locality":        tag["locality"],
            "is_commercial":   tag["is_commercial"],
            "is_tech_hub":     tag["is_tech_hub"],
            "is_transit_hub":  tag["is_transit_hub"],
            "neighbors":       neighbors,
            "geojson_boundary": boundary,
        })

    logger.info("Built registry for %d cells.", len(registry))
    return registry


# ---------------------------------------------------------------------------
# GeoJSON exporter
# ---------------------------------------------------------------------------

def export_geojson(registry: list[dict[str, Any]], output_path: Path = GEOJSON_OUT) -> None:
    """
    Write *registry* as a GeoJSON FeatureCollection to *output_path*.

    Each Feature contains:
    - geometry  : Polygon (hexagon boundary)
    - properties: h3_index, locality, is_commercial, is_tech_hub,
                  is_transit_hub, lat, lon, neighbors
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    features = []
    for rec in registry:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [rec["geojson_boundary"]],  # GeoJSON Polygon ring
            },
            "properties": {
                "h3_index":      rec["h3_index"],
                "locality":      rec["locality"],
                "is_commercial": rec["is_commercial"],
                "is_tech_hub":   rec["is_tech_hub"],
                "is_transit_hub": rec["is_transit_hub"],
                "lat":           rec["lat"],
                "lon":           rec["lon"],
                "neighbors":     rec["neighbors"],
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "total_cells": len(registry),
            "resolution":  RESOLUTION,
            "city":        "Bengaluru, Karnataka, India",
        },
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(geojson, fh, indent=2, ensure_ascii=False)

    logger.info("GeoJSON registry written to %s", output_path)
    print(f"  [OK] GeoJSON written -> {output_path}  ({output_path.stat().st_size / 1024:.1f} KB)")


# ---------------------------------------------------------------------------
# DuckDB exporter
# ---------------------------------------------------------------------------

def export_duckdb(registry: list[dict[str, Any]], db_path: Path = DUCKDB_OUT) -> None:
    """
    Persist *registry* to a DuckDB file as table ``h3_hex_spatial_registry``.

    The table is re-created on every call so the file stays up-to-date.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    try:
        con.execute("DROP TABLE IF EXISTS h3_hex_spatial_registry")
        con.execute("""
            CREATE TABLE h3_hex_spatial_registry (
                h3_index        VARCHAR PRIMARY KEY,
                locality        VARCHAR NOT NULL,
                lat             DOUBLE  NOT NULL,
                lon             DOUBLE  NOT NULL,
                is_commercial   BOOLEAN NOT NULL,
                is_tech_hub     BOOLEAN NOT NULL,
                is_transit_hub  BOOLEAN NOT NULL,
                neighbor_count  INTEGER NOT NULL,
                neighbors_json  VARCHAR NOT NULL
            )
        """)

        rows = [
            (
                rec["h3_index"],
                rec["locality"],
                rec["lat"],
                rec["lon"],
                rec["is_commercial"],
                rec["is_tech_hub"],
                rec["is_transit_hub"],
                len(rec["neighbors"]),
                json.dumps(rec["neighbors"]),
            )
            for rec in registry
        ]

        con.executemany(
            "INSERT INTO h3_hex_spatial_registry VALUES (?,?,?,?,?,?,?,?,?)",
            rows,
        )

        count = con.execute("SELECT COUNT(*) FROM h3_hex_spatial_registry").fetchone()[0]
        logger.info("DuckDB table h3_hex_spatial_registry has %d rows.", count)
        print(f"  [OK] DuckDB written  -> {db_path}  ({count} rows)")
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Convenience loader (used by other modules & tests)
# ---------------------------------------------------------------------------

def load_registry_from_geojson(path: Path = GEOJSON_OUT) -> list[dict[str, Any]]:
    """
    Load the previously exported GeoJSON FeatureCollection and return a list
    of property dicts (one per cell), augmenting each with a 'geojson_boundary'
    key for completeness.
    """
    with open(path, encoding="utf-8") as fh:
        fc = json.load(fh)

    records = []
    for feat in fc["features"]:
        props = dict(feat["properties"])
        props["geojson_boundary"] = feat["geometry"]["coordinates"][0]
        records.append(props)
    return records


def load_registry_from_duckdb(db_path: Path = DUCKDB_OUT) -> list[dict[str, Any]]:
    """Return all rows from the h3_hex_spatial_registry DuckDB table as dicts."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        rows = con.execute("SELECT * FROM h3_hex_spatial_registry ORDER BY h3_index").fetchall()
        cols = [
            "h3_index", "locality", "lat", "lon",
            "is_commercial", "is_tech_hub", "is_transit_hub",
            "neighbor_count", "neighbors_json",
        ]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        con.close()


# ---------------------------------------------------------------------------
# High-level public entry point
# ---------------------------------------------------------------------------

def generate_and_export(
    geojson_path: Path = GEOJSON_OUT,
    duckdb_path: Path = DUCKDB_OUT,
) -> list[dict[str, Any]]:
    """
    Build the complete Bengaluru H3 registry and persist both GeoJSON and
    DuckDB artefacts.  Returns the in-memory registry list.
    """
    print("\n  Building Bengaluru H3 Resolution-8 Spatial Registry ...")
    registry = build_registry()
    export_geojson(registry, geojson_path)
    export_duckdb(registry, duckdb_path)
    return registry
