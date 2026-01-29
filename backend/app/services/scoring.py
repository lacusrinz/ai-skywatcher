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
        altitude_score = self._calculate_altitude_score(max_altitude)
        brightness_score = self._calculate_brightness_score(magnitude)
        fov_score = self._calculate_fov_score(
            target_size, fov_horizontal, fov_vertical
        )
        duration_score = self._calculate_duration_score(duration_minutes)
        moonlight_score = self._score_moonlight(moonlight_pollution)

        total_score = altitude_score + brightness_score + fov_score + duration_score + moonlight_score

        return {
            "total_score": total_score,
            "breakdown": {
                "altitude": altitude_score,
                "brightness": brightness_score,
                "fov_match": fov_score,
                "duration": duration_score,
                "moonlight": moonlight_score
            }
        }

    def _calculate_altitude_score(self, max_altitude: float) -> int:
        """高度得分 (34分满分)"""
        if max_altitude < 30:
            return max(0, int((max_altitude - 15) / 15 * 34))
        elif max_altitude < 60:
            return int(34 + (max_altitude - 30) / 30 * 9)
        else:
            return 43

    def _calculate_brightness_score(self, magnitude: float) -> int:
        """亮度得分 (26分满分)"""
        if magnitude <= 2:
            return 26
        elif magnitude <= 4:
            return 22
        elif magnitude <= 6:
            return 16
        elif magnitude <= 8:
            return 9
        else:
            return 4

    def _calculate_fov_score(
        self,
        target_size: float,
        fov_h: float,
        fov_v: float
    ) -> int:
        """FOV匹配度得分 (17分满分)"""
        # 将FOV转换为角分
        fov_h_arcmin = fov_h * 60
        fov_v_arcmin = fov_v * 60
        min_fov = min(fov_h_arcmin, fov_v_arcmin)

        # 计算目标占画幅的比例
        ratio = target_size / min_fov

        if ratio < 0.1:
            return 4  # 太小
        elif ratio > 1.5:
            return 3  # 太大
        elif 0.2 <= ratio <= 0.7:
            return 17  # 理想
        elif 0.1 <= ratio < 0.2:
            return 13
        elif 0.7 < ratio <= 1.0:
            return 10
        else:
            return 7

    def _calculate_duration_score(self, duration_minutes: float) -> int:
        """时长得分 (8分满分)"""
        if duration_minutes > 240:  # >4小时
            return 8
        elif duration_minutes >= 120:  # 2-4小时
            return 6
        elif duration_minutes >= 60:  # 1-2小时
            return 4
        else:  # <1小时
            return 2

    def _score_moonlight(self, pollution: float) -> int:
        """月光得分 (15分满分)"""
        if pollution <= 0.1:
            return 15  # 无影响
        elif pollution <= 0.3:
            return 12  # 轻微影响
        elif pollution <= 0.5:
            return 7  # 中等影响
        elif pollution <= 0.7:
            return 3  # 严重影响
        else:
            return 0  # 极严重影响
