# backend/app/services/moon.py
from datetime import datetime
from typing import Dict
from skyfield.api import load, Topos, utc
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
