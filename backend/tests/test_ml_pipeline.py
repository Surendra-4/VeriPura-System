"""
Tests for ML pipeline components.
"""


from app.ml.features import FeatureExtractor
from app.ml.rules import RuleEngine


def test_feature_extraction():
    """Test feature extraction from text"""
    text = """
    Invoice #12345
    Date: 2024-01-15
    Amount: $1,500.00
    Customer: Acme Corp
    Email: billing@acme.com
    """

    extractor = FeatureExtractor()
    features = extractor.extract(text)

    # Check all expected features present
    expected_features = extractor.get_feature_names()
    assert len(features) == len(expected_features)

    # Check specific features
    assert features["char_count"] > 0
    assert features["word_count"] > 0
    assert features["date_count"] >= 1
    assert features["email_count"] >= 1
    assert features["number_count"] > 0


def test_empty_text_features():
    """Test feature extraction from empty text"""
    extractor = FeatureExtractor()
    features = extractor.extract("")

    assert features["char_count"] == 0
    assert features["word_count"] == 0


def test_rule_engine_minimum_content():
    """Test minimum content rule"""
    engine = RuleEngine()

    # Valid content
    valid_features = {
        "char_count": 100,
        "word_count": 20,
        "avg_word_length": 5.0,
        "entropy": 4.5,
        "date_count": 1,
    }
    violations = engine.validate(valid_features)
    assert len(violations) == 0  # May have other violations, but not minimum_content

    # Invalid content
    invalid_features = {"char_count": 5, "word_count": 1}
    violations = engine.validate(invalid_features)
    violation_names = [v.rule_name for v in violations]
    assert "minimum_content" in violation_names


def test_rule_engine_entropy():
    """Test entropy rule"""
    engine = RuleEngine()

    # Normal entropy
    normal_features = {"entropy": 4.5, "char_count": 100}
    violations = engine.validate(normal_features)
    entropy_violations = [v for v in violations if v.rule_name == "entropy_check"]
    assert len(entropy_violations) == 0

    # Abnormal entropy (too low)
    low_entropy = {"entropy": 1.0, "char_count": 100}
    violations = engine.validate(low_entropy)
    entropy_violations = [v for v in violations if v.rule_name == "entropy_check"]
    assert len(entropy_violations) > 0


def test_rule_severity_levels():
    """Test that rules have correct severity levels"""
    engine = RuleEngine()

    # Create features that violate multiple rules
    bad_features = {
        "char_count": 5,  # Critical violation
        "entropy": 1.0,  # High violation
    }

    violations = engine.validate(bad_features)
    assert len(violations) > 0

    max_severity = engine.get_max_severity(violations)
    assert max_severity in ["critical", "high", "medium", "low"]
