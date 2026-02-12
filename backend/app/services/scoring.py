"""Scoring service for target recommendations"""
import math


class ScoringService:
    """评分服务"""

    def calculate_score(
        self,
        max_altitude: float,
        magnitude: float,
        target_size: float,
        fov_horizontal: float,
        fov_vertical: float,
        duration_minutes: float,
        moonlight_pollution: float = 0.0
    ) -> dict:
        """
        计算推荐得分 (总分100)

        Args:
            max_altitude: 最大高度角
            magnitude: 星等
            target_size: 目标视大小 (角分)
            fov_horizontal: 水平FOV (度)
            fov_vertical: 垂直FOV (度)
            duration_minutes: 可见时长 (分钟)
            moonlight_pollution: 月光污染程度 (0-1)

        Returns:
            {
                "total_score": int,
                "breakdown": {
                    "altitude": int,
                    "brightness": int,
                    "fov_match": int,
                    "duration": int,
                    "moonlight": int
                }
            }
        """
        # Calculate individual scores (0-100)
        altitude_score = self._calculate_altitude_score(max_altitude)
        brightness_score = self._calculate_brightness_score(magnitude)
        size_score = self._calculate_fov_score(
            target_size, fov_horizontal, fov_vertical
        )
        duration_score = self._calculate_duration_score(duration_minutes)
        moonlight_score = self._score_moonlight(moonlight_pollution)

        # Apply weights as per spec
        weights = {
            "altitude": 0.25,      # 25%
            "magnitude": 0.25,     # 25%
            "size_match": 0.20,    # 20%
            "duration": 0.15,      # 15%
            "moonlight": 0.15      # 15%
        }

        total_score = (
            altitude_score * weights["altitude"] +
            brightness_score * weights["magnitude"] +
            size_score * weights["size_match"] +
            duration_score * weights["duration"] +
            moonlight_score * weights["moonlight"]
        )

        return {
            "total_score": int(total_score),
            "breakdown": {
                "altitude": altitude_score,
                "brightness": brightness_score,
                "fov_match": size_score,
                "duration": duration_score,
                "moonlight": moonlight_score
            }
        }

    def _calculate_altitude_score(self, max_altitude: float) -> int:
        """高度得分 (0-100分)"""
        if max_altitude < 30:
            return max(0, int((max_altitude - 15) / 15 * 100))
        elif max_altitude < 60:
            return int((max_altitude - 30) / 30 * 20 + 80)
        else:
            return 100

    def _calculate_brightness_score(self, magnitude: float) -> int:
        """亮度得分 (0-100分)"""
        if magnitude <= 2:
            return 100
        elif magnitude <= 4:
            return 85
        elif magnitude <= 6:
            return 65
        elif magnitude <= 8:
            return 35
        else:
            return 15

    def _calculate_fov_score(
        self,
        target_size: float,
        fov_h: float,
        fov_v: float
    ) -> int:
        """FOV匹配度得分 (0-100分)"""
        # 将FOV转换为角分
        fov_h_arcmin = fov_h * 60
        fov_v_arcmin = fov_v * 60
        min_fov = min(fov_h_arcmin, fov_v_arcmin)

        # 计算目标占画幅的比例
        ratio = target_size / min_fov

        if ratio < 0.1:
            return 25  # 太小
        elif ratio > 1.5:
            return 20  # 太大
        elif 0.2 <= ratio <= 0.7:
            return 100  # 理想
        elif 0.1 <= ratio < 0.2:
            return 75
        elif 0.7 < ratio <= 1.0:
            return 60
        else:
            return 40

    def _calculate_duration_score(self, duration_minutes: float) -> int:
        """时长得分 (0-100分)"""
        if duration_minutes > 240:  # >4小时
            return 100
        elif duration_minutes >= 120:  # 2-4小时
            return 75
        elif duration_minutes >= 60:  # 1-2小时
            return 50
        else:  # <1小时
            return 25

    def _score_moonlight(self, pollution: float) -> int:
        """月光得分 (0-100分)"""
        if pollution <= 0.1:
            return 100  # 无影响
        elif pollution <= 0.3:
            return 80  # 轻微影响
        elif pollution <= 0.5:
            return 45  # 中等影响
        elif pollution <= 0.7:
            return 20  # 严重影响
        else:
            return 0  # 极严重影响
