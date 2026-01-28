# Database Migration Guide

## Completed Migrations

### ✅ Targets API
- Migrated to DatabaseService
- Supports 13,318 objects from OpenNGC
- SIMBAD fallback for missing objects

### ✅ Visibility API (2025-01-28)
- Migrated from MockDataService to DatabaseService
- All 13,318 objects available for position calculations
- Uses ModelAdapter for data conversion

### ✅ Recommendations API (2025-01-28)
- Migrated from MockDataService to DatabaseService
- Real-time scoring and ranking from full database
- Filter support by type, magnitude
- Loads 1,500 sample objects when no filters specified

### ✅ Skymap API (2025-01-28)
- Migrated from MockDataService to DatabaseService
- `/data` endpoint loads 841+ real objects from database
- `/timeline` endpoint works with all NGC/IC objects
- Replaced 10 mock objects with real astronomical data

### All APIs Migrated ✅

**Status:** All APIs now use real database

**Completed:** 2025-01-28

**Summary:**
- Visibility API: Migrated to DatabaseService + ModelAdapter
- Recommendations API: Migrated to DatabaseService + ModelAdapter
- Skymap API: Migrated to DatabaseService + ModelAdapter

**Result:** No more MockDataService usage in production APIs

## Model Conversion

The `ModelAdapter` service converts between:
- `DeepSkyObject` (database model) → `DeepSkyTarget` (API model)

This maintains API compatibility while using real data.

## Testing

Run tests to verify migrations:
```bash
pytest tests/test_api/test_visibility.py -v
pytest tests/test_api/test_recommendations.py -v
pytest tests/test_database_service.py -v
pytest tests/test_model_adapter.py -v
```

## Performance

- Local query: 1-5ms
- Search query: 10-20ms
- Batch query (100 objects): 30-50ms
- Type filter (10,749 galaxies): 90-100ms
- Recommendations generation: <2 seconds
