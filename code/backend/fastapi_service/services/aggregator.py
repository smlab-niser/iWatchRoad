"""
Analytics aggregation logic.

Called by Django when it wants aggregate statistics computed over a
batch of pothole records. Runs in-memory on data Django passes in —
FastAPI never queries PostgreSQL directly.

Responsibilities:
  - Count total records
  - Compute severity distribution
  - Identify geographic hotspots (clusters with high counts)
  - Compute average model confidence
"""
from __future__ import annotations

import math
from collections import defaultdict

from fastapi_service.schemas import HotspotPoint, SeverityLevel

# Grid resolution for hotspot clustering (~500 m at Indian latitudes)
_HOTSPOT_GRID = 0.005

# Minimum reports in a cell to qualify as a hotspot
_HOTSPOT_MIN_COUNT = 3


def _snap(value: float, resolution: float) -> float:
    return math.floor(value / resolution) * resolution


def _dominant_severity(severities: list[str]) -> SeverityLevel:
    """Return the most severe level found in a list of severity strings."""
    order = [SeverityLevel.critical, SeverityLevel.high, SeverityLevel.medium, SeverityLevel.low]
    found = {SeverityLevel(s) for s in severities if s in SeverityLevel._value2member_map_}
    for level in order:
        if level in found:
            return level
    return SeverityLevel.low


def aggregate(records: list[dict]) -> dict:
    """
    Compute analytics over a list of pothole record dicts.

    Each record dict is expected to have at minimum:
        latitude, longitude, severity, confidence_score (optional)

    Returns a dict matching AnalyticsResponse fields:
        total_count, severity_distribution, hotspots, avg_confidence
    """
    if not records:
        return {
            "total_count": 0,
            "severity_distribution": {s.value: 0 for s in SeverityLevel},
            "hotspots": [],
            "avg_confidence": 0.0,
        }

    total_count = len(records)

    # ── Severity distribution ─────────────────────────────────────────────
    severity_dist: dict[str, int] = defaultdict(int)
    for record in records:
        sev = record.get("severity", "medium")
        severity_dist[sev] += 1

    # Fill in any missing severity keys with 0
    full_dist = {s.value: severity_dist.get(s.value, 0) for s in SeverityLevel}

    # ── Average confidence ────────────────────────────────────────────────
    confidences = [
        float(r["confidence_score"])
        for r in records
        if r.get("confidence_score") is not None
    ]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    # ── Hotspot detection (grid-based clustering) ─────────────────────────
    # Group records into geographic grid cells
    cell_data: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        try:
            lat = float(record["latitude"])
            lon = float(record["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        cell = (_snap(lat, _HOTSPOT_GRID), _snap(lon, _HOTSPOT_GRID))
        cell_data[cell].append(record)

    hotspots: list[HotspotPoint] = []
    for (snap_lat, snap_lon), cell_records in cell_data.items():
        if len(cell_records) < _HOTSPOT_MIN_COUNT:
            continue
        severities = [r.get("severity", "medium") for r in cell_records]
        hotspots.append(
            HotspotPoint(
                latitude=round(snap_lat + _HOTSPOT_GRID / 2, 6),
                longitude=round(snap_lon + _HOTSPOT_GRID / 2, 6),
                count=len(cell_records),
                severity=_dominant_severity(severities),
            )
        )

    # Sort hotspots by count descending so the worst areas appear first
    hotspots.sort(key=lambda h: h.count, reverse=True)

    return {
        "total_count": total_count,
        "severity_distribution": full_dist,
        "hotspots": [h.model_dump() for h in hotspots],
        "avg_confidence": round(avg_confidence, 4),
    }
