"""
Router: /validate

Called by Django immediately after receiving ML inference results from Flutter.
Decides whether the detection is trustworthy and computes adjusted severity.
"""
from fastapi import APIRouter
from fastapi_service.schemas import ValidateRequest, ValidateResponse
from fastapi_service.services.validation import validate

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
def validate_detection(payload: ValidateRequest) -> ValidateResponse:
    """
    Validate an ML inference result.

    Django sends this before deciding whether to process and store
    the pothole report. If is_valid=False, Django must reject the
    Flutter request with HTTP 422.
    """
    is_valid, reason, adjusted_severity = validate(
        latitude=payload.latitude,
        longitude=payload.longitude,
        num_potholes=payload.num_potholes,
        confidence_score=payload.confidence_score,
    )

    return ValidateResponse(
        is_valid=is_valid,
        reason=reason,
        adjusted_severity=adjusted_severity,
        confidence_score=payload.confidence_score,
    )
