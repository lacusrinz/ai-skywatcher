"""Recommendations API routes"""
from fastapi import APIRouter
from datetime import datetime
from app.services.recommendation import RecommendationService
from app.services.mock_data import MockDataService
from app.models.target import VisibleZone

router = APIRouter()
recommendation_service = RecommendationService()
mock_service = MockDataService()


@router.post("")
async def get_recommendations(request: dict) -> dict:
    """获取推荐目标"""
    # 转换可视区域格式
    visible_zones = [
        VisibleZone(
            id=zone.get("id", f"zone_{i}"),
            name=zone.get("name", f"Zone {i}"),
            polygon=zone["polygon"],
            priority=zone.get("priority", 1)
        )
        for i, zone in enumerate(request.get("visible_zones", []))
    ]

    # 加载所有目标
    targets = mock_service.load_targets()

    # 生成推荐
    recommendations = recommendation_service.generate_recommendations(
        targets=targets,
        observer_lat=request["location"]["latitude"],
        observer_lon=request["location"]["longitude"],
        date=datetime.fromisoformat(request["date"]),
        equipment=request["equipment"],
        visible_zones=visible_zones,
        filters=request.get("filters"),
        limit=request.get("limit", 20)
    )

    # 生成统计
    total_count = len(recommendations)
    by_period = {}
    by_type = {}
    total_score = 0

    for rec in recommendations:
        period = rec["period"]
        target_type = rec["target"]["type"]

        by_period[period] = by_period.get(period, 0) + 1
        by_type[target_type] = by_type.get(target_type, 0) + 1
        total_score += rec["score"]

    average_score = total_score / total_count if total_count > 0 else 0

    summary = {
        "total": total_count,
        "by_period": by_period,
        "by_type": by_type,
        "average_score": round(average_score, 1)
    }

    return {
        "success": True,
        "data": {
            "recommendations": recommendations,
            "summary": summary
        },
        "message": "推荐生成成功"
    }


@router.post("/by-period")
async def get_recommendations_by_period(request: dict) -> dict:
    """按时段获取推荐"""
    period = request.get("period", "tonight-golden")

    # 获取所有推荐
    all_recommendations = await get_recommendations(request)

    # 过滤时段
    filtered_recommendations = [
        rec for rec in all_recommendations["data"]["recommendations"]
        if rec["period"] == period
    ]

    return {
        "success": True,
        "data": {
            "recommendations": filtered_recommendations,
            "period": period
        },
        "message": f"获取{period}时段推荐成功"
    }


@router.post("/summary")
async def get_recommendation_summary(request: dict) -> dict:
    """获取推荐统计"""
    # 获取所有推荐
    all_recommendations = await get_recommendations(request)

    summary = all_recommendations["data"]["summary"]

    # 添加额外统计
    recommendations = all_recommendations["data"]["recommendations"]
    summary["visible_targets"] = len([r for r in recommendations if r["score"] > 0])
    summary["high_score_targets"] = len([r for r in recommendations if r["score"] >= 70])

    return {
        "success": True,
        "data": summary,
        "message": "获取统计成功"
    }
