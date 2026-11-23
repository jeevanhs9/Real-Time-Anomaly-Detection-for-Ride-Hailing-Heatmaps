# -*- coding: utf-8 -*-
"""Test suite for Phase 3 ML Pipeline components."""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

from app.core.featurizer import TelemetryFeaturizer
from app.ml.zscore_baseline import SeasonalZScoreModel
from app.ml.lightgbm_model import LightGBMRegressorModel
from app.ml.isolation_forest import IsoForestAnomalyModel

@pytest.fixture
def sample_telemetry_df():
    """Create a small sample telemetry DataFrame for testing."""
    np.random.seed(42)
    dates = pd.date_range("2026-09-01", periods=10*96, freq="15min")
    h3_indices = ["8860145a33fffff", "8860145a37fffff", "8860145a3bfffff"]
    rows = []
    for h3_idx in h3_indices:
        for i, ts in enumerate(dates):
            hour = ts.hour + ts.minute / 60.0
            demand_base = 50 + 30 * np.sin(2 * np.pi * hour / 24.0)
            supply_base = 40 + 10 * np.cos(2 * np.pi * hour / 24.0)
            demand = max(0, int(demand_base + np.random.normal(0, 10)))
            supply = max(1, int(supply_base + np.random.normal(0, 5)))
            rows.append({
                "tick_index": i,
                "timestamp": ts,
                "h3_index": h3_idx,
                "pickup_count": demand,
                "dropoff_count": int(demand * 0.9),
                "available_drivers": supply,
                "cancellation_rate": 0.08 + np.random.uniform(0, 0.05),
                "surge_multiplier": 1.0 + max(0, (demand - supply) / supply) * 0.5,
                "avg_eta_minutes": 5.0 + np.random.uniform(0, 2),
                "is_rainy": False,
                "rainfall_mm": 0.0,
                "scenario_flags": "[]",
            })
    df = pd.DataFrame(rows)
    anomaly_idx = df[(df["h3_index"] == h3_indices[0]) & (df["tick_index"] == 5*96 + 10*4)].index[0]
    df.at[anomaly_idx, "pickup_count"] = 300
    df.at[anomaly_idx, "scenario_flags"] = '["test_anomaly"]'
    return df

def test_featurizer_output_shape(sample_telemetry_df):
    """Test that featurizer produces all expected features."""
    featurizer = TelemetryFeaturizer()
    df_features = featurizer.fit_transform(sample_telemetry_df)
    expected_features = [
        "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos", "is_weekend",
        "demand_lag_15m", "demand_lag_30m", "demand_lag_1h",
        "demand_rolling_mean_1h", "demand_rolling_std_1h",
        "neighbor_avg_demand", "spatial_demand_gradient",
        "demand_supply_ratio",
    ]
    for feat in expected_features:
        assert feat in df_features.columns, f"Missing feature: {feat}"
    assert df_features["hour_sin"].isna().sum() == 0
    assert df_features["demand_supply_ratio"].isna().sum() == 0
    print(f"Test passed: Featurizer produced {len(df_features.columns)} columns")

def test_zscore_calculation(sample_telemetry_df):
    """Test Z-score model detects the injected anomaly."""
    featurizer = TelemetryFeaturizer()
    df_features = featurizer.fit_transform(sample_telemetry_df)
    df_train = df_features[df_features["tick_index"] < 7*96].copy()
    df_test = df_features[df_features["tick_index"] >= 7*96].copy()
    model = SeasonalZScoreModel(threshold=3.0)
    model.fit(df_train)
    z_scores = model.predict_zscore(df_test)
    anomalies = model.predict_anomaly(df_test)
    assert anomalies.sum() > 0, "Z-score model detected no anomalies"
    print(f"Test passed: Z-Score detected {anomalies.sum()} anomalies")

def test_lgbm_prediction_accuracy(sample_telemetry_df):
    """Test LightGBM model achieves reasonable WAPE."""
    featurizer = TelemetryFeaturizer()
    df_features = featurizer.fit_transform(sample_telemetry_df)
    feature_cols = [
        "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos", "is_weekend",
        "demand_lag_15m", "demand_lag_30m", "demand_lag_1h",
        "demand_rolling_mean_1h", "demand_rolling_std_1h",
        "neighbor_avg_demand", "spatial_demand_gradient",
        "demand_supply_ratio", "cancellation_rate", "surge_multiplier", "avg_eta_minutes",
        "is_rainy", "rainfall_mm",
    ]
    feature_cols = [f for f in feature_cols if f in df_features.columns]
    df_train = df_features[df_features["tick_index"] < 7*96].copy()
    df_test = df_features[df_features["tick_index"] >= 7*96].copy()
    X_train = df_train[feature_cols]
    y_train = df_train["pickup_count"]
    X_test = df_test[feature_cols]
    y_test = df_test["pickup_count"]
    model = LightGBMRegressorModel(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    metrics = model.evaluate(X_test, y_test)
    assert metrics["wape"] < 25.0, f"WAPE too high: {metrics['wape']:.2f}%"
    print(f"Test passed: LightGBM WAPE: {metrics['wape']:.2f}%")

def test_isoforest_outlier_detection(sample_telemetry_df):
    """Test Isolation Forest flags outliers."""
    featurizer = TelemetryFeaturizer()
    df_features = featurizer.fit_transform(sample_telemetry_df)
    market_features = [
        "pickup_count", "available_drivers",
        "cancellation_rate", "surge_multiplier", "avg_eta_minutes"
    ]
    df_train = df_features[df_features["tick_index"] < 7*96].copy()
    df_test = df_features[df_features["tick_index"] >= 7*96].copy()
    X_train = df_train[market_features]
    X_test = df_test[market_features]
    model = IsoForestAnomalyModel(contamination=0.05, n_estimators=50, random_state=42)
    model.fit(X_train)
    anomalies = model.predict_anomaly(X_test)
    assert anomalies.sum() > 0, "Isolation Forest detected no anomalies"
    print(f"Test passed: Isolation Forest detected {anomalies.sum()} anomalies")

def test_model_save_load(tmp_path, sample_telemetry_df):
    """Test that models can be saved and loaded."""
    featurizer = TelemetryFeaturizer()
    df_features = featurizer.fit_transform(sample_telemetry_df)
    df_train = df_features[df_features["tick_index"] < 7*96].copy()
    
    zscore_path = tmp_path / "zscore_test.joblib"
    zscore_model = SeasonalZScoreModel()
    zscore_model.fit(df_train)
    zscore_model.save(zscore_path)
    zscore_loaded = SeasonalZScoreModel()
    zscore_loaded.load(zscore_path)
    assert zscore_loaded.baselines_ is not None
    
    feature_cols = ["hour_sin", "hour_cos", "demand_lag_15m", "demand_supply_ratio"]
    feature_cols = [f for f in feature_cols if f in df_train.columns]
    X_train = df_train[feature_cols]
    y_train = df_train["pickup_count"]
    
    lgbm_path = tmp_path / "lgbm_test.joblib"
    lgbm_model = LightGBMRegressorModel(n_estimators=10, random_state=42)
    lgbm_model.fit(X_train, y_train)
    lgbm_model.save(lgbm_path)
    lgbm_loaded = LightGBMRegressorModel()
    lgbm_loaded.load(lgbm_path)
    assert lgbm_loaded.model_ is not None
    
    market_features = ["pickup_count", "available_drivers", "surge_multiplier"]
    X_market = df_train[market_features]
    
    isoforest_path = tmp_path / "isoforest_test.joblib"
    isoforest_model = IsoForestAnomalyModel(n_estimators=10, random_state=42)
    isoforest_model.fit(X_market)
    isoforest_model.save(isoforest_path)
    isoforest_loaded = IsoForestAnomalyModel()
    isoforest_loaded.load(isoforest_path)
    assert isoforest_loaded.model_ is not None
    
    print("Test passed: All models successfully saved and loaded")
