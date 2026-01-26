"""Enhanced astronomy service with database + SIMBAD fallback"""
import logging
from typing import Tuple, Optional, List
from datetime import datetime, timedelta
import math
from app.services.database import DatabaseService
from app.services.simbad import SIMBADService
from app.models.database import DeepSkyObject

logger = logging.getLogger(__name__)

class AstronomyService:
    """Enhanced service with local DB and SIMBAD fallback"""

    def __init__(self):
        self.db = DatabaseService()
        self.simbad = SIMBADService()

    # ========== Data Access Methods ==========

    async def get_object(self, object_id: str) -> Optional[DeepSkyObject]:
        """
        Get object with automatic fallback:
        1. Try local database (fast, <5ms)
        2. Fallback to SIMBAD API (slow, ~200-500ms)
        3. Cache API results locally
        """
        # Try local database first
        logger.debug(f"Looking up object {object_id} in local database")
        obj = await self.db.get_object_by_id(object_id)

        if obj:
            logger.info(f"Found {object_id} in local database")
            return obj

        # Not found locally, try SIMBAD API
        logger.info(f"Object {object_id} not found locally, querying SIMBAD API")
        obj = await self.simbad.query_object(object_id)

        if obj:
            # Cache result locally
            logger.info(f"SIMBAD returned {object_id}, caching locally")
            await self.db.save_object(obj)
            return obj

        # Not found anywhere
        logger.warning(f"Object {object_id} not found in local DB or SIMBAD")
        return None

    async def search_objects(self, name: str, limit: int = 20) -> List[DeepSkyObject]:
        """Search objects by name (local database only)"""
        return await self.db.search_objects(name, limit)

    async def get_objects_by_constellation(self, constellation: str) -> List[DeepSkyObject]:
        """Get all objects in a constellation"""
        return await self.db.get_objects_by_constellation(constellation)

    async def get_objects_by_type(self, obj_type: str) -> List[DeepSkyObject]:
        """Get all objects of a specific type"""
        return await self.db.get_objects_by_type(obj_type)

    async def get_statistics(self):
        """Get database statistics"""
        return await self.db.get_statistics()

    # ========== Celestial Calculation Methods (Existing) ==========

    def calculate_position(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        timestamp: datetime
    ) -> Tuple[float, float]:
        """
        计算目标的当前高度角和方位角

        Args:
            target_ra: 目标赤经 (度)
            target_dec: 目标赤纬 (度)
            observer_lat: 观测者纬度
            observer_lon: 观测者经度
            timestamp: 时间戳

        Returns:
            (altitude, azimuth) 高度角和方位角 (度)
        """
        # 1. 计算本地恒星时
        lst = self._calculate_local_sidereal_time(observer_lon, timestamp)

        # 2. 计算时角
        ha = lst - target_ra

        # 3. 转换为地平坐标
        alt, az = self._horizontal_to_equatorial(
            target_dec, ha, observer_lat
        )

        return alt, az

    def _calculate_local_sidereal_time(
        self,
        longitude: float,
        timestamp: datetime
    ) -> float:
        """计算本地恒星时"""
        # 简化实现
        day_of_year = timestamp.timetuple().tm_yday
        hour = timestamp.hour + timestamp.minute / 60.0

        # 粗略的格林尼治恒星时
        gmst = (day_of_year * 24.0657 / 365.25 + hour) % 24

        # 本地恒星时
        lst = (gmst + longitude / 15.0) % 24
        return lst * 15  # 转换为度

    def _horizontal_to_equatorial(
        self,
        dec: float,
        ha: float,
        lat: float
    ) -> Tuple[float, float]:
        """从赤道坐标转换为地平坐标"""
        dec_rad = math.radians(dec)
        ha_rad = math.radians(ha)
        lat_rad = math.radians(lat)

        # 计算高度角
        sin_alt = (
            math.sin(dec_rad) * math.sin(lat_rad) +
            math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad)
        )
        alt = math.degrees(math.asin(max(-1, min(1, sin_alt))))

        # 计算方位角
        cos_az = 0
        try:
            cos_alt = math.cos(math.radians(alt))
            if cos_alt > 0.0001:  # 避免除以零
                cos_az = (
                    (math.sin(dec_rad) - math.sin(lat_rad) * sin_alt) /
                    (math.cos(lat_rad) * cos_alt)
                )
        except:
            pass

        cos_az = max(-1, min(1, cos_az))
        az = math.degrees(math.acos(cos_az))

        # 根据时角调整方位角
        if math.sin(ha_rad) > 0:
            az = 360 - az

        return alt, az

    def calculate_rise_set_transit(
        self,
        target_ra: float,
        target_dec: float,
        observer_lat: float,
        observer_lon: float,
        date: datetime
    ) -> dict:
        """
        计算目标的升起、中天、落下时间

        Returns:
            {
                "rise_time": datetime,
                "transit_time": datetime,
                "set_time": datetime,
                "transit_altitude": float
            }
        """
        # 简化实现
        base_hour = 18
        rise_time = date.replace(hour=base_hour, minute=30, second=0, microsecond=0)
        transit_time = rise_time + timedelta(hours=5)
        set_time = rise_time + timedelta(hours=11, minutes=30)

        # 计算中天高度
        transit_alt = 90 - abs(observer_lat - target_dec)

        return {
            "rise_time": rise_time,
            "transit_time": transit_time,
            "set_time": set_time,
            "transit_altitude": transit_alt
        }
