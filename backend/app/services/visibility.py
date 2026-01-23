"""Visibility calculation service"""
from typing import List
from datetime import datetime, timedelta
from app.services.astronomy import AstronomyService
from app.models.target import VisibleZone


class VisibilityService:
    """可见性计算服务"""

    def __init__(self):
        self.astronomy = AstronomyService()

    def calculate_visibility_windows(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        date: datetime,
        visible_zones: List[VisibleZone],
        min_altitude: float = 15.0
    ) -> List[dict]:
        """
        计算目标在指定日期和可视区域的可见窗口

        Args:
            target_ra: 目标赤经
            target_dec: 目标赤纬
            observer_lat: 观测者纬度
            observer_lon: 观测者经度
            date: 观测日期
            visible_zones: 可视区域列表
            min_altitude: 最小高度角

        Returns:
            可见窗口列表
        """
        windows = []

        # 生成时间样本 (每5分钟)
        samples = self._generate_time_samples(date, interval_minutes=5)

        for zone in visible_zones:
            zone_windows = self._calculate_windows_for_zone(
                target_ra, target_dec,
                observer_lat, observer_lon,
                samples, zone,
                min_altitude
            )
            windows.extend(zone_windows)

        return windows

    def _generate_time_samples(
        self,
        date: datetime,
        interval_minutes: int = 5
    ) -> List[datetime]:
        """生成时间样本"""
        start = date.replace(hour=18, minute=0, second=0, microsecond=0)
        end = date + timedelta(days=1)
        end = end.replace(hour=6, minute=0, second=0, microsecond=0)

        samples = []
        current = start
        while current <= end:
            samples.append(current)
            current += timedelta(minutes=interval_minutes)

        return samples

    def _calculate_windows_for_zone(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        time_samples: List[datetime],
        zone: VisibleZone,
        min_altitude: float
    ) -> List[dict]:
        """计算单个区域的可见窗口"""
        windows = []
        in_window = False
        window_start = None
        max_altitude = 0
        max_altitude_time = None

        for time in time_samples:
            # 计算当前位置
            alt, az = self.astronomy.calculate_position(
                target_ra, target_dec,
                observer_lat, observer_lon,
                time
            )

            # 判断是否在区域内且高度足够
            is_in_zone = self._point_in_polygon(
                (az, alt), zone.polygon
            )
            meets_altitude = alt >= min_altitude

            if is_in_zone and meets_altitude:
                if not in_window:
                    window_start = time
                    in_window = True

                # 记录最大高度
                if alt > max_altitude:
                    max_altitude = alt
                    max_altitude_time = time
            else:
                if in_window:
                    # 窗口结束
                    duration = (time - window_start).total_seconds() / 60
                    windows.append({
                        "zone_id": zone.id,
                        "start_time": window_start.isoformat(),
                        "end_time": time.isoformat(),
                        "max_altitude": max_altitude,
                        "max_altitude_time": max_altitude_time.isoformat(),
                        "duration_minutes": duration
                    })
                    in_window = False
                    window_start = None
                    max_altitude = 0

        return windows

    def _point_in_polygon(
        self,
        point: tuple,
        polygon: List[tuple]
    ) -> bool:
        """射线法判断点是否在多边形内"""
        x, y = point
        inside = False

        for i in range(len(polygon)):
            j = (i - 1) % len(polygon)
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            intersect = ((yi > y) != (yj > y)) and \
                        (x < (xj - xi) * (y - yi) / (yj - yi + 0.0001) + xi)

            if intersect:
                inside = not inside

        return inside
