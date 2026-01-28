"""Integration tests for Sky Map API - end-to-end workflows"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_e2e_skymap_data_to_timeline_workflow():
    """Test: Get sky map data → use target IDs in timeline"""
    # Step 1: Get sky map data with targets
    data_response = client.post(
        "/api/v1/sky-map/data",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00",
            "include_targets": True,
            "target_types": ["galaxy"]
        }
    )

    assert data_response.status_code == 200
    data_data = data_response.json()
    assert data_data["success"] is True

    targets = data_data["data"]["targets"]
    assert len(targets) > 0

    # Step 2: Use first 3 target IDs in timeline request
    target_ids = [t["id"] for t in targets[:3]]

    timeline_response = client.post(
        "/api/v1/sky-map/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 60,
            "target_ids": target_ids
        }
    )

    assert timeline_response.status_code == 200
    timeline_data = timeline_response.json()
    assert timeline_data["success"] is True
    assert "timeline" in timeline_data["data"]
    assert len(timeline_data["data"]["timeline"]) > 0

@pytest.mark.asyncio
async def test_e2e_skymap_search_to_data_workflow():
    """Test: Search target → get sky map timeline for that target"""
    # Step 1: Search for Andromeda
    search_response = client.get("/api/v1/targets/search?q=Andromeda")

    assert search_response.status_code == 200
    search_data = search_response.json()
    targets = search_data["data"]["targets"]
    assert len(targets) > 0

    andromeda_id = targets[0]["id"]

    # Step 2: Get sky map timeline for Andromeda
    timeline_response = client.post(
        "/api/v1/sky-map/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 30,
            "target_ids": [andromeda_id]
        }
    )

    assert timeline_response.status_code == 200
    timeline_data = timeline_response.json()
    assert timeline_data["success"] is True

    # Verify Andromeda appears in timeline
    timeline = timeline_data["data"]["timeline"]
    andromeda_positions = [
        entry for entry in timeline
        if any(t["id"] == andromeda_id for t in entry["targets"])
    ]
    assert len(andromeda_positions) > 0, "Andromeda should be visible at some times"
