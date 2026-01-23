"""Sky Map API routes"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional, List
from app.services.astronomy import AstronomyService
from app.services.mock_data import MockDataService

router = APIRouter()
astronomy_service = AstronomyService()
mock_service = MockDataService()


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
            # 获取所有目标
            targets = mock_service.load_targets()

            # 过滤类型
            if target_types:
                targets = [t for t in targets if t.type in target_types]

            # 计算每个目标的位置
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

                    # 只包含在地平线以上的目标
                    if alt > 0:
                        # 根据类型设置颜色
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
                    target = mock_service.get_target_by_id(target_id)
                    if target:
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
