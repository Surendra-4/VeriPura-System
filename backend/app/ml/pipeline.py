from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.logger import logger
from app.ml.features import FeatureExtractor
from app.ml.model_loader import model_loader
from app.ml.parser import DocumentParser
from app.ml.rules import RuleEngine, RuleViolation
from app.schemas.upload import DocumentType


@dataclass
class ValidationResult:
    """Complete validation result for a document"""

    file_id: str
    fraud_score: float  # 0-100 (higher = more suspicious)
    is_anomaly: bool
    risk_level: str  # "low", "medium", "high", "critical"
    rule_violations: list[RuleViolation]
    top_features: list[tuple[str, float]]  # Top contributing features
    raw_features: dict[str, float]
    text_excerpt: str  # First 200 chars of extracted text
    structured_fields: dict[str, str | list[str] | None]


class MLPipeline:
    """
    End-to-end ML validation pipeline.

    Steps:
    1. Parse document → text
    2. Extract features
    3. Run rule-based validation
    4. ML anomaly detection
    5. Compute fraud score
    6. Generate explanation
    """

    def __init__(self):
        self.settings = get_settings()
        self.parser = DocumentParser()
        self.feature_extractor = FeatureExtractor()
        self.rule_engine = RuleEngine()

    async def validate_document(
        self, file_path: Path, file_id: str, doc_type: DocumentType
    ) -> ValidationResult:
        """
        Main validation pipeline.

        Args:
            file_path: Path to document file
            file_id: Unique file identifier
            doc_type: Document type

        Returns:
            ValidationResult with fraud score and explanations
        """
        logger.info(f"Starting ML validation for {file_id}")

        # Step 1: Parse document
        text = self.parser.parse(file_path, doc_type)
        text_excerpt = text[:200].replace("\n", " ")
        structured_fields = self.parser.extract_structured_fields(text)

        # Step 2: Extract features
        features = self.feature_extractor.extract(text)

        # Step 3: Rule-based validation
        violations = self.rule_engine.validate(features)

        # Step 4: ML anomaly detection
        is_anomaly, anomaly_score = self._detect_anomaly(features)

        # Step 5: Compute fraud score (hybrid: rules + ML)
        fraud_score = self._compute_fraud_score(violations, anomaly_score)

        # Step 6: Risk level
        risk_level = self._compute_risk_level(fraud_score, violations)

        # Step 7: Feature importance (top 5)
        top_features = self._get_top_features(features, anomaly_score)

        result = ValidationResult(
            file_id=file_id,
            fraud_score=fraud_score,
            is_anomaly=is_anomaly,
            risk_level=risk_level,
            rule_violations=violations,
            top_features=top_features,
            raw_features=features,
            text_excerpt=text_excerpt,
            structured_fields=structured_fields,
        )

        logger.info(
            f"Validation complete: {file_id} | Score: {fraud_score:.1f} | Risk: {risk_level}"
        )
        return result

    def _detect_anomaly(self, features: dict[str, float]) -> tuple[bool, float]:
        """
        Run ML anomaly detection.

        Returns:
            (is_anomaly, decision_score)
            decision_score: > 0 is inlier-like, < 0 is anomaly-like
        """
        model, scaler = model_loader.load_models()

        # Convert features to numpy array (ordered by feature names)
        feature_names = self.feature_extractor.get_feature_names()
        feature_vector = np.array([features.get(name, 0.0) for name in feature_names]).reshape(
            1, -1
        )

        # Scale features
        feature_vector_scaled = scaler.transform(feature_vector)

        # IsolationForest decision_function is centered around 0:
        # positive => inlier-like, negative => anomaly-like.
        decision_score = float(model.decision_function(feature_vector_scaled)[0])
        is_anomaly = decision_score <= self.settings.anomaly_decision_threshold

        return is_anomaly, decision_score

    def _compute_fraud_score(self, violations: list[RuleViolation], anomaly_score: float) -> float:
        """
        Compute final fraud score (0-100).

        Formula:
        - Base score from ML decision score (calibrated to 0-100 via sigmoid)
        - Add penalties for rule violations
        """
        # Convert decision score to risk score:
        # decision=0 => 50, positive => lower risk, negative => higher risk.
        ml_score = 100.0 / (1.0 + np.exp(10.0 * anomaly_score))

        # Add rule violation penalties
        severity_penalties = {"critical": 15, "high": 10, "medium": 5, "low": 2}
        rule_penalty = sum(severity_penalties.get(v.severity, 0) for v in violations)

        # Combine (cap at 100)
        fraud_score = max(0.0, min(100.0, ml_score + rule_penalty))

        return float(fraud_score)

    def _compute_risk_level(self, fraud_score: float, violations: list[RuleViolation]) -> str:
        """
        Map fraud score to risk level.
        Critical violations override score-based level.
        """
        # Check for critical rule violations
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            return "critical"

        # Score-based levels
        if fraud_score >= 75:
            return "critical"
        elif fraud_score >= 60:
            return "high"
        elif fraud_score >= 40:
            return "medium"
        else:
            return "low"

    def _get_top_features(
        self, features: dict[str, float], anomaly_score: float
    ) -> list[tuple[str, float]]:
        """
        Identify top contributing features for explainability.

        For now, uses simple heuristics.
        TODO: Use SHAP values for true feature importance.
        """
        # Sort by absolute deviation from expected ranges
        scored_features = []

        for name, value in features.items():
            # Compute "surprise" score (how far from normal)
            surprise = self._compute_surprise(name, value)
            scored_features.append((name, value, surprise))

        # Sort by surprise, take top 5
        scored_features.sort(key=lambda x: x[2], reverse=True)
        top_5 = [(name, value) for name, value, _ in scored_features[:5]]

        return top_5

    @staticmethod
    def _compute_surprise(feature_name: str, value: float) -> float:
        """
        Compute how unusual a feature value is.
        Uses rough heuristics for each feature.
        """
        # Expected ranges (from training data)
        expected_ranges = {
            "char_count": (100, 5000),
            "word_count": (20, 1000),
            "avg_word_length": (3, 13),
            "entropy": (3, 6),
            "digit_ratio": (0, 0.15),
            "date_count": (1, 10),
        }

        if feature_name not in expected_ranges:
            return 0.0

        low, high = expected_ranges[feature_name]
        if value < low:
            return (low - value) / low  # Fraction below minimum
        elif value > high:
            return (value - high) / high  # Fraction above maximum
        else:
            return 0.0  # Within normal range
