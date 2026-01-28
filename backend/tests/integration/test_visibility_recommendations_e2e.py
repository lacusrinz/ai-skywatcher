import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_e2e_visibility_and_recommendations():
    """End-to-end test: Get recommendations, check visibility"""
    # Step 1: Get recommendations
    rec_response = client.post(
        "/api/v1/recommendations",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "equipment": {"type": "refractor", "aperture": 80, "focal_length": 500},
            "limit": 5
        }
    )

    assert rec_response.status_code == 200
    rec_data = rec_response.json()
    assert rec_data["success"] is True
    recommendations = rec_data["data"]["recommendations"]
    assert len(recommendations) > 0

    # Step 2: Get visibility for first recommended target
    first_target_id = recommendations[0]["target"]["id"]

    vis_response = client.post(
        "/api/v1/visibility/position",
        json={
            "target_id": first_target_id,
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert vis_response.status_code == 200
    vis_data = vis_response.json()
    assert vis_data["success"] is True
    assert vis_data["data"]["target_id"] == first_target_id
    assert "altitude" in vis_data["data"]

@pytest.mark.asyncio
async def test_e2e_real_objects_not_mock():
    """Verify we're using real database, not mock data"""
    # Get recommendations with high limit
    response = client.post(
        "/api/v1/recommendations",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "equipment": {"type": "refractor", "aperture": 80, "focal_length": 500},
            "limit": 100
        }
    )

    assert response.status_code == 200
    data = response.json()
    recommendations = data["data"]["recommendations"]

    # Mock data only has 10 objects
    # Real database has 13,318 objects
    # Even with visibility filtering, we should get more than 10
    assert len(recommendations) > 10, "Should return more than mock data's 10 objects"

    # Verify we have real database IDs (NGC/IC format)
    real_db_ids = [r["target"]["id"] for r in recommendations if r["target"]["id"].startswith(("NGC", "IC"))]
    assert len(real_db_ids) > 0, "Should have NGC/IC objects from real database"

@pytest.mark.asyncio
async def test_e2e_search_to_visibility_flow():
    """Test search -> visibility workflow"""
    # Step 1: Search for Andromeda
    search_response = client.get("/api/v1/targets/search?q=Andromeda")

    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data["success"] is True
    targets = search_data["data"]["targets"]
    assert len(targets) > 0

    # Step 2: Get visibility for first result
    target_id = targets[0]["id"]

    vis_response = client.post(
        "/api/v1/visibility/position",
        json={
            "target_id": target_id,
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert vis_response.status_code == 200
    vis_data = vis_response.json()
    assert vis_data["data"]["target_id"] == target_id
