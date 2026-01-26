import pytest
from app.services.database import DatabaseService
from app.models.database import DeepSkyObject

@pytest.mark.asyncio
async def test_get_object_by_id():
    service = DatabaseService("app/data/deep_sky.db")
    # OpenNGC uses NGC/IC numbers as primary IDs
    obj = await service.get_object_by_id("NGC0224")
    assert obj is not None
    assert obj.id == "NGC0224"
    assert obj.name == "Andromeda Galaxy"
    # M31 should be in aliases
    assert "M31" in obj.aliases

@pytest.mark.asyncio
async def test_search_objects():
    service = DatabaseService("app/data/deep_sky.db")
    results = await service.search_objects("Andromeda")
    assert len(results) > 0
    assert any("M31" in obj.id or "Andromeda" in obj.name for obj in results)

@pytest.mark.asyncio
async def test_get_statistics():
    service = DatabaseService("app/data/deep_sky.db")
    stats = await service.get_statistics()
    assert stats.total_objects > 10000
