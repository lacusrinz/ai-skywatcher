# Sky Map API Migration to Real Database

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate Sky Map API from MockDataService (10 mock objects) to real astronomical database (13,318 objects), enabling production-ready sky map visualization with timeline support.

**Architecture:** Replace MockDataService with DatabaseService + ModelAdapter pattern (same as Visibility/Recommendations APIs). Load real deep sky objects from SQLite database, convert to API models, and return to frontend for 3D sky map visualization.

**Tech Stack:** FastAPI, aiosqlite, Pydantic, SQLite (OpenNGC database), ModelAdapter pattern

---

## Context

### What We're Building

The Sky Map API provides two endpoints:
1. `/api/v1/skymap/data` - Returns all visible targets for a given location/time
2. `/api/v1/skymap/timeline` - Returns position tracking for specific targets over time

Currently both use `MockDataService.load_targets()` which returns only 10 hardcoded objects. We'll migrate to use `DatabaseService` to access 13,318 real astronomical objects.

### Why This Matters

- Users sliding the timeline see only 10 mock objects instead of 13,318 real objects
- Timeline feature should show any real deep sky object (NGC, IC catalogs)
- Consistent with Visibility/Recommendations APIs (already migrated)

### Migration Pattern

Follow the exact same pattern used in Visibility/Recommendations migration:

```python
# OLD (skymap.py:50)
targets = mock_service.load_targets()  # 10 mock objects

# NEW
db_objects = await db_service.get_objects_by_type("GALAXY")
targets = [model_adapter.to_target(obj) for obj in db_objects]
```

---

## Task 1: Migrate `/data` Endpoint to Real Database

**Files:**
- Modify: `backend/app/api/skymap.py:6,10,48-93`
- Test: `backend/tests/test_api/test_skymap.py` (create new)

**Step 1: Write the failing test**

Create file `backend/tests/test_api/test_skymap.py`:

```python
"""Tests for Sky Map API with real database"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_skymap_data_returns_real_objects():
    """Test /data endpoint returns real database objects, not mock data"""
    response = client.post(
        "/api/v1/skymap/data",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00",
            "include_targets": True,
            "target_types": []
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "targets" in data["data"]

    targets = data["data"]["targets"]
    # Mock data has only 10 objects
    # Real database should return many more (even after filtering by visibility)
    assert len(targets) > 10, "Should return more than 10 mock objects"

    # Verify we have real database IDs (NGC/IC format)
    real_ids = [t["id"] for t in targets if t["id"].startswith(("NGC", "IC"))]
    assert len(real_ids) > 0, "Should have NGC/IC objects from real database"

@pytest.mark.asyncio
async def test_skymap_data_with_type_filter():
    """Test /data endpoint with type filter"""
    response = client.post(
        "/api/v1/skymap/data",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00",
            "include_targets": True,
            "target_types": ["galaxy", "cluster"]
        }
    )

    assert response.status_code == 200
    data = response.json()
    targets = data["data"]["targets"]

    # All targets should be of specified types
    for target in targets:
        assert target["type"] in ["galaxy", "cluster"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_api/test_skymap.py -v`

Expected: FAIL - Test will fail because current implementation only returns 10 mock objects, and some may not be visible or match the type filter

**Step 3: Write minimal implementation**

Modify `backend/app/api/skymap.py`:

```python
# Line 6: Replace import
from app.services.mock_data import MockDataService
# Change to:
from app.services.database import DatabaseService
from app.services.model_adapter import ModelAdapter

# Line 10: Replace service initialization
mock_service = MockDataService()
# Change to:
db_service = DatabaseService()
model_adapter = ModelAdapter()

# Lines 48-93: Replace the entire "if include_targets:" block
# OLD:
if include_targets:
    targets = mock_service.load_targets()
    if target_types:
        targets = [t for t in targets if t.type in target_types]
    # ... rest of code

# NEW:
if include_targets:
    # Load targets from database based on type filters
    if target_types:
        # Load specific types
        all_db_objects = []
        for obj_type in target_types:
            # Normalize API type to database type (galaxy -> GALAXY)
            db_type = obj_type.upper()
            objects = await db_service.get_objects_by_type(db_type)
            all_db_objects.extend(objects)
        # Limit to prevent overwhelming response
        all_db_objects = all_db_objects[:500]
    else:
        # Load sample objects from each type (500 each)
        all_db_objects = []
        for obj_type in ["GALAXY", "NEBULA", "CLUSTER"]:
            objects = await db_service.get_objects_by_type(obj_type)
            all_db_objects.extend(objects[:500])

    # Convert database models to API models
    targets = [model_adapter.to_target(obj) for obj in all_db_objects]

    # Calculate position for each target
    targets_with_position = []
    for target in targets:
        try:
            alt, az = astronomy_service.calculate_position(
                target.ra,
                target.dec,
                location.get("latitude", 39.9042),
                location.get("longitude", 116.4074),
                timestamp
            )

            # Only include targets above horizon
            if alt > 0:
                color_map = {
                    "emission-nebula": "#FF6B6B",
                    "galaxy": "#FFB86C",
                    "cluster": "#FFD93D",
                    "planetary-nebula": "#6BCF7F",
                    "supernova-remnant": "#A78BFA"
                }
                color = color_map.get(target.type, "#FFFFFF")

                targets_with_position.append({
                    "id": target.id,
                    "name": target.name,
                    "altitude": round(alt, 2),
                    "azimuth": round(az, 2),
                    "type": target.type,
                    "magnitude": target.magnitude,
                    "color": color
                })
        except Exception as e:
            print(f"Error calculating position for {target.id}: {e}")
            continue

    data["targets"] = targets_with_position
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_api/test_skymap.py -v`

Expected: PASS - Both tests should pass, showing real database objects are returned

**Step 5: Commit**

```bash
cd backend
git add app/api/skymap.py tests/test_api/test_skymap.py
git commit -m "feat: migrate /data endpoint to use real database"
```

---

## Task 2: Migrate `/timeline` Endpoint to Real Database

**Files:**
- Modify: `backend/app/api/skymap.py:105-170`
- Test: `backend/tests/test_api/test_skymap.py` (append tests)

**Step 1: Write the failing test**

Append to `backend/tests/test_api/test_skymap.py`:

```python
@pytest.mark.asyncio
async def test_skymap_timeline_with_real_target():
    """Test /timeline endpoint with real database target"""
    response = client.post(
        "/api/v1/skymap/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 60,
            "target_ids": ["NGC0224"]  # Andromeda Galaxy
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "timeline" in data["data"]

    timeline = data["data"]["timeline"]
    # Should have multiple time points (18:00 to 23:59 with 60 min interval)
    assert len(timeline) > 0

    # Each timeline entry should have positions
    first_entry = timeline[0]
    assert "timestamp" in first_entry
    assert "targets" in first_entry

@pytest.mark.asyncio
async def test_skymap_timeline_multiple_targets():
    """Test /timeline endpoint with multiple real targets"""
    response = client.post(
        "/api/v1/skymap/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 30,
            "target_ids": ["NGC0224", "NGC1952"]  # Andromeda + Crab Nebula
        }
    )

    assert response.status_code == 200
    data = response.json()
    timeline = data["data"]["timeline"]

    # Should have data for both targets
    assert len(timeline) > 0
    # At least some time points should have targets visible
    visible_entries = [t for t in timeline if len(t["targets"]) > 0]
    assert len(visible_entries) > 0
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_api/test_skymap.py::test_skymap_timeline_with_real_target -v`

Expected: FAIL - `mock_service.get_target_by_id("NGC0224")` returns None because mock data only has 10 objects

**Step 3: Write minimal implementation**

Modify `backend/app/api/skymap.py`, replace the `/timeline` endpoint (lines 105-170):

```python
@router.post("/timeline")
async def get_sky_map_timeline(request: dict) -> dict:
    """获取时间轴数据"""
    try:
        location = request.get("location", {})
        date_str = request.get("date")
        interval_minutes = request.get("interval_minutes", 30)
        target_ids = request.get("target_ids", [])

        # 解析日期
        if date_str:
            date = datetime.fromisoformat(date_str)
        else:
            date = datetime.now()

        # 生成时间序列
        from datetime import timedelta
        start_time = date.replace(hour=18, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        timeline = []
        current = start_time
        while current <= end_time:
            try:
                # 计算每个目标在此时刻的位置
                positions = []
                for target_id in target_ids:
                    # Load from database instead of mock service
                    obj = await db_service.get_object_by_id(target_id)
                    if obj:
                        # Convert to API model
                        target = model_adapter.to_target(obj)

                        alt, az = astronomy_service.calculate_position(
                            target.ra,
                            target.dec,
                            location.get("latitude", 39.9042),
                            location.get("longitude", 116.4074),
                            current
                        )

                        if alt > 0:
                            positions.append({
                                "id": target_id,
                                "altitude": round(alt, 2),
                                "azimuth": round(az, 2)
                            })

                timeline.append({
                    "timestamp": current.isoformat(),
                    "targets": positions
                })

                current += timedelta(minutes=interval_minutes)

            except Exception as e:
                print(f"Error calculating timeline for {current}: {e}")
                break

        return {
            "success": True,
            "data": {
                "date": date_str,
                "timeline": timeline
            },
            "message": "获取时间轴数据成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间轴数据失败: {str(e)}")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_api/test_skymap.py::test_skymap_timeline_with_real_target -v`

Expected: PASS - Real target NGC0224 is fetched from database and timeline is calculated

**Step 5: Commit**

```bash
cd backend
git add app/api/skymap.py tests/test_api/test_skymap.py
git commit -m "feat: migrate /timeline endpoint to use real database"
```

---

## Task 3: Add Integration Tests for Sky Map

**Files:**
- Create: `backend/tests/integration/test_skymap_e2e.py`
- Test: `backend/tests/integration/test_skymap_e2e.py`

**Step 1: Write the failing test**

Create file `backend/tests/integration/test_skymap_e2e.py`:

```python
"""Integration tests for Sky Map API - end-to-end workflows"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_e2e_skymap_data_to_timeline_workflow():
    """Test: Get sky map data → use target IDs in timeline"""
    # Step 1: Get sky map data with targets
    data_response = client.post(
        "/api/v1/skymap/data",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "timestamp": "2025-01-28T22:00:00",
            "include_targets": True,
            "target_types": ["galaxy"]
        }
    )

    assert data_response.status_code == 200
    data_data = data_response.json()
    assert data_data["success"] is True

    targets = data_data["data"]["targets"]
    assert len(targets) > 0

    # Step 2: Use first 3 target IDs in timeline request
    target_ids = [t["id"] for t in targets[:3]]

    timeline_response = client.post(
        "/api/v1/skymap/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 60,
            "target_ids": target_ids
        }
    )

    assert timeline_response.status_code == 200
    timeline_data = timeline_response.json()
    assert timeline_data["success"] is True
    assert "timeline" in timeline_data["data"]
    assert len(timeline_data["data"]["timeline"]) > 0

@pytest.mark.asyncio
async def test_e2e_skymap_search_to_data_workflow():
    """Test: Search target → get sky map data with that target"""
    # Step 1: Search for Andromeda
    search_response = client.get("/api/v1/targets/search?q=Andromeda")

    assert search_response.status_code == 200
    search_data = search_response.json()
    targets = search_data["data"]["targets"]
    assert len(targets) > 0

    andromeda_id = targets[0]["id"]

    # Step 2: Get sky map timeline for Andromeda
    timeline_response = client.post(
        "/api/v1/skymap/timeline",
        json={
            "location": {"latitude": 39.9, "longitude": 116.4},
            "date": "2025-01-28",
            "interval_minutes": 30,
            "target_ids": [andromeda_id]
        }
    )

    assert timeline_response.status_code == 200
    timeline_data = timeline_response.json()
    assert timeline_data["success"] is True

    # Verify Andromeda appears in timeline
    timeline = timeline_data["data"]["timeline"]
    andromeda_positions = [
        entry for entry in timeline
        if any(t["id"] == andromeda_id for t in entry["targets"])
    ]
    assert len(andromeda_positions) > 0, "Andromeda should be visible at some times"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/integration/test_skymap_e2e.py -v`

Expected: FAIL - Tests will fail if Tasks 1-2 not completed, or if API doesn't work with real data

**Step 3: Write minimal implementation**

No implementation needed - this is an integration test that validates the work from Tasks 1-2

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/integration/test_skymap_e2e.py -v`

Expected: PASS - All integration tests pass with real database

**Step 5: Commit**

```bash
cd backend
git add tests/integration/test_skymap_e2e.py
git commit -m "test: add integration tests for sky map API"
```

---

## Task 4: Update Migration Documentation

**Files:**
- Modify: `backend/MIGRATION_GUIDE.md`
- Modify: `docs/progress/2025-01-28-visibility-recommendations-real-database-migration.md`

**Step 1: Write the test (verify documentation needs update)**

Check if `backend/MIGRATION_GUIDE.md` still mentions skymap as not migrated:

Run: `grep -n "skymap\|Skymap\|SKYMAP" backend/MIGRATION_GUIDE.md`

Expected: FIND - Section "1. Skymap API Not Migrated" exists

**Step 2: Run test to verify it fails**

This is a documentation task - no test failure expected

**Step 3: Write minimal implementation**

Modify `backend/MIGRATION_GUIDE.md`:

Find the section:
```markdown
### 1. Skymap API Not Migrated

**Status:** Still uses MockDataService

**Reason:** Out of scope for current migration

**Future Work:** Migrate in separate task
```

Replace with:
```markdown
### 1. All APIs Migrated ✅

**Status:** All APIs now use real database

**Completed:** 2025-01-28

**Summary:**
- Visibility API: Migrated to DatabaseService + ModelAdapter
- Recommendations API: Migrated to DatabaseService + ModelAdapter
- Skymap API: Migrated to DatabaseService + ModelAdapter

**Result:** No more MockDataService usage in production APIs
```

Also update the `docs/progress/2025-01-28-visibility-recommendations-real-database-migration.md`:

Append to the end of the file:
```markdown
---

## Follow-up: Sky Map API Migration (2025-01-28)

### Additional Work

**Date:** 2025-01-28
**Files:** `backend/app/api/skymap.py`

Migrated Sky Map API to complete the full database migration:
- `/data` endpoint now loads real objects from database
- `/timeline` endpoint now fetches real targets by ID
- Added comprehensive test coverage (4 API tests + 2 integration tests)
- Updated migration guide to reflect 100% completion

**Impact:** Users can now slide timeline and see 13,318 real astronomical objects instead of 10 mock objects.

**Tests:** 6/6 passing
```

**Step 4: Run test to verify it passes**

Run: `grep -A 5 "All APIs Migrated" backend/MIGRATION_GUIDE.md`

Expected: PASS - Documentation shows migration is complete

**Step 5: Commit**

```bash
cd backend
git add MIGRATION_GUIDE.md
cd ..
git add docs/progress/2025-01-28-visibility-recommendations-real-database-migration.md
git commit -m "docs: update migration guide - all APIs now use real database"
```

---

## Task 5: Verify Full Test Suite and Performance

**Files:**
- Test: All backend tests

**Step 1: Write the test (run full test suite)**

Run: `cd backend && pytest tests/ -v --tb=short`

**Step 2: Run test to verify it passes**

Expected: PASS - All tests pass including new skymap tests

Check results:
- `tests/test_api/test_skymap.py`: 4 tests
- `tests/integration/test_skymap_e2e.py`: 2 tests
- All existing tests still pass

**Step 3: Verify with real API calls**

Start backend: `cd backend && uvicorn app.main:app --reload`

Test `/data` endpoint:
```bash
curl -X POST "http://localhost:8000/api/v1/skymap/data" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": 39.9, "longitude": 116.4},
    "timestamp": "2025-01-28T22:00:00",
    "include_targets": true
  }' | jq '.data.targets | length'
```

Expected: > 10 (proves real data, not mock)

Test `/timeline` endpoint:
```bash
curl -X POST "http://localhost:8000/api/v1/skymap/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": 39.9, "longitude": 116.4},
    "date": "2025-01-28",
    "interval_minutes": 60,
    "target_ids": ["NGC0224"]
  }' | jq '.data.timeline | length'
```

Expected: > 0 (timeline entries for Andromeda)

**Step 4: Performance check**

Load 500 galaxies with position calculations - should complete in < 3 seconds

**Step 5: Final commit if any fixes needed**

```bash
cd backend
git add ...
git commit -m "fix: ..."
```

---

## Success Criteria

After completing all tasks:

- [ ] `/data` endpoint returns real database objects (not 10 mock objects)
- [ ] `/timeline` endpoint works with any NGC/IC target ID
- [ ] All 4 skymap API tests pass
- [ ] All 2 integration tests pass
- [ ] All existing tests still pass (no regressions)
- [ ] Documentation updated (MIGRATION_GUIDE.md)
- [ ] Progress doc updated with follow-up section
- [ ] Manual verification with curl shows > 10 targets returned
- [ ] Timeline works with real NGC/IC IDs

---

## Technical Notes

### Database Query Strategy

For `/data` endpoint, we load objects by type:
- No filters: 500 each from GALAXY, NEBULA, CLUSTER (1,500 total)
- With filters: Up to 500 from each specified type

This prevents overwhelming the frontend while providing sufficient real data.

### Type Normalization

API uses lowercase types (galaxy, cluster, nebula) but database uses uppercase (GALAXY, CLUSTER, NEBULA). ModelAdapter handles this conversion.

### Position Calculation

AstronomyService.calculate_position() works with RA/Dec from database objects, same as before. No changes needed.

---

## Migration Complete

After this migration, all three APIs (Visibility, Recommendations, Skymap) will use the real astronomical database with 13,318 objects, completing the production readiness of the backend system.
