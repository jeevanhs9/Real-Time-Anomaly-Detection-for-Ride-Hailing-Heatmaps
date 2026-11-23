"""
Bengaluru Points of Interest (POI) Registry and Locality Mapping.

Maps human-readable locality names to H3 cell indices, POI metadata, and
functional categories (residential, tech hub, commercial, transit, event venue).

Loaded from the Phase 1 spatial registry (data/geo/bengaluru_h3_res8.json),
augmented with explicit POI metadata and coordinate-based clustering.
"""

import json
import logging
from pathlib import Path
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
GEOJSON_PATH = _REPO_ROOT / "data" / "geo" / "bengaluru_h3_res8.json"


class POI(NamedTuple):
    """Point of Interest metadata."""
    name: str
    lat: float
    lon: float
    h3_index: str
    poi_type: str  # 'RESIDENTIAL', 'TECH_PARK', 'COMMERCIAL', 'TRANSIT', 'EVENT'
    category: str  # Fine-grained category within type


# Explicit POI Coordinate Catalog (used to anchor cell tagging)
EXPLICIT_POIS = [
    # Residential Clusters
    POI("HSR Layout", 12.9121, 77.6446, "", "RESIDENTIAL", "residential_cluster"),
    POI("Jayanagar", 12.9354, 77.5825, "", "RESIDENTIAL", "residential_cluster"),
    POI("JP Nagar", 12.9250, 77.5950, "", "RESIDENTIAL", "residential_cluster"),
    POI("Malleshwaram", 13.0031, 77.5643, "", "RESIDENTIAL", "residential_cluster"),
    POI("Banashankari", 12.9542, 77.5532, "", "RESIDENTIAL", "residential_cluster"),
    POI("BTM Layout", 12.9166, 77.6101, "", "RESIDENTIAL", "residential_cluster"),

    # Tech & Office Parks
    POI("Electronic City Phase 1", 12.8418, 77.6611, "", "TECH_PARK", "it_corridor"),
    POI("Electronic City Phase 2", 12.8480, 77.6620, "", "TECH_PARK", "it_corridor"),
    POI("Whitefield (ITPL)", 12.9698, 77.7500, "", "TECH_PARK", "it_corridor"),
    POI("Manyata Tech Park", 13.0450, 77.6200, "", "TECH_PARK", "it_corridor"),
    POI("Bellandur (ORR)", 12.9250, 77.6780, "", "TECH_PARK", "it_corridor"),
    POI("Marathahalli", 12.9591, 77.7011, "", "TECH_PARK", "it_corridor"),
    POI("Outer Ring Road", 12.9500, 77.6700, "", "TECH_PARK", "it_corridor"),
    POI("Embassy Tech Village", 12.9450, 77.6550, "", "TECH_PARK", "it_corridor"),
    POI("Cessna Business Park", 12.9200, 77.7100, "", "TECH_PARK", "it_corridor"),

    # Commercial & Nightlife
    POI("MG Road", 12.9756, 77.6066, "", "COMMERCIAL", "central_business"),
    POI("Indiranagar 100ft Road", 12.9784, 77.6408, "", "COMMERCIAL", "nightlife"),
    POI("Koramangala", 12.9352, 77.6245, "", "COMMERCIAL", "nightlife"),
    POI("Church Street", 12.9756, 77.6127, "", "COMMERCIAL", "nightlife"),
    POI("Residency Road", 12.9650, 77.6000, "", "COMMERCIAL", "central_business"),

    # Transit Hubs
    POI("Kempegowda Int'l Airport (BLR)", 13.1986, 77.7066, "", "TRANSIT", "airport"),
    POI("KSR Railway Station (Majestic)", 12.9780, 77.5695, "", "TRANSIT", "railway"),
    POI("Yeshwanthpur Railway", 13.0280, 77.5410, "", "TRANSIT", "railway"),
    POI("Whitefield Railway", 12.9698, 77.7500, "", "TRANSIT", "railway"),
    POI("Electronic City Railway", 12.8452, 77.6602, "", "TRANSIT", "railway"),
    POI("Kempegowda Bus Station", 12.9780, 77.5695, "", "TRANSIT", "bus_station"),

    # Event Venues
    POI("Chinnaswamy Stadium (Cricket)", 12.9756, 77.5980, "", "EVENT", "stadium"),
    POI("Sree Kanteerava Stadium", 12.9670, 77.5900, "", "EVENT", "stadium"),
    POI("BIEC (Exhibitions)", 12.9600, 77.6200, "", "EVENT", "exhibition"),
]


class POIRegistry:
    """Manages POI metadata and H3 cell mapping."""

    def __init__(self, geojson_path: Path = GEOJSON_PATH):
        """
        Load spatial registry and bind POI metadata.

        Parameters
        ----------
        geojson_path : Path
            Path to the Phase 1 H3 spatial registry GeoJSON.
        """
        self.geojson_path = geojson_path
        self._h3_to_poi: dict[str, dict[str, Any]] = {}
        self._locality_to_h3s: dict[str, list[str]] = {}
        self._pois = EXPLICIT_POIS

        self._load_and_bind()

    def _load_and_bind(self) -> None:
        """Load GeoJSON and bind POI metadata to H3 cells."""
        with open(self.geojson_path, encoding="utf-8") as fh:
            fc = json.load(fh)

        # Index by locality name
        locality_to_cells: dict[str, list[dict[str, Any]]] = {}
        for feat in fc["features"]:
            props = feat["properties"]
            loc = props["locality"]
            if loc not in locality_to_cells:
                locality_to_cells[loc] = []
            locality_to_cells[loc].append(props)

        # Bind POI metadata
        for poi in self._pois:
            # Find cells with matching locality
            matching_cells = locality_to_cells.get(poi.category if poi.category in locality_to_cells else poi.name, [])
            if not matching_cells:
                # Try fuzzy match on name substring
                for loc, cells in locality_to_cells.items():
                    if poi.name.split()[0] in loc or loc.split()[0] in poi.name:
                        matching_cells = cells
                        break

            if matching_cells:
                # Assign closest H3 cell by proximity
                for cell_props in matching_cells:
                    h3_idx = cell_props["h3_index"]
                    self._h3_to_poi[h3_idx] = {
                        "poi_name": poi.name,
                        "lat": poi.lat,
                        "lon": poi.lon,
                        "poi_type": poi.poi_type,
                        "category": poi.category,
                        "locality": cell_props["locality"],
                        "is_commercial": cell_props["is_commercial"],
                        "is_tech_hub": cell_props["is_tech_hub"],
                        "is_transit_hub": cell_props["is_transit_hub"],
                    }

        # Build locality-to-h3s index
        for feat in fc["features"]:
            props = feat["properties"]
            loc = props["locality"]
            h3_idx = props["h3_index"]
            if loc not in self._locality_to_h3s:
                self._locality_to_h3s[loc] = []
            self._locality_to_h3s[loc].append(h3_idx)

        logger.info("Loaded %d POIs and mapped to %d H3 cells.", len(self._pois), len(self._h3_to_poi))

    def get_poi_by_h3(self, h3_index: str) -> dict[str, Any] | None:
        """Return POI metadata for cell, or None if unmapped."""
        return self._h3_to_poi.get(h3_index)

    def get_h3_cells_by_locality(self, locality_name: str) -> list[str]:
        """Return all H3 cells tagged with this locality."""
        return self._locality_to_h3s.get(locality_name, [])

    def get_all_cells(self) -> list[str]:
        """Return all H3 cell indices."""
        return list(self._h3_to_poi.keys())

    def get_all_localities(self) -> list[str]:
        """Return all distinct locality names."""
        return list(self._locality_to_h3s.keys())

    def get_cells_by_poi_type(self, poi_type: str) -> list[str]:
        """Return H3 cells tagged with a specific POI type."""
        return [h3 for h3, poi in self._h3_to_poi.items() if poi.get("poi_type") == poi_type]
