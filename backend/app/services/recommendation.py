"""Recommendation engine service"""
from typing import List, Optional, Tuple
from datetime import datetime
from app.services.visibility import VisibilityService
from app.services.scoring import ScoringService
from app.services.astronomy import AstronomyService
from app.services.database import DatabaseService
from app.services.model_adapter import ModelAdapter
from app.services.moon import MoonService
from app.models.target import DeepSkyTarget, VisibleZone
from app.models.database import DeepSkyObject as DBDeepSkyObject


class RecommendationService:
    """Recommendation engine with real database support"""

    def __init__(self):
        self.visibility = VisibilityService()
        self.scoring = ScoringService()
        self.astronomy = AstronomyService()
        self.db_service = DatabaseService()  # NEW: Real database
        self.model_adapter = ModelAdapter()  # NEW: Model adapter
        self.moon = MoonService()  # NEW: Moon service

    async def generate_recommendations(
        self,
        targets: Optional[List[DeepSkyTarget]],  # DEPRECATED: Not used anymore
        observer_lat: float,
        observer_lon: float,
        date: datetime,
        equipment: dict,
        visible_zones: List[VisibleZone],
        filters: Optional[dict] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        Generate recommendations from real database

        Args:
            targets: IGNORED (kept for backward compatibility)
            observer_lat: Observer latitude
            observer_lon: Observer longitude
            date: Observation date
            equipment: Equipment parameters
            visible_zones: Visible zones
            filters: Filter conditions
            limit: Return limit

        Returns:
            List of recommendations
        """
        # Calculate moon data
        moon_data = self._calculate_moon_data(observer_lat, observer_lon, date)

        # Load all targets from real database
        db_objects = await self._load_targets_from_db(filters)

        recommendations = []

        for db_obj in db_objects:
            # Convert to API model
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

            # Calculate best window score
            best_window = max(windows, key=lambda w: w["max_altitude"])

            # Calculate moonlight pollution at best window
            moonlight_pollution = self._calculate_moonlight_pollution(
                observer_lat, observer_lon,
                target, best_window,
                moon_data, date
            )

            # Get current position at specified time
            current_alt, current_az = self.astronomy.calculate_position(
                target.ra, target.dec,
                observer_lat, observer_lon,
                date  # ✅ FIX: 使用传入的date参数
            )

            # 【新增】检查是否在可视区域内
            is_in_zone = self._check_target_in_visible_zones(
                current_az, current_alt, visible_zones
            )

            # 计算惩罚分数
            zone_penalty = 0 if is_in_zone else 50

            # Calculate score with moonlight and zone penalty
            score_result = self.scoring.calculate_score(
                max_altitude=best_window["max_altitude"],
                magnitude=target.magnitude,
                target_size=target.size,
                fov_horizontal=equipment.get("fov_horizontal", 2.0),
                fov_vertical=equipment.get("fov_vertical", 1.5),
                duration_minutes=best_window["duration_minutes"],
                moonlight_pollution=moonlight_pollution,
                zone_penalty=zone_penalty
            )

            # Determine period
            period = self._determine_period(best_window["start_time"])

            recommendations.append({
                "target": target.model_dump(),
                "visibility_windows": windows,
                "current_position": {
                    "altitude": current_alt,
                    "azimuth": current_az,
                    "timestamp": date.isoformat()  # ✅ FIX: 使用传入的date
                },
                "score": score_result["total_score"],
                "score_breakdown": score_result["breakdown"],
                "period": period,
                "moonlight_impact": self._get_impact_level(moonlight_pollution)
            })

        # Sort by score
        recommendations.sort(key=lambda r: r["score"], reverse=True)

        return recommendations[:limit]

    async def _load_targets_from_db(
        self,
        filters: Optional[dict] = None
    ) -> List[DBDeepSkyObject]:
        """Load targets from database with optional filters"""
        # TODO: For performance, implement proper pagination
        # For now, load a reasonable subset

        # If type filter specified, use optimized query
        if filters and "types" in filters:
            all_objects = []
            for obj_type in filters["types"]:
                objects = await self.db_service.get_objects_by_type(obj_type)
                all_objects.extend(objects)
            return all_objects[:1000]  # Limit to 1000 for performance

        # If no filters, get a sample across different types
        # In production, this should use cursor-based pagination
        sample_objects = []

        # Get some galaxies, nebulae, and clusters
        for obj_type in ["GALAXY", "NEBULA", "CLUSTER"]:
            objects = await self.db_service.get_objects_by_type(obj_type)
            sample_objects.extend(objects[:500])  # 500 of each type

        return sample_objects

    def _apply_filters(
        self,
        target: DeepSkyTarget,
        db_obj: DBDeepSkyObject,
        filters: dict
    ) -> bool:
        """Apply filter conditions"""
        # Magnitude filter
        if "min_magnitude" in filters:
            mag_limit = filters["min_magnitude"]
            if target.magnitude is not None and target.magnitude > mag_limit:
                return False

        # Type filter (already handled in database query)
        # Altitude filter would be applied in visibility calculation

        return True

    def _determine_period(self, start_time: str) -> str:
        """Determine time period from start time"""
        hour = datetime.fromisoformat(start_time).hour

        if 18 <= hour < 24:
            return "tonight-golden"
        elif 0 <= hour < 3:
            return "post-midnight"
        else:
            return "pre-dawn"

    def _calculate_moon_data(
        self,
        observer_lat: float,
        observer_lon: float,
        date: datetime
    ) -> dict:
        """
        Calculate moon position and phase

        Args:
            observer_lat: Observer latitude
            observer_lon: Observer longitude
            date: Observation date

        Returns:
            Dictionary with moon position and phase data
        """
        # Get moon position
        moon_position = self.moon.get_moon_position(
            observer_lat, observer_lon, date
        )

        # Get moon phase
        moon_phase = self.moon.get_moon_phase(date)

        return {
            "position": moon_position,
            "phase": moon_phase
        }

    def _calculate_moonlight_pollution(
        self,
        observer_lat: float,
        observer_lon: float,
        target: DeepSkyTarget,
        best_window: dict,
        moon_data: dict,
        date: datetime
    ) -> float:
        """
        Calculate moonlight pollution for target at best window

        Args:
            observer_lat: Observer latitude
            observer_lon: Observer longitude
            target: Target object
            best_window: Best visibility window
            moon_data: Moon data
            date: Observation date

        Returns:
            Moonlight pollution level (0-1)
        """
        # Get target position at best window time
        best_time = datetime.fromisoformat(best_window["start_time"])
        target_alt, target_az = self.astronomy.calculate_position(
            target.ra, target.dec,
            observer_lat, observer_lon,
            best_time
        )

        # Calculate moonlight pollution
        pollution = self.moon.calculate_light_pollution(
            moon_altitude=moon_data["position"]["altitude"],
            moon_azimuth=moon_data["position"]["azimuth"],
            moon_phase=moon_data["phase"]["percentage"],
            target_altitude=target_alt,
            target_azimuth=target_az
        )

        return pollution

    def _get_impact_level(self, pollution: float) -> str:
        """
        Get human-readable impact level from pollution value

        Args:
            pollution: Pollution level (0-1)

        Returns:
            Impact level string
        """
        if pollution <= 0.1:
            return "无影响"
        elif pollution <= 0.3:
            return "轻微"
        elif pollution <= 0.5:
            return "中等"
        elif pollution <= 0.7:
            return "严重"
        else:
            return "极严重"

    def _check_target_in_visible_zones(
        self,
        azimuth: float,
        altitude: float,
        visible_zones: List[VisibleZone]
    ) -> bool:
        """
        检查目标位置是否在任何可视区域内

        Args:
            azimuth: 目标方位角 (0-360°)
            altitude: 目标高度角 (0-90°)
            visible_zones: 可视区域列表

        Returns:
            True if in any zone, False otherwise
        """
        for zone in visible_zones:
            if self._is_point_in_polygon(azimuth, altitude, zone.polygon):
                return True
        return False

    def _is_point_in_polygon(
        self,
        az: float,
        alt: float,
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """
        射线法判断点是否在多边形内

        Args:
            az: 点的方位角
            alt: 点的高度角
            polygon: 多边形顶点列表 [[az1, alt1], [az2, alt2], ...]

        Returns:
            True if point is inside polygon, False otherwise
        """
        n = len(polygon)
        if n < 3:
            return False

        # Check if polygon crosses 0/360 boundary
        azimuths = [p[0] for p in polygon]
        crosses_boundary = (max(azimuths) - min(azimuths)) > 180

        # Normalize coordinates once before loop
        def normalize_azimuth(az_val: float) -> float:
            if crosses_boundary and az_val > 180:
                return az_val - 360
            return az_val

        # Normalize all coordinates
        point_az = normalize_azimuth(az)
        normalized_polygon = [(normalize_azimuth(p[0]), p[1]) for p in polygon]

        # Check if point is on any edge (boundary case)
        for i in range(n):
            p1 = normalized_polygon[i]
            p2 = normalized_polygon[(i + 1) % n]

            # Check if point is on this edge
            if self._point_on_segment(point_az, alt, p1[0], p1[1], p2[0], p2[1]):
                return True

        # Ray casting algorithm
        inside = False
        p1x, p1y = normalized_polygon[0]

        for i in range(1, n + 1):
            p2x, p2y = normalized_polygon[i % n]

            # Ray casting condition
            if alt > min(p1y, p2y):
                if alt <= max(p1y, p2y):
                    if point_az <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (alt - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or point_az <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _point_on_segment(
        self,
        px: float, py: float,
        x1: float, y1: float,
        x2: float, y2: float
    ) -> bool:
        """Check if point (px, py) is on segment from (x1, y1) to (x2, y2)"""
        # Check if point is within bounding box of segment
        if not (min(x1, x2) - 1e-9 <= px <= max(x1, x2) + 1e-9 and
                min(y1, y2) - 1e-9 <= py <= max(y1, y2) + 1e-9):
            return False

        # Check collinearity using cross product
        cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
        return abs(cross) < 1e-9
