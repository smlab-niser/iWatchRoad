"""
Flutter → Django → FastAPI → PostgreSQL report endpoint.

This is a NEW dedicated view for pothole reports coming from the
Flutter mobile app with ML inference results attached.

It does NOT replace PotholeViewSet in views.py — that handles
dashboard/admin CRUD. This view handles the mobile reporting flow only.

Endpoint: POST /api/potholes/report/

Flow:
    1. Flutter sends inference result (lat, lon, count, confidence)
    2. Django validates input via serializer
    3. Django calls FastAPI /validate (via Unix socket)
    4. If invalid → 422 back to Flutter
    5. Django calls FastAPI /postprocess (via Unix socket)
    6. If should_store=False → 200 OK, discard silently
    7. Django writes enriched Pothole to PostgreSQL
    8. 201 Created returned to Flutter
"""
from __future__ import annotations

import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from potholes.models import Pothole
from services.fastapi_client import (
    postprocess_detection,
    validate_inference,
)

logger = logging.getLogger(__name__)


# ── Local fallback helpers (used when FastAPI is down) ───────────────────────

def _local_severity(num_potholes: int, confidence_score: float) -> str:
    """
    Simplified severity rule used ONLY when FastAPI is unreachable.
    Mirrors the logic in fastapi_service/services/validation.py.
    """
    if num_potholes >= 10 and confidence_score >= 0.80:
        return "critical"
    if num_potholes >= 5 or confidence_score >= 0.90:
        return "high"
    if num_potholes >= 2 or confidence_score >= 0.80:
        return "medium"
    return "low"


def _local_description(num_potholes: int, severity: str, frame_number: int | None) -> str:
    frame_info = f" (frame #{frame_number})" if frame_number else ""
    return (
        f"{num_potholes} pothole{'s' if num_potholes != 1 else ''} detected"
        f"{frame_info}. Severity: {severity}. (FastAPI offline — local fallback used)"
    )


# ── Main report view ──────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def report_pothole(request):
    """
    Receive ML inference result from Flutter and store validated pothole.

    Expected JSON body:
    {
        "latitude":         20.4625,        // required
        "longitude":        85.0999,        // required
        "num_potholes":     3,              // required, int >= 0
        "confidence_score": 0.87,           // required, 0.0–1.0
        "frame_number":     142,            // optional
        "device_id":        "flutter-abc"   // optional
    }

    Responses:
        201  Created         — stored successfully
        200  OK              — valid but deduplicated (not stored)
        400  Bad Request     — missing/invalid fields
        422  Unprocessable   — FastAPI rejected (low confidence, bad GPS, etc.)
        500  Server Error    — unexpected failure
    """
    import json

    # ── 1. Parse and validate request body ───────────────────────────────────
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # Required fields
    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        num_potholes = int(data["num_potholes"])
        confidence_score = float(data["confidence_score"])
    except (KeyError, TypeError, ValueError) as exc:
        return JsonResponse(
            {"error": f"Missing or invalid required field: {exc}"},
            status=400,
        )

    # Basic range checks before calling FastAPI
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return JsonResponse({"error": "Coordinates out of range"}, status=400)
    if not (0.0 <= confidence_score <= 1.0):
        return JsonResponse({"error": "confidence_score must be between 0.0 and 1.0"}, status=400)
    if num_potholes < 0:
        return JsonResponse({"error": "num_potholes must be >= 0"}, status=400)

    # Optional fields
    frame_number: int | None = data.get("frame_number")
    device_id: str | None = data.get("device_id")

    # ── 2. FastAPI /validate ──────────────────────────────────────────────────
    validation_result = validate_inference(
        latitude=latitude,
        longitude=longitude,
        num_potholes=num_potholes,
        confidence_score=confidence_score,
        frame_number=frame_number,
        device_id=device_id,
    )

    if validation_result is None:
        # FastAPI is down — use local fallback severity, continue storing
        logger.warning(
            "[report_pothole] FastAPI /validate unreachable — "
            "using local fallback for (%.4f, %.4f)",
            latitude, longitude,
        )
        severity = _local_severity(num_potholes, confidence_score)
        fastapi_used = False
    else:
        if not validation_result["is_valid"]:
            # FastAPI explicitly rejected this detection — tell Flutter
            return JsonResponse(
                {
                    "error": "Detection rejected by validation service",
                    "reason": validation_result.get("reason"),
                },
                status=422,
            )
        severity = validation_result["adjusted_severity"]
        fastapi_used = True

    # ── 3. FastAPI /postprocess ───────────────────────────────────────────────
    postprocess_result = postprocess_detection(
        latitude=latitude,
        longitude=longitude,
        num_potholes=num_potholes,
        confidence_score=confidence_score,
        adjusted_severity=severity,
        frame_number=frame_number,
    )

    if postprocess_result is None:
        # FastAPI down — build minimal description locally and store anyway
        logger.warning(
            "[report_pothole] FastAPI /postprocess unreachable — using defaults"
        )
        final_lat = latitude
        final_lon = longitude
        final_severity = severity
        final_description = _local_description(num_potholes, severity, frame_number)
        should_store = True
    else:
        if not postprocess_result["should_store"]:
            # FastAPI flagged this as a duplicate — silently discard
            logger.info(
                "[report_pothole] FastAPI marked detection as duplicate at (%.4f, %.4f) — discarding",
                latitude, longitude,
            )
            return JsonResponse(
                {"message": "Detection received (duplicate suppressed)"},
                status=200,
            )
        final_lat = postprocess_result["latitude"]
        final_lon = postprocess_result["longitude"]
        final_severity = postprocess_result["severity"]
        final_description = postprocess_result["description"]
        should_store = True

    # ── 4. Write to PostgreSQL via Django ORM ─────────────────────────────────
    if should_store:
        try:
            pothole = Pothole.objects.create(
                latitude=final_lat,
                longitude=final_lon,
                num_potholes=num_potholes,
                severity=final_severity,
                description=final_description,
                frame_number=frame_number,
                status="reported",
            )
        except Exception as exc:
            logger.exception("[report_pothole] DB write failed: %s", exc)
            return JsonResponse({"error": "Failed to store pothole report"}, status=500)

        logger.info(
            "[report_pothole] Stored Pothole #%d at (%.4f, %.4f) severity=%s fastapi=%s",
            pothole.pk, final_lat, final_lon, final_severity, fastapi_used,
        )

        return JsonResponse(
            {
                "id": pothole.pk,
                "latitude": float(pothole.latitude),
                "longitude": float(pothole.longitude),
                "num_potholes": pothole.num_potholes,
                "severity": pothole.severity,
                "description": pothole.description,
                "status": pothole.status,
                "timestamp": pothole.timestamp.isoformat(),
                "fastapi_validated": fastapi_used,
            },
            status=201,
        )
