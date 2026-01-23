"""Test configuration"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_location():
    """Sample location fixture"""
    return {
        "latitude": 39.9042,
        "longitude": 116.4074
    }


@pytest.fixture
def sample_equipment():
    """Sample equipment fixture"""
    return {
        "fov_horizontal": 10.3,
        "fov_vertical": 6.9
    }


@pytest.fixture
def sample_visible_zone():
    """Sample visible zone fixture"""
    return {
        "id": "zone_1",
        "name": "东侧空地",
        "polygon": [[90, 20], [120, 20], [120, 60], [90, 60]],
        "priority": 1
    }
