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

def test_get_moon_phase_returns_dict(moon_service):
    """Test that get_moon_phase returns correct structure"""
    result = moon_service.get_moon_phase(datetime(2025, 1, 29, 20, 0, 0))

    assert isinstance(result, dict)
    assert 'percentage' in result
    assert 'age_days' in result
    assert 'illumination' in result
    assert 'name' in result
    assert 0 <= result['percentage'] <= 100
    assert 0 <= result['age_days'] <= 29.53
    assert 0 <= result['illumination'] <= 1

def test_get_moon_phase_known_values(moon_service):
    """Test with known moon phase (new moon)"""
    # January 29, 2025 was new moon (around 0-5%)
    result = moon_service.get_moon_phase(datetime(2025, 1, 29, 20, 0, 0))

    # Should be near new moon (0-10%)
    assert 0 <= result['percentage'] <= 10
    assert result['name'] in ['新月', '娥眉月']

import math

def test_calculate_light_pollution_returns_value(moon_service):
    """Test that pollution calculation returns 0-1"""
    result = moon_service.calculate_light_pollution(
        moon_altitude=45.0,
        moon_azimuth=180.0,
        moon_phase=50.0,
        target_altitude=45.0,
        target_azimuth=180.0
    )

    assert isinstance(result, float)
    assert 0 <= result <= 1

def test_calculate_light_pollution_full_moon_overhead(moon_service):
    """Test full moon overhead gives high pollution"""
    result = moon_service.calculate_light_pollution(
        moon_altitude=80.0,
        moon_azimuth=180.0,
        moon_phase=100.0,  # Full moon
        target_altitude=80.0,
        target_azimuth=180.0
    )

    # Should be very high pollution
    assert result > 0.8

def test_calculate_light_pollution_new_moon(moon_service):
    """Test new moon gives low pollution"""
    result = moon_service.calculate_light_pollution(
        moon_altitude=45.0,
        moon_azimuth=180.0,
        moon_phase=0.0,  # New moon
        target_altitude=45.0,
        target_azimuth=180.0
    )

    # Should be very low pollution
    assert result < 0.1

def test_calculate_light_pollution_far_angular_distance(moon_service):
    """Test that far targets have less pollution"""
    # Same position
    result_close = moon_service.calculate_light_pollution(
        moon_altitude=45.0,
        moon_azimuth=180.0,
        moon_phase=100.0,
        target_altitude=45.0,
        target_azimuth=180.0
    )

    # Far away (90 degrees difference)
    result_far = moon_service.calculate_light_pollution(
        moon_altitude=45.0,
        moon_azimuth=90.0,
        moon_phase=100.0,
        target_altitude=45.0,
        target_azimuth=180.0
    )

    assert result_close > result_far

def test_get_pollution_heatmap_returns_list(moon_service):
    """Test that heatmap returns list of points"""
    result = moon_service.get_pollution_heatmap(
        observer_lat=40.7128,
        observer_lon=-74.0060,
        timestamp=datetime(2025, 1, 29, 20, 0, 0),
        resolution=10  # Small grid for testing
    )

    assert isinstance(result, list)
    assert len(result) == 100  # 10x10 grid

    # Check first point structure
    point = result[0]
    assert 'azimuth' in point
    assert 'altitude' in point
    assert 'pollution' in point
    assert 0 <= point['pollution'] <= 1

def test_get_pollution_heatmap_coverages_sky(moon_service):
    """Test that heatmap covers full sky"""
    result = moon_service.get_pollution_heatmap(
        observer_lat=40.7128,
        observer_lon=-74.0060,
        timestamp=datetime(2025, 1, 29, 20, 0, 0),
        resolution=18  # 18x18 = 324 points
    )

    # Check coverage
    azimuths = [p['azimuth'] for p in result]
    altitudes = [p['altitude'] for p in result]

    assert min(azimuths) >= 0
    assert max(azimuths) <= 360
    assert min(altitudes) >= 0
    assert max(altitudes) <= 90
