"""Tests for Sky Map API with real database"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_skymap_data_returns_real_objects():
    """Test /data endpoint returns real database objects, not mock data"""
    response = client.post(
        "/api/v1/sky-map/data",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00",
            "include_targets": True,
            "target_types": []
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "targets" in data["data"]

    targets = data["data"]["targets"]
    # Mock data has only 10 objects
    # Real database should return many more (even after filtering by visibility)
    assert len(targets) > 10, "Should return more than 10 mock objects"

    # Verify we have real database IDs (NGC/IC format)
    real_ids = [t["id"] for t in targets if t["id"].startswith(("NGC", "IC"))]
    assert len(real_ids) > 0, "Should have NGC/IC objects from real database"

@pytest.mark.asyncio
async def test_skymap_data_with_type_filter():
    """Test /data endpoint with type filter"""
    response = client.post(
        "/api/v1/sky-map/data",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00",
            "include_targets": True,
            "target_types": ["galaxy", "cluster"]
        }
    )

    assert response.status_code == 200
    data = response.json()
    targets = data["data"]["targets"]

    # All targets should be of specified types
    for target in targets:
        assert target["type"] in ["galaxy", "cluster"]
