# Real Astronomical Data Integration Design

**Date**: 2026-01-24
**Version**: 1.0
**Status**: Design Approved

## Overview

This document describes the design for integrating real astronomical data into AI Skywatcher, replacing the current mock data with authentic deep-sky object information from OpenNGC and SIMBAD.

**Goals:**
- Replace mock data with real deep-sky objects (Messier, Caldwell, NGC/IC catalogs)
- Prioritize local performance with API fallback
- Support ~10,000+ objects with comprehensive observational data
- Maintain fast query responses (<5ms for local data)

**Scope:**
- Messier catalog (110 objects)
- Caldwell catalog (109 objects)
- NGC/IC catalog (~10,000+ objects)
- Total: ~500-1,000 high-value targets initially

---

## System Architecture

### Three-Tier Architecture

**Data Layer (SQLite)**
- Pre-generated `deep_sky.db` file (~5-10 MB) committed to repository
- Three normalized tables: `objects`, `aliases`, `observational_info`
- Indexed on `id`, `name`, and `ra`/`dec` coordinates for fast lookups
- Serves 99%+ of queries without network calls

**Service Layer**
- `DatabaseService` for local SQLite queries
- `SIMBADService` for on-demand API fallback
- `ImportService` (development only) for OpenNGC → SQLite conversion
- `AstronomyService` enhanced to orchestrate both services
- All services use Pydantic models for type safety

**API Layer** (FastAPI routes)
- Existing endpoints (`/targets`, `/targets/{id}`) use local DB
- New `/targets/sync` endpoint (admin only) for manual API refresh
- New `/targets/stats` endpoint for database statistics
- Transparent fallback to SIMBAD if object not found locally

### Query Flow

```
1. Request → Check SQLite (1-5ms)
2. Found → Return immediately
3. Not found → Query SIMBAD TAP API (200-500ms)
4. API success → Cache in SQLite + return
5. API failure → Log error + return "not found"
```

---

## Database Schema

### Table: `objects`

Primary table for core object data.

```sql
CREATE TABLE objects (
  id TEXT PRIMARY KEY,              -- e.g., "M31", "NGC224"
  name TEXT NOT NULL,               -- Common name: "Andromeda Galaxy"
  type TEXT NOT NULL,               -- 'GALAXY', 'NEBULA', 'CLUSTER'
  ra REAL NOT NULL,                 -- Right Ascension (degrees)
  dec REAL NOT NULL,                -- Declination (degrees)
  magnitude REAL,                   -- Apparent magnitude
  size_major REAL,                  -- Major axis (arcminutes)
  size_minor REAL,                  -- Minor axis (arcminutes)
  constellation TEXT,               -- Parent constellation
  surface_brightness REAL,          -- Surface brightness (mag/arcmin²)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_objects_ra_dec ON objects(ra, dec);
CREATE INDEX idx_objects_constellation ON objects(constellation);
CREATE INDEX idx_objects_type ON objects(type);
```

### Table: `aliases`

Alternative names and identifiers.

```sql
CREATE TABLE aliases (
  object_id TEXT NOT NULL,
  alias TEXT NOT NULL,
  FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE,
  PRIMARY KEY (object_id, alias)
);

CREATE INDEX idx_aliases_alias ON aliases(alias);
```

### Table: `observational_info`

Viewing guidance and difficulty ratings.

```sql
CREATE TABLE observational_info (
  object_id TEXT PRIMARY KEY,
  best_month INTEGER,               -- Best viewing month (1-12)
  difficulty TEXT,                  -- 'EASY', 'MODERATE', 'DIFFICULT'
  min_aperture REAL,                -- Recommended telescope aperture (mm)
  min_magnitude REAL,               -- Faintest detail visible
  notes TEXT,                       -- Observing tips
  FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
);
```

**Example: M31 (Andromeda Galaxy)**
- One entry in `objects` (id="M31", name="Andromeda Galaxy")
- Three entries in `aliases` ("M31", "NGC224", "Andromeda Galaxy")
- One entry in `observational_info` (best_month=10, difficulty="EASY")

---

## Service Layer Components

### DatabaseService

New service for local SQLite queries.

```python
class DatabaseService:
    def __init__(self, db_path: str = "app/data/deep_sky.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_indexes()

    def get_object_by_id(self, object_id: str) -> Optional[DeepSkyObject]:
        """Fetch object with aliases and observational info"""
        # Join query across 3 tables
        # Return None if not found

    def search_objects(self, name: str) -> List[DeepSkyObject]:
        """Search by name/alias using LIKE query"""

    def get_objects_by_constellation(self, constellation: str) -> List[DeepSkyObject]:
        """Query by constellation with index"""

    def get_objects_by_type(self, obj_type: str) -> List[DeepSkyObject]:
        """Query by type with index"""

    def save_object(self, obj: DeepSkyObject) -> None:
        """Insert or update object (used by SIMBAD cache)"""

    def get_statistics(self) -> Dict:
        """Return database statistics"""
```

### SIMBADService

New service for API fallback.

```python
class SIMBADService:
    BASE_URL = "http://simbad.u-strasbg.fr/simbad/sim-tap"
    TIMEOUT = 10  # seconds

    async def query_object(self, object_id: str) -> Optional[DeepSkyObject]:
        """Query SIMBAD TAP API for single object"""
        # Use ADQL: SELECT ... FROM basic WHERE ...
        # Parse response, return Pydantic model
        # Return None if not found or API error

    async def query_objects_batch(self, object_ids: List[str]) -> List[DeepSkyObject]:
        """Batch query multiple objects in one request"""
        # ADQL: WHERE oid IN (...)
        # More efficient than multiple single queries
```

### AstronomyService (Enhanced)

Orchestration service combining both data sources.

```python
class AstronomyService:
    def __init__(self):
        self.db = DatabaseService()
        self.simbad = SIMBADService()

    async def get_object(self, object_id: str) -> Optional[DeepSkyObject]:
        """Get object with automatic fallback"""
        # 1. Try local database
        obj = self.db.get_object_by_id(object_id)
        if obj:
            return obj

        # 2. Fallback to SIMBAD API
        obj = await self.simbad.query_object(object_id)
        if obj:
            self.db.save_object(obj)  # Cache locally
            return obj

        # 3. Not found
        return None
```

---

## Data Import Workflow

### One-Time Import Script

**File:** `scripts/import_openngc.py`

```python
"""
OpenNGC → SQLite Import Script
Run once: python scripts/import_openngc.py
Output: app/data/deep_sky.db
"""

def import_openngc():
    # 1. Download OpenNGC JSON from GitHub
    url = "https://github.com/mundialogue/OpenNGC/blob/master/data/openngc.json"
    data = fetch_json(url)  # ~10,000 objects

    # 2. Initialize SQLite database
    conn = sqlite3.connect("app/data/deep_sky.db")
    create_tables(conn)

    # 3. Transform and insert data
    for item in data:
        # Map OpenNGC fields to our schema
        obj = {
            "id": f"M{item['messier']}" if item['messier'] else f"NGC{item['ngc']}",
            "name": item['name'],
            "type": map_type(item['type']),
            "ra": item['ra'],
            "dec": item['dec'],
            "magnitude": item['mag'],
            "size_major": item['size_major'],
            "size_minor": item['size_minor'],
            "constellation": item['constellation']
        }

        insert_object(conn, obj)

        # Insert aliases
        for alias in item['identifiers']:
            insert_alias(conn, obj['id'], alias)

        # Insert observational info
        insert_observational_info(conn, {
            "object_id": obj['id'],
            "best_month": calculate_best_month(obj['ra']),
            "difficulty": calculate_difficulty(obj),
            "min_aperture": estimate_aperture(obj['magnitude']),
            "notes": generate_notes(item)
        })

    # 4. Create indexes and optimize
    create_indexes(conn)
    conn.commit()
    print(f"✅ Imported {len(data)} objects to deep_sky.db")
```

### OpenNGC Field Mapping

| OpenNGC Field | Our Schema | Notes |
|--------------|-----------|-------|
| `messier` | `id` (e.g., M31) | Priority identifier |
| `ngc` | `aliases` | Secondary identifier |
| `name` | `name` | Common name |
| `type` | `type` | Mapped to enum |
| `ra` | `ra` | Already in degrees |
| `dec` | `dec` | Already in degrees |
| `mag` | `magnitude` | Apparent magnitude |
| `constellation` | `constellation` | Direct use |
| `identifiers`[] | `aliases` | Array of names |

### Workflow

1. Run import script during development
2. Generated `deep_sky.db` (~5-10 MB)
3. Commit to `backend/app/data/` directory
4. Production code reads from pre-generated file

---

## SIMBAD TAP API Integration

### TAP Query Implementation

```python
class SIMBADService:
    BASE_URL = "https://simbad.u-strasbg.fr/simbad/sim-tap"
    TIMEOUT = 10  # seconds

    async def query_object(self, object_id: str) -> Optional[DeepSkyObject]:
        """Query SIMBAD for single object by ID"""

        # Parse ID to extract number
        num = extract_number(object_id)  # "M31" → 31, "NGC224" → 224

        # Build ADQL query
        query = f"""
            SELECT
                oid, main_id, ra, dec,
                galdim_majaxis, galdim_minaxis,
                V, sp_type, all_types
            FROM basic
            WHERE oid = '{object_id}'
               OR messier = {num}
               OR ngc = {num}
            LIMIT 1
        """

        # Execute TAP query
        response = await self._execute_tap_query(query)

        if not response or not response.get('data'):
            logger.warning(f"SIMBAD: Object {object_id} not found")
            return None

        # Transform SIMBAD response to our model
        row = response['data'][0]
        return self._parse_simbad_row(object_id, row)

    async def query_objects_batch(self, object_ids: List[str]) -> List[DeepSkyObject]:
        """Batch query multiple objects efficiently"""

        # Build IN clause
        ids_str = ", ".join([f"'{id}'" for id in object_ids])
        query = f"""
            SELECT oid, main_id, ra, dec, galdim_majaxis, galdim_minaxis, V
            FROM basic
            WHERE oid IN ({ids_str})
        """

        response = await self._execute_tap_query(query)
        return [self._parse_simbad_row(row['oid'], row) for row in response['data']]

    async def _execute_tap_query(self, adql: str) -> Dict:
        """Execute ADQL query via TAP sync endpoint"""
        params = {
            'request': 'doQuery',
            'lang': 'adql',
            'query': adql,
            'format': 'json'
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.BASE_URL}/sync",
                    data=params,
                    timeout=self.TIMEOUT
                )
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as e:
                logger.error(f"SIMBAD API error: {e}")
                return None
```

### Response Parsing

```python
def _parse_simbad_row(self, object_id: str, row: Dict) -> DeepSkyObject:
    """Map SIMBAD TAP response to our Pydantic model"""
    return DeepSkyObject(
        id=object_id,
        name=row['main_id'].decode('utf-8'),
        type=self._map_simbad_type(row['all_types']),
        ra=float(row['ra']),
        dec=float(row['dec']),
        magnitude=float(row['V']) if row['V'] else None,
        size_major=float(row['galdim_majaxis']) if row['galdim_majaxis'] else None,
        size_minor=float(row['galdim_minaxis']) if row['galdim_minaxis'] else None
    )
```

---

## Error Handling and Logging

### Error Handling Hierarchy

**1. Database Errors (Critical)**
```python
try:
    obj = await astronomy_service.get_object(object_id)
except sqlite3.DatabaseError as e:
    logger.critical(f"Database corruption: {e}")
    raise HTTPException(
        status_code=500,
        detail="Database error. Please contact administrator."
    )
```

**2. SIMBAD API Errors (Non-Critical)**
```python
# Logged but don't crash the request
logger.warning(f"SIMBAD fallback failed for {object_id}: {error}")
# Return "not found" to user
return {"success": True, "data": None, "message": "Object not found"}
```

**3. Query Not Found (Expected)**
```python
# No logging needed, just return empty
return {"success": True, "data": None, "message": "Object not found"}
```

### Logging Configuration

```python
# backend/app/config.py
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/astronomy.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        'astronomy': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': False
        }
    }
}
```

### Log Levels

- **DEBUG**: API query details (disabled in production)
- **INFO**: Object not found in local DB (triggers API fallback)
- **WARNING**: SIMBAD API errors, rate limits, timeouts
- **ERROR**: Database connection failures, data corruption
- **CRITICAL**: Database completely unavailable

### Example Log Output

```
2026-01-24 10:30:15 INFO astronomy.service: Object IC1234 not found locally, querying SIMBAD
2026-01-24 10:30:15 WARNING astronomy.simbad: SIMBAD API timeout for IC1234
2026-01-24 10:30:15 INFO astronomy.api: Returning "not found" for IC1234
```

---

## API Endpoints

### Existing Endpoints (Enhanced)

**GET `/api/v1/targets/{id}`**
- Checks local SQLite first (~1-5ms)
- Falls back to SIMBAD API if not found (~200-500ms)
- Caches API results in SQLite

```python
@router.get("/{id}")
async def get_target(id: str):
    obj = await astronomy_service.get_object(id)

    if not obj:
        return {
            "success": True,
            "data": None,
            "message": "Object not found"
        }

    return {
        "success": True,
        "data": obj_to_dict(obj),
        "message": "Object retrieved successfully"
    }
```

**GET `/api/v1/targets/search?q=`**
- Uses LIKE query on aliases table
- Returns partial matches (e.g., "Andromeda" → M31)

```python
@router.get("/search")
async def search_targets(q: str, limit: int = 20):
    results = await db_service.search_objects(q)
    return {
        "success": True,
        "data": {"targets": results[:limit]},
        "message": f"Found {len(results)} objects"
    }
```

### New Endpoints

**POST `/api/v1/targets/sync`** (Admin only)
- Manually trigger SIMBAD sync for specific objects
- Useful for refreshing data or adding new objects

```python
@router.post("/sync")
async def sync_from_simbad(request: SyncRequest):
    synced = []
    failed = []

    for object_id in request.object_ids:
        obj = await simbad_service.query_object(object_id)
        if obj:
            db_service.save_object(obj)
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
```

**GET `/api/v1/targets/stats`**
- Return database statistics
- Total object count
- Objects by type
- Coverage by constellation

```python
@router.get("/stats")
async def get_database_stats():
    stats = await db_service.get_statistics()
    return {"success": True, "data": stats}
```

---

## Implementation Plan

### Phase 1: Database and Import (Week 1)

**Tasks:**
1. Create database schema SQL scripts
2. Implement `ImportService` for OpenNGC → SQLite
3. Run import script and generate `deep_sky.db`
4. Add database file to repository
5. Write unit tests for database queries

**Deliverables:**
- `app/data/deep_sky.db` (~5-10 MB)
- `scripts/import_openngc.py`
- `tests/test_database.py`

### Phase 2: Service Layer (Week 2)

**Tasks:**
1. Implement `DatabaseService` with CRUD operations
2. Implement `SIMBADService` with TAP API integration
3. Enhance `AstronomyService` with fallback logic
4. Add Pydantic models for database entities
5. Write unit tests for all services

**Deliverables:**
- `app/services/database.py`
- `app/services/simbad.py`
- `app/models/database.py`
- `tests/test_services.py`

### Phase 3: API Integration (Week 3)

**Tasks:**
1. Update existing endpoints to use new services
2. Add new admin endpoints (`/sync`, `/stats`)
3. Update API documentation (OpenAPI)
4. Write integration tests for API endpoints
5. Performance testing and optimization

**Deliverables:**
- Updated API routes
- API documentation
- `tests/test_api_integration.py`
- Performance benchmarks

### Phase 4: Frontend Integration (Week 4)

**Tasks:**
1. Update frontend to handle larger dataset
2. Add search by alias functionality
3. Display observational info (difficulty, best month)
4. Add sync UI for admin users
5. Testing with real data

**Deliverables:**
- Updated frontend components
- New observational info display
- Admin sync interface

---

## Testing Strategy

### Unit Tests

**DatabaseService Tests:**
- Test object retrieval by ID
- Test search functionality
- Test constellation and type queries
- Test alias lookup

**SIMBADService Tests:**
- Mock SIMBAD API responses
- Test single object queries
- Test batch queries
- Test error handling (timeout, 404, 500)

**AstronomyService Tests:**
- Test local database fallback
- Test API fallback trigger
- Test caching behavior
- Test error scenarios

### Integration Tests

**API Endpoint Tests:**
- Test `/targets/{id}` with local objects
- Test `/targets/{id}` with API fallback
- Test `/targets/search?q=` functionality
- Test `/targets/sync` endpoint

**Performance Tests:**
- Measure local query response time (<5ms target)
- Measure API fallback response time (<500ms target)
- Test concurrent requests (100+ simultaneous)
- Memory usage monitoring

### Data Validation

**OpenNGC Import Validation:**
- Verify all 10,000+ objects imported
- Check coordinate accuracy (sample verification)
- Validate alias mappings
- Verify constellation assignments

**SIMBAD Response Validation:**
- Parse test objects (M31, M42, M45)
- Validate field mappings
- Check coordinate transformation accuracy

---

## Performance Considerations

### Expected Performance

| Operation | Expected Time | Notes |
|-----------|--------------|-------|
| Local DB query | 1-5 ms | With indexes |
| SIMBAD API fallback | 200-500 ms | Network dependent |
| Search (LIKE query) | 5-20 ms | Depends on results |
| Batch API query (10 objects) | 300-800 ms | Single TAP request |

### Optimization Strategies

1. **Indexing**: All frequently queried fields indexed
2. **Connection Pooling**: Reuse SQLite connections
3. **Query Caching**: Cache common queries in memory
4. **Batch API Requests**: Use TAP batch queries for multiple objects
5. **Async Operations**: All API calls are async (httpx)

---

## Future Enhancements

### Short-term (Post-MVP)

1. **Additional Catalogs**
   - Add IC catalog separately
   - Include Abell planetaries
   - Add Sharpless catalog (emission nebulae)

2. **User Contributions**
   - Allow users to submit observational notes
   - Community difficulty ratings
   - User-uploaded images

3. **Enhanced Search**
   - Full-text search on notes
   - Filter by difficulty, aperture
   - Season-based recommendations

### Long-term

1. **Real-time Updates**
   - Background job to refresh data
   - Periodic SIMBAD sync
   - Change detection and alerts

2. **Extended Data**
   - Cross-references to other catalogs
   - Image URLs (Wikisky, DSS)
   - Spectral data for advanced users

3. **Offline Mode**
   - Progressive Web App (PWA)
   - Service worker for offline access
   - Full offline capability

---

## Dependencies

### Python Packages

```txt
# backend/requirements.txt (additions)
aiosqlite>=0.19.0           # Async SQLite support
httpx>=0.25.0               # Async HTTP client
astral>=3.2                 # Astronomical calculations (optional)
```

### External Services

- **OpenNGC Database**: https://github.com/mundialogue/OpenNGC
- **SIMBAD TAP API**: http://simbad.u-strasbg.fr/simbad/sim-tap

---

## Risks and Mitigation

### Risk 1: SIMBAD API Rate Limiting

**Impact**: Users may hit rate limits during API fallback
**Probability**: Medium
**Mitigation**:
- Local database serves 99%+ of queries
- Implement request queuing if needed
- Add rate limit headers monitoring
- Graceful degradation on API errors

### Risk 2: Database Corruption

**Impact**: System becomes unusable
**Probability**: Low
**Mitigation**:
- Pre-generated database in Git (backup)
- Read-only operations in production
- SQLite transactions and WAL mode
- Regular integrity checks

### Risk 3: SIMBAD API Changes

**Impact**: API fallback breaks
**Probability**: Low
**Mitigation**:
- Use stable TAP standard (less likely to change)
- Version the API client
- Monitor SIMBAD announcements
- Have fallback to cached data

---

## Success Criteria

### Functional Requirements

- ✅ Replace all mock data with real astronomical objects
- ✅ Support Messier, Caldwell, and NGC/IC catalogs
- ✅ Local queries return in <5ms
- ✅ API fallback works transparently
- ✅ Data can be refreshed via admin endpoint

### Non-Functional Requirements

- ✅ Database size <10 MB
- ✅ 99%+ queries served from local database
- ✅ API fallback response time <500ms
- ✅ No data loss during import
- ✅ Comprehensive error logging

### User Experience

- ✅ Users can search by any alias (M31, NGC224, Andromeda)
- ✅ Observational info helps beginners select targets
- ✅ System remains responsive during API fallback
- ✅ Clear error messages when objects not found

---

## Conclusion

This design provides a robust, performant system for integrating real astronomical data into AI Skywatcher. The hybrid approach (local database + API fallback) ensures fast response times while maintaining flexibility for future expansion.

The phased implementation allows for incremental development and testing, with each phase delivering value to users.

**Next Steps:**
1. Review and approve this design
2. Set up development environment
3. Begin Phase 1 implementation

---

**Document Version:** 1.0
**Last Updated:** 2026-01-24
**Status:** Design Approved, Ready for Implementation
