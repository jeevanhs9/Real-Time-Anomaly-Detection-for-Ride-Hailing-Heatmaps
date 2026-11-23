#!/usr/bin/env python3
"""CLI to generate 60-day historical telemetry for Bengaluru."""

import sys
from pathlib import Path
import argparse

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.simulation.generator import TelemetryGenerator


def main():
    parser = argparse.ArgumentParser(description="Generate Bengaluru telemetry")
    parser.add_argument("--days", type=int, default=60, help="Number of days to generate")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = parser.parse_args()

    gen = TelemetryGenerator(seed=args.seed)
    df = gen.generate_historical_days(num_days=args.days, include_scenarios=True)

    # Ensure timestamp is datetime for summary calculation
    import pandas as pd
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    print("\n" + "=" * 70)
    print("  TELEMETRY GENERATION SUMMARY")
    print("=" * 70)
    print(f"  Total Rows Generated  : {len(df):,}")
    print(f"  Date Range            : {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Unique H3 Cells       : {df['h3_index'].nunique()}")
    print(f"  Avg Daily Pickups     : {df.groupby(df['timestamp'].dt.date)['pickup_count'].sum().mean():.0f}")
    print(f"  Avg Available Drivers : {df['available_drivers'].mean():.1f}")
    print(f"  Avg Cancellation Rate : {df['cancellation_rate'].mean():.3f}")
    print(f"  Avg ETA (minutes)     : {df['avg_eta_minutes'].mean():.1f}")
    print(f"  Rainy Ticks           : {df['is_rainy'].sum()} ({df['is_rainy'].sum() / len(df) * 100:.1f}%)")
    print(f"  Scenarios Injected    : {df['scenario_flags'].str.len().gt(2).sum()}")
    print("=" * 70)
    print("  PHASE 2 TELEMETRY GENERATION COMPLETE!")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
