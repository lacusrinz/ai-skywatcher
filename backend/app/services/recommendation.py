"""Recommendation engine service"""
from typing import List, Optional
from datetime import datetime
from app.services.visibility import VisibilityService
from app.services.scoring import ScoringService
from app.services.astronomy import AstronomyService
from app.models.target import DeepSkyTarget, VisibleZone


class RecommendationService:
    """推荐引擎服务"""

    def __init__(self):
        self.visibility = VisibilityService()
        self.scoring = ScoringService()
        self.astronomy = AstronomyService()

    def generate_recommendations(
        self,
        targets: List[DeepSkyTarget],
        observer_lat: float,
        observer_lon: float,
        date: datetime,
        equipment: dict,
        visible_zones: List[VisibleZone],
        filters: Optional[dict] = None,
        limit: int = 20
    ) -> List[dict]:
        """
        生成推荐目标列表

        Args:
            targets: 候选目标列表
            observer_lat: 观测者纬度
            observer_lon: 观测者经度
            date: 观测日期
            equipment: 设备参数
            visible_zones: 可视区域
            filters: 过滤条件
            limit: 返回数量限制

        Returns:
            推荐列表
        """
        recommendations = []

        for target in targets:
            # 应用过滤条件
            if filters and not self._apply_filters(target, filters):
                continue

            # 计算可见窗口
            windows = self.visibility.calculate_visibility_windows(
                target.ra, target.dec,
                observer_lat, observer_lon,
                date, visible_zones
            )

            if not windows:
                continue

            # 计算最佳窗口的评分
            best_window = max(windows, key=lambda w: w["max_altitude"])

            # 计算得分
            score_result = self.scoring.calculate_score(
                max_altitude=best_window["max_altitude"],
                magnitude=target.magnitude,
                target_size=target.size,
                fov_horizontal=equipment["fov_horizontal"],
                fov_vertical=equipment["fov_vertical"],
                duration_minutes=best_window["duration_minutes"]
            )

            # 确定时段
            period = self._determine_period(best_window["start_time"])

            # 获取当前位置
            current_alt, current_az = self.astronomy.calculate_position(
                target.ra, target.dec,
                observer_lat, observer_lon,
                datetime.now()
            )

            recommendations.append({
                "target": target.model_dump(),
                "visibility_windows": windows,
                "current_position": {
                    "altitude": current_alt,
                    "azimuth": current_az,
                    "timestamp": datetime.now().isoformat()
                },
                "score": score_result["total_score"],
                "score_breakdown": score_result["breakdown"],
                "period": period
            })

        # 排序
        recommendations.sort(key=lambda r: r["score"], reverse=True)

        return recommendations[:limit]

    def _apply_filters(self, target: DeepSkyTarget, filters: dict) -> bool:
        """应用过滤条件"""
        if "min_magnitude" in filters and target.magnitude > filters["min_magnitude"]:
            return False

        if "types" in filters and target.type not in filters["types"]:
            return False

        if "min_score" in filters:
            # 需要先计算分数，这里简化处理
            pass

        return True

    def _determine_period(self, start_time: str) -> str:
        """确定时段"""
        hour = datetime.fromisoformat(start_time).hour

        if 18 <= hour < 24:
            return "tonight-golden"
        elif 0 <= hour < 3:
            return "post-midnight"
        else:
            return "pre-dawn"
