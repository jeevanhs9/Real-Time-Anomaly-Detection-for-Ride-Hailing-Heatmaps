"""
Tri-model Anomaly Arbiter.

Scoring weights
---------------
  Z-Score   |Z| > threshold  →  0–30 pts  (scales to |Z| = 6)
  LightGBM  |r| > k·σ        →  0–40 pts  (scales to 3× threshold)
  IsoForest score > threshold →  0–30 pts  (scales to 1.0)

Severity bands: CRITICAL ≥ 75, HIGH ≥ 50, MEDIUM ≥ 25, NORMAL < 25
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

LGBM_FEATURES = [
    "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos", "is_weekend",
    "demand_lag_15m", "demand_lag_30m", "demand_lag_1h",
    "demand_lag_24h", "demand_lag_7d",
    "demand_rolling_mean_1h", "demand_rolling_std_1h",
    "neighbor_avg_demand", "spatial_demand_gradient",
    "demand_supply_ratio", "cancellation_rate",
    "surge_multiplier", "avg_eta_minutes",
    "is_rainy", "rainfall_mm",
]

ISO_FEATURES = [
    "pickup_count", "available_drivers",
    "cancellation_rate", "surge_multiplier", "avg_eta_minutes",
]


@dataclass
class CellAnomalyResult:
    h3_index: str
    z_score: float
    lgbm_pred: float
    residual: float
    iso_score: float
    anomaly_score: float
    severity: str
    root_cause: str


class AnomalyArbiter:
    def __init__(self, zscore_model, lgbm_model, isoforest_model) -> None:
        self.zm = zscore_model
        self.lm = lgbm_model
        self.im = isoforest_model

    # ------------------------------------------------------------------ public

    def score_batch(self, df: pd.DataFrame) -> list[CellAnomalyResult]:
        """Score a featurized DataFrame (one row per cell)."""
        z_scores = self.zm.predict_zscore(df)

        avail_l = [f for f in LGBM_FEATURES if f in df.columns]
        lgbm_preds = self.lm.predict(df[avail_l])
        residuals = df["pickup_count"].values - lgbm_preds
        sigma = self.lm.residual_std_ or 1.0

        avail_i = [f for f in ISO_FEATURES if f in df.columns]
        iso_scores = self.im.predict_anomaly_score(df[avail_i])

        results: list[CellAnomalyResult] = []
        for i, (_, row) in enumerate(df.iterrows()):
            z   = float(z_scores.iloc[i])
            p   = float(lgbm_preds[i])
            r   = float(residuals[i])
            iso = float(iso_scores[i])
            score, severity = self._composite_score(z, r, sigma, iso)
            results.append(CellAnomalyResult(
                h3_index=row["h3_index"],
                z_score=z, lgbm_pred=p, residual=r, iso_score=iso,
                anomaly_score=score, severity=severity,
                root_cause=self._root_cause(row, r, iso),
            ))
        return results

    # ----------------------------------------------------------------- private

    def _composite_score(
        self, z: float, r: float, sigma: float, iso: float
    ) -> tuple[float, str]:
        s = 0.0
        # Layer 1 — Z-Score
        if abs(z) > settings.zscore_threshold:
            s += min(30.0, 30.0 * abs(z) / 6.0)
        # Layer 2 — LightGBM residual
        thresh = settings.residual_sigma_k * sigma
        if abs(r) > thresh:
            s += min(40.0, 40.0 * min(abs(r) / max(thresh * 3, 1e-9), 1.0))
        # Layer 3 — IsoForest
        if iso > settings.isoforest_threshold:
            gap = max(1.0 - settings.isoforest_threshold, 1e-9)
            s += min(30.0, 30.0 * (iso - settings.isoforest_threshold) / gap)
        severity = (
            "CRITICAL" if s >= 75 else
            "HIGH"     if s >= 50 else
            "MEDIUM"   if s >= 25 else
            "NORMAL"
        )
        return round(s, 2), severity

    def _root_cause(self, row: pd.Series, residual: float, iso: float) -> str:
        rain  = float(row.get("rainfall_mm", 0.0))
        dsr   = float(row.get("demand_supply_ratio", 0.0))
        canc  = float(row.get("cancellation_rate", 0.0))
        surge = float(row.get("surge_multiplier", 1.0))
        if rain > 5.0:
            return "WEATHER_DISRUPTION"
        if dsr > 3.0 and residual > 0:
            return "DEMAND_SPIKE"
        if dsr < 0.5 and residual < 0:
            return "SUPPLY_COLLAPSE"
        if canc > 0.25 or surge > 2.5 or iso > settings.isoforest_threshold:
            return "MARKET_ANOMALY"
        return "NORMAL"
