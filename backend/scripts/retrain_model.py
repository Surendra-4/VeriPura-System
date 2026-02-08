"""
Retrain anomaly detection model using real uploaded data.

This script:
1. Loads training data exported from uploaded documents
2. Trains new Isolation Forest model
3. Evaluates model performance
4. Saves versioned model artifacts
5. Creates model comparison report

Usage:
    poetry run python scripts/retrain_model.py --version v2
"""

import argparse
import json
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import get_settings
from app.logger import logger
from app.ml.features import FeatureExtractor


def load_training_data(model_dir: Path):
    """Load exported training data"""
    data_path = model_dir / "training_data.csv"

    if not data_path.exists():
        raise FileNotFoundError(
            "Training data not found. Run: poetry run python scripts/export_training_data.py"
        )

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} training samples")

    return df


def prepare_features(df: pd.DataFrame):
    """Extract feature columns for training"""
    feature_extractor = FeatureExtractor()
    feature_names = feature_extractor.get_feature_names()

    # Extract feature matrix
    X = df[feature_names].values

    # Remove any NaN/inf values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    logger.info(f"Feature matrix shape: {X.shape}")

    return X, feature_names


def train_model(X: np.ndarray, contamination: float = 0.1):
    """Train Isolation Forest model"""
    logger.info("Training Isolation Forest...")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )

    model.fit(X_scaled)

    logger.info("Training complete")

    return model, scaler


def evaluate_model(model, scaler, X: np.ndarray):
    """Evaluate model performance"""
    X_scaled = scaler.transform(X)

    # Predict
    predictions = model.predict(X_scaled)
    scores = model.score_samples(X_scaled)

    # Count anomalies
    anomaly_count = np.sum(predictions == -1)
    anomaly_rate = anomaly_count / len(predictions)

    # Score statistics
    score_stats = {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
        "anomaly_rate": float(anomaly_rate),
        "anomaly_count": int(anomaly_count),
        "total_samples": len(predictions),
    }

    logger.info(f"Anomaly rate: {anomaly_rate:.2%}")
    logger.info(f"Score range: [{score_stats['min']:.3f}, {score_stats['max']:.3f}]")

    return score_stats


def save_model(model, scaler, version: str, stats: dict, model_dir: Path):
    """Save model artifacts with version"""
    # Save model
    model_path = model_dir / f"anomaly_model_{version}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Save scaler
    scaler_path = model_dir / f"scaler_{version}.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Save metadata
    metadata = {
        "version": version,
        "trained_at": datetime.utcnow().isoformat(),
        "model_type": "IsolationForest",
        "n_estimators": model.n_estimators,
        "contamination": model.contamination,
        "performance": stats,
    }

    metadata_path = model_dir / f"model_{version}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model saved: {model_path}")
    logger.info(f"Scaler saved: {scaler_path}")
    logger.info(f"Metadata saved: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description="Retrain anomaly detection model")
    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="Model version (e.g., v2, v3)",
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.1,
        help="Expected proportion of anomalies (default: 0.1)",
    )

    args = parser.parse_args()

    settings = get_settings()
    model_dir = settings.model_dir

    logger.info(f"Starting model retraining: {args.version}")

    # Load data
    df = load_training_data(model_dir)

    # Prepare features
    X, feature_names = prepare_features(df)

    # Train model
    model, scaler = train_model(X, contamination=args.contamination)

    # Evaluate
    stats = evaluate_model(model, scaler, X)

    # Save
    save_model(model, scaler, args.version, stats, model_dir)

    logger.info(f"Retraining complete: {args.version}")


if __name__ == "__main__":
    main()
