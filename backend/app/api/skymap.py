"""Sky Map API routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional, List, Dict
from app.services.astronomy import AstronomyService
from app.services.database import DatabaseService
from app.services.model_adapter import ModelAdapter
from app.services.mock_data import MockDataService
import logging

# Constants
DEFAULT_MAX_TARGETS = 500
DEFAULT_LATITUDE = 39.9042  # Beijing
DEFAULT_LONGITUDE = 116.4074  # Beijing
HORIZON_THRESHOLD = 0.0

# Color mapping for target types
TARGET_COLOR_MAP = {
    "emission-nebula": "#FF6B6B",
    "galaxy": "#FFB86C",
    "cluster": "#FFD93D",
    "planetary-nebula": "#6BCF7F",
    "supernova-remnant": "#A78BFA"
}

logger = logging.getLogger(__name__)

router = APIRouter()
astronomy_service = AstronomyService()
db_service = DatabaseService()
model_adapter = ModelAdapter()
mock_service = MockDataService()


def _prepare_target_filters(target_types: List[str]) -> List[str]:
    """
    Prepare and normalize target type filters.

    Args:
        target_types: List of target type names (lowercase)

    Returns:
        List of normalized database type names (uppercase)
    """
    if target_types:
        # Normalize API type to database type (galaxy -> GALAXY)
        return [obj_type.upper() for obj_type in target_types]
    else:
        # Default types when no filter specified
        return ["GALAXY", "NEBULA", "CLUSTER"]


def _calculate_targets_positions(
    targets: list,
    location: Dict[str, float],
    timestamp: datetime
) -> List[Dict]:
    """
    Calculate positions for a list of targets.

    Args:
        targets: List of target objects with ra/dec
        location: Location dict with latitude/longitude
        timestamp: Datetime for calculation

    Returns:
        List of target dicts with altitude/azimuth
    """
    targets_with_position = []

    for target in targets:
        try:
            alt, az = astronomy_service.calculate_position(
                target.ra,
                target.dec,
                location.get("latitude", DEFAULT_LATITUDE),
                location.get("longitude", DEFAULT_LONGITUDE),
                timestamp
            )

            # Only include targets above horizon
            if alt > HORIZON_THRESHOLD:
                color = TARGET_COLOR_MAP.get(target.type, "#FFFFFF")

                targets_with_position.append({
                    "id": target.id,
                    "name": target.name,
                    "altitude": round(alt, 2),
                    "azimuth": round(az, 2),
                    "type": target.type,
                    "magnitude": target.magnitude,
                    "color": color
                })
        except Exception as e:
            logger.error(f"Error calculating position for {target.id}: {e}")
            continue

    return targets_with_position


@router.post("/data")
async def get_sky_map_data(request: dict) -> dict:
    """
    获取天空图数据

    Uses real astronomical database (13,318+ objects) instead of mock data.
    """
    try:
        location = request.get("location", {})
        timestamp_str = request.get("timestamp")
        include_targets = request.get("include_targets", False)
        target_types = request.get("target_types", [])

        # Parse timestamp with validation
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timestamp format. Use ISO 8601 format: {str(e)}"
                )
        else:
            timestamp = datetime.now()

        # Prepare response data
        data = {
            "timestamp": timestamp.isoformat(),
            "location": location,
            "grid": {
                "altitude_lines": [0, 15, 30, 45, 60, 75, 90],
                "azimuth_labels": {
                    "0": "N",
                    "45": "NE",
                    "90": "E",
                    "135": "SE",
                    "180": "S",
                    "225": "SW",
                    "270": "W",
                    "315": "NW"
                }
            }
        }

        # Load targets if requested
        if include_targets:
            # Prepare type filters
            db_types = _prepare_target_filters(target_types)

            # Load targets from database
            all_db_objects = []
            for db_type in db_types:
                objects = await db_service.get_objects_by_type(db_type)
                all_db_objects.extend(objects[:DEFAULT_MAX_TARGETS])

            # Convert database models to API models
            targets = [model_adapter.to_target(obj) for obj in all_db_objects]

            # Calculate positions
            targets_with_position = _calculate_targets_positions(
                targets, location, timestamp
            )

            data["targets"] = targets_with_position

        return {
            "success": True,
            "data": data,
            "message": "获取天空图数据成功"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in get_sky_map_data: {e}")
        raise HTTPException(status_code=500, detail=f"获取天空图数据失败: {str(e)}")


@router.post("/timeline")
async def get_sky_map_timeline(request: dict) -> dict:
    """获取时间轴数据"""
    try:
        location = request.get("location", {})
        date_str = request.get("date")
        interval_minutes = request.get("interval_minutes", 30)
        target_ids = request.get("target_ids", [])

        # Parse date with validation
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format. Use ISO 8601 format: {str(e)}"
                )
        else:
            date = datetime.now()

        # Generate time series
        from datetime import timedelta
        start_time = date.replace(hour=18, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        timeline = []
        current = start_time
        while current <= end_time:
            try:
                # Calculate position for each target at this time
                positions = []
                for target_id in target_ids:
                    target = mock_service.get_target_by_id(target_id)
                    if target:
                        alt, az = astronomy_service.calculate_position(
                            target.ra,
                            target.dec,
                            location.get("latitude", DEFAULT_LATITUDE),
                            location.get("longitude", DEFAULT_LONGITUDE),
                            current
                        )

                        if alt > HORIZON_THRESHOLD:
                            positions.append({
                                "id": target_id,
                                "altitude": round(alt, 2),
                                "azimuth": round(az, 2)
                            })

                timeline.append({
                    "timestamp": current.isoformat(),
                    "targets": positions
                })

                current += timedelta(minutes=interval_minutes)

            except Exception as e:
                logger.error(f"Error calculating timeline for {current}: {e}")
                break

        return {
            "success": True,
            "data": {
                "date": date_str,
                "timeline": timeline
            },
            "message": "获取时间轴数据成功"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in get_sky_map_timeline: {e}")
        raise HTTPException(status_code=500, detail=f"获取时间轴数据失败: {str(e)}")
