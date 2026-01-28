import pytest
from app.services.model_adapter import ModelAdapter
from app.models.database import DeepSkyObject, ObservationalInfo
from app.models.target import DeepSkyTarget

@pytest.mark.asyncio
async def test_convert_deep_sky_object_to_target():
    """Test conversion from database model to API model"""
    # Create a DeepSkyObject (database model)
    db_obj = DeepSkyObject(
        id="NGC0224",
        name="Andromeda Galaxy",
        type="GALAXY",
        ra=10.684,
        dec=41.269,
        magnitude=3.4,
        size_major=178.0,
        size_minor=60.0,
        constellation="And",
        surface_brightness=23.5,
        aliases=["M31", "NGC224"],
        observational_info=ObservationalInfo(
            best_month=11,
            difficulty="EASY",
            min_aperture=50.0,
            notes="Visible to naked eye"
        )
    )

    # Convert to DeepSkyTarget (API model)
    adapter = ModelAdapter()
    target = adapter.to_target(db_obj)

    # Verify conversion
    assert target.id == "NGC0224"
    assert target.name == "Andromeda Galaxy"
    assert target.name_en == "Andromeda Galaxy"  # Fallback from name
    assert target.type == "galaxy"  # GALAXY -> galaxy
    assert target.ra == 10.684
    assert target.dec == 41.269
    assert target.magnitude == 3.4
    assert target.size == 119.0  # Average of major (178.0) and minor (60.0)
    assert target.constellation == "And"
    assert target.difficulty == 1  # EASY -> 1

@pytest.mark.asyncio
async def test_convert_object_with_minimal_data():
    """Test conversion with missing optional fields"""
    db_obj = DeepSkyObject(
        id="IC0123",
        name="IC 123",
        type="NEBULA",
        ra=83.633,
        dec=-5.391,
        magnitude=None,
        size_major=None,
        size_minor=None,
        constellation="Ori"
    )

    adapter = ModelAdapter()
    target = adapter.to_target(db_obj)

    assert target.id == "IC0123"
    assert target.magnitude == 99.0  # Default for missing magnitude
    assert target.size == 10.0  # Default for missing size

def test_normalize_type_galaxy():
    """Test type normalization"""
    adapter = ModelAdapter()
    assert adapter._normalize_type("GALAXY") == "galaxy"
    assert adapter._normalize_type("NEBULA") == "emission-nebula"
    assert adapter._normalize_type("CLUSTER") == "cluster"
    assert adapter._normalize_type("PLANETARY") == "planetary-nebula"

def test_difficulty_mapping():
    """Test difficulty level mapping"""
    adapter = ModelAdapter()
    assert adapter._map_difficulty("EASY") == 1
    assert adapter._map_difficulty("MODERATE") == 2
    assert adapter._map_difficulty("DIFFICULT") == 3
    assert adapter._map_difficulty(None) == 3  # Default
