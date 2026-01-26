"""Manual performance test execution"""
import asyncio
import time
import sys
from pathlib.path import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database import DatabaseService

async def test_filter_by_type_performance():
    """Test filtering by type performance"""
    print("Testing get_objects_by_type performance...")
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    galaxies = await service.get_objects_by_type("GALAXY")
    elapsed = time.time() - start

    elapsed_ms = elapsed * 1000

    print(f"\n{'='*60}")
    print(f"RESULTS: test_filter_by_type_performance")
    print(f"{'='*60}")
    print(f"Query time: {elapsed_ms:.2f}ms")
    print(f"Galaxies found: {len(galaxies)}")
    print(f"Target: <100ms")
    print(f"Status: {'✓ PASSED' if elapsed < 0.100 else '✗ FAILED'}")
    print(f"{'='*60}\n")

    # Assertions from the test
    assert len(galaxies) > 4000, f"Expected >4000 galaxies, got {len(galaxies)}"
    assert elapsed < 0.100, f"Expected <100ms, got {elapsed_ms:.2f}ms"

    return elapsed_ms, len(galaxies)

if __name__ == "__main__":
    try:
        result = asyncio.run(test_filter_by_type_performance())
        print(f"Test completed successfully!")
    except AssertionError as e:
        print(f"Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
