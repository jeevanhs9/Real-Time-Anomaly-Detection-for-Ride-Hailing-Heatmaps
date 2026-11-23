# -*- coding: utf-8 -*-
"""Phase 3 Training and Evaluation Pipeline."""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.core.featurizer import TelemetryFeaturizer
from app.ml.zscore_baseline import SeasonalZScoreModel
from app.ml.lightgbm_model import LightGBMRegressorModel
from app.ml.isolation_forest import IsoForestAnomalyModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = REPO_ROOT / 'data'
PARQUET_PATH = DATA_DIR / 'parquet' / 'telemetry_60d.parquet'
MODELS_DIR = DATA_DIR / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)
ZSCORE_MODEL_PATH = MODELS_DIR / 'zscore_baseline.joblib'
LGBM_MODEL_PATH = MODELS_DIR / 'lightgbm_demand.joblib'
ISOFOREST_MODEL_PATH = MODELS_DIR / 'isoforest_market.joblib'
REPORT_PATH = REPO_ROOT / 'docs' / 'model_evaluation_report.md'
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_data():
    logger.info('Loading data...')
    df = pd.read_parquet(PARQUET_PATH)
    logger.info('Loaded %d rows', len(df))
    return df

def extract_ground_truth(df):
    df_copy = df.copy()
    df_copy['flags_parsed'] = df_copy['scenario_flags'].apply(lambda x: json.loads(x) if isinstance(x, str) else [])
    result = df_copy['flags_parsed'].apply(lambda x: 1 if len(x) > 0 else 0)
    return pd.Series(result.values, index=df.index)

def split_data(df):
    train_cut = 45 * 96
    val_cut = 50 * 96
    return (df[df['tick_index'] < train_cut].copy(),
            df[(df['tick_index'] >= train_cut) & (df['tick_index'] < val_cut)].copy(),
            df[df['tick_index'] >= val_cut].copy())

def train_models(df_train, df_val):
    logger.info('Training Z-Score...')
    zscore_model = SeasonalZScoreModel(threshold=3.0)
    zscore_model.fit(df_train)
    zscore_model.save(ZSCORE_MODEL_PATH)
    
    logger.info('Training LightGBM...')
    features = ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_weekend',
                'demand_lag_15m', 'demand_lag_30m', 'demand_lag_1h', 'demand_lag_24h', 'demand_lag_7d',
                'demand_rolling_mean_1h', 'demand_rolling_std_1h', 'neighbor_avg_demand',
                'spatial_demand_gradient', 'demand_supply_ratio', 'cancellation_rate',
                'surge_multiplier', 'avg_eta_minutes', 'is_rainy', 'rainfall_mm']
    features = [f for f in features if f in df_train.columns]
    lgbm_model = LightGBMRegressorModel(n_estimators=500, learning_rate=0.05, num_leaves=31, random_state=42)
    lgbm_model.fit(df_train[features], df_train['pickup_count'], df_val[features], df_val['pickup_count'])
    lgbm_model.save(LGBM_MODEL_PATH)
    
    logger.info('Training Isolation Forest...')
    market_features = ['pickup_count', 'available_drivers', 'cancellation_rate', 'surge_multiplier', 'avg_eta_minutes']
    df_full = pd.concat([df_train, df_val], ignore_index=True)
    isoforest_model = IsoForestAnomalyModel(contamination=0.03, n_estimators=100, random_state=42)
    isoforest_model.fit(df_full[market_features])
    isoforest_model.save(ISOFOREST_MODEL_PATH)
    
    return zscore_model, lgbm_model, isoforest_model

def evaluate_models(df_test, zscore_model, lgbm_model, isoforest_model):
    y_true = extract_ground_truth(df_test).values
    features = ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_weekend',
                'demand_lag_15m', 'demand_lag_30m', 'demand_lag_1h', 'demand_lag_24h', 'demand_lag_7d',
                'demand_rolling_mean_1h', 'demand_rolling_std_1h', 'neighbor_avg_demand',
                'spatial_demand_gradient', 'demand_supply_ratio', 'cancellation_rate',
                'surge_multiplier', 'avg_eta_minutes', 'is_rainy', 'rainfall_mm']
    features = [f for f in features if f in df_test.columns]
    market_features = ['pickup_count', 'available_drivers', 'cancellation_rate', 'surge_multiplier', 'avg_eta_minutes']
    
    logger.info('Evaluating models...')
    lgbm_metrics = lgbm_model.evaluate(df_test[features], df_test['pickup_count'])
    logger.info('LightGBM - MAE: %.2f, RMSE: %.2f, WAPE: %.2f%%', lgbm_metrics['mae'], lgbm_metrics['rmse'], lgbm_metrics['wape'])
    
    y_pred_zscore = zscore_model.predict_anomaly(df_test).values
    y_pred_lgbm = lgbm_model.predict_anomaly(df_test[features], df_test['pickup_count']).values
    y_pred_isoforest = isoforest_model.predict_anomaly(df_test[market_features]).values
    
    results = {'lgbm_regression': lgbm_metrics}
    for name, pred in [('zscore', y_pred_zscore), ('lgbm_residual', y_pred_lgbm), ('isolation_forest', y_pred_isoforest)]:
        p, r, f1 = precision_score(y_true, pred, zero_division=0), recall_score(y_true, pred, zero_division=0), f1_score(y_true, pred, zero_division=0)
        results[f'{name}_anomaly'] = {'precision': p, 'recall': r, 'f1': f1}
        logger.info('%s - P: %.4f, R: %.4f, F1: %.4f', name.upper(), p, r, f1)
    
    votes = y_pred_zscore + y_pred_lgbm + y_pred_isoforest
    y_ens = (votes >= 2).astype(int)
    p_ens, r_ens, f1_ens = precision_score(y_true, y_ens, zero_division=0), recall_score(y_true, y_ens, zero_division=0), f1_score(y_true, y_ens, zero_division=0)
    results['ensemble_anomaly'] = {'precision': p_ens, 'recall': r_ens, 'f1': f1_ens}
    logger.info('ENSEMBLE - P: %.4f, R: %.4f, F1: %.4f', p_ens, r_ens, f1_ens)
    
    return results

def generate_report(results):
    report = ['# Model Evaluation Report', '', f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '---', '',
              '## LightGBM Performance', '']
    lgbm = results['lgbm_regression']
    report.append(f'- MAE: {lgbm["mae"]:.2f}')
    report.append(f'- RMSE: {lgbm["rmse"]:.2f}')
    report.append(f'- WAPE: {lgbm["wape"]:.2f}%')
    report.append('')
    report.append('## Anomaly Detection Results')
    report.append('')
    report.append('| Model | Precision | Recall | F1 |')
    report.append('|-------|-----------|--------|-----|')
    for name in ['zscore', 'lgbm_residual', 'isolation_forest']:
        m = results[f'{name}_anomaly']
        report.append(f'| {name} | {m["precision"]:.4f} | {m["recall"]:.4f} | {m["f1"]:.4f} |')
    ens = results['ensemble_anomaly']
    report.append(f'| **Ensemble** | **{ens["precision"]:.4f}** | **{ens["recall"]:.4f}** | **{ens["f1"]:.4f}** |')
    with open(REPORT_PATH, 'w') as f:
        f.write('\n'.join(report))
    logger.info('Report saved to %s', REPORT_PATH)

def main():
    print('='*80)
    print(' PHASE 3: TRAINING PIPELINE')
    print('='*80)
    df = load_data()
    logger.info('Running feature engineering...')
    featurizer = TelemetryFeaturizer()
    df_features = featurizer.fit_transform(df)
    df_train, df_val, df_test = split_data(df_features)
    logger.info('Train: %d, Val: %d, Test: %d', len(df_train), len(df_val), len(df_test))
    zscore, lgbm, isoforest = train_models(df_train, df_val)
    results = evaluate_models(df_test, zscore, lgbm, isoforest)
    generate_report(results)
    print('='*80)
    print(' PHASE 3 COMPLETE')
    print('='*80)
    print(f'Report: {REPORT_PATH}')
    print(f'Models: {MODELS_DIR}')

if __name__ == '__main__':
    main()
