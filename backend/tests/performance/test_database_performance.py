"""Performance tests for database queries"""
import pytest
import time
import asyncio
from app.services.database import DatabaseService

@pytest.mark.asyncio
async def test_local_query_performance():
    """Test local database query performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    obj = await service.get_object_by_id("NGC0224")
    elapsed = time.time() - start

    assert obj is not None
    assert elapsed < 0.005  # <5ms
    print(f"Local query time: {elapsed*1000:.2f}ms")

@pytest.mark.asyncio
async def test_search_performance():
    """Test search query performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    results = await service.search_objects("NGC", limit=20)
    elapsed = time.time() - start

    assert len(results) > 0
    assert elapsed < 0.020  # <20ms
    print(f"Search query time: {elapsed*1000:.2f}ms (found {len(results)} results)")

@pytest.mark.asyncio
async def test_batch_query_performance():
    """Test batch query performance (100 queries)"""
    service = DatabaseService("app/data/deep_sky.db")

    # Common NGC objects
    object_ids = [f"NGC{i:04d}" for i in range(1, 101)]

    start = time.time()
    results = await asyncio.gather(*[
        service.get_object_by_id(obj_id) for obj_id in object_ids
    ])
    elapsed = time.time() - start

    successful = sum(1 for r in results if r is not None)
    assert successful > 90  # At least 90% should exist
    assert elapsed < 1.0  # <1 second for 100 queries
    print(f"Batch query time (100 objects): {elapsed*1000:.2f}ms")
    print(f"Successful: {successful}/100")

@pytest.mark.asyncio
async def test_get_statistics_performance():
    """Test statistics query performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    stats = await service.get_statistics()
    elapsed = time.time() - start

    assert stats.total_objects > 10000
    assert elapsed < 0.050  # <50ms
    print(f"Statistics query time: {elapsed*1000:.2f}ms")
    print(f"Total objects: {stats.total_objects}")

@pytest.mark.asyncio
async def test_filter_by_type_performance():
    """Test filtering by type performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    galaxies = await service.get_objects_by_type("GALAXY")
    elapsed = time.time() - start

    assert len(galaxies) > 4000
    assert elapsed < 0.100  # <100ms
    print(f"Filter by type time: {elapsed*1000:.2f}ms (found {len(galaxies)} galaxies)")

@pytest.mark.asyncio
async def test_filter_by_constellation_performance():
    """Test filtering by constellation performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    orion_objects = await service.get_objects_by_constellation("Ori")
    elapsed = time.time() - start

    assert len(orion_objects) > 0
    assert elapsed < 0.050  # <50ms
    print(f"Filter by constellation time: {elapsed*1000:.2f}ms (found {len(orion_objects)} objects)")
