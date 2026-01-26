"""Targets API endpoints with real database"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.astronomy import AstronomyService
from app.models.database import DeepSkyObject, DatabaseStats
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
astronomy_service = AstronomyService()


# IMPORTANT: Specific routes must be defined before parameterized routes
# Otherwise "/search" will be matched by "/{target_id}"


@router.get("/search")
async def search_targets(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    Search objects by name or alias

    - Uses LIKE query on aliases table
    - Returns partial matches
    """
    try:
        results = await astronomy_service.search_objects(q, limit)
    except Exception as e:
        logger.error(f"Error searching objects: {e}")
        results = []

    return {
        "success": True,
        "data": {
            "targets": [obj.model_dump() for obj in results],
            "count": len(results)
        },
        "message": f"Found {len(results)} objects matching '{q}'"
    }


@router.get("/stats")
async def get_statistics():
    """
    Return database statistics

    - Total object count
    - Objects by type
    - Constellations covered
    """
    stats = await astronomy_service.get_statistics()

    return {
        "success": True,
        "data": stats.model_dump() if stats else {
            "total_objects": 0,
            "objects_by_type": {},
            "constellations_covered": 0
        },
        "message": "Database statistics"
    }


@router.post("/sync")
async def sync_from_simbad(object_ids: List[str]):
    """
    Manually trigger SIMBAD sync for specific objects

    Useful for:
    - Refreshing data
    - Adding new objects
    - Updating existing objects
    """
    synced = []
    failed = []

    for object_id in object_ids:
        obj = await astronomy_service.simbad.query_object(object_id)
        if obj:
            await astronomy_service.db.save_object(obj)
            synced.append(object_id)
        else:
            failed.append(object_id)

    return {
        "success": True,
        "data": {
            "synced": synced,
            "failed": failed
        },
        "message": f"Synced {len(synced)} objects, {len(failed)} failed"
    }


@router.get("")
async def list_targets(
    type: Optional[str] = Query(None, description="目标类型"),
    constellation: Optional[str] = Query(None, description="星座"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    List targets with optional filters

    - Filter by type: GALAXY, NEBULA, CLUSTER, PLANETARY
    - Filter by constellation name
    - Pagination support
    """
    try:
        if type:
            objects = await astronomy_service.get_objects_by_type(type)
        elif constellation:
            objects = await astronomy_service.get_objects_by_constellation(constellation)
        else:
            # Return all (with simple pagination on first page)
            # For full pagination, we'd need a dedicated method
            objects = await astronomy_service.get_objects_by_type("GALAXY")
            objects += await astronomy_service.get_objects_by_type("NEBULA")
            objects += await astronomy_service.get_objects_by_type("CLUSTER")
            objects += await astronomy_service.get_objects_by_type("PLANETARY")
    except Exception as e:
        logger.error(f"Error fetching objects: {e}")
        objects = []

    start = (page - 1) * page_size
    end = start + page_size
    paginated = objects[start:end]

    return {
        "success": True,
        "data": {
            "targets": [obj.model_dump() for obj in paginated],
            "page": page,
            "page_size": page_size,
            "total": len(objects)
        },
        "message": f"Returning {len(paginated)} objects"
    }


@router.get("/{target_id}")
async def get_target(target_id: str):
    """
    Get deep sky object by ID

    - Checks local SQLite first (~1-5ms)
    - Falls back to SIMBAD API if not found (~200-500ms)
    - Caches API results in SQLite
    """
    obj = await astronomy_service.get_object(target_id)

    if not obj:
        return {
            "success": True,
            "data": None,
            "message": f"Object {target_id} not found"
        }

    return {
        "success": True,
        "data": obj.model_dump(),
        "message": "Object retrieved successfully"
    }


@router.get("")
async def list_targets(
    type: Optional[str] = Query(None, description="目标类型"),
    constellation: Optional[str] = Query(None, description="星座"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    List targets with optional filters

    - Filter by type: GALAXY, NEBULA, CLUSTER, PLANETARY
    - Filter by constellation name
    - Pagination support
    """
    try:
        if type:
            objects = await astronomy_service.get_objects_by_type(type)
        elif constellation:
            objects = await astronomy_service.get_objects_by_constellation(constellation)
        else:
            # Return all (with simple pagination on first page)
            # For full pagination, we'd need a dedicated method
            objects = await astronomy_service.get_objects_by_type("GALAXY")
            objects += await astronomy_service.get_objects_by_type("NEBULA")
            objects += await astronomy_service.get_objects_by_type("CLUSTER")
            objects += await astronomy_service.get_objects_by_type("PLANETARY")
    except Exception as e:
        logger.error(f"Error fetching objects: {e}")
        objects = []

    start = (page - 1) * page_size
    end = start + page_size
    paginated = objects[start:end]

    return {
        "success": True,
        "data": {
            "targets": [obj.model_dump() for obj in paginated],
            "page": page,
            "page_size": page_size,
            "total": len(objects)
        },
        "message": f"Returning {len(paginated)} objects"
    }


@router.get("/stats")
async def get_statistics():
    """
    Return database statistics

    - Total object count
    - Objects by type
    - Constellations covered
    """
    stats = await astronomy_service.get_statistics()

    return {
        "success": True,
        "data": stats.model_dump() if stats else {
            "total_objects": 0,
            "objects_by_type": {},
            "constellations_covered": 0
        },
        "message": "Database statistics"
    }


@router.post("/sync")
async def sync_from_simbad(object_ids: List[str]):
    """
    Manually trigger SIMBAD sync for specific objects

    Useful for:
    - Refreshing data
    - Adding new objects
    - Updating existing objects
    """
    synced = []
    failed = []

    for object_id in object_ids:
        obj = await astronomy_service.simbad.query_object(object_id)
        if obj:
            await astronomy_service.db.save_object(obj)
            synced.append(object_id)
        else:
            failed.append(object_id)

    return {
        "success": True,
        "data": {
            "synced": synced,
            "failed": failed
        },
        "message": f"Synced {len(synced)} objects, {len(failed)} failed"
    }
