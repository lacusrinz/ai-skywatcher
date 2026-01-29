# backend/app/services/moon.py
from datetime import datetime
from typing import Dict
from skyfield.api import load, Topos, utc
import logging
import numpy as np
import math

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
        # Ensure timezone-aware datetime (assume UTC if naive)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=utc)

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
        # Ensure timezone-aware datetime (assume UTC if naive)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=utc)

        ts = load.timescale()
        t = ts.from_datetime(timestamp)

        # Get moon position relative to earth
        astrometric = self.earth.at(t).observe(self.moon)
        _, _, distance = astrometric.apparent().radec()

        # Calculate phase angle
        sun = self.ephemeris['sun']
        sun_astrometric = self.earth.at(t).observe(sun)
        moon_astrometric = self.earth.at(t).observe(self.moon)

        # Get positions
        sun_pos = sun_astrometric.position.au[0:2]  # x, y
        moon_pos = moon_astrometric.position.au[0:2]

        # Calculate angle between sun and moon as seen from earth
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
