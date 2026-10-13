"""
Post-processing business logic.

Runs after /validate passes. Enriches the detection data before
Django writes it to PostgreSQL. Stateless — no DB, no I/O.

Responsibilities:
  - Generate a human-readable description string
  - Apply a lightweight proximity-based deduplication guard
    (coarse grid snapping — prevents duplicate reports for the
     same physical pothole submitted within ~50 m)
  - Return should_store=False for records that look like duplicates
    NOTE: True deduplication lives in Django/DB (unique constraints).
          This is a fast pre-filter only.
"""
from __future__ import annotations

import math

from fastapi_service.schemas import SeverityLevel

# Grid cell size in degrees (~55 m at Indian latitudes)
_GRID_RESOLUTION = 0.0005

# In-process seen-set — lost on worker restart (intentional: soft dedup only)
# Keyed by (snapped_lat, snapped_lon, num_potholes) tuples
_seen_cells: set[tuple] = set()


def _snap(value: float, resolution: float) -> float:
    """Snap a coordinate to the nearest grid cell centre."""
    return math.floor(value / resolution) * resolution


def _make_description(
    num_potholes: int,
    severity: SeverityLevel,
    confidence_score: float,
    frame_number: int | None,
) -> str:
    """Build a short, human-readable summary for the DB description field."""
    frame_info = f" (frame #{frame_number})" if frame_number is not None else ""
    return (
        f"{num_potholes} pothole{'s' if num_potholes != 1 else ''} detected"
        f"{frame_info}. Severity: {severity.value}. "
        f"Model confidence: {confidence_score:.0%}."
    )


def postprocess(
    latitude: float,
    longitude: float,
    num_potholes: int,
    confidence_score: float,
    adjusted_severity: SeverityLevel,
    frame_number: int | None = None,
) -> dict:
    """
    Enrich and deduplicate a validated detection.

    Returns a dict matching PostprocessResponse fields:
        latitude, longitude, num_potholes, severity,
        description, should_store
    """
    snapped = (_snap(latitude, _GRID_RESOLUTION), _snap(longitude, _GRID_RESOLUTION), num_potholes)

    if snapped in _seen_cells:
        # Likely a duplicate from the same drive pass — skip storage
        return {
            "latitude": latitude,
            "longitude": longitude,
            "num_potholes": num_potholes,
            "severity": adjusted_severity,
            "description": _make_description(num_potholes, adjusted_severity, confidence_score, frame_number),
            "should_store": False,
        }

    _seen_cells.add(snapped)

    return {
        "latitude": latitude,
        "longitude": longitude,
        "num_potholes": num_potholes,
        "severity": adjusted_severity,
        "description": _make_description(num_potholes, adjusted_severity, confidence_score, frame_number),
        "should_store": True,
    }
