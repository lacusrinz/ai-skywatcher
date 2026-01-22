"""Test targets API"""
from fastapi.testclient import TestClient


def test_list_targets(client: TestClient):
    """Test listing targets"""
    response = client.get("/api/v1/targets")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "targets" in data["data"]
    assert "total" in data["data"]
    assert isinstance(data["data"]["targets"], list)


def test_get_target_by_id(client: TestClient):
    """Test getting a specific target"""
    response = client.get("/api/v1/targets/M42")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "M42"
    assert data["data"]["name"] == "猎户座大星云"


def test_search_targets(client: TestClient):
    """Test searching targets"""
    response = client.get("/api/v1/targets/search?q=Orion")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "results" in data["data"]


def test_filter_targets_by_type(client: TestClient):
    """Test filtering targets by type"""
    response = client.get("/api/v1/targets?type=emission-nebula")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # Verify all returned targets are of the specified type
    for target in data["data"]["targets"]:
        assert target["type"] == "emission-nebula"
