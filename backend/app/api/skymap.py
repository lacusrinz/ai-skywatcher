"""Sky Map API routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional, List
from app.services.astronomy import AstronomyService
from app.services.database import DatabaseService
from app.services.model_adapter import ModelAdapter

router = APIRouter()
astronomy_service = AstronomyService()
db_service = DatabaseService()
model_adapter = ModelAdapter()


@router.post("/data")
async def get_sky_map_data(request: dict) -> dict:
    """获取天空图数据"""
    try:
        location = request.get("location", {})
        timestamp_str = request.get("timestamp")
        include_targets = request.get("include_targets", False)
        target_types = request.get("target_types", [])

        # 解析时间戳
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()

        # 准备响应数据
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

        # 如果需要包含目标
        if include_targets:
            # Load targets from database based on type filters
            if target_types:
                # Load specific types
                all_db_objects = []
                for obj_type in target_types:
                    # Normalize API type to database type (galaxy -> GALAXY)
                    db_type = obj_type.upper()
                    objects = await db_service.get_objects_by_type(db_type)
                    all_db_objects.extend(objects)
                # Limit to prevent overwhelming response
                all_db_objects = all_db_objects[:500]
            else:
                # Load sample objects from each type (500 each)
                all_db_objects = []
                for obj_type in ["GALAXY", "NEBULA", "CLUSTER"]:
                    objects = await db_service.get_objects_by_type(obj_type)
                    all_db_objects.extend(objects[:500])

            # Convert database models to API models
            targets = [model_adapter.to_target(obj) for obj in all_db_objects]

            # Calculate position for each target
            targets_with_position = []
            for target in targets:
                try:
                    alt, az = astronomy_service.calculate_position(
                        target.ra,
                        target.dec,
                        location.get("latitude", 39.9042),
                        location.get("longitude", 116.4074),
                        timestamp
                    )

                    # Only include targets above horizon
                    if alt > 0:
                        color_map = {
                            "emission-nebula": "#FF6B6B",
                            "galaxy": "#FFB86C",
                            "cluster": "#FFD93D",
                            "planetary-nebula": "#6BCF7F",
                            "supernova-remnant": "#A78BFA"
                        }
                        color = color_map.get(target.type, "#FFFFFF")

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
                    print(f"Error calculating position for {target.id}: {e}")
                    continue

            data["targets"] = targets_with_position

        return {
            "success": True,
            "data": data,
            "message": "获取天空图数据成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取天空图数据失败: {str(e)}")


@router.post("/timeline")
async def get_sky_map_timeline(request: dict) -> dict:
    """获取时间轴数据"""
    try:
        location = request.get("location", {})
        date_str = request.get("date")
        interval_minutes = request.get("interval_minutes", 30)
        target_ids = request.get("target_ids", [])

        # 解析日期
        if date_str:
            date = datetime.fromisoformat(date_str)
        else:
            date = datetime.now()

        # 生成时间序列
        from datetime import timedelta
        start_time = date.replace(hour=18, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        timeline = []
        current = start_time
        while current <= end_time:
            try:
                # 计算每个目标在此时刻的位置
                positions = []
                for target_id in target_ids:
                    db_obj = await db_service.get_object_by_id(target_id)
                    if db_obj:
                        target = model_adapter.to_target(db_obj)
                        alt, az = astronomy_service.calculate_position(
                            target.ra,
                            target.dec,
                            location.get("latitude", 39.9042),
                            location.get("longitude", 116.4074),
                            current
                        )

                        if alt > 0:
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
                print(f"Error calculating timeline for {current}: {e}")
                break

        return {
            "success": True,
            "data": {
                "date": date_str,
                "timeline": timeline
            },
            "message": "获取时间轴数据成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间轴数据失败: {str(e)}")
