"""Test equipment API"""
from fastapi.testclient import TestClient


def test_get_presets(client: TestClient):
    """Test getting equipment presets"""
    response = client.get("/api/v1/equipment/presets")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_calculate_fov(client: TestClient):
    """Test FOV calculation"""
    fov_request = {
        "sensor_width": 36.0,
        "sensor_height": 24.0,
        "focal_length": 200
    }

    response = client.post("/api/v1/equipment/calculate-fov", json=fov_request)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "fov_horizontal" in data["data"]
    assert "fov_vertical" in data["data"]
    assert data["data"]["fov_horizontal"] > 0
    assert data["data"]["fov_vertical"] > 0


def test_create_equipment(client: TestClient):
    """Test creating equipment configuration"""
    equipment_data = {
        "name": "全画幅+200mm",
        "sensor_size": "full-frame",
        "sensor_width": 36.0,
        "sensor_height": 24.0,
        "focal_length": 200,
        "custom_name": "我的设备"
    }

    response = client.post("/api/v1/equipment", json=equipment_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]
    assert data["data"]["name"] == "我的设备"
