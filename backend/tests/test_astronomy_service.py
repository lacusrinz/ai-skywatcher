import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.astronomy import AstronomyService

@pytest.mark.asyncio
async def test_get_object_from_local_db():
    """Test retrieving object from local database"""
    service = AstronomyService()

    # Mock database to return object
    mock_obj = MagicMock()
    mock_obj.id = "M31"
    service.db.get_object_by_id = AsyncMock(return_value=mock_obj)

    # Mock SIMBAD to track if it's called
    service.simbad.query_object = AsyncMock()

    obj = await service.get_object("M31")

    assert obj is not None
    assert obj.id == "M31"
    # SIMBAD should not be called
    service.simbad.query_object.assert_not_called()

@pytest.mark.asyncio
async def test_get_object_with_simbad_fallback():
    """Test fallback to SIMBAD when not in local DB"""
    service = AstronomyService()

    # Mock database to return None
    service.db.get_object_by_id = AsyncMock(return_value=None)

    # Mock SIMBAD to return object
    mock_obj = MagicMock()
    mock_obj.id = "IC999"
    service.simbad.query_object = AsyncMock(return_value=mock_obj)

    # Mock database save
    service.db.save_object = AsyncMock()

    obj = await service.get_object("IC999")

    assert obj is not None
    assert obj.id == "IC999"
    # Verify SIMBAD was called and result was cached
    service.simbad.query_object.assert_called_once_with("IC999")
    service.db.save_object.assert_called_once_with(mock_obj)

@pytest.mark.asyncio
async def test_get_object_not_found():
    """Test object not found anywhere"""
    service = AstronomyService()

    service.db.get_object_by_id = AsyncMock(return_value=None)
    service.simbad.query_object = AsyncMock(return_value=None)

    obj = await service.get_object("UNKNOWN")

    assert obj is None

@pytest.mark.asyncio
async def test_search_objects():
    """Test searching objects by name"""
    service = AstronomyService()

    mock_obj1 = MagicMock()
    mock_obj1.id = "M31"
    mock_obj2 = MagicMock()
    mock_obj2.id = "M32"

    service.db.search_objects = AsyncMock(return_value=[mock_obj1, mock_obj2])

    results = await service.search_objects("M3")

    assert len(results) == 2
    service.db.search_objects.assert_called_once_with("M3", 20)

@pytest.mark.asyncio
async def test_get_objects_by_constellation():
    """Test getting objects by constellation"""
    service = AstronomyService()

    mock_obj = MagicMock()
    mock_obj.id = "NGC0224"

    service.db.get_objects_by_constellation = AsyncMock(return_value=[mock_obj])

    results = await service.get_objects_by_constellation("And")

    assert len(results) == 1
    service.db.get_objects_by_constellation.assert_called_once_with("And")

@pytest.mark.asyncio
async def test_get_statistics():
    """Test getting database statistics"""
    service = AstronomyService()

    mock_stats = MagicMock()
    mock_stats.total_objects = 13318

    service.db.get_statistics = AsyncMock(return_value=mock_stats)

    stats = await service.get_statistics()

    assert stats.total_objects == 13318
    service.db.get_statistics.assert_called_once()
