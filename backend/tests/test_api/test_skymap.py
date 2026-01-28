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

@pytest.mark.asyncio
async def test_skymap_timeline_with_real_target():
    """Test /timeline endpoint with real database target"""
    response = client.post(
        "/api/v1/sky-map/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 60,
            "target_ids": ["NGC0224"]  # Andromeda Galaxy
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "timeline" in data["data"]

    timeline = data["data"]["timeline"]
    # Should have multiple time points (18:00 to 23:59 with 60 min interval)
    assert len(timeline) > 0

    # Each timeline entry should have positions
    first_entry = timeline[0]
    assert "timestamp" in first_entry
    assert "targets" in first_entry

    # CRITICAL: Should have NGC0224 target data (mock service returns None)
    # At least some time points should have visible targets
    visible_entries = [t for t in timeline if len(t["targets"]) > 0]
    assert len(visible_entries) > 0, "Should have visible NGC0224 targets in timeline (mock service returns None)"

@pytest.mark.asyncio
async def test_skymap_timeline_multiple_targets():
    """Test /timeline endpoint with multiple real targets"""
    response = client.post(
        "/api/v1/sky-map/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 30,
            "target_ids": ["NGC0224", "NGC1952"]  # Andromeda + Crab Nebula
        }
    )

    assert response.status_code == 200
    data = response.json()
    timeline = data["data"]["timeline"]

    # Should have data for both targets
    assert len(timeline) > 0
    # At least some time points should have targets visible
    visible_entries = [t for t in timeline if len(t["targets"]) > 0]
    assert len(visible_entries) > 0
