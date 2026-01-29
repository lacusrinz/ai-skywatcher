"""Moon API routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional
from app.services.moon import MoonService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
moon_service = MoonService()


@router.post("/position")
async def get_moon_position(request: dict) -> dict:
    """
    获取月球位置

    Returns moon position in both equatorial and horizontal coordinates,
    plus moon phase information.
    """
    try:
        location = request.get("location", {})
        timestamp_str = request.get("timestamp")

        # Validate location
        if "latitude" not in location or "longitude" not in location:
            raise HTTPException(
                status_code=400,
                detail="Location must include latitude and longitude"
            )

        # Parse timestamp
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

        # Get moon position
        moon_position = moon_service.get_moon_position(
            observer_lat=location["latitude"],
            observer_lon=location["longitude"],
            timestamp=timestamp
        )

        # Get moon phase
        moon_phase = moon_service.get_moon_phase(timestamp)

        return {
            "success": True,
            "data": {
                "timestamp": timestamp.isoformat(),
                "location": location,
                "position": moon_position,
                "phase": moon_phase
            },
            "message": "获取月球位置成功"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in get_moon_position: {e}")
        raise HTTPException(status_code=500, detail=f"获取月球位置失败: {str(e)}")


@router.post("/heatmap")
async def get_moon_heatmap(request: dict) -> dict:
    """
    获取月光污染热力图

    Generates a grid of moonlight pollution values across the sky.
    """
    try:
        location = request.get("location", {})
        timestamp_str = request.get("timestamp")
        resolution = request.get("resolution", 36)

        # Validate location
        if "latitude" not in location or "longitude" not in location:
            raise HTTPException(
                status_code=400,
                detail="Location must include latitude and longitude"
            )

        # Validate resolution
        if not isinstance(resolution, int) or resolution < 10 or resolution > 100:
            raise HTTPException(
                status_code=400,
                detail="Resolution must be an integer between 10 and 100"
            )

        # Parse timestamp
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

        # Get moon data
        moon_position = moon_service.get_moon_position(
            observer_lat=location["latitude"],
            observer_lon=location["longitude"],
            timestamp=timestamp
        )
        moon_phase = moon_service.get_moon_phase(timestamp)

        # Generate heatmap
        heatmap = moon_service.get_pollution_heatmap(
            observer_lat=location["latitude"],
            observer_lon=location["longitude"],
            timestamp=timestamp,
            resolution=resolution
        )

        return {
            "success": True,
            "data": {
                "timestamp": timestamp.isoformat(),
                "location": location,
                "moon_position": moon_position,
                "moon_phase": moon_phase,
                "heatmap": heatmap
            },
            "message": "获取月光污染热力图成功"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in get_moon_heatmap: {e}")
        raise HTTPException(status_code=500, detail=f"获取月光污染热力图失败: {str(e)}")


@router.post("/pollution")
async def get_moon_pollution(request: dict) -> dict:
    """
    计算目标位置的月光污染

    Calculates moonlight pollution for a specific target position.
    """
    try:
        location = request.get("location", {})
        target_position = request.get("target_position", {})
        timestamp_str = request.get("timestamp")

        # Validate location
        if "latitude" not in location or "longitude" not in location:
            raise HTTPException(
                status_code=400,
                detail="Location must include latitude and longitude"
            )

        # Validate target position
        if "altitude" not in target_position or "azimuth" not in target_position:
            raise HTTPException(
                status_code=400,
                detail="Target position must include altitude and azimuth"
            )

        # Parse timestamp
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

        # Get moon data
        moon_position = moon_service.get_moon_position(
            observer_lat=location["latitude"],
            observer_lon=location["longitude"],
            timestamp=timestamp
        )
        moon_phase = moon_service.get_moon_phase(timestamp)

        # Calculate pollution
        pollution = moon_service.calculate_light_pollution(
            moon_altitude=moon_position["altitude"],
            moon_azimuth=moon_position["azimuth"],
            moon_phase=moon_phase["percentage"],
            target_altitude=target_position["altitude"],
            target_azimuth=target_position["azimuth"]
        )

        # Determine impact level
        if pollution <= 0.1:
            impact_level = "无影响"
        elif pollution <= 0.3:
            impact_level = "轻微"
        elif pollution <= 0.5:
            impact_level = "中等"
        elif pollution <= 0.7:
            impact_level = "严重"
        else:
            impact_level = "极严重"

        return {
            "success": True,
            "data": {
                "timestamp": timestamp.isoformat(),
                "location": location,
                "target_position": target_position,
                "moon_position": moon_position,
                "moon_phase": moon_phase,
                "pollution_level": round(pollution, 4),
                "impact_level": impact_level
            },
            "message": "计算月光污染成功"
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error in get_moon_pollution: {e}")
        raise HTTPException(status_code=500, detail=f"计算月光污染失败: {str(e)}")
