"""Locations API routes"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.location import (
    LocationCreate,
    LocationResponse,
    LocationValidate,
    LocationValidateResponse
)

router = APIRouter()

# Mock 存储位置数据
locations_storage = {
    "loc_1": {
        "id": "loc_1",
        "name": "北京",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "timezone": "Asia/Shanghai",
        "country": "CN",
        "region": "Beijing",
        "is_default": True
    }
}


@router.post("/geolocate")
async def geolocate():
    """自动定位"""
    return {
        "success": True,
        "data": {
            "name": "自动定位",
            "latitude": 39.9042,
            "longitude": 116.4074,
            "timezone": "Asia/Shanghai",
            "country": "CN",
            "region": "Beijing"
        },
        "message": "定位成功"
    }


@router.post("/validate")
async def validate_location(request: LocationValidate):
    """验证位置"""
    return {
        "success": True,
        "data": {
            "latitude": request.latitude or 39.9042,
            "longitude": request.longitude or 116.4074,
            "timezone": "Asia/Shanghai",
            "validated": True
        },
        "message": "位置验证成功"
    }


@router.get("")
async def list_locations() -> dict:
    """获取保存的地点列表"""
    return {
        "success": True,
        "data": list(locations_storage.values()),
        "message": "获取成功"
    }


@router.post("")
async def create_location(location: LocationCreate) -> dict:
    """保存地点"""
    import uuid
    location_id = f"loc_{uuid.uuid4().hex[:8]}"

    new_location = {
        "id": location_id,
        "name": location.name,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "timezone": location.timezone,
        "country": location.country,
        "region": location.region,
        "is_default": False
    }

    locations_storage[location_id] = new_location

    return {
        "success": True,
        "data": new_location,
        "message": "地点保存成功"
    }


@router.delete("/{location_id}")
async def delete_location(location_id: str) -> dict:
    """删除地点"""
    if location_id not in locations_storage:
        raise HTTPException(status_code=404, detail="地点不存在")

    del locations_storage[location_id]

    return {
        "success": True,
        "message": "地点已删除"
    }
