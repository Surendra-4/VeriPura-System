from dataclasses import dataclass
from typing import Callable

from app.logger import logger


@dataclass
class RuleViolation:
    """Represents a failed validation rule"""

    rule_name: str
    severity: str  # "critical", "high", "medium", "low"
    message: str
    feature_values: dict[str, float]


class RuleEngine:
    """
    Hard-coded business rules for document validation.
    These catch obvious fraud/errors before ML scoring.
    """

    def __init__(self):
        self.rules: list[tuple[str, str, Callable, str]] = [
            (
                "minimum_content",
                "critical",
                lambda f: f.get("char_count", 0) >= 10,
                "Document has insufficient content (possible blank or corrupted file)",
            ),
            (
                "maximum_content",
                "high",
                lambda f: f.get("char_count", 0) <= 100000,
                "Document exceeds maximum size (possible attack or malformed file)",
            ),
            (
                "reasonable_word_length",
                "medium",
                lambda f: 2 <= f.get("avg_word_length", 0) <= 15,
                "Average word length is unusual (possible gibberish or encoding error)",
            ),
            (
                "entropy_check",
                "high",
                lambda f: 2.0 <= f.get("entropy", 0) <= 7.0,
                "Text entropy is abnormal (too repetitive or too random)",
            ),
            (
                "digit_ratio_check",
                "low",
                lambda f: f.get("digit_ratio", 0) <= 0.5,
                "Excessive digits in text (unusual for typical documents)",
            ),
            (
                "has_date",
                "medium",
                lambda f: f.get("date_count", 0) >= 1,
                "No date found in document (invoices/certificates require dates)",
            ),
        ]

    def validate(self, features: dict[str, float]) -> list[RuleViolation]:
        """
        Run all rules against extracted features.

        Returns:
            List of violations (empty if all rules pass)
        """
        violations = []

        for rule_name, severity, rule_func, message in self.rules:
            try:
                if not rule_func(features):
                    violation = RuleViolation(
                        rule_name=rule_name,
                        severity=severity,
                        message=message,
                        feature_values={k: features.get(k, 0.0) for k in self._relevant_features(rule_name)},
                    )
                    violations.append(violation)
                    logger.info(f"Rule violation: {rule_name} ({severity})")

            except Exception as e:
                logger.error(f"Rule execution error ({rule_name}): {str(e)}")

        return violations

    @staticmethod
    def _relevant_features(rule_name: str) -> list[str]:
        """Map rule names to relevant features for explainability"""
        mapping = {
            "minimum_content": ["char_count", "word_count"],
            "maximum_content": ["char_count"],
            "reasonable_word_length": ["avg_word_length"],
            "entropy_check": ["entropy"],
            "digit_ratio_check": ["digit_ratio", "char_count"],
            "has_date": ["date_count"],
        }
        return mapping.get(rule_name, [])

    def get_max_severity(self, violations: list[RuleViolation]) -> str:
        """
        Determine worst violation severity.
        Used for quick rejection decisions.
        """
        if not violations:
            return "none"

        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        max_severity = max(violations, key=lambda v: severity_order.get(v.severity, 0))
        return max_severity.severity
