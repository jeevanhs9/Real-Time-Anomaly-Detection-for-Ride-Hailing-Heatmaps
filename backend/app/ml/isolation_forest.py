"""
Multivariate Isolation Forest Anomaly Detection Model.

Detects anomalous patterns in multi-dimensional market dynamics (demand, supply,
cancellation, surge, ETA) using unsupervised tree-based outlier detection.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class IsoForestAnomalyModel:
    """
    Isolation Forest model for multivariate anomaly detection.
    
    Trains on market dynamics features to identify unusual patterns such as:
    - High demand + low supply + high cancellation rate
    - Normal demand + extreme surge multiplier
    - High ETA with normal demand/supply
    """

    def __init__(
        self,
        contamination: float = 0.03,
        n_estimators: int = 100,
        max_samples: int | str = "auto",
        random_state: int = 42,
        anomaly_threshold: float = 0.65,
    ):
        """
        Parameters
        ----------
        contamination : float
            Expected proportion of anomalies in dataset (default 3%).
        n_estimators : int
            Number of isolation trees.
        max_samples : int or "auto"
            Number of samples to draw for each tree.
        random_state : int
            Random seed.
        anomaly_threshold : float
            Anomaly score threshold (scores > threshold are anomalies).
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.random_state = random_state
        self.anomaly_threshold = anomaly_threshold
        
        self.model_: IsolationForest | None = None
        self.feature_names_: list[str] | None = None
    
    def fit(self, X: pd.DataFrame) -> "IsoForestAnomalyModel":
        """
        Train the Isolation Forest model.
        
        Parameters
        ----------
        X : pd.DataFrame
            Market dynamics features (pickup_count, available_drivers,
            cancellation_rate, surge_multiplier, avg_eta_minutes).
        
        Returns
        -------
        self
        """
        logger.info("Training Isolation Forest on %d samples...", len(X))
        
        self.feature_names_ = list(X.columns)
        
        self.model_ = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            random_state=self.random_state,
            n_jobs=-1,
        )
        
        self.model_.fit(X)
        
        logger.info("Isolation Forest training complete.")
        
        return self
    
    def predict_anomaly_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute anomaly scores in [0, 1] range.
        
        Higher scores indicate higher anomaly likelihood.
        
        Parameters
        ----------
        X : pd.DataFrame
            Market dynamics features.
        
        Returns
        -------
        np.ndarray
            Anomaly scores (0 = normal, 1 = extreme anomaly).
        """
        if self.model_ is None:
            raise ValueError("Model must be fitted before prediction.")
        
        # IsolationForest.score_samples returns negative anomaly scores
        # (lower = more anomalous). Transform to [0, 1] range.
        raw_scores = self.model_.score_samples(X)
        
        # Normalize to [0, 1] where 1 = most anomalous
        # Using sigmoid-like transformation
        scores = 1.0 / (1.0 + np.exp(raw_scores))
        
        return scores
    
    def predict_anomaly(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict binary anomaly labels.
        
        Parameters
        ----------
        X : pd.DataFrame
            Market dynamics features.
        
        Returns
        -------
        pd.Series
            Binary anomaly labels (1 = anomaly, 0 = normal).
        """
        scores = self.predict_anomaly_score(X)
        anomalies = (scores > self.anomaly_threshold).astype(int)
        
        logger.info("Detected %d anomalies out of %d samples (%.2f%%).",
                    anomalies.sum(), len(anomalies), 100 * anomalies.mean())
        
        return pd.Series(anomalies, index=X.index)
    
    def save(self, path: Path) -> None:
        """Save model to disk."""
        model_data = {
            "model": self.model_,
            "feature_names": self.feature_names_,
            "params": {
                "contamination": self.contamination,
                "n_estimators": self.n_estimators,
                "anomaly_threshold": self.anomaly_threshold,
            },
        }
        joblib.dump(model_data, path)
        logger.info("Isolation Forest model saved to %s", path)
    
    def load(self, path: Path) -> "IsoForestAnomalyModel":
        """Load model from disk."""
        model_data = joblib.load(path)
        self.model_ = model_data["model"]
        self.feature_names_ = model_data["feature_names"]
        
        params = model_data.get("params", {})
        self.contamination = params.get("contamination", self.contamination)
        self.n_estimators = params.get("n_estimators", self.n_estimators)
        self.anomaly_threshold = params.get("anomaly_threshold", self.anomaly_threshold)
        
        logger.info("Isolation Forest model loaded from %s", path)
        return self
