import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.database import DatabaseService

client = TestClient(app)

@pytest.mark.asyncio
async def test_calculate_position_with_real_db():
    """Test position calculation using real database"""
    response = client.post(
        "/api/v1/visibility/position",
        json={
            "target_id": "NGC0224",  # M31 Andromeda
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "altitude" in data["data"]
    assert "azimuth" in data["data"]
    assert data["data"]["target_id"] == "NGC0224"

@pytest.mark.asyncio
async def test_calculate_position_not_found():
    """Test position calculation with invalid ID"""
    response = client.post(
        "/api/v1/visibility/position",
        json={
            "target_id": "INVALID999",
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_batch_positions_with_real_db():
    """Test batch position calculations"""
    response = client.post(
        "/api/v1/visibility/positions-batch",
        json={
            "target_ids": ["NGC0224", "NGC1976", "IC0123"],
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["positions"]) > 0
