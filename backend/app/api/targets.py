"""Targets API routes"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.services.mock_data import MockDataService
from app.models.target import DeepSkyTarget

router = APIRouter()
mock_service = MockDataService()


@router.get("")
async def list_targets(
    type: Optional[str] = Query(None, description="目标类型"),
    constellation: Optional[str] = Query(None, description="星座"),
    min_magnitude: Optional[float] = Query(None, description="最小星等"),
    max_magnitude: Optional[float] = Query(None, description="最大星等"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
) -> dict:
    """获取所有目标"""
    targets = mock_service.load_targets()

    # 应用过滤条件
    if type:
        targets = [t for t in targets if t.type == type]

    if constellation:
        targets = [t for t in targets if t.constellation.lower() == constellation.lower()]

    if min_magnitude is not None:
        targets = [t for t in targets if t.magnitude >= min_magnitude]

    if max_magnitude is not None:
        targets = [t for t in targets if t.magnitude <= max_magnitude]

    total = len(targets)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_targets = targets[start:end]

    return {
        "success": True,
        "data": {
            "targets": [t.model_dump() for t in paginated_targets],
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "message": "获取成功"
    }


@router.get("/search")
async def search_targets(q: str = Query(..., description="搜索关键词")) -> dict:
    """搜索目标"""
    results = mock_service.search_targets(q)

    return {
        "success": True,
        "data": {
            "results": [t.model_dump() for t in results]
        },
        "message": "搜索成功"
    }


@router.get("/{target_id}")
async def get_target(target_id: str) -> dict:
    """获取单个目标详情"""
    target = mock_service.get_target_by_id(target_id)

    if not target:
        raise HTTPException(status_code=404, detail="目标不存在")

    return {
        "success": True,
        "data": target.model_dump(),
        "message": "获取成功"
    }
