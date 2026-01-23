"""Test locations API"""
from fastapi.testclient import TestClient


def test_geolocate(client: TestClient):
    """Test automatic geolocation"""
    response = client.post("/api/v1/locations/geolocate")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "latitude" in data["data"]
    assert "longitude" in data["data"]


def test_list_locations(client: TestClient):
    """Test listing locations"""
    response = client.get("/api/v1/locations")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_create_location(client: TestClient):
    """Test creating a location"""
    location_data = {
        "name": "测试地点",
        "latitude": 40.0,
        "longitude": 116.0,
        "timezone": "Asia/Shanghai"
    }

    response = client.post("/api/v1/locations", json=location_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "测试地点"
    assert "id" in data["data"]


def test_validate_location(client: TestClient):
    """Test location validation"""
    location_data = {
        "latitude": 39.9042,
        "longitude": 116.4074
    }

    response = client.post("/api/v1/locations/validate", json=location_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["validated"] is True
