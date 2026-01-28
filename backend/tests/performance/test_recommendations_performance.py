"""Performance tests for recommendation generation"""
import pytest
import time
from app.services.recommendation import RecommendationService
from app.models.target import VisibleZone
from datetime import datetime


# Create a default full-sky visible zone for testing
DEFAULT_FULL_SKY_ZONE = VisibleZone(
    id="full_sky",
    name="Full Sky",
    polygon=[
        (0, 15), (90, 15), (180, 15), (270, 15),
        (270, 90), (180, 90), (90, 90), (0, 90)
    ],
    priority=1
)


@pytest.mark.asyncio
async def test_recommendation_performance():
    """Test that recommendations complete in reasonable time"""
    service = RecommendationService()

    start_time = time.time()

    recommendations = await service.generate_recommendations(
        targets=None,
        observer_lat=39.9,
        observer_lon=116.4,
        date=datetime.fromisoformat("2025-01-28"),
        equipment={"type": "refractor", "aperture": 80, "focal_length": 500},
        visible_zones=[DEFAULT_FULL_SKY_ZONE],
        filters=None,
        limit=20
    )

    elapsed = time.time() - start_time

    # Should complete in less than 5 seconds for 20 recommendations
    assert elapsed < 5.0, f"Recommendations took {elapsed:.2f}s, expected < 5s"
    assert len(recommendations) > 0

    print(f"\n✓ Generated {len(recommendations)} recommendations in {elapsed:.2f}s")


@pytest.mark.asyncio
async def test_recommendation_performance_with_filters():
    """Test performance with type filters (should be faster)"""
    service = RecommendationService()

    start_time = time.time()

    recommendations = await service.generate_recommendations(
        targets=None,
        observer_lat=39.9,
        observer_lon=116.4,
        date=datetime.fromisoformat("2025-01-28"),
        equipment={"type": "refractor", "aperture": 80, "focal_length": 500},
        visible_zones=[DEFAULT_FULL_SKY_ZONE],
        filters={"types": ["GALAXY"], "min_magnitude": 12.0},
        limit=20
    )

    elapsed = time.time() - start_time

    # With filters, should be even faster
    assert elapsed < 5.0, f"Filtered recommendations took {elapsed:.2f}s, expected < 5s"
    assert len(recommendations) > 0

    print(f"\n✓ Generated {len(recommendations)} filtered recommendations in {elapsed:.2f}s")


@pytest.mark.asyncio
async def test_recommendation_performance_large_limit():
    """Test performance with larger limit (stress test)"""
    service = RecommendationService()

    start_time = time.time()

    recommendations = await service.generate_recommendations(
        targets=None,
        observer_lat=39.9,
        observer_lon=116.4,
        date=datetime.fromisoformat("2025-01-28"),
        equipment={"type": "refractor", "aperture": 80, "focal_length": 500},
        visible_zones=[DEFAULT_FULL_SKY_ZONE],
        filters={"types": ["GALAXY"]},
        limit=100
    )

    elapsed = time.time() - start_time

    # For 100 recommendations, allow up to 10 seconds
    assert elapsed < 10.0, f"Large recommendation set took {elapsed:.2f}s, expected < 10s"
    assert len(recommendations) > 0

    print(f"\n✓ Generated {len(recommendations)} recommendations in {elapsed:.2f}s")
