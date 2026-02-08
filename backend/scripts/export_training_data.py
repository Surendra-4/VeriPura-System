"""
Export uploaded documents as training data for model retraining.

This script:
1. Reads all ledger records
2. Extracts file IDs and validation results
3. Parses documents to extract features
4. Saves as training dataset (features + labels)

Usage:
    poetry run python scripts/export_training_data.py
"""

import asyncio
import json

import pandas as pd

from app.config import get_settings
from app.infra.ledger import Ledger
from app.infra.storage import StorageService
from app.logger import logger
from app.ml.features import FeatureExtractor
from app.ml.parser import DocumentParser
from app.schemas.upload import DocumentType


async def export_training_data():
    """
    Export training data from uploaded documents.

    Output:
    - training_data.csv: Feature matrix with labels
    - training_metadata.json: Dataset statistics
    """
    settings = get_settings()
    ledger = Ledger()
    storage = StorageService()
    parser = DocumentParser()
    feature_extractor = FeatureExtractor()

    logger.info("Starting training data export")

    # Load all ledger records
    records = await ledger.get_all_records(limit=10000)
    logger.info(f"Found {len(records)} ledger records")

    if len(records) == 0:
        logger.warning("No records found. Upload documents first.")
        return

    # Extract features from each document
    training_samples = []
    skipped = 0

    for record in records:
        try:
            # Get file path
            file_id = record.file_id
            doc_type = DocumentType(record.document_metadata.document_type)
            file_path = storage.get_file_path(file_id, f".{doc_type.value}")

            if not file_path.exists():
                logger.warning(f"File not found: {file_id}")
                skipped += 1
                continue

            # Parse document
            text = parser.parse(file_path, doc_type)

            # Extract features
            features = feature_extractor.extract(text)

            # Add labels (from validation result)
            features["fraud_score"] = record.validation_result.fraud_score
            features["risk_level"] = record.validation_result.risk_level
            features["is_anomaly"] = int(record.validation_result.is_anomaly)

            # Add metadata
            features["batch_id"] = record.batch_id
            features["file_id"] = file_id
            features["document_type"] = doc_type.value

            training_samples.append(features)

            logger.info(f"Exported: {record.batch_id}")

        except Exception as e:
            logger.error(f"Failed to export {record.batch_id}: {str(e)}")
            skipped += 1

    # Convert to DataFrame
    df = pd.DataFrame(training_samples)

    # Save to CSV
    output_path = settings.model_dir / "training_data.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Training data saved: {output_path}")
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Skipped: {skipped}")

    # Save metadata
    metadata = {
        "total_samples": len(df),
        "skipped": skipped,
        "feature_count": len(feature_extractor.get_feature_names()),
        "risk_distribution": df["risk_level"].value_counts().to_dict(),
        "anomaly_count": int(df["is_anomaly"].sum()),
        "export_timestamp": pd.Timestamp.now().isoformat(),
    }

    metadata_path = settings.model_dir / "training_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Metadata saved: {metadata_path}")
    logger.info(f"Risk distribution: {metadata['risk_distribution']}")


if __name__ == "__main__":
    asyncio.run(export_training_data())
