import math
import re
from collections import Counter
from typing import Any

import numpy as np

from app.logger import logger
from app.ml.parser import DocumentParser


class FeatureExtractor:
    """
    Extracts numerical features from document text.
    Features must be:
    - Numerical (for ML model input)
    - Explainable (for fraud reasoning)
    - Robust (handle missing/malformed data)
    """

    def __init__(self):
        self.parser = DocumentParser()

    def extract(self, text: str) -> dict[str, Any]:
        """
        Extract all features from document text.

        Returns:
            Dictionary of features (all numeric)
        """
        features = {}

        # Basic text statistics
        features.update(self._text_statistics(text))

        # Content quality metrics
        features.update(self._quality_metrics(text))

        # Numeric content analysis
        features.update(self._numeric_analysis(text))

        # Structural features
        features.update(self._structural_features(text))

        logger.debug(f"Extracted {len(features)} features")
        return features

    @staticmethod
    def _text_statistics(text: str) -> dict[str, float]:
        """Basic text properties"""
        words = text.split()
        chars = len(text)

        return {
            "char_count": float(chars),
            "word_count": float(len(words)),
            "avg_word_length": np.mean([len(w) for w in words]) if words else 0.0,
            "line_count": float(len(text.split("\n"))),
            "whitespace_ratio": text.count(" ") / chars if chars > 0 else 0.0,
        }

    @staticmethod
    def _quality_metrics(text: str) -> dict[str, float]:
        """
        Document quality indicators.
        Low quality might indicate tampering or OCR errors.
        """
        chars = len(text)
        if chars == 0:
            return {
                "entropy": 0.0,
                "uppercase_ratio": 0.0,
                "digit_ratio": 0.0,
                "special_char_ratio": 0.0,
            }

        # Shannon entropy (measure of randomness)
        # High entropy = more random, low = repetitive
        counter = Counter(text)
        entropy = -sum(
            (count / chars) * math.log2(count / chars) for count in counter.values()
        )

        return {
            "entropy": entropy,
            "uppercase_ratio": sum(1 for c in text if c.isupper()) / chars,
            "digit_ratio": sum(1 for c in text if c.isdigit()) / chars,
            "special_char_ratio": sum(1 for c in text if not c.isalnum() and not c.isspace())
            / chars,
        }

    def _numeric_analysis(self, text: str) -> dict[str, float]:
        """
        Analyze numeric content (amounts, prices, quantities).
        """
        numbers = self.parser.extract_numbers(text)

        if not numbers:
            return {
                "number_count": 0.0,
                "number_mean": 0.0,
                "number_std": 0.0,
                "number_max": 0.0,
                "large_number_count": 0.0,  # > 10,000
            }

        return {
            "number_count": float(len(numbers)),
            "number_mean": float(np.mean(numbers)),
            "number_std": float(np.std(numbers)),
            "number_max": float(np.max(numbers)),
            "large_number_count": float(sum(1 for n in numbers if n > 10000)),
        }

    def _structural_features(self, text: str) -> dict[str, float]:
        """
        Document structure analysis.
        Well-formed documents have consistent structure.
        """
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Date patterns
        dates = self.parser.extract_dates(text)

        # Email pattern
        email_count = len(re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text))

        # URL pattern
        url_count = len(re.findall(r"https?://[^\s]+", text))

        return {
            "empty_line_ratio": (len(lines) - len(non_empty_lines)) / len(lines)
            if lines
            else 0.0,
            "date_count": float(len(dates)),
            "email_count": float(email_count),
            "url_count": float(url_count),
        }

    def get_feature_names(self) -> list[str]:
        """
        Return ordered list of feature names.
        Must match extract() output keys.
        """
        return [
            "char_count",
            "word_count",
            "avg_word_length",
            "line_count",
            "whitespace_ratio",
            "entropy",
            "uppercase_ratio",
            "digit_ratio",
            "special_char_ratio",
            "number_count",
            "number_mean",
            "number_std",
            "number_max",
            "large_number_count",
            "empty_line_ratio",
            "date_count",
            "email_count",
            "url_count",
        ]