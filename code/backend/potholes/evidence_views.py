"""Evidence upload endpoint for the on-device (edge) detection pipeline.

This is the contract the mobile app uses once inference runs on the phone.
It replaces the old "upload the whole video and let the server detect"
flow (`/api/upload-videos/` -> `/api/process-video/`), which moved hundreds of
megabytes per drive and is explicitly ruled out by the project brief.

    POST /api/potholes/evidence/        multipart/form-data
        frame           JPEG file       required -- the single best frame
        metadata        JSON string     required -- see below
        Authorization: Bearer <jwt>     required

`metadata` mirrors `pipeline/edge/schemas.py::PotholeFrameRecord` so the
Python reference pipeline and the app speak the same language:

    {
      "track_id":      17,              // dedup key within a session
      "session_id":    "uuid",
      "device_id":     "android-abc",
      "captured_at":   "2026-07-26T10:15:30Z",
      "gps":           {"lat": 20.46, "lon": 85.09},
      "bbox_xyxy":     [120.0, 88.0, 260.0, 190.0],
      "confidence":    0.87,
      "num_potholes":  1,               // optional, default 1
      "frame_number":  142              // optional
    }

Why multipart rather than a base64 field in JSON: the frame travels as raw
bytes (no ~33% base64 inflation), is streamed to disk instead of buffered in
the request body, and the database stores only the path. See
Plan/EVIDENCE_STORAGE.md.

Idempotency: (session_id, track_id) is unique per session. A retry of an
already-accepted record returns 200 with the existing id instead of creating a
duplicate, so the app's offline queue can retry freely.
"""
from __future__ import annotations

import json
import logging

from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .frame_storage import FrameStorageError, save_frame_bytes
from .models import Pothole

logger = logging.getLogger(__name__)

# Keep in step with edge/config.py's confidence floor; anything below this the
# device should not have bothered uploading.
MIN_CONFIDENCE = 0.25


def _severity_from(num_potholes: int, confidence: float) -> str:
    """Same ladder as report_view/_local_severity, kept in one place."""
    if num_potholes >= 10 and confidence >= 0.80:
        return "critical"
    if num_potholes >= 5 or confidence >= 0.90:
        return "high"
    if num_potholes >= 2 or confidence >= 0.80:
        return "medium"
    return "low"


def _bad(message, **extra):
    return Response({"success": False, "message": message, **extra},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def upload_evidence(request):
    """Accept one verified detection: a JPEG frame plus its metadata."""

    frame = request.FILES.get("frame")
    if frame is None:
        return _bad("Missing 'frame' file part")

    raw_meta = request.data.get("metadata")
    if not raw_meta:
        return _bad("Missing 'metadata' part")

    try:
        meta = json.loads(raw_meta)
    except (json.JSONDecodeError, TypeError):
        return _bad("'metadata' is not valid JSON")
    if not isinstance(meta, dict):
        return _bad("'metadata' must be a JSON object")

    # --- required metadata ------------------------------------------------
    try:
        gps = meta["gps"]
        latitude = float(gps["lat"])
        longitude = float(gps["lon"])
        confidence = float(meta["confidence"])
        track_id = int(meta["track_id"])
        session_id = str(meta["session_id"])
    except (KeyError, TypeError, ValueError) as exc:
        return _bad(f"Missing or invalid metadata field: {exc}")

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return _bad("Coordinates out of range")
    if not (0.0 <= confidence <= 1.0):
        return _bad("confidence must be between 0.0 and 1.0")
    if confidence < MIN_CONFIDENCE:
        return _bad(f"confidence {confidence:.2f} below the {MIN_CONFIDENCE} floor")

    # --- optional metadata ------------------------------------------------
    num_potholes = int(meta.get("num_potholes", 1) or 1)
    frame_number = meta.get("frame_number")
    bbox = meta.get("bbox_xyxy")
    device_id = meta.get("device_id", "unknown")

    # --- idempotency ------------------------------------------------------
    # The app retries from an offline queue; the same (session, track) must not
    # land twice. Marker lives in `description` because there is no dedicated
    # column and adding one would mean a schema change on a 2.1 GB database.
    dedup_key = f"[edge:{session_id}:{track_id}]"
    existing = Pothole.objects.filter(description__contains=dedup_key).only("id").first()
    if existing is not None:
        return Response(
            {"success": True, "message": "Already recorded (duplicate suppressed)",
             "data": {"id": existing.pk, "duplicate": True}},
            status=status.HTTP_200_OK,
        )

    severity = _severity_from(num_potholes, confidence)
    description = (
        f"Edge detection from {device_id}. "
        f"Confidence {confidence:.0%}. Severity: {severity}. {dedup_key}"
    )

    pothole = Pothole(
        latitude=latitude,
        longitude=longitude,
        num_potholes=num_potholes,
        severity=severity,
        status="reported",
        description=description,
        frame_number=frame_number,
    )
    pothole.save()

    try:
        save_frame_bytes(pothole, frame.read(), frame_number)
    except FrameStorageError as exc:
        # The row is useless without its evidence frame.
        pothole.delete()
        return _bad(f"Rejected frame: {exc}")

    logger.info(
        "[evidence] stored pothole #%s session=%s track=%s conf=%.2f bbox=%s",
        pothole.pk, session_id, track_id, confidence, bbox,
    )

    return Response(
        {
            "success": True,
            "message": "Evidence accepted",
            "data": {
                "id": pothole.pk,
                "duplicate": False,
                "severity": pothole.severity,
                "frame_image": pothole.frame_image.url if pothole.frame_image else None,
                "timestamp": pothole.timestamp.isoformat(),
            },
        },
        status=status.HTTP_201_CREATED,
    )
