"""
Router: /postprocess

Called by Django after /validate passes. Enriches detection data and
decides whether it should be written to PostgreSQL.
"""
from fastapi import APIRouter
from fastapi_service.schemas import PostprocessRequest, PostprocessResponse
from fastapi_service.services.postprocessor import postprocess

router = APIRouter()


@router.post("/postprocess", response_model=PostprocessResponse)
def postprocess_detection(payload: PostprocessRequest) -> PostprocessResponse:
    """
    Enrich a validated pothole detection.

    Django calls this before the final DB write. The response fields
    (severity, description, should_store) are used directly by Django:
      - should_store=False → Django silently discards the record
      - should_store=True  → Django writes to PostgreSQL using the
                             returned severity + description values
    """
    result = postprocess(
        latitude=payload.latitude,
        longitude=payload.longitude,
        num_potholes=payload.num_potholes,
        confidence_score=payload.confidence_score,
        adjusted_severity=payload.adjusted_severity,
        frame_number=payload.frame_number,
    )

    return PostprocessResponse(**result)
