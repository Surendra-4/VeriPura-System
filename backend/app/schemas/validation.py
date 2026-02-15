from pydantic import BaseModel, Field


class ExtractedStructuredFields(BaseModel):
    """Structured entities extracted from document content."""

    batch_id: str | None = None
    exporter: str | None = None
    quantity: str | None = None
    dates: list[str] = Field(default_factory=list)
    certificate_id: str | None = None


class RuleViolationSchema(BaseModel):
    """Schema for rule violation"""

    rule_name: str
    severity: str
    message: str
    feature_values: dict[str, float]


class ValidationResponse(BaseModel):
    """Response for document validation"""

    file_id: str
    fraud_score: float = Field(..., ge=0, le=100, description="Fraud risk score (0-100)")
    is_anomaly: bool
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    rule_violations: list[RuleViolationSchema]
    top_features: list[tuple[str, float]] = Field(
        ..., description="Top 5 features contributing to score"
    )
    text_excerpt: str = Field(..., description="First 200 chars of extracted text")
    structured_fields: ExtractedStructuredFields = Field(
        default_factory=ExtractedStructuredFields,
        description="Structured entities extracted from the document",
    )
