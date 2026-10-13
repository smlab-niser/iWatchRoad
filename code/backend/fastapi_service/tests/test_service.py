"""
Unit tests for FastAPI service — no running server required.

Tests all three layers:
  - schemas (Pydantic validation)
  - services (business logic)
  - routers (FastAPI endpoint integration via TestClient)

Run:
    cd backend/
    pytest fastapi_service/tests/test_service.py -v
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from fastapi_service.main import app
from fastapi_service.schemas import SeverityLevel
from fastapi_service.services.aggregator import aggregate
from fastapi_service.services.postprocessor import postprocess
from fastapi_service.services.validation import compute_severity, is_within_india, validate

client = TestClient(app)


# ── Schema / enum tests ───────────────────────────────────────────────────────

class TestSchemas:
    def test_severity_enum_values(self):
        assert SeverityLevel.low == "low"
        assert SeverityLevel.medium == "medium"
        assert SeverityLevel.high == "high"
        assert SeverityLevel.critical == "critical"

    def test_severity_from_string(self):
        assert SeverityLevel("high") == SeverityLevel.high


# ── Validation service tests ──────────────────────────────────────────────────

class TestValidationService:
    def test_zero_potholes_rejected(self):
        is_valid, reason, _ = validate(20.4625, 85.0999, 0, 0.9)
        assert not is_valid
        assert reason is not None

    def test_low_confidence_rejected(self):
        is_valid, reason, _ = validate(20.4625, 85.0999, 3, 0.30)
        assert not is_valid
        assert reason is not None
        assert "0.30" in reason

    def test_out_of_india_rejected(self):
        # New York coordinates
        is_valid, reason, _ = validate(40.7128, -74.0060, 3, 0.90)
        assert not is_valid
        assert reason is not None
        assert "geographic" in reason.lower()

    def test_valid_detection_accepted(self):
        is_valid, reason, severity = validate(20.4625, 85.0999, 3, 0.87)
        assert is_valid
        assert reason is None
        assert isinstance(severity, SeverityLevel)

    def test_is_within_india(self):
        assert is_within_india(20.4625, 85.0999)   # NISER, Bhubaneswar
        assert is_within_india(28.6139, 77.2090)   # New Delhi
        assert not is_within_india(51.5074, -0.1278)  # London

    def test_severity_critical(self):
        assert compute_severity(12, 0.92) == SeverityLevel.critical

    def test_severity_high_by_count(self):
        assert compute_severity(6, 0.55) == SeverityLevel.high

    def test_severity_medium(self):
        assert compute_severity(2, 0.60) == SeverityLevel.medium

    def test_severity_low(self):
        assert compute_severity(1, 0.50) == SeverityLevel.low


# ── Postprocessor service tests ───────────────────────────────────────────────

class TestPostprocessorService:
    def test_first_detection_should_store(self):
        # Use unique coordinates to avoid collision with other tests
        result = postprocess(20.1111, 85.1111, 2, 0.80, SeverityLevel.medium, frame_number=10)
        assert result["should_store"] is True
        assert "description" in result
        assert "2 potholes" in result["description"]

    def test_description_contains_severity(self):
        result = postprocess(20.2222, 85.2222, 1, 0.75, SeverityLevel.high, frame_number=None)
        assert "high" in result["description"]

    def test_description_includes_frame_number(self):
        result = postprocess(20.3333, 85.3333, 1, 0.75, SeverityLevel.low, frame_number=42)
        assert "frame #42" in result["description"]

    def test_result_fields_present(self):
        result = postprocess(20.4444, 85.4444, 3, 0.88, SeverityLevel.critical)
        assert "latitude" in result
        assert "longitude" in result
        assert "num_potholes" in result
        assert "severity" in result
        assert "description" in result
        assert "should_store" in result


# ── Aggregator service tests ──────────────────────────────────────────────────

class TestAggregatorService:
    def test_empty_records(self):
        result = aggregate([])
        assert result["total_count"] == 0
        assert result["avg_confidence"] == 0.0
        assert result["hotspots"] == []

    def test_count(self):
        records = [
            {"latitude": 20.4, "longitude": 85.0, "severity": "high", "confidence_score": 0.8},
            {"latitude": 20.5, "longitude": 85.1, "severity": "low", "confidence_score": 0.5},
        ]
        result = aggregate(records)
        assert result["total_count"] == 2

    def test_severity_distribution(self):
        records = [
            {"latitude": 20.4, "longitude": 85.0, "severity": "high", "confidence_score": 0.9},
            {"latitude": 20.4, "longitude": 85.0, "severity": "high", "confidence_score": 0.8},
            {"latitude": 20.4, "longitude": 85.0, "severity": "low", "confidence_score": 0.5},
        ]
        result = aggregate(records)
        assert result["severity_distribution"]["high"] == 2
        assert result["severity_distribution"]["low"] == 1

    def test_avg_confidence(self):
        records = [
            {"latitude": 20.4, "longitude": 85.0, "severity": "medium", "confidence_score": 0.8},
            {"latitude": 20.5, "longitude": 85.1, "severity": "medium", "confidence_score": 0.6},
        ]
        result = aggregate(records)
        assert abs(result["avg_confidence"] - 0.7) < 0.001

    def test_hotspot_detected(self):
        """Cluster 4 records in the same grid cell — should produce 1 hotspot."""
        base = {"latitude": 20.401, "longitude": 85.001, "severity": "high", "confidence_score": 0.9}
        records = [
            {**base, "latitude": 20.401 + i * 0.0001}
            for i in range(4)
        ]
        result = aggregate(records)
        assert len(result["hotspots"]) >= 1
        assert result["hotspots"][0]["count"] == 4


# ── HTTP endpoint tests (via FastAPI TestClient) ──────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert data["service"] == "fastapi-iwatchroad"


class TestValidateEndpoint:
    def test_valid_payload_returns_200(self):
        response = client.post("/validate", json={
            "latitude": 20.4625,
            "longitude": 85.0999,
            "num_potholes": 3,
            "confidence_score": 0.87,
        })
        assert response.status_code == 200

    def test_valid_response_schema(self):
        data = client.post("/validate", json={
            "latitude": 20.4625,
            "longitude": 85.0999,
            "num_potholes": 3,
            "confidence_score": 0.87,
        }).json()
        assert "is_valid" in data
        assert "adjusted_severity" in data
        assert "confidence_score" in data

    def test_zero_potholes_rejected(self):
        data = client.post("/validate", json={
            "latitude": 20.4625,
            "longitude": 85.0999,
            "num_potholes": 0,
            "confidence_score": 0.90,
        }).json()
        assert data["is_valid"] is False

    def test_low_confidence_rejected(self):
        data = client.post("/validate", json={
            "latitude": 20.4625,
            "longitude": 85.0999,
            "num_potholes": 3,
            "confidence_score": 0.10,
        }).json()
        assert data["is_valid"] is False

    def test_missing_required_field_returns_422(self):
        response = client.post("/validate", json={"latitude": 20.4625})
        assert response.status_code == 422

    def test_out_of_range_latitude_returns_422(self):
        response = client.post("/validate", json={
            "latitude": 999,
            "longitude": 85.0999,
            "num_potholes": 3,
            "confidence_score": 0.87,
        })
        assert response.status_code == 422


class TestPostprocessEndpoint:
    def test_valid_payload_returns_200(self):
        response = client.post("/postprocess", json={
            "latitude": 20.9001,
            "longitude": 85.9001,
            "num_potholes": 2,
            "confidence_score": 0.85,
            "adjusted_severity": "medium",
        })
        assert response.status_code == 200

    def test_response_has_should_store(self):
        data = client.post("/postprocess", json={
            "latitude": 20.9002,
            "longitude": 85.9002,
            "num_potholes": 2,
            "confidence_score": 0.85,
            "adjusted_severity": "medium",
        }).json()
        assert "should_store" in data
        assert "description" in data
        assert "severity" in data

    def test_invalid_severity_returns_422(self):
        response = client.post("/postprocess", json={
            "latitude": 20.4625,
            "longitude": 85.0999,
            "num_potholes": 2,
            "confidence_score": 0.85,
            "adjusted_severity": "ultra",   # not a valid SeverityLevel
        })
        assert response.status_code == 422


class TestAnalyticsEndpoint:
    def test_empty_records(self):
        response = client.post("/analytics", json={"pothole_records": []})
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0

    def test_with_records(self):
        records = [
            {"latitude": 20.4, "longitude": 85.0, "severity": "high", "confidence_score": 0.9},
            {"latitude": 20.4, "longitude": 85.0, "severity": "medium", "confidence_score": 0.7},
        ]
        response = client.post("/analytics", json={"pothole_records": records})
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert "severity_distribution" in data
        assert "hotspots" in data
        assert "avg_confidence" in data
