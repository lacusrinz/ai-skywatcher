"""Tests for Recommendations API with real database"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_recommendations_with_real_db():
    """Test recommendations using real database"""
    response = client.post(
        "/api/v1/recommendations",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "equipment": {
                "type": "refractor",
                "aperture": 80,
                "focal_length": 500
            },
            "limit": 5
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "recommendations" in data["data"]
    assert "summary" in data["data"]

@pytest.mark.asyncio
async def test_recommendations_with_filters():
    """Test recommendations with type filters"""
    response = client.post(
        "/api/v1/recommendations",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "equipment": {
                "type": "refractor",
                "aperture": 80,
                "focal_length": 500
            },
            "filters": {
                "min_magnitude": 8,
                "types": ["GALAXY", "NEBULA"]
            },
            "limit": 10
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
