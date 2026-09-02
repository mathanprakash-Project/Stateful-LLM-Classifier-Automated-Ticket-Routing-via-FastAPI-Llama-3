"""
LLM response validation using Pydantic.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from pydantic import ValidationError

from app.schema import TicketClassification, Priority


@dataclass
class ValidationResult:
    is_valid: bool
    validated_classification: Optional[TicketClassification] = None
    error_details: list[str] = field(default_factory=list)


def validate_classification(raw: Any) -> ValidationResult:
    """
    Validate LLM output against TicketClassification schema.
    Accepts a dict, a TicketClassification instance, or any JSON-serializable object.
    """
    errors: list[str] = []

    # 1. Basic Type Check & Unwrap
    if isinstance(raw, TicketClassification):
        data = raw.model_dump()
    elif isinstance(raw, dict):
        data = raw
        if "properties" in data and isinstance(data["properties"], dict):
            data = data["properties"]
    else:
        return ValidationResult(
            is_valid=False,
            error_details=[f"Unexpected type: {type(raw).__name__}"],
        )

    # 2. Pydantic structural validation
    try:
        classification = TicketClassification.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            errors.append(f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}")
        return ValidationResult(is_valid=False, error_details=errors)

    # 3. Extra business-rule checks
    if not (0.0 <= classification.confidence_score <= 1.0):
        errors.append(f"confidence_score {classification.confidence_score} out of range [0, 1]")

    if classification.confidence_score < 0.5 and not classification.requires_human_review:
        errors.append("Low confidence score should set requires_human_review=True")

    if classification.priority == Priority.CRITICAL and not classification.requires_human_review:
        errors.append("CRITICAL priority must always require human review")

    # 4. Final Verdict
    if errors:
        return ValidationResult(is_valid=False, error_details=errors)

    return ValidationResult(is_valid=True, validated_classification=classification)


if __name__ == "__main__":
    good = {
        "issue_category": "payment_issue",
        "assigned_team": "payments_team",
        "priority": "high",
        "user_sentiment": "angry",
        "confidence_score": 0.95,
        "reasoning": "Customer reports duplicate charge",
        "requires_human_review": False,
    }
    bad_structure = {
        "issue_category": "invalid_category",
        "assigned_team": "payments_team",
        "priority": "urgent",
        "user_sentiment": "angry",
        "confidence_score": 1.5,
        "reasoning": "",
        "requires_human_review": False,
    }
    bad_business_rule = {
        "issue_category": "payment_issue",
        "assigned_team": "payments_team",
        "priority": "critical",
        "user_sentiment": "angry",
        "confidence_score": 0.95, 
        "reasoning": "Major site outage preventing payments.",
        "requires_human_review": False,
    }

    for label, data in [("VALID", good), ("INVALID_STRUCTURE", bad_structure), ("INVALID_BUSINESS_RULE", bad_business_rule)]:
        result = validate_classification(data)
        print(f"[{label}] is_valid={result.is_valid}")
        if result.error_details:
            for e in result.error_details:
                print(f"  - {e}")
