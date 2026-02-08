"""
Model training script for anomaly detection.

This is a SEPARATE script (not part of the API).
Run manually when you have training data.

Usage:
    poetry run python scripts/train_model.py
"""

import pickle

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import get_settings
from app.logger import logger


def generate_synthetic_training_data(n_samples: int = 1000) -> np.ndarray:
    """
    Generate synthetic document features for initial model training.

    In production, replace this with REAL uploaded documents.
    This is a bootstrap: the model will improve as real data accumulates.
    """
    logger.info(f"Generating {n_samples} synthetic training samples")

    # Feature ranges based on normal documents
    # (These are rough estimates; tune with real data)
    features = np.random.rand(n_samples, 18)

    # Scale features to realistic ranges
    features[:, 0] = features[:, 0] * 5000 + 100  # char_count: 100-5100
    features[:, 1] = features[:, 1] * 1000 + 20  # word_count: 20-1020
    features[:, 2] = features[:, 2] * 10 + 3  # avg_word_length: 3-13
    features[:, 3] = features[:, 3] * 100 + 10  # line_count: 10-110
    features[:, 4] = features[:, 4] * 0.3 + 0.1  # whitespace_ratio: 0.1-0.4
    features[:, 5] = features[:, 5] * 3 + 3  # entropy: 3-6
    features[:, 6] = features[:, 6] * 0.2  # uppercase_ratio: 0-0.2
    features[:, 7] = features[:, 7] * 0.15  # digit_ratio: 0-0.15
    features[:, 8] = features[:, 8] * 0.2  # special_char_ratio: 0-0.2
    features[:, 9] = features[:, 9] * 30 + 5  # number_count: 5-35
    features[:, 10] = features[:, 10] * 10000 + 100  # number_mean: 100-10100
    features[:, 11] = features[:, 11] * 5000  # number_std: 0-5000
    features[:, 12] = features[:, 12] * 50000  # number_max: 0-50000
    features[:, 13] = features[:, 13] * 5  # large_number_count: 0-5
    features[:, 14] = features[:, 14] * 0.3  # empty_line_ratio: 0-0.3
    features[:, 15] = features[:, 15] * 10 + 1  # date_count: 1-11
    features[:, 16] = features[:, 16] * 3  # email_count: 0-3
    features[:, 17] = features[:, 17] * 3  # url_count: 0-3

    return features


def train_anomaly_detector():
    """
    Train Isolation Forest model for anomaly detection.
    Saves model + scaler to disk.
    """
    settings = get_settings()
    model_dir = settings.model_dir

    logger.info("Starting model training")

    # Generate training data
    X_train = generate_synthetic_training_data(n_samples=1000)

    # Standardize features (zero mean, unit variance)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Train Isolation Forest
    # contamination=0.1 means 10% of training data assumed anomalous
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
    )
    model.fit(X_train_scaled)

    # Save artifacts
    model_path = model_dir / f"anomaly_model_{settings.model_version}.pkl"
    scaler_path = model_dir / f"scaler_{settings.model_version}.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    logger.info(f"Model saved to {model_path}")
    logger.info(f"Scaler saved to {scaler_path}")

    # Test prediction
    test_sample = X_train_scaled[0:1]
    prediction = model.predict(test_sample)
    score = model.score_samples(test_sample)

    logger.info(f"Test prediction: {prediction[0]} (score: {score[0]:.3f})")
    logger.info("Training complete")


if __name__ == "__main__":
    train_anomaly_detector()
