"""Target models"""
from pydantic import BaseModel, Field
from typing import List, Tuple, Optional


class DeepSkyTarget(BaseModel):
    """深空天体模型"""
    id: str
    name: str
    name_en: str
    type: str = Field(..., pattern="^(emission-nebula|reflection-nebula|galaxy|cluster|planetary-nebula|supernova-remnant)$")
    ra: float = Field(..., ge=0, le=360, description="赤经 (度)")
    dec: float = Field(..., ge=-90, le=90, description="赤纬 (度)")
    magnitude: float = Field(..., description="星等")
    size: float = Field(..., description="视大小 (角分)")
    constellation: str
    difficulty: int = Field(..., ge=1, le=5, description="难度等级 (1-5)")
    description: Optional[str] = None
    optimal_season: Optional[List[str]] = None
    optimal_fov: Optional[dict] = None
    tags: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "M42",
                "name": "猎户座大星云",
                "name_en": "Orion Nebula",
                "type": "emission-nebula",
                "ra": 83.633,
                "dec": -5.391,
                "magnitude": 4.0,
                "size": 85,
                "constellation": "Orion",
                "difficulty": 1
            }
        }


class VisibleZone(BaseModel):
    """可视区域模型"""
    id: str
    name: str
    polygon: List[Tuple[float, float]] = Field(..., description="[方位角, 高度角]")
    priority: int = Field(default=1, ge=1, le=10)


class VisibleZoneCreate(BaseModel):
    """创建可视区域请求"""
    name: str
    polygon: List[Tuple[float, float]]
    priority: int = Field(default=1, ge=1, le=10)


class VisibleZoneResponse(VisibleZone):
    """可视区域响应"""
    azimuth_range: Tuple[float, float]
    altitude_range: Tuple[float, float]


class TargetListResponse(BaseModel):
    """目标列表响应"""
    targets: List[DeepSkyTarget]
    total: int
    page: int
    page_size: int


class TargetSearchResponse(BaseModel):
    """目标搜索响应"""
    results: List[DeepSkyTarget]
