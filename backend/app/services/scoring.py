"""Scoring service for target recommendations"""
import math


class ScoringService:
    """评分服务"""

    def calculate_score(
        self,
        magnitude: float,
        target_size: float,
        fov_horizontal: float,
        fov_vertical: float,
        duration_minutes: float,
        moonlight_pollution: float = 0.0,
        zone_penalty: int = 0
    ) -> dict:
        """
        计算推荐得分 (总分100)

        新的权重分配（每项25%）：
        - brightness: 25%
        - fov_match: 25%
        - duration: 25%
        - moonlight: 25%

        移除：
        - altitude: 0% (在可视区域内的目标自然满足)
        """
        # 计算各项得分
        brightness_score = self._calculate_brightness_score(magnitude)
        size_score = self._calculate_fov_score(
            target_size, fov_horizontal, fov_vertical
        )
        duration_score = self._calculate_duration_score(duration_minutes)
        moonlight_score = self._score_moonlight(moonlight_pollution)

        # 新的权重（每项25%）
        weights = {
            "brightness": 0.25,
            "size_match": 0.25,
            "duration": 0.25,
            "moonlight": 0.25
        }

        # 计算总分
        total_score = (
            brightness_score * weights["brightness"] +
            size_score * weights["size_match"] +
            duration_score * weights["duration"] +
            moonlight_score * weights["moonlight"]
        )

        # 扣除可视区域惩罚
        total_score = max(0, total_score - zone_penalty)

        return {
            "total_score": int(total_score),
            "breakdown": {
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
        """
        FOV匹配度得分 (0-100分) - 优化版本

        评分曲线：
        - <10%:  0-30分 (线性，太小)
        - 10-20%: 30-60分 (线性，可接受)
        - 20-70%: 100分 (理想范围)
        - 70-100%: 100-70分 (线性下降，较大)
        - >100%: 最低20分 (过大，线性下降)
        """
        # 计算FOV对角线
        fov_diagonal = math.sqrt(fov_h**2 + fov_v**2)

        # 将目标大小从角分转换为度
        target_size_degrees = target_size / 60

        # 计算目标占FOV对角线的百分比
        ratio = target_size_degrees / fov_diagonal

        # 分段评分
        if ratio < 0.1:
            # 太小：<10%
            return max(0, min(30, int(ratio / 0.1 * 30)))
        elif 0.1 <= ratio < 0.2:
            # 较小：10-20%
            normalized = (ratio - 0.1) / 0.1
            return 30 + int(normalized * 30)
        elif 0.2 <= ratio <= 0.7:
            # 理想：20-70%
            return 100
        elif 0.7 < ratio <= 1.0:
            # 较大：70-100%
            normalized = (ratio - 0.7) / 0.3
            return 100 - int(normalized * 30)
        else:
            # 太大：>100%
            excess = ratio - 1.0
            return max(20, 70 - int(excess * 50))

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
