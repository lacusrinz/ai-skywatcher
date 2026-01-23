"""Visibility models"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PositionRequest(BaseModel):
    """位置计算请求"""
    target_id: str
    location: dict  # {latitude, longitude}
    timestamp: Optional[str] = None  # ISO 8601 format, defaults to now


class PositionResponse(BaseModel):
    """位置计算响应"""
    target_id: str
    altitude: float
    azimuth: float
    rise_time: Optional[str] = None
    set_time: Optional[str] = None
    transit_time: Optional[str] = None
    transit_altitude: Optional[float] = None
    is_visible: bool


class VisibilityWindowsRequest(BaseModel):
    """可见窗口计算请求"""
    target_id: str
    location: dict  # {latitude, longitude}
    date: str  # YYYY-MM-DD
    visible_zones: List[dict]


class VisibilityWindowsResponse(BaseModel):
    """可见窗口计算响应"""
    target_id: str
    windows: List[dict]
    total_duration_minutes: int


class BatchPositionsRequest(BaseModel):
    """批量位置计算请求"""
    target_ids: List[str]
    location: dict  # {latitude, longitude}
    timestamp: Optional[str] = None


class BatchPositionsResponse(BaseModel):
    """批量位置计算响应"""
    positions: List[dict]
