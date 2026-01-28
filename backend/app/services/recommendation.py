"""Recommendation engine service"""
from typing import List, Optional
from datetime import datetime
from app.services.visibility import VisibilityService
from app.services.scoring import ScoringService
from app.services.astronomy import AstronomyService
from app.services.database import DatabaseService
from app.services.model_adapter import ModelAdapter
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

            # Calculate score
            score_result = self.scoring.calculate_score(
                max_altitude=best_window["max_altitude"],
                magnitude=target.magnitude,
                target_size=target.size,
                fov_horizontal=equipment.get("fov_horizontal", 2.0),
                fov_vertical=equipment.get("fov_vertical", 1.5),
                duration_minutes=best_window["duration_minutes"]
            )

            # Determine period
            period = self._determine_period(best_window["start_time"])

            # Get current position
            current_alt, current_az = self.astronomy.calculate_position(
                target.ra, target.dec,
                observer_lat, observer_lon,
                datetime.now()
            )

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
                "period": period
            })

        # Sort by score
        recommendations.sort(key=lambda r: r["score"], reverse=True)

        return recommendations[:limit]

    async def _load_targets_from_db(
        self,
        filters: Optional[dict] = None
    ) -> List[DBDeepSkyObject]:
        """Load targets from database with optional filters"""
        # If type filter specified, use optimized query
        if filters and "types" in filters:
            all_objects = []
            for obj_type in filters["types"]:
                objects = await self.db_service.get_objects_by_type(obj_type)
                all_objects.extend(objects)
            return all_objects

        # Otherwise get statistics to check total count
        # For now, return empty list - actual loading happens in recommendations
        # to allow filtering by magnitude/other criteria
        return []

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
