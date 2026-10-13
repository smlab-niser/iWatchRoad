"""
Validation business logic.

Decides whether an ML inference result from Flutter is trustworthy
enough to be stored. Runs purely in-memory — no DB, no I/O.

Rules (tuned for NISER/road-watch context):
  - confidence_score < 0.45  → reject (too noisy)
  - num_potholes == 0        → reject (nothing detected)
  - GPS out of plausible India bounding box → reject
  - Otherwise               → accept, compute adjusted severity
"""
from __future__ import annotations

from fastapi_service.schemas import SeverityLevel

# Loose bounding box for India (covers all states + island territories)
_INDIA_LAT_MIN, _INDIA_LAT_MAX = 6.5, 37.6
_INDIA_LON_MIN, _INDIA_LON_MAX = 68.1, 97.4

# Confidence thresholds
_MIN_CONFIDENCE = 0.45
_HIGH_CONFIDENCE = 0.80
_CRITICAL_CONFIDENCE = 0.90

# Count thresholds for severity
_HIGH_COUNT = 5
_CRITICAL_COUNT = 10


def is_within_india(latitude: float, longitude: float) -> bool:
    """Return True if coords fall inside the India bounding box."""
    return (
        _INDIA_LAT_MIN <= latitude <= _INDIA_LAT_MAX
        and _INDIA_LON_MIN <= longitude <= _INDIA_LON_MAX
    )


def compute_severity(num_potholes: int, confidence_score: float) -> SeverityLevel:
    """
    Derive severity from detection count and model confidence.
    Both dimensions contribute — high count + high confidence → critical.
    """
    if num_potholes >= _CRITICAL_COUNT and confidence_score >= _HIGH_CONFIDENCE:
        return SeverityLevel.critical
    if num_potholes >= _HIGH_COUNT or confidence_score >= _CRITICAL_CONFIDENCE:
        return SeverityLevel.high
    if num_potholes >= 2 or confidence_score >= _HIGH_CONFIDENCE:
        return SeverityLevel.medium
    return SeverityLevel.low


def validate(
    latitude: float,
    longitude: float,
    num_potholes: int,
    confidence_score: float,
) -> tuple[bool, str | None, SeverityLevel]:
    """
    Core validation logic.

    Returns:
        (is_valid, rejection_reason_or_None, adjusted_severity)
    """
    if num_potholes == 0:
        return False, "No potholes detected in frame — skipping", SeverityLevel.low

    if confidence_score < _MIN_CONFIDENCE:
        return (
            False,
            f"Confidence {confidence_score:.2f} is below minimum threshold {_MIN_CONFIDENCE}",
            SeverityLevel.low,
        )

    if not is_within_india(latitude, longitude):
        return (
            False,
            f"Coordinates ({latitude}, {longitude}) are outside expected geographic region",
            SeverityLevel.low,
        )

    severity = compute_severity(num_potholes, confidence_score)
    return True, None, severity
