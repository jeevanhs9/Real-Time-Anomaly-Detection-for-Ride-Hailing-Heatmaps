#!/usr/bin/env python3
"""
CLI Script to generate and export the master Bengaluru H3 Resolution-8 spatial registry.

Usage:
    python backend/scripts/generate_h3_registry.py

Outputs:
    data/geo/bengaluru_h3_res8.json
    data/geo/bengaluru_hex_registry.duckdb
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path when script is executed directly
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.h3_manager import generate_and_export, GEOJSON_OUT, DUCKDB_OUT


def main() -> int:
    print("=" * 70)
    print("  BENGALURU H3 RESOLUTION-8 SPATIAL REGISTRY GENERATOR")
    print("=" * 70)

    try:
        registry = generate_and_export(GEOJSON_OUT, DUCKDB_OUT)
    except Exception as exc:
        print(f"\n[ERROR] Generation failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Compute spatial statistics
    total_cells = len(registry)
    lats = [r["lat"] for r in registry]
    lons = [r["lon"] for r in registry]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Locality breakdown
    locality_counts: dict[str, int] = {}
    for r in registry:
        loc = r["locality"]
        locality_counts[loc] = locality_counts.get(loc, 0) + 1

    comm_count = sum(1 for r in registry if r["is_commercial"])
    tech_count = sum(1 for r in registry if r["is_tech_hub"])
    transit_count = sum(1 for r in registry if r["is_transit_hub"])

    # Print Summary Table
    print("\n" + "-" * 70)
    print("  SPATIAL REGISTRY GENERATION SUMMARY")
    print("-" * 70)
    print(f"  Total Registered H3 Cells (Res-8) : {total_cells}")
    print(f"  Expected Target Range             : 400 - 600 cells")
    print(f"  Status                            : {'PASS [OPTIMAL]' if 400 <= total_cells <= 600 else 'WARN'}")
    print(f"  Distinct Localities Tagged        : {len(locality_counts)}")
    print(f"  Commercial Hub Hexagons           : {comm_count} ({comm_count/total_cells*100:.1f}%)")
    print(f"  Tech Hub Hexagons                 : {tech_count} ({tech_count/total_cells*100:.1f}%)")
    print(f"  Transit Hub Hexagons              : {transit_count} ({transit_count/total_cells*100:.1f}%)")
    print("-" * 70)
    print("  GEOGRAPHIC BOUNDING ENVELOPE:")
    print(f"  Latitude Span  : {min_lat:.4f} N  -->  {max_lat:.4f} N  (span: {max_lat - min_lat:.4f})")
    print(f"  Longitude Span : {min_lon:.4f} E  -->  {max_lon:.4f} E  (span: {max_lon - min_lon:.4f})")
    print("-" * 70)
    print("  LOCALITY BREAKDOWN:")
    for loc, count in sorted(locality_counts.items(), key=lambda x: -x[1]):
        bar = "#" * int(count / 2)
        print(f"    {loc:<28} : {count:>3} cells  {bar}")
    print("-" * 70)
    print("  EXPORTED ARTEFACTS:")
    if GEOJSON_OUT.exists():
        size_kb = GEOJSON_OUT.stat().st_size / 1024
        print(f"  GeoJSON FeatureCollection : {GEOJSON_OUT.resolve()} ({size_kb:.1f} KB)")
    if DUCKDB_OUT.exists():
        size_kb = DUCKDB_OUT.stat().st_size / 1024
        print(f"  DuckDB Analytical Store   : {DUCKDB_OUT.resolve()} ({size_kb:.1f} KB)")
    print("=" * 70)
    print("  PHASE 1 SPATIAL REGISTRY GENERATION COMPLETE!")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
