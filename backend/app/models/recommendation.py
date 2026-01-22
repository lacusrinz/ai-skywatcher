"""Recommendation models"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ScoreBreakdown(BaseModel):
    """评分细分"""
    altitude: int = Field(..., ge=0, le=50)
    brightness: int = Field(..., ge=0, le=30)
    fov_match: int = Field(..., ge=0, le=20)
    duration: int = Field(..., ge=0, le=10)


class VisibilityWindow(BaseModel):
    """可见窗口"""
    zone_id: str
    start_time: str
    end_time: str
    max_altitude: float
    max_altitude_time: str
    duration_minutes: float


class TargetPosition(BaseModel):
    """目标位置"""
    altitude: float
    azimuth: float
    timestamp: str


class RecommendationItem(BaseModel):
    """推荐项"""
    target: dict
    visibility_windows: List[VisibilityWindow]
    current_position: TargetPosition
    score: int = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    period: str


class RecommendationRequest(BaseModel):
    """推荐请求"""
    location: dict  # {latitude, longitude, timezone}
    date: str  # YYYY-MM-DD
    equipment: dict  # {fov_horizontal, fov_vertical}
    visible_zones: List[dict]
    filters: Optional[dict] = None
    sort_by: str = "score"
    limit: int = Field(default=20, ge=1, le=100)


class RecommendationResponse(BaseModel):
    """推荐响应"""
    recommendations: List[RecommendationItem]
    summary: dict


class RecommendationSummary(BaseModel):
    """推荐统计"""
    total_targets: int
    visible_targets: int
    high_score_targets: int
    by_type: dict
    by_period: dict
    average_score: float
