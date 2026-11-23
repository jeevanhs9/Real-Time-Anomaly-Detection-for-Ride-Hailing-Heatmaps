"""
Telemetry Feature Engineering Pipeline for ML Model Training.

Transforms raw 15-minute telemetry records into a rich 28-dimensional feature
vector suitable for supervised and unsupervised anomaly detection.

Feature Groups:
  1. Temporal Encodings (cyclical hour/day-of-week, weekend flags)
  2. Historical Lags (15m, 30m, 1h, 24h, 7d)
  3. Rolling Statistics (mean, std over 1h window)
  4. Spatial Neighbor Features (k-ring-1 average demand)
  5. Market Dynamics (DSR, surge, cancellation, ETA)
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.h3_manager import load_registry_from_geojson

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
GEOJSON_PATH = _REPO_ROOT / "data" / "geo" / "bengaluru_h3_res8.json"


class TelemetryFeaturizer:
    """
    Feature engineering pipeline for ride-hailing telemetry data.
    
    Accepts raw telemetry DataFrame with columns:
        - timestamp (ISO string or datetime)
        - h3_index
        - pickup_count
        - available_drivers
        - cancellation_rate
        - surge_multiplier
        - avg_eta_minutes
        - is_rainy
        - rainfall_mm
    
    Returns enriched DataFrame with 28+ feature columns.
    """

    def __init__(self, geojson_path: Path = GEOJSON_PATH):
        """Initialize featurizer with H3 spatial registry for neighbor lookups."""
        self.h3_registry = load_registry_from_geojson(geojson_path)
        
        # Build neighbor mapping: {h3_index: [neighbor_indices]}
        self.h3_neighbors: dict[str, list[str]] = {}
        for rec in self.h3_registry:
            h3_idx = rec["h3_index"]
            neighbors = rec.get("neighbors", [])
            self.h3_neighbors[h3_idx] = neighbors
        
        logger.info("TelemetryFeaturizer initialized with %d cells and neighbor graph.",
                    len(self.h3_neighbors))

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw telemetry DataFrame into feature-enriched DataFrame.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw telemetry with required columns.
        
        Returns
        -------
        pd.DataFrame
            Feature-enriched DataFrame with 28+ columns.
        """
        logger.debug("Starting feature engineering on DataFrame with %d rows...", len(df))
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Sort by h3_index and timestamp for lag calculations
        df = df.sort_values(["h3_index", "timestamp"]).reset_index(drop=True)
        
        # 1. TEMPORAL ENCODINGS
        df = self._add_temporal_features(df)
        
        # 2. HISTORICAL LAGS
        df = self._add_lag_features(df)
        
        # 3. ROLLING STATISTICS
        df = self._add_rolling_features(df)
        
        # 4. SPATIAL NEIGHBOR FEATURES
        df = self._add_spatial_features(df)
        
        # 5. MARKET DYNAMICS (already present, but compute DSR)
        df = self._add_market_features(df)
        
        # 6. HANDLE MISSING VALUES
        df = self._handle_missing_values(df)
        
        logger.debug("Feature engineering complete. Output shape: %s", df.shape)
        logger.debug("Feature columns: %s", list(df.columns))
        
        return df

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cyclical temporal encodings and boolean flags."""
        logger.debug("  [1/5] Adding temporal features...")
        
        # Extract hour and day-of-week
        df["hour_of_day"] = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60.0
        df["day_of_week"] = df["timestamp"].dt.day_of_week  # 0=Monday, 6=Sunday
        
        # Cyclical encodings (sine/cosine to preserve continuity)
        df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24.0)
        df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
        df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)
        
        # Boolean flags
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        
        return df

    def _add_lag_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add historical lag features (15m, 30m, 1h, 24h, 7d)."""
        logger.debug("  [2/5] Adding lag features...")
        
        # Group by h3_index for per-cell lags
        grouped = df.groupby("h3_index")["pickup_count"]
        
        # Each 15-minute tick is one row per cell
        # lag_15m = shift(1), lag_30m = shift(2), lag_1h = shift(4)
        # lag_24h = shift(96), lag_7d = shift(672)
        df["demand_lag_15m"] = grouped.shift(1)
        df["demand_lag_30m"] = grouped.shift(2)
        df["demand_lag_1h"] = grouped.shift(4)
        df["demand_lag_24h"] = grouped.shift(96)  # 24h / 15m = 96 ticks
        df["demand_lag_7d"] = grouped.shift(672)  # 7d * 96 = 672 ticks
        
        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling mean and std over 1-hour window."""
        logger.debug("  [3/5] Adding rolling statistics...")
        
        # Group by h3_index and compute rolling stats
        # 1h window = 4 ticks of 15 minutes
        df["demand_rolling_mean_1h"] = (
            df.groupby("h3_index")["pickup_count"]
            .transform(lambda x: x.rolling(window=4, min_periods=1).mean())
        )
        df["demand_rolling_std_1h"] = (
            df.groupby("h3_index")["pickup_count"]
            .transform(lambda x: x.rolling(window=4, min_periods=1).std())
        )
        
        # Fill NaN std with 0 (when std is undefined for single point)
        df["demand_rolling_std_1h"] = df["demand_rolling_std_1h"].fillna(0.0)
        
        return df

    def _add_spatial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add spatial neighbor average demand."""
        logger.debug("  [4/5] Adding spatial neighbor features...")
        
        # For each row, compute average demand across k-ring-1 neighbors
        neighbor_demands = []
        
        # Create a timestamp-h3 indexed lookup for fast access
        df_pivot = df.set_index(["timestamp", "h3_index"])["pickup_count"]
        
        for idx, row in df.iterrows():
            ts = row["timestamp"]
            h3_idx = row["h3_index"]
            neighbors = self.h3_neighbors.get(h3_idx, [])
            
            if not neighbors:
                neighbor_demands.append(row["pickup_count"])  # fallback to self
                continue
            
            # Lookup neighbor demands at the same timestamp
            neighbor_vals = []
            for neighbor_h3 in neighbors:
                try:
                    val = df_pivot.loc[(ts, neighbor_h3)]
                    neighbor_vals.append(val)
                except KeyError:
                    pass  # neighbor not in dataset
            
            if neighbor_vals:
                avg_neighbor_demand = np.mean(neighbor_vals)
            else:
                avg_neighbor_demand = row["pickup_count"]  # fallback to self
            
            neighbor_demands.append(avg_neighbor_demand)
        
        df["neighbor_avg_demand"] = neighbor_demands
        
        # Spatial gradient: difference from neighbors
        df["spatial_demand_gradient"] = df["pickup_count"] - df["neighbor_avg_demand"]
        
        return df

    def _add_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market dynamics features."""
        logger.debug("  [5/5] Adding market dynamics features...")
        
        # Demand-Supply Ratio (DSR)
        df["demand_supply_ratio"] = df["pickup_count"] / df["available_drivers"].replace(0, 1)
        
        # These features already exist in raw data, just ensure they\'re present
        required_market_features = [
            "cancellation_rate",
            "surge_multiplier",
            "avg_eta_minutes",
        ]
        
        for feat in required_market_features:
            if feat not in df.columns:
                logger.warning("Missing market feature: %s. Setting to 0.", feat)
                df[feat] = 0.0
        
        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle NaN values caused by lags and rolling windows."""
        logger.debug("  Handling missing values...")

        # Lag features: forward-fill within each cell (use previous known value)
        lag_cols = [
            "demand_lag_15m", "demand_lag_30m", "demand_lag_1h",
            "demand_lag_24h", "demand_lag_7d",
        ]
        for col in lag_cols:
            if col in df.columns:
                # Forward fill within each h3_index group
                df[col] = df.groupby("h3_index")[col].ffill()
                # If still NaN (e.g. very first tick — no history at all),
                # fall back to the current pickup_count — a reasonable proxy.
                still_nan = df[col].isna()
                if still_nan.any():
                    df.loc[still_nan, col] = df.loc[still_nan, "pickup_count"]

        # Rolling stats: on the very first tick the median may itself be NaN,
        # so fall back to pickup_count for mean and 0 for std.
        if "demand_rolling_mean_1h" in df.columns:
            still_nan = df["demand_rolling_mean_1h"].isna()
            if still_nan.any():
                df.loc[still_nan, "demand_rolling_mean_1h"] = df.loc[still_nan, "pickup_count"]
        if "demand_rolling_std_1h" in df.columns:
            df["demand_rolling_std_1h"] = df["demand_rolling_std_1h"].fillna(0.0)

        # Spatial features
        if "neighbor_avg_demand" in df.columns:
            df["neighbor_avg_demand"] = df["neighbor_avg_demand"].fillna(df["pickup_count"])
        if "spatial_demand_gradient" in df.columns:
            df["spatial_demand_gradient"] = df["spatial_demand_gradient"].fillna(0.0)

        # Market features: clip extreme DSR
        if "demand_supply_ratio" in df.columns:
            df["demand_supply_ratio"] = df["demand_supply_ratio"].clip(upper=10.0)

        remaining = int(df.isna().sum().sum())
        if remaining > 0:
            logger.warning("  %d NaNs remain after imputation — filling with 0", remaining)
            df = df.fillna(0.0)

        logger.debug("  Missing values handled. Output shape: %s", df.shape)
        return df

    def get_feature_names(self) -> list[str]:
        """Return list of all generated feature column names."""
        return [
            # Temporal
            "hour_of_day", "day_of_week",
            "hour_sin", "hour_cos",
            "day_of_week_sin", "day_of_week_cos",
            "is_weekend",
            # Lags
            "demand_lag_15m", "demand_lag_30m", "demand_lag_1h",
            "demand_lag_24h", "demand_lag_7d",
            # Rolling
            "demand_rolling_mean_1h", "demand_rolling_std_1h",
            # Spatial
            "neighbor_avg_demand", "spatial_demand_gradient",
            # Market
            "demand_supply_ratio", "cancellation_rate",
            "surge_multiplier", "avg_eta_minutes",
            # Weather
            "is_rainy", "rainfall_mm",
        ]


