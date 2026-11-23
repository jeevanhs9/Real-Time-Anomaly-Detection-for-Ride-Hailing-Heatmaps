"""
Seasonal Z-Score Baseline Anomaly Detection Model.

Computes statistical baselines (mean and std) for each hexagon based on
(hour_of_day, day_of_week) patterns. Anomalies are flagged when current
demand deviates significantly (|Z| > 3.0) from the seasonal expectation.
"""

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)


class SeasonalZScoreModel:
    """
    Statistical baseline model using seasonal Z-scores.
    
    Training: Computes mean and std of pickup_count grouped by
              (h3_index, hour_of_day_bin, is_weekend).
    
    Inference: Z = (actual - mean) / (std + epsilon)
               Anomaly if |Z| > threshold (default 3.0).
    """

    def __init__(self, threshold: float = 3.0, epsilon: float = 1e-6):
        """
        Parameters
        ----------
        threshold : float
            Z-score threshold for anomaly detection (default 3.0 = 3-sigma).
        epsilon : float
            Small constant to avoid division by zero.
        """
        self.threshold = threshold
        self.epsilon = epsilon
        self.baselines_: pd.DataFrame | None = None
    
    def fit(self, df: pd.DataFrame) -> "SeasonalZScoreModel":
        """
        Train the model by computing seasonal baselines.
        
        Parameters
        ----------
        df : pd.DataFrame
            Training data with columns: h3_index, hour_of_day, is_weekend, pickup_count.
        
        Returns
        -------
        self
        """
        logger.info("Training Seasonal Z-Score Model on %d samples...", len(df))
        
        # Bin hour_of_day into hourly slots (0-23)
        df = df.copy()
        df["hour_bin"] = df["hour_of_day"].astype(int)
        
        # Compute mean and std grouped by (h3_index, hour_bin, is_weekend)
        baselines = (
            df.groupby(["h3_index", "hour_bin", "is_weekend"])["pickup_count"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )
        
        # Fill missing std with epsilon (for cells with zero variance)
        baselines["std"] = baselines["std"].fillna(self.epsilon)
        baselines["std"] = baselines["std"].replace(0.0, self.epsilon)
        
        self.baselines_ = baselines
        
        logger.info("Seasonal baselines computed for %d (hex, hour, weekend) groups.",
                    len(self.baselines_))
        
        return self
    
    def predict_zscore(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute Z-scores for each row.
        
        Parameters
        ----------
        df : pd.DataFrame
            Data with columns: h3_index, hour_of_day, is_weekend, pickup_count.
        
        Returns
        -------
        pd.Series
            Z-scores for each row.
        """
        if self.baselines_ is None:
            raise ValueError("Model must be fitted before prediction.")
        
        df = df.copy()
        df["hour_bin"] = df["hour_of_day"].astype(int)
        
        # Merge with baselines
        df_merged = df.merge(
            self.baselines_,
            on=["h3_index", "hour_bin", "is_weekend"],
            how="left",
            suffixes=("", "_baseline")
        )
        
        # Compute Z-score
        z_scores = (
            (df_merged["pickup_count"] - df_merged["mean"])
            / (df_merged["std"] + self.epsilon)
        )
        
        # Fill NaN (for unseen groups) with 0
        z_scores = z_scores.fillna(0.0)
        
        return z_scores
    
    def predict_anomaly(self, df: pd.DataFrame) -> pd.Series:
        """
        Predict anomaly labels (1 = anomaly, 0 = normal).
        
        Parameters
        ----------
        df : pd.DataFrame
            Data with columns: h3_index, hour_of_day, is_weekend, pickup_count.
        
        Returns
        -------
        pd.Series
            Binary anomaly labels.
        """
        z_scores = self.predict_zscore(df)
        anomalies = (np.abs(z_scores) > self.threshold).astype(int)
        
        logger.info("Detected %d anomalies out of %d samples (%.2f%%).",
                    anomalies.sum(), len(anomalies), 100 * anomalies.mean())
        
        return anomalies
    
    def save(self, path: Path) -> None:
        """Save model baselines to disk."""
        joblib.dump(self.baselines_, path)
        logger.info("Seasonal Z-Score baselines saved to %s", path)
    
    def load(self, path: Path) -> "SeasonalZScoreModel":
        """Load model baselines from disk."""
        self.baselines_ = joblib.load(path)
        logger.info("Seasonal Z-Score baselines loaded from %s", path)
        return self
