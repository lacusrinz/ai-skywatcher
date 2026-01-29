# backend/tests/test_services/test_moon.py
import pytest
from datetime import datetime
from app.services.moon import MoonService

@pytest.fixture
def moon_service():
    return MoonService()

def test_get_moon_position_returns_dict(moon_service):
    """Test that get_moon_position returns correct structure"""
    result = moon_service.get_moon_position(
        observer_lat=40.7128,
        observer_lon=-74.0060,
        timestamp=datetime(2025, 1, 29, 20, 0, 0)
    )

    assert isinstance(result, dict)
    assert 'ra' in result
    assert 'dec' in result
    assert 'altitude' in result
    assert 'azimuth' in result
    assert 'distance' in result
    assert isinstance(result['ra'], float)
    assert isinstance(result['dec'], float)
    assert isinstance(result['altitude'], float)
    assert isinstance(result['azimuth'], float)
    assert isinstance(result['distance'], float)

def test_get_moon_position_reasonable_values(moon_service):
    """Test that moon position returns reasonable values"""
    result = moon_service.get_moon_position(
        observer_lat=40.7128,
        observer_lon=-74.0060,
        timestamp=datetime(2025, 1, 29, 20, 0, 0)
    )

    # RA: 0-360 degrees
    assert 0 <= result['ra'] <= 360
    # Dec: -90 to 90 degrees
    assert -90 <= result['dec'] <= 90
    # Altitude: -90 to 90 degrees
    assert -90 <= result['altitude'] <= 90
    # Azimuth: 0-360 degrees
    assert 0 <= result['azimuth'] <= 360
    # Distance: ~360,000-400,000 km
    assert 360000 <= result['distance'] <= 400000
