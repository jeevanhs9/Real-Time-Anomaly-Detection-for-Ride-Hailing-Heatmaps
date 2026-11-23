"""
Unit and Integration Tests for Bengaluru H3 Spatial Registry Manager.

Validates:
1. Cell count lands strictly within target range (400 - 600 cells).
2. All cell centroids fall strictly within Bengaluru geographic bounds.
3. Every cell generates a valid closed 6-vertex GeoJSON polygon ring.
4. Every cell has 6 valid adjacent neighbours.
5. Critical Bengaluru ride-hailing hubs are correctly tagged.
6. GeoJSON and DuckDB export and load functions preserve full fidelity.
"""

import sys
from pathlib import Path
import pytest
import h3

# Ensure backend directory is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.h3_manager import (
    RESOLUTION,
    BENGALURU_BOUNDARY_COORDS,
    LANDMARKS,
    get_all_bengaluru_cells,
    get_cell_centroid,
    get_cell_boundary_geojson,
    get_cell_neighbors,
    tag_cell,
    build_registry,
    export_geojson,
    export_duckdb,
    load_registry_from_geojson,
    load_registry_from_duckdb,
)

# Geographic bounding envelope for greater Bengaluru metropolitan area
BENGALURU_MIN_LAT = 12.80
BENGALURU_MAX_LAT = 13.25
BENGALURU_MIN_LON = 77.45
BENGALURU_MAX_LON = 77.80

REQUIRED_KEY_LOCALITIES = [
    "Koramangala",
    "Indiranagar",
    "Whitefield",
    "Kempegowda Airport (BLR)",
    "Silk Board Junction",
    "Electronic City",
    "HSR Layout",
    "Majestic / KSR Station",
    "Manyata Tech Park / Hebbal",
    "Bellandur / ORR",
]


@pytest.fixture(scope="module")
def cells():
    """Module-level fixture returning the active cell list."""
    return get_all_bengaluru_cells(RESOLUTION)


@pytest.fixture(scope="module")
def registry():
    """Module-level fixture returning the complete built registry."""
    return build_registry()


def test_hex_count_within_expected_range(cells):
    """Verify total Resolution-8 cells are between 400 and 600 (target ~450 to 550)."""
    cell_count = len(cells)
    assert 400 <= cell_count <= 600, (
        f"Cell count {cell_count} is outside the expected range [400, 600]."
    )


def test_cells_within_bengaluru_bounds(cells):
    """Verify that every cell centroid falls strictly within Bengaluru metropolitan bounds."""
    for cell in cells:
        lat, lon = get_cell_centroid(cell)
        assert BENGALURU_MIN_LAT <= lat <= BENGALURU_MAX_LAT, (
            f"Cell {cell} centroid lat {lat:.4f} outside [{BENGALURU_MIN_LAT}, {BENGALURU_MAX_LAT}]."
        )
        assert BENGALURU_MIN_LON <= lon <= BENGALURU_MAX_LON, (
            f"Cell {cell} centroid lon {lon:.4f} outside [{BENGALURU_MIN_LON}, {BENGALURU_MAX_LON}]."
        )


def test_all_cells_have_valid_geojson_boundaries(cells):
    """
    Verify each cell produces a valid 6-vertex closed GeoJSON polygon ring.
    The ring must have exactly 7 coordinates with ring[0] == ring[-1].
    Coordinates must be in [lon, lat] format (GeoJSON standard).
    """
    for cell in cells:
        ring = get_cell_boundary_geojson(cell)
        # 6 hexagon vertices + 1 closing coordinate = 7 items
        assert len(ring) == 7, f"Cell {cell} boundary has {len(ring)} vertices, expected 7."
        assert ring[0] == ring[-1], f"Cell {cell} polygon ring is not closed: {ring[0]} != {ring[-1]}"

        for pt in ring:
            assert len(pt) == 2, f"Invalid point coordinate: {pt}"
            lon, lat = pt[0], pt[1]
            # Longitude should be ~77, Latitude should be ~12-13 in Bengaluru
            assert 77.0 <= lon <= 78.0, f"Longitude {lon} out of range in cell {cell}"
            assert 12.0 <= lat <= 14.0, f"Latitude {lat} out of range in cell {cell}"


def test_neighbor_connectivity(cells):
    """Verify every cell has exactly 6 valid adjacent ring-1 neighbours."""
    for cell in cells:
        neighbors = get_cell_neighbors(cell)
        assert len(neighbors) == 6, f"Cell {cell} has {len(neighbors)} neighbors, expected 6."
        assert cell not in neighbors, f"Cell {cell} listed as its own neighbor."
        for n in neighbors:
            assert h3.is_valid_cell(n), f"Neighbor {n} of cell {cell} is not a valid H3 cell index."


def test_key_localities_tagged(registry):
    """Verify critical hubs and landmarks are tagged and represented in the registry."""
    found_localities = {r["locality"] for r in registry}
    for req_loc in REQUIRED_KEY_LOCALITIES:
        assert req_loc in found_localities, (
            f"Required locality '{req_loc}' was not found in the tagged registry. "
            f"Available localities: {sorted(found_localities)}"
        )


def test_category_flags(registry):
    """Verify that commercial, tech hub, and transit hub category flags are assigned properly."""
    comm_count = sum(1 for r in registry if r["is_commercial"])
    tech_count = sum(1 for r in registry if r["is_tech_hub"])
    transit_count = sum(1 for r in registry if r["is_transit_hub"])

    assert comm_count > 0, "No commercial cells found."
    assert tech_count > 0, "No tech hub cells found."
    assert transit_count > 0, "No transit hub cells found."


def test_geojson_export_and_reload(registry, tmp_path):
    """Test exporting to GeoJSON and reloading preserves exact cell count and fields."""
    temp_json = tmp_path / "test_bengaluru_h3.json"
    export_geojson(registry, temp_json)

    assert temp_json.exists()
    reloaded = load_registry_from_geojson(temp_json)
    assert len(reloaded) == len(registry)

    # Verify first cell attributes match exactly
    orig_first = registry[0]
    reloaded_first = reloaded[0]
    assert orig_first["h3_index"] == reloaded_first["h3_index"]
    assert orig_first["locality"] == reloaded_first["locality"]
    assert len(reloaded_first["neighbors"]) == 6
    assert len(reloaded_first["geojson_boundary"]) == 7


def test_duckdb_export_and_query(registry, tmp_path):
    """Test exporting to DuckDB and querying rows matches registry."""
    temp_db = tmp_path / "test_registry.duckdb"
    export_duckdb(registry, temp_db)

    assert temp_db.exists()
    reloaded = load_registry_from_duckdb(temp_db)
    assert len(reloaded) == len(registry)

    # Check a specific row
    first = reloaded[0]
    assert "h3_index" in first
    assert "locality" in first
    assert first["neighbor_count"] == 6
