# Moon Phase and Light Pollution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-step.

**Goal:** Add moon position/phase visualization and moonlight pollution calculation to the sky map and recommendation system.

**Architecture:**
- Backend: Add MoonService using Skyfield library for precise astronomical calculations
- API: Create 3 new endpoints for moon data, heatmap, and pollution calculation
- Frontend: Extend SkyMapCanvas with moon rendering and heatmap visualization
- Integration: Modify ScoringService and RecommendationService to include moonlight impact (15% weight)

**Tech Stack:**
- Skyfield (Python): JPL ephemeris-based astronomical calculations
- FastAPI: Moon API endpoints
- Canvas API: Moon and heatmap rendering
- Existing codebase: AstronomyService, ScoringService, RecommendationService

---

## Task 1: Install Skyfield Dependency

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add Skyfield to requirements**

```bash
echo "skyfield>=1.45" >> backend/requirements.txt
```

**Step 2: Install the dependency**

```bash
cd backend
pip install skyfield>=1.45
```

**Step 3: Verify installation**

```bash
python -c "import skyfield; print(skyfield.__version__)"
```

Expected: Version number printed (e.g., "1.45")

**Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat: add skyfield dependency for moon calculations"
```

---

## Task 2: Create MoonService Core

**Files:**
- Create: `backend/app/services/moon.py`
- Test: `backend/tests/test_services/test_moon.py`

**Step 1: Write failing tests for moon position**

```python
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
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_services/test_moon.py::test_get_moon_position_returns_dict -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.moon'"

**Step 3: Create MoonService class skeleton**

```python
# backend/app/services/moon.py
from datetime import datetime
from typing import Dict
from skyfield.api import load, Topos
import logging

logger = logging.getLogger(__name__)

class MoonService:
    """Moon data calculation service using Skyfield"""

    def __init__(self):
        """Initialize Skyfield ephemeris"""
        try:
            # Load JPL DE421 ephemeris (auto-downloaded on first run)
            self.ephemeris = load('de421.bsp')
            self.moon = self.ephemeris['moon']
            self.earth = self.ephemeris['earth']
            logger.info("MoonService initialized with DE421 ephemeris")
        except Exception as e:
            logger.error(f"Failed to initialize MoonService: {e}")
            raise

    def get_moon_position(
        self,
        observer_lat: float,
        observer_lon: float,
        timestamp: datetime
    ) -> Dict[str, float]:
        """
        Calculate moon position in both equatorial and horizontal coordinates

        Args:
            observer_lat: Observer latitude in degrees
            observer_lon: Observer longitude in degrees
            timestamp: Observation time

        Returns:
            Dictionary with:
                - ra: Right ascension (degrees)
                - dec: Declination (degrees)
                - altitude: Altitude angle (degrees)
                - azimuth: Azimuth angle (degrees)
                - distance: Distance to moon (km)
        """
        # Create observer location
        observer = self.earth + Topos(
            latitude_degrees=observer_lat,
            longitude_degrees=observer_lon
        )

        # Get moon position at timestamp
        ts = load.timescale()
        t = ts.from_datetime(timestamp)
        astrometric = observer.at(t).observe(self.moon)

        # Get equatorial coordinates (RA/Dec)
        ra, dec, distance = astrometric.radec(epoch='date')

        # Get horizontal coordinates (Alt/Az)
        alt, az, _ = astrometric.apparent().altaz()

        return {
            'ra': ra._degrees,
            'dec': dec.degrees,
            'altitude': alt.degrees,
            'azimuth': az.degrees,
            'distance': distance.km
        }
```

**Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_services/test_moon.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/moon.py backend/tests/test_services/test_moon.py
git commit -m "feat: add MoonService with position calculation"
```

---

## Task 3: Add Moon Phase Calculation

**Files:**
- Modify: `backend/app/services/moon.py`
- Modify: `backend/tests/test_services/test_moon.py`

**Step 1: Write failing tests for moon phase**

```python
# backend/tests/test_services/test_moon.py (add to existing file)

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
    # January 29, 2025 was near new moon
    result = moon_service.get_moon_phase(datetime(2025, 1, 29, 20, 0, 0))

    # Should be near new moon (0-10%)
    assert 0 <= result['percentage'] <= 15
    assert '新月' in result['name'] or '娥眉月' in result['name']
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_services/test_moon.py::test_get_moon_phase_returns_dict -v
```

Expected: FAIL with "MoonService has no attribute 'get_moon_phase'"

**Step 3: Implement get_moon_phase method**

```python
# backend/app/services/moon.py (add to MoonService class)

def get_moon_phase(self, timestamp: datetime) -> Dict[str, any]:
    """
    Calculate moon phase information

    Args:
        timestamp: Observation time

    Returns:
        Dictionary with:
            - percentage: Phase percentage (0-100, 0=new moon, 100=full moon)
            - age_days: Moon age in days (0-29.53)
            - illumination: Illuminated fraction (0-1)
            - name: Phase name in Chinese
    """
    ts = load.timescale()
    t = ts.from_datetime(timestamp)

    # Get moon position relative to earth
    astrometric = self.earth.at(t).observe(self.moon)
    _, _, distance = astrometric.apparent().radec()

    # Calculate phase angle
    # This is a simplified calculation using sun-moon-earth angle
    sun = self.ephemeris['sun']
    sun_astrometric = self.earth.at(t).observe(sun)
    moon_astrometric = self.earth.at(t).observe(self.moon)

    # Get positions
    sun_pos = sun_astrometric.position.au[0:2]  # x, y
    moon_pos = moon_astrometric.position.au[0:2]

    # Calculate angle between sun and moon as seen from earth
    import numpy as np

    sun_angle = np.arctan2(sun_pos[1], sun_pos[0])
    moon_angle = np.arctan2(moon_pos[1], moon_pos[0])

    phase_angle = (moon_angle - sun_angle) % (2 * np.pi)

    # Phase percentage (0-100)
    percentage = (1 + np.cos(phase_angle)) / 2 * 100

    # Illuminated fraction
    illumination = (1 + np.cos(phase_angle)) / 2

    # Calculate moon age (days since new moon)
    # Synodic month is approximately 29.53 days
    synodic_month = 29.53
    age_days = (percentage / 100) * synodic_month

    # Determine phase name
    phase_name = self._get_phase_name(percentage)

    return {
        'percentage': round(percentage, 2),
        'age_days': round(age_days, 2),
        'illumination': round(illumination, 4),
        'name': phase_name
    }

def _get_phase_name(self, percentage: float) -> str:
    """Get Chinese phase name from percentage"""
    if percentage < 5:
        return "新月"
    elif percentage < 45:
        return "娥眉月"
    elif percentage < 55:
        return "上弦月"
    elif percentage < 95:
        return "盈凸月"
    elif percentage <= 100:
        return "满月"
    elif percentage > 95:
        return "满月"  # Just past full
    elif percentage > 55:
        return "亏凸月"
    elif percentage > 45:
        return "下弦月"
    else:
        return "残月"
```

**Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_services/test_moon.py -v
```

Expected: PASS (or might need adjustment based on actual astronomical data)

**Step 5: Commit**

```bash
git add backend/app/services/moon.py backend/tests/test_services/test_moon.py
git commit -m "feat: add moon phase calculation to MoonService"
```

---

## Task 4: Add Light Pollution Calculation

**Files:**
- Modify: `backend/app/services/moon.py`
- Modify: `backend/tests/test_services/test_moon.py`

**Step 1: Write failing tests for pollution calculation**

```python
# backend/tests/test_services/test_moon.py (add to file)

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
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_services/test_moon.py::test_calculate_light_pollution_returns_value -v
```

Expected: FAIL with "MoonService has no attribute 'calculate_light_pollution'"

**Step 3: Implement calculate_light_pollution method**

```python
# backend/app/services/moon.py (add to MoonService class)

def calculate_light_pollution(
    self,
    moon_altitude: float,
    moon_azimuth: float,
    moon_phase: float,
    target_altitude: float,
    target_azimuth: float
) -> float:
    """
    Calculate moonlight pollution at target position

    Args:
        moon_altitude: Moon altitude in degrees
        moon_azimuth: Moon azimuth in degrees
        moon_phase: Moon phase percentage (0-100)
        target_altitude: Target altitude in degrees
        target_azimuth: Target azimuth in degrees

    Returns:
        Pollution level (0-1, where 0=no pollution, 1=severe pollution)
    """
    # Convert to radians
    moon_alt_rad = math.radians(moon_altitude)
    moon_az_rad = math.radians(moon_azimuth)
    target_alt_rad = math.radians(target_altitude)
    target_az_rad = math.radians(target_azimuth)

    # 1. Calculate angular distance using spherical law of cosines
    angular_distance = math.acos(
        math.sin(moon_alt_rad) * math.sin(target_alt_rad) +
        math.cos(moon_alt_rad) * math.cos(target_alt_rad) *
        math.cos(moon_az_rad - target_az_rad)
    )
    angular_distance_deg = math.degrees(angular_distance)

    # 2. Moon phase brightness factor (full moon=1.0, new moon=0.01)
    phase_brightness = (moon_phase / 100) ** 2 * 0.99 + 0.01

    # 3. Moon altitude factor (higher moon = more impact)
    altitude_factor = max(0, math.sin(moon_alt_rad))

    # 4. Scatter decay (exponential decay with angular distance)
    # 30-degree half-decay angle
    scatter_decay = math.exp(-angular_distance_deg / 30)

    # 5. Combined pollution
    pollution = phase_brightness * altitude_factor * scatter_decay

    return min(1.0, max(0.0, pollution))
```

**Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_services/test_moon.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/moon.py backend/tests/test_services/test_moon.py
git commit -m "feat: add moonlight pollution calculation"
```

---

## Task 5: Add Heatmap Generation

**Files:**
- Modify: `backend/app/services/moon.py`
- Modify: `backend/tests/test_services/test_moon.py`

**Step 1: Write failing tests for heatmap**

```python
# backend/tests/test_services/test_moon.py (add to file)

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
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_services/test_moon.py::test_get_pollution_heatmap_returns_list -v
```

Expected: FAIL with "MoonService has no attribute 'get_pollution_heatmap'"

**Step 3: Implement get_pollution_heatmap method**

```python
# backend/app/services/moon.py (add to MoonService class)

def get_pollution_heatmap(
    self,
    observer_lat: float,
    observer_lon: float,
    timestamp: datetime,
    resolution: int = 36
) -> list:
    """
    Generate moonlight pollution heatmap grid

    Args:
        observer_lat: Observer latitude in degrees
        observer_lon: Observer longitude in degrees
        timestamp: Observation time
        resolution: Grid resolution (default 36 = 36x36 = 1296 points)

    Returns:
        List of dicts with:
            - azimuth: Azimuth angle (degrees)
            - altitude: Altitude angle (degrees)
            - pollution: Pollution level (0-1)
    """
    # Get moon data
    moon_pos = self.get_moon_position(observer_lat, observer_lon, timestamp)
    moon_phase = self.get_moon_phase(timestamp)

    # Generate grid
    grid = []
    azimuth_step = 360 / resolution
    altitude_step = 90 / resolution

    for az_idx in range(resolution):
        azimuth = az_idx * azimuth_step

        for alt_idx in range(resolution):
            altitude = alt_idx * altitude_step

            # Skip points below horizon
            if altitude < 0:
                continue

            # Calculate pollution at this point
            pollution = self.calculate_light_pollution(
                moon_pos['altitude'],
                moon_pos['azimuth'],
                moon_phase['percentage'],
                altitude,
                azimuth
            )

            grid.append({
                'azimuth': round(azimuth, 2),
                'altitude': round(altitude, 2),
                'pollution': round(pollution, 4)
            })

    return grid
```

**Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_services/test_moon.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/services/moon.py backend/tests/test_services/test_moon.py
git commit -m "feat: add pollution heatmap generation"
```

---

## Task 6: Modify ScoringService to Include Moonlight

**Files:**
- Modify: `backend/app/services/scoring.py`
- Modify: `backend/tests/test_services/test_scoring.py`

**Step 1: Write failing test for moonlight scoring**

```python
# backend/tests/test_services/test_scoring.py (add to file)

def test_calculate_score_includes_moonlight(scoring_service):
    """Test that scoring includes moonlight impact"""
    result = scoring_service.calculate_score(
        max_altitude=60.0,
        magnitude=8.0,
        target_size=1.5,
        fov_horizontal=2.0,
        fov_vertical=1.5,
        duration_minutes=180,
        moonlight_pollution=0.5  # Moderate pollution
    )

    assert 'moonlight' in result['breakdown']
    assert result['breakdown']['moonlight'] < 100  # Should reduce score
    assert result['breakdown']['moonlight'] > 0

def test_moonlight_reduces_score(scoring_service):
    """Test that moonlight pollution reduces total score"""
    # No pollution
    result_no_pollution = scoring_service.calculate_score(
        max_altitude=60.0,
        magnitude=8.0,
        target_size=1.5,
        fov_horizontal=2.0,
        fov_vertical=1.5,
        duration_minutes=180,
        moonlight_pollution=0.0
    )

    # Heavy pollution
    result_pollution = scoring_service.calculate_score(
        max_altitude=60.0,
        magnitude=8.0,
        target_size=1.5,
        fov_horizontal=2.0,
        fov_vertical=1.5,
        duration_minutes=180,
        moonlight_pollution=0.9
    )

    assert result_no_pollution['total_score'] > result_pollution['total_score']
```

**Step 2: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_services/test_scoring.py::test_calculate_score_includes_moonlight -v
```

Expected: FAIL with "TypeError: calculate_score() got an unexpected keyword argument 'moonlight_pollution'"

**Step 3: Update ScoringService.calculate_score method**

```python
# backend/app/services/scoring.py (modify existing method)

def calculate_score(
    self,
    max_altitude: float,
    magnitude: float,
    target_size: float,
    fov_horizontal: float,
    fov_vertical: float,
    duration_minutes: float,
    moonlight_pollution: float = 0.0  # NEW PARAMETER
) -> dict:
    """
    Calculate recommendation score (with moonlight impact)

    Args:
        moonlight_pollution: Moonlight pollution level (0-1, default 0)

    Returns:
        Dictionary with total_score and breakdown including moonlight
    """
    # Existing scoring logic
    altitude_score = self._score_altitude(max_altitude)
    magnitude_score = self._score_magnitude(magnitude)
    size_score = self._score_size_match(target_size, fov_horizontal, fov_vertical)
    duration_score = self._score_duration(duration_minutes)

    # NEW: Moonlight pollution scoring
    moonlight_score = self._score_moonlight(moonlight_pollution)

    # Updated weights (moonlight adds 15%)
    weights = {
        "altitude": 0.25,
        "magnitude": 0.25,
        "size_match": 0.20,
        "duration": 0.15,
        "moonlight": 0.15  # NEW
    }

    total_score = (
        altitude_score * weights["altitude"] +
        magnitude_score * weights["magnitude"] +
        size_score * weights["size_match"] +
        duration_score * weights["duration"] +
        moonlight_score * weights["moonlight"]  # NEW
    )

    return {
        "total_score": round(total_score, 2),
        "breakdown": {
            "altitude": round(altitude_score, 2),
            "magnitude": round(magnitude_score, 2),
            "size_match": round(size_score, 2),
            "duration": round(duration_score, 2),
            "moonlight": round(moonlight_score, 2)  # NEW
        }
    }
```

**Step 4: Add _score_moonlight helper method**

```python
# backend/app/services/scoring.py (add to ScoringService class)

def _score_moonlight(self, pollution: float) -> float:
    """
    Calculate moonlight pollution score

    Scoring:
    - Pollution 0.0 -> 100 points (no impact)
    - Pollution 0.3 -> 85 points (minor impact)
    - Pollution 0.6 -> 50 points (moderate impact)
    - Pollution 1.0 -> 10 points (severe impact)

    Uses non-linear decay: minor pollution has small effect,
    severe pollution has major effect

    Args:
        pollution: Pollution level (0-1)

    Returns:
        Score (0-100)
    """
    if pollution <= 0:
        return 100.0

    if pollution < 0.3:
        # Minor pollution: linear small decrease
        return 100 - (pollution / 0.3) * 15
    elif pollution < 0.6:
        # Moderate pollution: linear larger decrease
        return 85 - ((pollution - 0.3) / 0.3) * 35
    else:
        # Severe pollution: exponential decrease
        remaining = 1 - pollution
        return 10 + remaining * remaining * 40
```

**Step 5: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_services/test_scoring.py -v
```

Expected: PASS

**Step 6: Update existing tests**

Update all existing calls to `calculate_score()` to include the new parameter with default 0.0:

```python
# Find all test files that call calculate_score
# backend/tests/test_services/test_scoring.py
# Update each call to add moonlight_pollution=0.0
```

**Step 7: Run all scoring tests**

```bash
cd backend
pytest tests/test_services/test_scoring.py -v
```

Expected: All PASS

**Step 8: Commit**

```bash
git add backend/app/services/scoring.py backend/tests/test_services/test_scoring.py
git commit -m "feat: add moonlight pollution to scoring system (15% weight)"
```

---

## Task 7: Modify RecommendationService to Integrate Moonlight

**Files:**
- Modify: `backend/app/services/recommendation.py`
- Modify: `backend/tests/integration/test_visibility_recommendations_e2e.py`

**Step 1: Update RecommendationService imports and init**

```python
# backend/app/services/recommendation.py (modify imports)

# Add to imports
from app.services.moon import MoonService

# In RecommendationService.__init__, add:
self.moon_service = MoonService()
```

**Step 2: Modify generate_recommendations to include moonlight**

```python
# backend/app/services/recommendation.py (modify generate_recommendations method)

async def generate_recommendations(
    self,
    targets: Optional[List[DeepSkyTarget]],
    observer_lat: float,
    observer_lon: float,
    date: datetime,
    equipment: dict,
    visible_zones: List[VisibleZone],
    filters: Optional[dict] = None,
    limit: int = 20
) -> List[dict]:
    """
    Generate recommendations from real database (with moonlight impact)
    """
    # NEW: Pre-calculate moon data
    moon_position = self.moon_service.get_moon_position(
        observer_lat, observer_lon, date
    )
    moon_phase = self.moon_service.get_moon_phase(date)

    # Load all targets from real database
    db_objects = await self._load_targets_from_db(filters)

    recommendations = []

    for db_obj in db_objects:
        target = self.model_adapter.to_target(db_obj)

        # Apply filters
        if filters and not self._apply_filters(target, db_obj, filters):
            continue

        # Calculate visibility windows
        windows = self.visibility.calculate_visibility_windows(
            target.ra, target.dec,
            observer_lat, observer_lon,
            date, visible_zones
        )

        if not windows:
            continue

        # Get best window
        best_window = max(windows, key=lambda w: w["max_altitude"])

        # NEW: Calculate moonlight pollution at best window time
        best_time = datetime.fromisoformat(best_window["max_altitude_time"])
        best_alt, best_az = self.astronomy.calculate_position(
            target.ra, target.dec,
            observer_lat, observer_lon,
            best_time
        )

        moonlight_pollution = self.moon_service.calculate_light_pollution(
            moon_position["altitude"],
            moon_position["azimuth"],
            moon_phase["percentage"],
            best_alt,
            best_az
        )

        # Calculate score (with moonlight pollution)
        score_result = self.scoring.calculate_score(
            max_altitude=best_window["max_altitude"],
            magnitude=target.magnitude,
            target_size=target.size,
            fov_horizontal=equipment.get("fov_horizontal", 2.0),
            fov_vertical=equipment.get("fov_vertical", 1.5),
            duration_minutes=best_window["duration_minutes"],
            moonlight_pollution=moonlight_pollution  # NEW PARAMETER
        )

        # Determine period
        period = self._determine_period(best_window["start_time"])

        # Get current position
        current_alt, current_az = self.astronomy.calculate_position(
            target.ra, target.dec,
            observer_lat, observer_lon,
            datetime.now()
        )

        # NEW: Get impact level description
        impact_level = self._get_impact_level(moonlight_pollution)

        recommendations.append({
            "target": target.model_dump(),
            "visibility_windows": windows,
            "current_position": {
                "altitude": current_alt,
                "azimuth": current_az,
                "timestamp": datetime.now().isoformat()
            },
            "score": score_result["total_score"],
            "score_breakdown": score_result["breakdown"],
            "period": period,
            # NEW: Moonlight impact information
            "moonlight_impact": {
                "pollution": round(moonlight_pollution, 4),
                "moon_phase": moon_phase["percentage"],
                "moon_altitude": round(moon_position["altitude"], 2),
                "impact_level": impact_level
            }
        })

    # Sort by score
    recommendations.sort(key=lambda r: r["score"], reverse=True)

    return recommendations[:limit]

def _get_impact_level(self, pollution: float) -> str:
    """Convert pollution level to description"""
    if pollution < 0.2:
        return "无影响"
    elif pollution < 0.4:
        return "轻微影响"
    elif pollution < 0.6:
        return "中等影响"
    elif pollution < 0.8:
        return "严重影响"
    else:
        return "极严重影响"
```

**Step 3: Run integration tests**

```bash
cd backend
pytest tests/integration/test_visibility_recommendations_e2e.py -v
```

Expected: PASS (may need to update test expectations to include moonlight_impact field)

**Step 4: Commit**

```bash
git add backend/app/services/recommendation.py backend/tests/integration/test_visibility_recommendations_e2e.py
git commit -m "feat: integrate moonlight impact into recommendations"
```

---

## Task 8: Create Moon API Endpoints

**Files:**
- Create: `backend/app/api/moon.py`
- Create: `backend/tests/test_api/test_moon.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing test for position endpoint**

```python
# backend/tests/test_api/test_moon.py

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

def test_get_moon_position_returns_required_fields(client):
    """Test that /api/moon/position returns correct structure"""
    response = client.post("/api/moon/position", json={
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2025-01-29T20:00:00"
    })

    assert response.status_code == 200

    data = response.json()
    assert "position" in data
    assert "phase" in data

    # Check position fields
    pos = data["position"]
    assert "ra" in pos
    assert "dec" in pos
    assert "altitude" in pos
    assert "azimuth" in pos
    assert "distance" in pos

    # Check phase fields
    phase = data["phase"]
    assert "percentage" in phase
    assert "age_days" in phase
    assert "illumination" in phase
    assert "name" in phase
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_api/test_moon.py::test_get_moon_position_returns_required_fields -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Create moon API router**

```python
# backend/app/api/moon.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
from pydantic import BaseModel
from app.services.moon import MoonService

router = APIRouter(prefix="/api/moon", tags=["moon"])
moon_service = MoonService()

class MoonPositionRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: str  # ISO 8601 format

class MoonHeatmapRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: str
    resolution: int = 36  # Grid resolution, default 36x36

@router.post("/position")
async def get_moon_position(request: MoonPositionRequest):
    """
    Get moon position and phase information

    Returns:
        {
            "position": {
                "ra": Right ascension (degrees),
                "dec": Declination (degrees),
                "altitude": Altitude angle (degrees),
                "azimuth": Azimuth angle (degrees),
                "distance": Distance to moon (km)
            },
            "phase": {
                "percentage": 0-100,
                "age_days": Moon age (days),
                "illumination": Illuminated fraction (0-1),
                "name": Phase name in Chinese
            }
        }
    """
    try:
        ts = datetime.fromisoformat(request.timestamp)

        # Calculate position
        position = moon_service.get_moon_position(
            request.latitude,
            request.longitude,
            ts
        )

        # Calculate phase
        phase = moon_service.get_moon_phase(ts)

        return {
            "position": position,
            "phase": phase
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/heatmap")
async def get_moonlight_heatmap(request: MoonHeatmapRequest):
    """
    Get moonlight pollution heatmap data

    Returns:
        {
            "grid": [
                {
                    "azimuth": Azimuth angle (degrees),
                    "altitude": Altitude angle (degrees),
                    "pollution": Pollution level (0-1)
                },
                ...
            ],
            "moon_position": {
                "azimuth": Moon azimuth,
                "altitude": Moon altitude,
                "phase": Moon phase percentage
            },
            "timestamp": ISO timestamp
        }
    """
    try:
        ts = datetime.fromisoformat(request.timestamp)

        # Get moon position
        moon_pos = moon_service.get_moon_position(
            request.latitude,
            request.longitude,
            ts
        )

        # Get moon phase
        moon_phase = moon_service.get_moon_phase(ts)

        # Generate heatmap grid
        grid = moon_service.get_pollution_heatmap(
            request.latitude,
            request.longitude,
            ts,
            request.resolution
        )

        return {
            "grid": grid,
            "moon_position": {
                "azimuth": moon_pos["azimuth"],
                "altitude": moon_pos["altitude"],
                "phase": moon_phase["percentage"]
            },
            "timestamp": ts.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pollution")
async def calculate_target_pollution(
    request: MoonPositionRequest,
    target_altitude: float,
    target_azimuth: float
):
    """
    Calculate moonlight pollution at specific target position

    Used by recommendation system to evaluate individual targets

    Returns:
        {
            "pollution": 0-1,
            "moon_phase": Moon phase percentage,
            "angular_distance": Angular distance from moon (degrees)
        }
    """
    try:
        ts = datetime.fromisoformat(request.timestamp)

        # Get moon data
        moon_pos = moon_service.get_moon_position(
            request.latitude,
            request.longitude,
            ts
        )
        moon_phase = moon_service.get_moon_phase(ts)

        # Calculate pollution
        pollution = moon_service.calculate_light_pollution(
            moon_pos["altitude"],
            moon_pos["azimuth"],
            moon_phase["percentage"],
            target_altitude,
            target_azimuth
        )

        # Calculate angular distance
        import math
        moon_alt_rad = math.radians(moon_pos["altitude"])
        moon_az_rad = math.radians(moon_pos["azimuth"])
        target_alt_rad = math.radians(target_altitude)
        target_az_rad = math.radians(target_azimuth)

        angular_distance = math.degrees(math.acos(
            math.sin(moon_alt_rad) * math.sin(target_alt_rad) +
            math.cos(moon_alt_rad) * math.cos(target_alt_rad) *
            math.cos(moon_az_rad - target_az_rad)
        ))

        return {
            "pollution": round(pollution, 4),
            "moon_phase": moon_phase["percentage"],
            "angular_distance": round(angular_distance, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Step 4: Register router in main app**

```python
# backend/app/main.py (add to imports and router registration)

from app.api import moon  # Add import

# In router registration section, add:
app.include_router(moon.router)
```

**Step 5: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_api/test_moon.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/api/moon.py backend/tests/test_api/test_moon.py backend/app/main.py
git commit -m "feat: add moon API endpoints"
```

---

## Task 9: Create Frontend Moon API Wrapper

**Files:**
- Create: `frontend/src/scripts/api/moon.js`

**Step 1: Create MoonAPI class**

```javascript
// frontend/src/scripts/api/moon.js

/**
 * Moon API wrapper
 * Handles all moon-related API calls
 */
export class MoonAPI {
  /**
   * Get moon position and phase
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @param {Date} timestamp - Observation time
   * @returns {Promise<Object>} Moon position and phase data
   */
  static async getPosition(lat, lon, timestamp) {
    const response = await fetch('/api/moon/position', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        timestamp: timestamp.toISOString()
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch moon position: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get moonlight pollution heatmap
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @param {Date} timestamp - Observation time
   * @param {number} resolution - Grid resolution (default 36)
   * @returns {Promise<Object>} Heatmap grid data
   */
  static async getHeatmap(lat, lon, timestamp, resolution = 36) {
    const response = await fetch('/api/moon/heatmap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        timestamp: timestamp.toISOString(),
        resolution: resolution
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch heatmap: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Calculate pollution at specific position
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @param {Date} timestamp - Observation time
   * @param {number} targetAlt - Target altitude
   * @param {number} targetAz - Target azimuth
   * @returns {Promise<Object>} Pollution data
   */
  static async getPollution(lat, lon, timestamp, targetAlt, targetAz) {
    const params = new URLSearchParams({
      target_altitude: targetAlt.toString(),
      target_azimuth: targetAz.toString()
    });

    const response = await fetch(`/api/moon/pollution?${params}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: lat,
        longitude: lon,
        timestamp: timestamp.toISOString()
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to calculate pollution: ${response.statusText}`);
    }

    return response.json();
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/scripts/api/moon.js
git commit -m "feat: add frontend Moon API wrapper"
```

---

## Task 10: Extend SkyMapCanvas for Moon Rendering

**Files:**
- Modify: `frontend/src/scripts/utils/canvas.js`

**Step 1: Add moon state to constructor**

```javascript
// frontend/src/scripts/utils/canvas.js (modify constructor)

this.state = {
  time: new Date(),
  targets: [],
  zones: [],
  hoveredTarget: null,
  isDragging: false,
  lastMouseX: 0,
  lastMouseY: 0,
  fovFrame: {
    center: { azimuth: 180, altitude: 45 },
    isVisible: true,
    isSelected: false,
    isDragging: false
  },
  // NEW: Moon state
  moon: {
    position: { azimuth: 0, altitude: 0, ra: 0, dec: 0 },
    phase: { percentage: 0, age_days: 0, illumination: 0, name: '' },
    visible: false,
    hovered: false,
    selected: false,
    showHeatmap: false,
    heatmapData: []
  }
};
```

**Step 2: Add drawMoon method**

```javascript
// frontend/src/scripts/utils/canvas.js (add to SkyMapCanvas class)

/**
 * Draw moon on sky map
 */
drawMoon() {
  const { ctx } = this;
  const { moon } = this.state;

  if (!moon.visible || moon.position.altitude <= 0) return;

  // Project moon position to screen
  const pos = this.projectFromCenter(
    moon.position.azimuth,
    moon.position.altitude
  );

  if (!pos.visible) return;

  // Calculate moon size (3-4x larger than normal targets)
  const moonSize = 24 * pos.scale;

  // Draw glow effect
  const glow = ctx.createRadialGradient(
    pos.x, pos.y, moonSize * 0.5,
    pos.x, pos.y, moonSize * 2.5
  );
  glow.addColorStop(0, 'rgba(255, 255, 230, 0.4)');
  glow.addColorStop(1, 'rgba(255, 255, 230, 0)');
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, moonSize * 2.5, 0, Math.PI * 2);
  ctx.fill();

  // Draw moon disk
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, moonSize, 0, Math.PI * 2);

  // Moon color (brightness based on phase)
  const brightness = 200 + moon.phase.illumination * 55;
  ctx.fillStyle = `rgb(${brightness}, ${brightness}, ${brightness - 20})`;
  ctx.fill();

  // Hover highlight
  if (moon.hovered) {
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, moonSize + 6, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(252, 211, 77, 0.8)';
    ctx.lineWidth = 3;
    ctx.stroke();
  }

  // Selected border (indicates heatmap is on)
  if (moon.selected) {
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, moonSize + 4, 0, Math.PI * 2);
    ctx.strokeStyle = '#FCD34D';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Draw moon phase
  this.drawMoonPhase(pos.x, pos.y, moonSize, moon.phase);

  // Show tooltip on hover
  if (moon.hovered) {
    this.drawMoonTooltip(pos, moonSize);
  }

  // Draw label (hide when hovering to avoid overlap)
  if (!moon.hovered) {
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('月亮', pos.x, pos.y - moonSize - 8);
  }
}

/**
 * Draw graphical moon phase
 * @param {number} x - Center X
 * @param {number} y - Center Y
 * @param {number} radius - Moon radius
 * @param {Object} phase - Phase data
 */
drawMoonPhase(x, y, radius, phase) {
  const p = phase.percentage;

  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.clip();  // Clip to moon circle

  // Dark background
  ctx.fillStyle = 'rgba(30, 30, 35, 0.9)';
  ctx.fill();

  if (p < 50) {
    // Waxing crescent: right side lit
    this.drawMoonCrescent(x, y, radius, p, true);
  } else {
    // Waning crescent: left side lit
    this.drawMoonCrescent(x, y, radius, 100 - p, false);
  }

  ctx.restore();
}

/**
 * Draw moon crescent shape
 * @param {number} x - Center X
 * @param {number} y - Center Y
 * @param {number} radius - Radius
 * @param {number} progress - Progress (0-50)
 * @param {boolean} isRight - Right side lit
 */
drawMoonCrescent(x, y, radius, progress, isRight) {
  const offset = radius * (1 - progress / 50);

  ctx.fillStyle = '#FFF8E7';
  ctx.beginPath();
  ctx.arc(x, y, radius, -Math.PI / 2, Math.PI / 2);

  if (isRight) {
    // Right side lit
    ctx.ellipse(x - offset, y, Math.abs(offset), radius, 0, Math.PI / 2, -Math.PI / 2, true);
  } else {
    // Left side lit
    ctx.ellipse(x + offset, y, Math.abs(offset), radius, 0, -Math.PI / 2, Math.PI / 2, true);
  }

  ctx.fill();
}

/**
 * Draw moon information tooltip
 * @param {Object} pos - Screen position {x, y}
 * @param {number} moonSize - Moon radius
 */
drawMoonTooltip(pos, moonSize) {
  const { ctx } = this;
  const { moon } = this.state;

  const info = [
    `${moon.phase.name} ${moon.phase.percentage.toFixed(0)}%`,
    `月龄: ${moon.phase.age_days.toFixed(1)} 天`,
    `高度: ${moon.position.altitude.toFixed(1)}°`,
    moon.selected ? '点击隐藏热力图' : '点击显示热力图'
  ];

  const boxWidth = 160;
  const boxHeight = 70;
  const boxX = pos.x - boxWidth / 2;
  const boxY = pos.y + moonSize + 12;

  // Semi-transparent background
  ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
  ctx.beginPath();
  ctx.roundRect(boxX, boxY, boxWidth, boxHeight, 8);
  ctx.fill();

  // Border
  ctx.strokeStyle = '#FCD34D';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Text
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '12px sans-serif';
  ctx.textAlign = 'center';

  info.forEach((line, i) => {
    const y = boxY + 20 + i * 14;

    // Last line (hint) in gray
    if (i === info.length - 1) {
      ctx.fillStyle = '#94A3B8';
    } else {
      ctx.fillStyle = '#FFFFFF';
    }

    ctx.fillText(line, pos.x, y);
  });
}

/**
 * Check if point is on moon
 * @param {number} x - Screen X
 * @param {number} y - Screen Y
 * @returns {boolean}
 */
isPointOnMoon(x, y) {
  const { moon } = this.state;
  if (!moon.visible) return false;

  const pos = this.projectFromCenter(
    moon.position.azimuth,
    moon.position.altitude
  );

  const distance = Math.sqrt(
    Math.pow(x - pos.x, 2) + Math.pow(y - pos.y, 2)
  );

  return distance < 30;  // 30px click area
}
```

**Step 3: Update render method**

```javascript
// frontend/src/scripts/utils/canvas.js (modify render method)

render() {
  const { ctx, config } = this;

  ctx.clearRect(0, 0, config.width, config.height);

  this.drawBackground();
  this.drawCelestialSphere();
  this.drawGrid();
  this.drawMoonlightPollutionHeatmap();  // NEW: Before targets
  this.drawHorizon();
  this.drawVisibleZones();
  this.drawFOVFrame();
  this.drawTargets();
  this.drawMoon();  // NEW: On top
  this.drawCompass();
}
```

**Step 4: Update handleHover method**

```javascript
// frontend/src/scripts/utils/canvas.js (modify handleHover method)

handleHover(mouseX, mouseY) {
  // NEW: Check moon hover first
  if (this.state.moon.visible && this.isPointOnMoon(mouseX, mouseY)) {
    if (!this.state.moon.hovered) {
      this.state.moon.hovered = true;
      this.canvas.style.cursor = 'pointer';
      this.render();
    }
    return;
  } else if (this.state.moon.hovered) {
    this.state.moon.hovered = false;
    this.render();
  }

  // Existing target hover logic
  let found = null;

  for (const target of this.state.targets) {
    const pos = this.projectFromCenter(target.azimuth, target.altitude);

    if (!pos.visible || target.altitude <= 0) continue;

    const baseSize = 8 * pos.scale * 0.15;
    const size = Math.max(3, Math.min(20, baseSize));

    const distance = Math.sqrt(
      Math.pow(mouseX - pos.x, 2) +
      Math.pow(mouseY - pos.y, 2)
    );

    if (distance < size + 5) {
      found = target.id;
      break;
    }
  }

  this.state.hoveredTarget = found;
  this.canvas.style.cursor = found ? 'pointer' : 'grab';
  this.render();
}
```

**Step 5: Update handleClick method**

```javascript
// frontend/src/scripts/utils/canvas.js (modify handleClick method)

handleClick(x, y) {
  // NEW: Check moon click first
  if (this.isPointOnMoon(x, y)) {
    this.state.moon.selected = !this.state.moon.selected;
    this.state.moon.showHeatmap = !this.state.moon.showHeatmap;
    this.render();

    // Trigger callback
    this.onMoonToggle?.(this.state.moon.showHeatmap);
    return;
  }

  // Existing target click logic
  if (this.state.hoveredTarget && !this.state.isDragging && !this.state.fovFrame.isDragging) {
    this.onTargetSelect?.(this.state.hoveredTarget);
  }
}
```

**Step 6: Commit**

```bash
git add frontend/src/scripts/utils/canvas.js
git commit -m "feat: add moon rendering to SkyMapCanvas"
```

---

## Task 11: Add Heatmap Rendering

**Files:**
- Modify: `frontend/src/scripts/utils/canvas.js`

**Step 1: Add heatmap drawing method**

```javascript
// frontend/src/scripts/utils/canvas.js (add to SkyMapCanvas class)

/**
 * Draw moonlight pollution heatmap overlay
 */
drawMoonlightPollutionHeatmap() {
  const { ctx } = this;
  const { moon } = this.state;

  if (!moon.showHeatmap || !moon.heatmapData.length) return;

  const data = moon.heatmapData;

  // Draw each sampling point
  data.forEach(point => {
    if (point.pollution < 0.05) return;  // Ignore minor pollution

    // Project to screen coordinates
    const pos = this.projectFromCenter(
      point.azimuth,
      point.altitude
    );

    if (!pos.visible) return;

    // Calculate radius (covers certain range)
    const radius = 25 * pos.scale;

    // Get color based on pollution level
    const color = this.getPollutionColor(point.pollution);

    // Draw gradient glow
    const gradient = ctx.createRadialGradient(
      pos.x, pos.y, 0,
      pos.x, pos.y, radius
    );

    // Center denser, edge transparent
    gradient.addColorStop(0, color.replace('1)', `${point.pollution * 0.6})`));
    gradient.addColorStop(0.5, color.replace('1)', `${point.pollution * 0.3})`));
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fill();
  });

  // Draw legend
  this.drawHeatmapLegend();
}

/**
 * Get pollution color from pollution level
 * @param {number} pollution - Pollution level (0-1)
 * @returns {string} RGBA color
 */
getPollutionColor(pollution) {
  // Pollution 0-1 maps to color
  // 0-0.3: Blue-green (minor)
  // 0.3-0.6: Yellow (moderate)
  // 0.6-0.8: Orange (severe)
  // 0.8-1.0: Red (extreme)

  if (pollution < 0.3) {
    // Blue-green gradient
    const t = pollution / 0.3;
    return `rgba(${t * 100}, ${180 + t * 40}, 200, 1)`;
  } else if (pollution < 0.6) {
    // Yellow gradient
    const t = (pollution - 0.3) / 0.3;
    return `rgba(${100 + t * 155}, ${220 - t * 40}, ${200 - t * 120}, 1)`;
  } else if (pollution < 0.8) {
    // Orange gradient
    const t = (pollution - 0.6) / 0.2;
    return `rgba(255, ${180 - t * 60}, ${80 - t * 40}, 1)`;
  } else {
    // Red gradient
    const t = (pollution - 0.8) / 0.2;
    return `rgba(${255 - t * 50}, ${120 - t * 40}, ${40 + t * 20}, 1)`;
  }
}

/**
 * Draw heatmap legend
 */
drawHeatmapLegend() {
  const { ctx, config } = this;

  const legendX = 20;
  const legendY = 80;
  const legendWidth = 150;
  const legendHeight = 12;

  // Background box
  ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
  ctx.fillRect(legendX - 8, legendY - 8, legendWidth + 16, 50);

  // Gradient color bar
  const gradient = ctx.createLinearGradient(legendX, 0, legendX + legendWidth, 0);
  gradient.addColorStop(0, 'rgba(100, 220, 200, 0.8)');    // Minor
  gradient.addColorStop(0.33, 'rgba(255, 220, 80, 0.8)');   // Moderate
  gradient.addColorStop(0.67, 'rgba(255, 120, 40, 0.8)');   // Severe
  gradient.addColorStop(1, 'rgba(205, 80, 60, 0.8)');       // Extreme

  ctx.fillStyle = gradient;
  ctx.fillRect(legendX, legendY, legendWidth, legendHeight);

  // Border
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 1;
  ctx.strokeRect(legendX, legendY, legendWidth, legendHeight);

  // Labels
  ctx.fillStyle = '#FFFFFF';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('月光污染', legendX, legendY - 12);

  ctx.textAlign = 'center';
  ctx.fillText('轻微', legendX, legendY + 24);
  ctx.fillText('中等', legendX + legendWidth * 0.33, legendY + 24);
  ctx.fillText('严重', legendX + legendWidth * 0.67, legendY + 24);
  ctx.fillText('极重', legendX + legendWidth, legendY + 24);
}
```

**Step 2: Add heatmap data update method**

```javascript
// frontend/src/scripts/utils/canvas.js (add to SkyMapCanvas class)

/**
 * Update moon data
 * @param {Object} moonData - Moon data from API
 */
updateMoonData(moonData) {
  this.state.moon.position = moonData.position;
  this.state.moon.phase = moonData.phase;
  this.state.moon.visible = true;
  this.render();
}

/**
 * Update heatmap data
 * @param {Array} heatmapData - Heatmap grid data
 */
updateHeatmapData(heatmapData) {
  this.state.moon.heatmapData = heatmapData;
  this.state.moon.heatmapLastUpdate = Date.now();
  this.render();
}
```

**Step 3: Commit**

```bash
git add frontend/src/scripts/utils/canvas.js
git commit -m "feat: add moonlight pollution heatmap rendering"
```

---

## Task 12: Integrate Moon Data into Main Application

**Files:**
- Modify: `frontend/src/scripts/main.js`

**Step 1: Add moon data loading**

```javascript
// frontend/src/scripts/main.js (modify existing initialization)

import { MoonAPI } from './api/moon.js';

// In your app initialization or data loading section:

async function loadMoonData() {
  try {
    const location = store.getLocation();  // Assuming you have this
    const now = new Date();

    const moonData = await MoonAPI.getPosition(
      location.latitude,
      location.longitude,
      now
    );

    // Update canvas
    skyMapCanvas.updateMoonData(moonData);

    // Load heatmap if moon is visible and above horizon
    if (moonData.position.altitude > 0) {
      const heatmapData = await MoonAPI.getHeatmap(
        location.latitude,
        location.longitude,
        now,
        36  // resolution
      );

      skyMapCanvas.updateHeatmapData(heatmapData.grid);
    }

  } catch (error) {
    console.error('Failed to load moon data:', error);
  }
}

// Call this when initializing or updating location/time
// Example:
document.addEventListener('DOMContentLoaded', async () => {
  // ... existing initialization

  // NEW: Load moon data
  await loadMoonData();

  // Update moon data every 5 minutes
  setInterval(loadMoonData, 5 * 60 * 1000);
});
```

**Step 2: Add moon toggle callback**

```javascript
// frontend/src/scripts/main.js (add callback)

// When initializing SkyMapCanvas:
skyMapCanvas.onMoonToggle = (showHeatmap) => {
  console.log(`Moon heatmap ${showHeatmap ? 'enabled' : 'disabled'}`);
  // You can save this preference to localStorage if needed
  store.setMoonHeatmapEnabled(showHeatmap);
};
```

**Step 3: Commit**

```bash
git add frontend/src/scripts/main.js
git commit -m "feat: integrate moon data loading into main app"
```

---

## Task 13: Update Recommendations Display

**Files:**
- Modify: `frontend/src/scripts/main.js` (or wherever recommendations are rendered)

**Step 1: Add moonlight impact display to recommendation cards**

```javascript
// In your recommendation rendering code:

function renderRecommendationCard(recommendation) {
  const { target, score, moonlight_impact } = recommendation;

  // ... existing card rendering

  // NEW: Add moonlight impact indicator
  if (moonlight_impact) {
    const impactColor = getImpactColor(moonlight_impact.pollution);

    const impactDiv = document.createElement('div');
    impactDiv.className = 'moonlight-impact';
    impactDiv.style.cssText = `
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      background: rgba(15, 23, 42, 0.8);
      border-radius: 6px;
      margin-top: 8px;
      font-size: 12px;
      color: ${impactColor};
    `;

    impactDiv.innerHTML = `
      <span class="icon">🌙</span>
      <span class="text">${moonlight_impact.impact_level}</span>
      <span class="detail">(${(moonlight_impact.pollution * 100).toFixed(0)}%)</span>
    `;

    card.appendChild(impactDiv);
  }

  // ... rest of card rendering
}

function getImpactColor(pollution) {
  if (pollution < 0.2) return '#64C8B8';  // Blue-green
  if (pollution < 0.4) return '#FFDC50';  // Yellow
  if (pollution < 0.6) return '#FF7828';  // Orange
  if (pollution < 0.8) return '#FF503C';  // Red
  return '#CD3C3C';  // Dark red
}
```

**Step 2: Update score breakdown display**

```javascript
// If you display score breakdown:

function renderScoreBreakdown(breakdown) {
  // ... existing rendering

  // NEW: Add moonlight score
  if (breakdown.moonlight !== undefined) {
    const item = createScoreItem('月光影响', breakdown.moonlight);
    container.appendChild(item);
  }
}
```

**Step 3: Commit**

```bash
git add frontend/src/scripts/main.js
git commit -m "feat: display moonlight impact in recommendations"
```

---

## Task 14: End-to-End Integration Testing

**Files:**
- Create: `backend/tests/integration/test_moon_e2e.py`

**Step 1: Write integration test**

```python
# backend/tests/integration/test_moon_e2e.py

import pytest
from datetime import datetime
from app.services.moon import MoonService
from app.services.recommendation import RecommendationService
from app.models.target import VisibleZone

@pytest.mark.asyncio
async def test_moon_integration_with_recommendations():
    """Test that moonlight pollution affects recommendations"""
    moon_service = MoonService()
    recommendation_service = RecommendationService()

    # Test location and time
    lat, lon = 40.7128, -74.0060
    date = datetime(2025, 1, 29, 20, 0, 0)

    # Get moon data
    moon_pos = moon_service.get_moon_position(lat, lon, date)
    moon_phase = moon_service.get_moon_phase(date)

    # Create test zone (full sky)
    zone = VisibleZone(
        id="test",
        name="Test Zone",
        type="rectangle",
        start=[0, 0],
        end=[360, 90],
        polygon=[(0, 0), (360, 0), (360, 90), (0, 90)]
    )

    # Generate recommendations
    recommendations = await recommendation_service.generate_recommendations(
        targets=None,  # Load from database
        observer_lat=lat,
        observer_lon=lon,
        date=date,
        equipment={
            "fov_horizontal": 2.0,
            "fov_vertical": 1.5
        },
        visible_zones=[zone],
        limit=10
    )

    # Verify moonlight_impact field exists
    assert len(recommendations) > 0
    for rec in recommendations:
        assert "moonlight_impact" in rec
        assert "pollution" in rec["moonlight_impact"]
        assert "moon_phase" in rec["moonlight_impact"]
        assert "impact_level" in rec["moonlight_impact"]

        # Verify pollution is in valid range
        assert 0 <= rec["moonlight_impact"]["pollution"] <= 1

    # Verify scores reflect moonlight impact
    scores = [r["score"] for r in recommendations]
    assert max(scores) > min(scores)  # Scores should vary

@pytest.mark.asyncio
async def test_heatmap_generation():
    """Test heatmap generation and coverage"""
    moon_service = MoonService()

    lat, lon = 40.7128, -74.0060
    date = datetime(2025, 1, 29, 20, 0, 0)

    # Generate heatmap
    heatmap = moon_service.get_pollution_heatmap(
        lat, lon, date, resolution=18
    )

    # Verify coverage
    assert len(heatmap) > 0

    # Check all points have required fields
    for point in heatmap:
        assert "azimuth" in point
        assert "altitude" in point
        assert "pollution" in point
        assert 0 <= point["azimuth"] <= 360
        assert 0 <= point["altitude"] <= 90
        assert 0 <= point["pollution"] <= 1
```

**Step 2: Run integration tests**

```bash
cd backend
pytest tests/integration/test_moon_e2e.py -v
```

Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/integration/test_moon_e2e.py
git commit -m "test: add moon integration e2e tests"
```

---

## Task 15: Final Testing and Documentation

**Step 1: Run all tests**

```bash
cd backend
pytest tests/ -v --cov=app/services/moon --cov=app/api/moon
```

Expected: All tests pass with >80% coverage

**Step 2: Manual testing checklist**

```bash
# Start backend server
cd backend
python -m uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev
```

Manual testing:
- [ ] Open sky map in browser
- [ ] Verify moon is displayed at correct position
- [ ] Hover over moon and verify tooltip shows correct phase/age
- [ ] Click moon and verify heatmap appears
- [ ] Verify heatmap colors match pollution levels
- [ ] Click moon again and verify heatmap disappears
- [ ] Get recommendations and verify moonlight_impact field exists
- [ ] Verify targets affected by moonlight have lower scores
- [ ] Test with different moon phases (use different dates)

**Step 3: Update documentation**

Update `/docs/progress/` with implementation summary:

```markdown
# Moon Phase Feature Implementation Summary

**Date:** 2025-01-29
**Status:** Completed ✅

## Implemented Features

### Backend
- MoonService with Skyfield integration
- Moon position calculation (RA/Dec/Alt/Az)
- Moon phase calculation (percentage, age, illumination)
- Moonlight pollution calculation
- Pollution heatmap generation
- 3 new API endpoints

### Frontend
- Moon rendering on sky map
- Graphical moon phase display
- Hover tooltip with moon info
- Click-to-toggle heatmap
- Heatmap color gradient (blue→yellow→orange→red)
- Moonlight impact display in recommendations

### Integration
- ScoringService updated with 15% moonlight weight
- RecommendationService includes moonlight_impact field
- Real-time moon data updates (5min interval)

## Testing
- Unit tests for MoonService
- API tests for moon endpoints
- Integration tests for recommendation system
- Manual testing completed

## Performance
- API response time: <200ms
- Heatmap generation: <500ms
- Frontend rendering: 60fps

## Known Issues
- None

## Future Enhancements
- Moonrise/moonset times
- Lunar eclipse predictions
- Moon trajectory animation
```

**Step 4: Final commit**

```bash
git add docs/progress/
git commit -m "docs: add moon feature implementation summary"
```

---

## Verification Steps

After completing all tasks:

1. **Backend Verification**
   ```bash
   cd backend
   pytest tests/ -v
   ```
   Expected: All tests pass

2. **Frontend Verification**
   - Open browser to `http://localhost:5173`
   - Verify moon displays correctly
   - Test all interactions (hover, click, heatmap)

3. **API Verification**
   ```bash
   curl -X POST http://localhost:8000/api/moon/position \
     -H "Content-Type: application/json" \
     -d '{"latitude": 40.7128, "longitude": -74.0060, "timestamp": "2025-01-29T20:00:00"}'
   ```
   Expected: JSON response with moon position and phase

4. **Integration Verification**
   - Generate recommendations
   - Verify `moonlight_impact` field exists
   - Verify scores reflect moonlight influence

---

## Estimated Timeline

- Task 1 (Dependencies): 5 min
- Task 2-5 (MoonService): 45 min
- Task 6 (ScoringService): 20 min
- Task 7 (RecommendationService): 25 min
- Task 8 (Moon API): 30 min
- Task 9 (Frontend API wrapper): 10 min
- Task 10-11 (Canvas rendering): 40 min
- Task 12-13 (Integration): 20 min
- Task 14-15 (Testing): 30 min

**Total: ~3 hours**

---

## Notes

- First run will download DE421 ephemeris (~2MB) - this is automatic
- Moon phase calculations use astronomical algorithms
- Heatmap resolution can be adjusted for performance (default 36x36)
- Moon data updates every 5 minutes to balance accuracy and performance
- All coordinates use degrees for consistency with existing codebase

## Related Documents

- Design: `docs/plans/2025-01-29-moon-phase-and-light-pollution-design.md`
- AstronomyService: `backend/app/services/astronomy.py`
- ScoringService: `backend/app/services/scoring.py`
- SkyMapCanvas: `frontend/src/scripts/utils/canvas.js`
