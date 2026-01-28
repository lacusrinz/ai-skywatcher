"""
Visibility API routes

Uses real astronomical data from DatabaseService (OpenNGC database with 13,318 objects).
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.services.astronomy import AstronomyService
from app.services.visibility import VisibilityService
from app.services.database import DatabaseService
from app.services.model_adapter import ModelAdapter
from app.models.visibility import PositionRequest, VisibilityWindowsRequest, BatchPositionsRequest

router = APIRouter()
astronomy_service = AstronomyService()
visibility_service = VisibilityService()
db_service = DatabaseService()  # CHANGED: Use real database
model_adapter = ModelAdapter()  # NEW: Model adapter


@router.post("/position")
async def calculate_position(request: PositionRequest) -> dict:
    """Calculate target position using real database"""
    # Get object from real database
    obj = await db_service.get_object_by_id(request.target_id)

    if not obj:
        raise HTTPException(status_code=404, detail="目标不存在")

    # Convert to API model
    target = model_adapter.to_target(obj)

    timestamp = datetime.fromisoformat(request.timestamp) if request.timestamp else datetime.now()

    alt, az = astronomy_service.calculate_position(
        target.ra,
        target.dec,
        request.location["latitude"],
        request.location["longitude"],
        timestamp
    )

    rise_set = astronomy_service.calculate_rise_set_transit(
        target.ra,
        target.dec,
        request.location["latitude"],
        request.location["longitude"],
        timestamp
    )

    return {
        "success": True,
        "data": {
            "target_id": request.target_id,
            "altitude": round(alt, 2),
            "azimuth": round(az, 2),
            "rise_time": rise_set["rise_time"].isoformat(),
            "set_time": rise_set["set_time"].isoformat(),
            "transit_time": rise_set["transit_time"].isoformat(),
            "transit_altitude": round(rise_set["transit_altitude"], 2),
            "is_visible": alt > 15
        },
        "message": "计算成功"
    }


@router.post("/windows")
async def calculate_visibility_windows(request: VisibilityWindowsRequest) -> dict:
    """Calculate visibility windows using real database"""
    # Get object from real database
    obj = await db_service.get_object_by_id(request.target_id)

    if not obj:
        raise HTTPException(status_code=404, detail="目标不存在")

    # Convert to API model
    target = model_adapter.to_target(obj)

    # 转换可视区域格式
    from app.models.target import VisibleZone
    visible_zones = [
        VisibleZone(
            id=zone.get("id", f"zone_{i}"),
            name=zone.get("name", f"Zone {i}"),
            polygon=zone["polygon"],
            priority=zone.get("priority", 1)
        )
        for i, zone in enumerate(request.visible_zones)
    ]

    date = datetime.fromisoformat(request.date)

    windows = visibility_service.calculate_visibility_windows(
        target.ra,
        target.dec,
        request.location["latitude"],
        request.location["longitude"],
        date,
        visible_zones
    )

    total_duration = sum(w["duration_minutes"] for w in windows)

    return {
        "success": True,
        "data": {
            "target_id": request.target_id,
            "windows": windows,
            "total_duration_minutes": int(total_duration)
        },
        "message": "计算成功"
    }


@router.post("/positions-batch")
async def calculate_batch_positions(request: BatchPositionsRequest) -> dict:
    """Batch calculate positions using real database"""
    timestamp = datetime.fromisoformat(request.timestamp) if request.timestamp else datetime.now()

    positions = []
    for target_id in request.target_ids:
        # Get object from real database
        obj = await db_service.get_object_by_id(target_id)

        if not obj:
            continue

        # Convert to API model
        target = model_adapter.to_target(obj)

        alt, az = astronomy_service.calculate_position(
            target.ra,
            target.dec,
            request.location["latitude"],
            request.location["longitude"],
            timestamp
        )

        positions.append({
            "target_id": target_id,
            "altitude": round(alt, 2),
            "azimuth": round(az, 2),
            "is_visible": alt > 15
        })

    return {
        "success": True,
        "data": {
            "positions": positions
        },
        "message": "批量计算成功"
    }
