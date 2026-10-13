"""
Router: /analytics

Called by Django (e.g. from an admin view or management command) when
it needs aggregate statistics computed over a batch of pothole records.
FastAPI does the heavy aggregation so Django's ORM layer stays clean.
"""
from fastapi import APIRouter
from fastapi_service.schemas import AnalyticsRequest, AnalyticsResponse, HotspotPoint
from fastapi_service.services.aggregator import aggregate

router = APIRouter()


@router.post("/analytics", response_model=AnalyticsResponse)
def compute_analytics(payload: AnalyticsRequest) -> AnalyticsResponse:
    """
    Aggregate pothole statistics over a list of records.

    Django passes raw pothole dicts (from a queryset .values() call).
    FastAPI returns computed metrics Django can serve to the dashboard
    or store in a summary table.

    Expected keys in each record dict:
        latitude, longitude, severity, confidence_score (optional)
    """
    result = aggregate(payload.pothole_records)

    return AnalyticsResponse(
        total_count=result["total_count"],
        severity_distribution=result["severity_distribution"],
        hotspots=[HotspotPoint(**h) for h in result["hotspots"]],
        avg_confidence=result["avg_confidence"],
    )
