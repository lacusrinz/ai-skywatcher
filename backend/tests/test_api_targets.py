import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_target_m31():
    """Test getting M31 from local database"""
    response = client.get("/api/v1/targets/NGC0224")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Note: OpenNGC uses NGC/IC numbers as primary IDs
    assert data["data"]["id"] == "NGC0224"
    assert "Andromeda" in data["data"]["name"]

def test_search_targets():
    """Test searching for objects"""
    # Search for NGC (should return many results)
    response = client.get("/api/v1/targets/search?q=NGC&limit=10")
    assert response.status_code == 200
    data = response.json()
    print(f"\n=== Search Response ===")
    print(f"Success: {data.get('success')}")
    print(f"Data: {data.get('data')}")
    print(f"Message: {data.get('message')}")
    print(f"Full response: {data}")
    print(f"=======================\n")
    assert data["success"] is True
    assert data["data"] is not None, f"data field should not be None. Full response: {data}"
    assert data["data"]["count"] > 0
    assert len(data["data"]["targets"]) > 0

def test_get_statistics():
    """Test getting database statistics"""
    response = client.get("/api/v1/targets/stats")
    assert response.status_code == 200
    data = response.json()
    print(f"Statistics response: {data}")
    assert data["success"] is True
    assert data["data"] is not None, "data field should not be None"
    assert data["data"]["total_objects"] > 10000

def test_list_targets_by_type():
    """Test listing targets filtered by type"""
    response = client.get("/api/v1/targets?type=GALAXY&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["targets"]) > 0
    assert all(t["type"] == "GALAXY" for t in data["data"]["targets"])

def test_list_targets_by_constellation():
    """Test listing targets filtered by constellation"""
    response = client.get("/api/v1/targets?constellation=And&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Should return objects in Andromeda constellation

def test_sync_from_simbad():
    """Test manual SIMBAD sync (with mock)"""
    # This would need mocking in real scenario
    # For now, just test the endpoint exists
    response = client.post("/api/v1/targets/sync", json=["IC999"])
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "synced" in data["data"]
    assert "failed" in data["data"]
