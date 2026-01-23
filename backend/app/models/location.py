"""Location models"""
from pydantic import BaseModel, Field
from typing import Optional


class Location(BaseModel):
    """观测位置模型"""
    name: str
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    timezone: str
    country: Optional[str] = None
    region: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "北京",
                "latitude": 39.9042,
                "longitude": 116.4074,
                "timezone": "Asia/Shanghai"
            }
        }


class LocationCreate(Location):
    """创建位置请求模型"""
    pass


class LocationResponse(Location):
    """位置响应模型"""
    id: str
    is_default: bool = False


class LocationValidate(BaseModel):
    """位置验证请求模型"""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    latitude_dms: Optional[str] = None
    longitude_dms: Optional[str] = None


class LocationValidateResponse(BaseModel):
    """位置验证响应模型"""
    latitude: float
    longitude: float
    timezone: str
    validated: bool
