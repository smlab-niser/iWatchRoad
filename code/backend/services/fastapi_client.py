"""
Django → FastAPI internal client.

Communicates with the FastAPI service EXCLUSIVELY via Unix Domain Socket.
NEVER uses TCP, 127.0.0.1, or any port number.

Socket path: /run/fastapi-iwatchroad/fastapi.sock

Usage in Django views:
    from services.fastapi_client import validate_inference, postprocess_detection

All public functions return:
    - dict   → success (use the data)
    - None   → FastAPI is unreachable (apply local fallback, never crash)
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

# MUST match RuntimeDirectory in fastapi-iwatchroad.service
FASTAPI_SOCKET_PATH = "/run/fastapi-iwatchroad/fastapi.sock"

# Max seconds to wait for FastAPI to respond.
# Kept short — local Unix socket calls should take < 2 ms normally.
FASTAPI_TIMEOUT = 5.0


def _get_client() -> httpx.Client:
    """
    Build an httpx.Client that routes all traffic through the Unix socket.
    Called lazily so import-time errors don't crash Django startup if the
    socket doesn't exist yet (e.g. during collectstatic / migrations).
    """
    transport = httpx.HTTPTransport(uds=FASTAPI_SOCKET_PATH)
    return httpx.Client(
        transport=transport,
        # Hostname is ignored for UDS — httpx uses the socket file path instead.
        base_url="http://fastapi-internal",
        timeout=FASTAPI_TIMEOUT,
    )


# Module-level singleton — created once, reused across requests.
# Gunicorn forks AFTER module load, so each worker gets its own copy. ✓
_client: httpx.Client | None = None


def _get_or_create_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = _get_client()
    return _client


# ── Core internal helper ──────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict) -> dict | None:
    """
    POST JSON to a FastAPI endpoint via Unix socket.

    Returns parsed response dict on success, or None on any failure.
    Callers MUST treat None as 'FastAPI unavailable — use fallback'.

    Errors are logged but never re-raised — FastAPI being down must
    NEVER crash Django or block pothole data from being stored.
    """
    client = _get_or_create_client()
    try:
        response = client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()

    except httpx.TimeoutException:
        logger.warning(
            "[FastAPI] Timeout on %s after %.1fs — falling back to local logic",
            endpoint,
            FASTAPI_TIMEOUT,
        )

    except httpx.ConnectError:
        logger.error(
            "[FastAPI] Cannot connect to socket %s — "
            "is fastapi-iwatchroad.service running? "
            "Check: sudo systemctl status fastapi-iwatchroad",
            FASTAPI_SOCKET_PATH,
        )

    except httpx.HTTPStatusError as exc:
        logger.error(
            "[FastAPI] HTTP %s on %s — response: %s",
            exc.response.status_code,
            endpoint,
            exc.response.text[:200],
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("[FastAPI] Unexpected error on %s: %s", endpoint, exc)

    return None


# ── Public API used by Django views & services ────────────────────────────────

def validate_inference(
    latitude: float,
    longitude: float,
    num_potholes: int,
    confidence_score: float,
    frame_number: int | None = None,
    device_id: str | None = None,
) -> dict | None:
    """
    Validate ML inference result received from Flutter.

    Returns dict with keys:
        is_valid         bool
        reason           str | None   (why rejected)
        adjusted_severity str         (low/medium/high/critical)
        confidence_score float

    Returns None if FastAPI is unreachable.

    Django caller pattern:
        result = validate_inference(lat, lon, count, conf)
        if result is None:
            severity = _local_severity_fallback(count, conf)
        elif not result["is_valid"]:
            return JsonResponse({"error": result["reason"]}, status=422)
        else:
            severity = result["adjusted_severity"]
    """
    return _post("/validate", {
        "latitude": latitude,
        "longitude": longitude,
        "num_potholes": num_potholes,
        "confidence_score": confidence_score,
        "frame_number": frame_number,
        "device_id": device_id,
    })


def postprocess_detection(
    latitude: float,
    longitude: float,
    num_potholes: int,
    confidence_score: float,
    adjusted_severity: str,
    frame_number: int | None = None,
) -> dict | None:
    """
    Enrich a validated pothole detection before DB storage.

    Returns dict with keys:
        latitude       float
        longitude      float
        num_potholes   int
        severity       str    (final, use this for DB write)
        description    str    (auto-generated, store in Pothole.description)
        should_store   bool   (if False, Django must silently discard)

    Returns None if FastAPI is unreachable.

    Django caller pattern:
        result = postprocess_detection(lat, lon, count, conf, severity)
        if result is None or result["should_store"]:
            Pothole.objects.create(...)   # use result fields if available
        # if should_store is False, return 200 and discard silently
    """
    return _post("/postprocess", {
        "latitude": latitude,
        "longitude": longitude,
        "num_potholes": num_potholes,
        "confidence_score": confidence_score,
        "adjusted_severity": adjusted_severity,
        "frame_number": frame_number,
    })


def compute_analytics(pothole_records: list[dict]) -> dict | None:
    """
    Compute aggregate statistics over a batch of pothole records.

    pothole_records: list of dicts from Django ORM .values() call.
    Each dict should have: latitude, longitude, severity, confidence_score

    Returns dict with keys:
        total_count             int
        severity_distribution   dict[str, int]
        hotspots                list[dict]
        avg_confidence          float

    Returns None if FastAPI is unreachable.
    """
    return _post("/analytics", {"pothole_records": pothole_records})


def check_fastapi_health() -> bool:
    """
    Quick liveness probe. Returns True if FastAPI is responding.

    Use this in Django admin views or management commands to surface
    FastAPI status without crashing if it's down.

    Example:
        from services.fastapi_client import check_fastapi_health
        if not check_fastapi_health():
            logger.warning("FastAPI service is down")
    """
    client = _get_or_create_client()
    try:
        response = client.get("/health")
        return response.status_code == 200
    except Exception:
        return False
