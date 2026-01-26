# backend/app/models/database.py
"""Database models for deep sky objects"""
from pydantic import BaseModel
from typing import Optional, List

class ObservationalInfo(BaseModel):
    """Observational information for viewing guidance"""
    best_month: Optional[int] = None
    difficulty: Optional[str] = None  # 'EASY', 'MODERATE', 'DIFFICULT'
    min_aperture: Optional[float] = None  # mm
    min_magnitude: Optional[float] = None
    notes: Optional[str] = None

class DeepSkyObject(BaseModel):
    """Complete deep sky object data"""
    id: str
    name: str
    type: str  # 'GALAXY', 'NEBULA', 'CLUSTER', 'PLANETARY'
    ra: float  # Right Ascension in degrees
    dec: float  # Declination in degrees
    magnitude: Optional[float] = None
    size_major: Optional[float] = None  # arcminutes
    size_minor: Optional[float] = None  # arcminutes
    constellation: Optional[str] = None
    surface_brightness: Optional[float] = None
    aliases: List[str] = []
    observational_info: Optional[ObservationalInfo] = None

class DatabaseStats(BaseModel):
    """Database statistics"""
    total_objects: int
    objects_by_type: dict
    constellations_covered: int
