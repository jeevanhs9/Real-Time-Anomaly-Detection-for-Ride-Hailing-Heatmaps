"""
LightGBM Demand Forecasting & Residual Anomaly Detection Model.

Trains a gradient-boosted decision tree (GBDT) regressor to predict expected
pickup_count given temporal, spatial, and market features. Anomalies are
detected via large residuals: |actual - predicted| > k * std(residuals).
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)


class LightGBMRegressorModel:
    """
    LightGBM-based demand forecasting model with residual anomaly detection.
    
    Training: Fits GBDT regressor on feature-enriched telemetry.
    Inference: Computes residuals and flags anomalies if |residual| > k * sigma.
    """

    def __init__(
        self,
        n_estimators: int = 500,
        learning_rate: float = 0.05,
        num_leaves: int = 31,
        max_depth: int = -1,
        min_child_samples: int = 20,
        residual_threshold_sigma: float = 3.0,
        random_state: int = 42,
    ):
        """
        Parameters
        ----------
        n_estimators : int
            Number of boosting rounds.
        learning_rate : float
            Learning rate (step size shrinkage).
        num_leaves : int
            Maximum tree leaves.
        max_depth : int
            Maximum tree depth (-1 = no limit).
        min_child_samples : int
            Minimum samples required in a leaf.
        residual_threshold_sigma : float
            Multiplier for residual std to define anomaly threshold.
        random_state : int
            Random seed.
        """
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.num_leaves = num_leaves
        self.max_depth = max_depth
        self.min_child_samples = min_child_samples
        self.residual_threshold_sigma = residual_threshold_sigma
        self.random_state = random_state
        
        self.model_: lgb.Booster | None = None
        self.feature_names_: list[str] | None = None
        self.residual_std_: float | None = None
        self.train_mae_: float | None = None
        self.train_rmse_: float | None = None
    
    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
    ) -> "LightGBMRegressorModel":
        """
        Train the LightGBM regressor.
        
        Parameters
        ----------
        X_train : pd.DataFrame
            Training features.
        y_train : pd.Series
            Training target (pickup_count).
        X_val : pd.DataFrame or None
            Validation features (optional).
        y_val : pd.Series or None
            Validation target (optional).
        
        Returns
        -------
        self
        """
        logger.info("Training LightGBM Regressor on %d samples...", len(X_train))
        
        self.feature_names_ = list(X_train.columns)
        
        # Create LightGBM datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        valid_sets = [train_data]
        valid_names = ["train"]
        
        if X_val is not None and y_val is not None:
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            valid_sets.append(val_data)
            valid_names.append("valid")
        
        # Train model
        params = {
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "num_leaves": self.num_leaves,
            "learning_rate": self.learning_rate,
            "max_depth": self.max_depth,
            "min_child_samples": self.min_child_samples,
            "verbosity": -1,
            "random_state": self.random_state,
        }
        
        self.model_ = lgb.train(
            params,
            train_data,
            num_boost_round=self.n_estimators,
            valid_sets=valid_sets,
            valid_names=valid_names,
            callbacks=[
                lgb.early_stopping(stopping_rounds=50, verbose=False),
                lgb.log_evaluation(period=100),
            ],
        )
        
        # Compute training metrics
        y_pred_train = self.model_.predict(X_train)
        self.train_mae_ = mean_absolute_error(y_train, y_pred_train)
        self.train_rmse_ = np.sqrt(mean_squared_error(y_train, y_pred_train))
        
        # Compute residual std on training set
        residuals = y_train - y_pred_train
        self.residual_std_ = np.std(residuals)
        
        logger.info("Training complete. MAE=%.2f, RMSE=%.2f, Residual Std=%.2f",
                    self.train_mae_, self.train_rmse_, self.residual_std_)
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict pickup_count for given features.
        
        Parameters
        ----------
        X : pd.DataFrame
            Features.
        
        Returns
        -------
        np.ndarray
            Predicted pickup counts.
        """
        if self.model_ is None:
            raise ValueError("Model must be fitted before prediction.")
        
        return self.model_.predict(X)
    
    def compute_residuals(self, X: pd.DataFrame, y_true: pd.Series) -> np.ndarray:
        """
        Compute residuals: actual - predicted.
        
        Parameters
        ----------
        X : pd.DataFrame
            Features.
        y_true : pd.Series
            Actual pickup counts.
        
        Returns
        -------
        np.ndarray
            Residuals.
        """
        y_pred = self.predict(X)
        return y_true.values - y_pred
    
    def predict_anomaly(self, X: pd.DataFrame, y_true: pd.Series) -> pd.Series:
        """
        Predict anomalies based on residual magnitude.
        
        Parameters
        ----------
        X : pd.DataFrame
            Features.
        y_true : pd.Series
            Actual pickup counts.
        
        Returns
        -------
        pd.Series
            Binary anomaly labels (1 = anomaly, 0 = normal).
        """
        if self.residual_std_ is None:
            raise ValueError("Model must be fitted to compute residual threshold.")
        
        residuals = self.compute_residuals(X, y_true)
        threshold = self.residual_threshold_sigma * self.residual_std_
        anomalies = (np.abs(residuals) > threshold).astype(int)
        
        logger.info("Detected %d anomalies out of %d samples (%.2f%%) using threshold=%.2f.",
                    anomalies.sum(), len(anomalies), 100 * anomalies.mean(), threshold)
        
        return pd.Series(anomalies, index=y_true.index)
    
    def evaluate(self, X: pd.DataFrame, y_true: pd.Series) -> dict[str, float]:
        """
        Evaluate model performance.
        
        Returns
        -------
        dict
            Dictionary with MAE, RMSE, and WAPE metrics.
        """
        y_pred = self.predict(X)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        wape = np.sum(np.abs(y_true - y_pred)) / np.sum(y_true) * 100
        
        return {
            "mae": mae,
            "rmse": rmse,
            "wape": wape,
        }
    
    def save(self, path: Path) -> None:
        """Save model to disk."""
        model_data = {
            "model": self.model_,
            "feature_names": self.feature_names_,
            "residual_std": self.residual_std_,
            "train_mae": self.train_mae_,
            "train_rmse": self.train_rmse_,
            "params": {
                "n_estimators": self.n_estimators,
                "learning_rate": self.learning_rate,
                "num_leaves": self.num_leaves,
                "residual_threshold_sigma": self.residual_threshold_sigma,
            },
        }
        joblib.dump(model_data, path)
        logger.info("LightGBM model saved to %s", path)
    
    def load(self, path: Path) -> "LightGBMRegressorModel":
        """Load model from disk."""
        model_data = joblib.load(path)
        self.model_ = model_data["model"]
        self.feature_names_ = model_data["feature_names"]
        self.residual_std_ = model_data["residual_std"]
        self.train_mae_ = model_data.get("train_mae")
        self.train_rmse_ = model_data.get("train_rmse")
        
        params = model_data.get("params", {})
        self.n_estimators = params.get("n_estimators", self.n_estimators)
        self.learning_rate = params.get("learning_rate", self.learning_rate)
        self.num_leaves = params.get("num_leaves", self.num_leaves)
        self.residual_threshold_sigma = params.get("residual_threshold_sigma", self.residual_threshold_sigma)
        
        logger.info("LightGBM model loaded from %s", path)
        return self
