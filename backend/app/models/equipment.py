"""Equipment models"""
from pydantic import BaseModel, Field
from typing import Optional


class Equipment(BaseModel):
    """设备配置模型"""
    name: str
    sensor_size: str = Field(..., pattern="^(full-frame|aps-c|m4/3|custom)$")
    sensor_width: float = Field(..., gt=0, description="传感器宽度 (mm)")
    sensor_height: float = Field(..., gt=0, description="传感器高度 (mm)")
    focal_length: float = Field(..., gt=0, description="焦距 (mm)")
    fov_horizontal: Optional[float] = Field(None, gt=0, description="水平视场角 (度)")
    fov_vertical: Optional[float] = Field(None, gt=0, description="垂直视场角 (度)")
    custom_name: Optional[str] = None


class EquipmentPreset(BaseModel):
    """预设设备配置"""
    id: str
    name: str
    sensor_size: str
    sensor_width: float
    sensor_height: float
    focal_length: int
    fov_horizontal: float
    fov_vertical: float


class FOVCalculateRequest(BaseModel):
    """FOV 计算请求"""
    sensor_width: float = Field(..., gt=0)
    sensor_height: float = Field(..., gt=0)
    focal_length: float = Field(..., gt=0)


class FOVCalculateResponse(BaseModel):
    """FOV 计算响应"""
    fov_horizontal: float
    fov_vertical: float
    fov_diagonal: float
    aspect_ratio: str


class EquipmentCreate(Equipment):
    """创建设备配置请求"""
    pass


class EquipmentResponse(BaseModel):
    """设备配置响应"""
    id: str
    name: str
    fov_horizontal: float
    fov_vertical: float
