"""Equipment API routes"""
from fastapi import APIRouter
import math
from app.models.equipment import (
    EquipmentPreset,
    FOVCalculateRequest,
    FOVCalculateResponse,
    EquipmentCreate,
    EquipmentResponse
)

router = APIRouter()

# 预设设备配置
PRESETS = [
    {
        "id": "preset_ff_200mm",
        "name": "全画幅 + 200mm",
        "sensor_size": "full-frame",
        "sensor_width": 36.0,
        "sensor_height": 24.0,
        "focal_length": 200,
        "fov_horizontal": 10.3,
        "fov_vertical": 6.9
    },
    {
        "id": "preset_ff_85mm",
        "name": "全画幅 + 85mm",
        "sensor_size": "full-frame",
        "sensor_width": 36.0,
        "sensor_height": 24.0,
        "focal_length": 85,
        "fov_horizontal": 23.9,
        "fov_vertical": 16.0
    },
    {
        "id": "preset_ff_50mm",
        "name": "全画幅 + 50mm",
        "sensor_size": "full-frame",
        "sensor_width": 36.0,
        "sensor_height": 24.0,
        "focal_length": 50,
        "fov_horizontal": 39.6,
        "fov_vertical": 26.7
    },
    {
        "id": "preset_apsc_85mm",
        "name": "APS-C + 85mm",
        "sensor_size": "aps-c",
        "sensor_width": 23.6,
        "sensor_height": 15.6,
        "focal_length": 85,
        "fov_horizontal": 15.2,
        "fov_vertical": 10.1
    },
    {
        "id": "preset_apsc_50mm",
        "name": "APS-C + 50mm",
        "sensor_size": "aps-c",
        "sensor_width": 23.6,
        "sensor_height": 15.6,
        "focal_length": 50,
        "fov_horizontal": 25.8,
        "fov_vertical": 17.1
    }
]

# 存储的设备配置
equipment_storage = {}


@router.get("/presets")
async def get_presets() -> dict:
    """获取预设配置"""
    return {
        "success": True,
        "data": PRESETS,
        "message": "获取预设成功"
    }


@router.post("/calculate-fov")
async def calculate_fov(request: FOVCalculateRequest) -> dict:
    """计算 FOV"""
    fov_h_rad = 2 * math.atan(request.sensor_width / (2 * request.focal_length))
    fov_v_rad = 2 * math.atan(request.sensor_height / (2 * request.focal_length))

    fov_horizontal = math.degrees(fov_h_rad)
    fov_vertical = math.degrees(fov_v_rad)
    fov_diagonal = math.degrees(2 * math.atan(
        math.sqrt(request.sensor_width**2 + request.sensor_height**2) /
        (2 * request.focal_length)
    ))

    # 计算宽高比
    gcd = math.gcd(int(request.sensor_width), int(request.sensor_height))
    aspect_w = int(request.sensor_width / gcd)
    aspect_h = int(request.sensor_height / gcd)
    aspect_ratio = f"{aspect_w}:{aspect_h}"

    return {
        "success": True,
        "data": {
            "fov_horizontal": round(fov_horizontal, 2),
            "fov_vertical": round(fov_vertical, 2),
            "fov_diagonal": round(fov_diagonal, 2),
            "aspect_ratio": aspect_ratio
        },
        "message": "FOV 计算成功"
    }


@router.post("")
async def create_equipment(equipment: EquipmentCreate) -> dict:
    """保存设备配置"""
    import uuid

    # 计算 FOV
    import math
    fov_h_rad = 2 * math.atan(equipment.sensor_width / (2 * equipment.focal_length))
    fov_v_rad = 2 * math.atan(equipment.sensor_height / (2 * equipment.focal_length))

    equipment_id = f"eq_{uuid.uuid4().hex[:8]}"

    new_equipment = {
        "id": equipment_id,
        "name": equipment.custom_name or equipment.name,
        "sensor_size": equipment.sensor_size,
        "sensor_width": equipment.sensor_width,
        "sensor_height": equipment.sensor_height,
        "focal_length": equipment.focal_length,
        "fov_horizontal": round(math.degrees(fov_h_rad), 2),
        "fov_vertical": round(math.degrees(fov_v_rad), 2)
    }

    equipment_storage[equipment_id] = new_equipment

    return {
        "success": True,
        "data": {
            "id": new_equipment["id"],
            "name": new_equipment["name"],
            "fov_horizontal": new_equipment["fov_horizontal"],
            "fov_vertical": new_equipment["fov_vertical"]
        },
        "message": "设备配置保存成功"
    }


@router.get("")
async def list_equipment() -> dict:
    """获取保存的设备配置列表"""
    return {
        "success": True,
        "data": list(equipment_storage.values()),
        "message": "获取成功"
    }
