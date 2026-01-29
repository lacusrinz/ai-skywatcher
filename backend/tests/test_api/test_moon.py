"""Test moon API endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_moon_position():
    """Test GET /api/v1/moon/position"""
    response = client.post(
        "/api/v1/moon/position",
        json={
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "position" in data["data"]
    assert "ra" in data["data"]["position"]
    assert "dec" in data["data"]["position"]
    assert "altitude" in data["data"]["position"]
    assert "azimuth" in data["data"]["position"]
    assert "distance" in data["data"]["position"]


@pytest.mark.asyncio
async def test_get_moon_position_missing_location():
    """Test GET /api/v1/moon/position with missing location"""
    response = client.post(
        "/api/v1/moon/position",
        json={
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_moon_heatmap():
    """Test GET /api/v1/moon/heatmap"""
    response = client.post(
        "/api/v1/moon/heatmap",
        json={
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "timestamp": "2025-01-28T22:00:00",
            "resolution": 20
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "heatmap" in data["data"]
    assert len(data["data"]["heatmap"]) > 0
    assert "moon_position" in data["data"]
    assert "moon_phase" in data["data"]


@pytest.mark.asyncio
async def test_get_moon_heatmap_invalid_resolution():
    """Test GET /api/v1/moon/heatmap with invalid resolution"""
    response = client.post(
        "/api/v1/moon/heatmap",
        json={
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "resolution": 200  # Too high
        }
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_moon_pollution():
    """Test POST /api/v1/moon/pollution"""
    response = client.post(
        "/api/v1/moon/pollution",
        json={
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "target_position": {
                "altitude": 45.0,
                "azimuth": 180.0
            },
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pollution_level" in data["data"]
    assert "impact_level" in data["data"]
    assert "moon_position" in data["data"]
    assert "moon_phase" in data["data"]
    assert 0 <= data["data"]["pollution_level"] <= 1


@pytest.mark.asyncio
async def test_get_moon_pollution_missing_target():
    """Test POST /api/v1/moon/pollution with missing target position"""
    response = client.post(
        "/api/v1/moon/pollution",
        json={
            "location": {
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "timestamp": "2025-01-28T22:00:00"
        }
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_moon_pollution_impact_levels():
    """Test different pollution impact levels"""
    # Test with various target positions
    test_cases = [
        {"altitude": 10, "azimuth": 0},   # Low altitude
        {"altitude": 45, "azimuth": 90},   # Medium altitude
        {"altitude": 80, "azimuth": 180},  # High altitude
    ]

    for target_pos in test_cases:
        response = client.post(
            "/api/v1/moon/pollution",
            json={
                "location": {
                    "latitude": 39.9042,
                    "longitude": 116.4074
                },
                "target_position": target_pos,
                "timestamp": "2025-01-28T22:00:00"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["impact_level"] in ["无影响", "轻微", "中等", "严重", "极严重"]
