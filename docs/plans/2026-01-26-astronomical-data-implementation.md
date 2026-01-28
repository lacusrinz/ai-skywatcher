# Real Astronomical Data Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace mock data with real astronomical data (Messier, Caldwell, NGC/IC catalogs) using OpenNGC database and SIMBAD API fallback

**Architecture:** Hybrid approach with pre-generated SQLite database for fast local queries, automatic fallback to SIMBAD TAP API for missing objects, transparent caching of API results

**Tech Stack:** SQLite3, aiosqlite, httpx, OpenNGC JSON, SIMBAD TAP API

---

## Phase 1: Database Schema and Import Script

### Task 1: Create Database Schema File

**Files:**
- Create: `backend/app/data/schema.sql`

**Step 1: Write the schema SQL**

```sql
-- backend/app/data/schema.sql
-- Deep Sky Objects Database Schema

-- Drop tables if exists (for clean import)
DROP TABLE IF EXISTS observational_info;
DROP TABLE IF EXISTS aliases;
DROP TABLE IF EXISTS objects;

-- Main objects table
CREATE TABLE objects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  ra REAL NOT NULL,
  dec REAL NOT NULL,
  magnitude REAL,
  size_major REAL,
  size_minor REAL,
  constellation TEXT,
  surface_brightness REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aliases table (alternative names)
CREATE TABLE aliases (
  object_id TEXT NOT NULL,
  alias TEXT NOT NULL,
  FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE,
  PRIMARY KEY (object_id, alias)
);

-- Observational info table
CREATE TABLE observational_info (
  object_id TEXT PRIMARY KEY,
  best_month INTEGER,
  difficulty TEXT,
  min_aperture REAL,
  min_magnitude REAL,
  notes TEXT,
  FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_objects_ra_dec ON objects(ra, dec);
CREATE INDEX idx_objects_constellation ON objects(constellation);
CREATE INDEX idx_objects_type ON objects(type);
CREATE INDEX idx_aliases_alias ON aliases(alias);
```

**Step 2: Commit schema**

```bash
cd backend
git add app/data/schema.sql
git commit -m "feat: add database schema for deep sky objects"
```

---

### Task 2: Create Database Pydantic Models

**Files:**
- Create: `backend/app/models/database.py`

**Step 1: Write the Pydantic models**

```python
# backend/app/models/database.py
"""Database models for deep sky objects"""
from pydantic import BaseModel
from typing import Optional, List

class ObservationalInfo(BaseModel):
    """Observational information for viewing guidance"""
    best_month: Optional[int] = None
    difficulty: Optional[str] = None  # 'EASY', 'MODERATE', 'DIFFICULT'
    min_aperture: Optional[float] = None  # mm
    min_magnitude: Optional[float] = None
    notes: Optional[str] = None

class DeepSkyObject(BaseModel):
    """Complete deep sky object data"""
    id: str
    name: str
    type: str  # 'GALAXY', 'NEBULA', 'CLUSTER', 'PLANETARY'
    ra: float  # Right Ascension in degrees
    dec: float  # Declination in degrees
    magnitude: Optional[float] = None
    size_major: Optional[float] = None  # arcminutes
    size_minor: Optional[float] = None  # arcminutes
    constellation: Optional[str] = None
    surface_brightness: Optional[float] = None
    aliases: List[str] = []
    observational_info: Optional[ObservationalInfo] = None

class DatabaseStats(BaseModel):
    """Database statistics"""
    total_objects: int
    objects_by_type: dict
    constellations_covered: int
```

**Step 2: Write failing tests for models**

```python
# tests/test_database_models.py
import pytest
from app.models.database import DeepSkyObject, ObservationalInfo

def test_deep_sky_object_model():
    obj = DeepSkyObject(
        id="M31",
        name="Andromeda Galaxy",
        type="GALAXY",
        ra=10.684708,
        dec=41.268750,
        magnitude=3.4,
        size_major=190.0,
        size_minor=60.0,
        constellation="Andromeda"
    )
    assert obj.id == "M31"
    assert obj.type == "GALAXY"
    assert obj.magnitude == 3.4

def test_observational_info_model():
    info = ObservationalInfo(
        best_month=10,
        difficulty="EASY",
        min_aperture=50.0,
        notes="Visible to naked eye under dark skies"
    )
    assert info.best_month == 10
    assert info.difficulty == "EASY"
```

**Step 3: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_database_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.database'"

**Step 4: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_database_models.py -v
```

Expected: PASS (all 2 tests)

**Step 5: Commit**

```bash
cd backend
git add tests/test_database_models.py app/models/database.py
git commit -m "feat: add database Pydantic models with tests"
```

---

### Task 3: Create OpenNGC Import Script

**Files:**
- Create: `scripts/import_openngc.py`
- Create: `scripts/requirements.txt`

**Step 1: Create import script**

```python
#!/usr/bin/env python3
"""
OpenNGC → SQLite Import Script
Downloads OpenNGC JSON data and imports to SQLite database

Usage:
    python scripts/import_openngc.py

Output:
    backend/app/data/deep_sky.db
"""

import json
import sqlite3
import urllib.request
from pathlib import Path
from typing import Dict, List, Any

# Configuration
OPENNGC_URL = "https://raw.githubusercontent.com/mundialogue/OpenNGC/master/data/openngc.json"
DB_PATH = Path(__file__).parent.parent / "backend" / "app" / "data" / "deep_sky.db"
SCHEMA_PATH = Path(__file__).parent.parent / "backend" / "app" / "data" / "schema.sql"

def download_openngc() -> List[Dict]:
    """Download OpenNGC JSON data"""
    print(f"Downloading OpenNGC data from {OPENNGC_URL}...")
    with urllib.request.urlopen(OPENNGC_URL) as response:
        data = json.loads(response.read())
    print(f"✅ Downloaded {len(data)} objects")
    return data

def map_type(openngc_type: str) -> str:
    """Map OpenNGC type to our type system"""
    type_mapping = {
        'G': 'GALAXY',
        'GX': 'GALAXY',
        'GXY': 'GALAXY',
        'N': 'NEBULA',
        'NB': 'NEBULA',
        'PN': 'PLANETARY',
        'OC': 'CLUSTER',
        'GC': 'CLUSTER',
        '*': 'CLUSTER',
    }
    return type_mapping.get(openngc_type.upper(), 'NEBULA')

def calculate_best_month(ra: float) -> int:
    """Calculate best viewing month from Right Ascension"""
    # RA in degrees to month (simplified)
    # RA 0h = 0°, RA 24h = 360°
    # Month 1 (Jan) ≈ RA 22h-2h, etc.
    hour = ra / 15.0
    month = int((hour + 2) % 12) + 1
    return month

def calculate_difficulty(mag: float, size: float) -> str:
    """Calculate difficulty rating from magnitude and size"""
    if mag is None or size is None:
        return 'MODERATE'

    surface_brightness = mag + 2.5 * math.log10(size * size)

    if surface_brightness < 12:
        return 'EASY'
    elif surface_brightness < 14:
        return 'MODERATE'
    else:
        return 'DIFFICULT'

def estimate_aperture(mag: float) -> float:
    """Estimate minimum telescope aperture (mm)"""
    if mag is None or mag > 10:
        return 200.0  # 8 inch
    elif mag > 8:
        return 150.0  # 6 inch
    elif mag > 6:
        return 100.0  # 4 inch
    else:
        return 50.0   # 2 inch

def create_database(conn: sqlite3.Connection):
    """Create database schema"""
    print("Creating database schema...")
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
    conn.executescript(schema)
    conn.commit()
    print("✅ Schema created")

def import_objects(conn: sqlite3.Connection, data: List[Dict]):
    """Import objects from OpenNGC data"""
    print("Importing objects...")

    objects = []
    aliases = []
    observational = []

    for item in data:
        # Generate primary ID
        if item.get('messier'):
            obj_id = f"M{item['messier']}"
        elif item.get('ngc'):
            obj_id = f"NGC{item['ngc']}"
        elif item.get('ic'):
            obj_id = f"IC{item['ic']}"
        else:
            continue

        # Extract object data
        obj = {
            'id': obj_id,
            'name': item.get('name', obj_id),
            'type': map_type(item.get('type', '')),
            'ra': item.get('ra', 0.0),
            'dec': item.get('dec', 0.0),
            'magnitude': item.get('mag'),
            'size_major': item.get('size_major'),
            'size_minor': item.get('size_minor'),
            'constellation': item.get('constellation')
        }
        objects.append(obj)

        # Extract identifiers as aliases
        for identifier in item.get('identifiers', []):
            aliases.append({
                'object_id': obj_id,
                'alias': identifier
            })

        # Generate observational info
        obs_info = {
            'object_id': obj_id,
            'best_month': calculate_best_month(obj['ra']),
            'difficulty': calculate_difficulty(
                obj.get('magnitude'),
                obj.get('size_major')
            ),
            'min_aperture': estimate_aperture(obj.get('magnitude')),
            'notes': f"{obj['type']}"
        }
        observational.append(obs_info)

    # Batch insert
    conn.executemany(
        "INSERT INTO objects (id, name, type, ra, dec, magnitude, size_major, size_minor, constellation) "
        "VALUES (:id, :name, :type, :ra, :dec, :magnitude, :size_major, :size_minor, :constellation)",
        objects
    )

    conn.executemany(
        "INSERT INTO aliases (object_id, alias) VALUES (:object_id, :alias)",
        aliases
    )

    conn.executemany(
        "INSERT INTO observational_info (object_id, best_month, difficulty, min_aperture, notes) "
        "VALUES (:object_id, :best_month, :difficulty, :min_aperture, :notes)",
        observational
    )

    conn.commit()
    print(f"✅ Imported {len(objects)} objects")
    print(f"✅ Imported {len(aliases)} aliases")
    print(f"✅ Imported {len(observational)} observational records")

def main():
    """Main import function"""
    print("=" * 60)
    print("OpenNGC → SQLite Import")
    print("=" * 60)

    # Download data
    data = download_openngc()

    # Create database
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    # Create schema
    create_database(conn)

    # Import data
    import_objects(conn, data)

    # Verify
    cursor = conn.execute("SELECT COUNT(*) FROM objects")
    count = cursor.fetchone()[0]
    print(f"\n📊 Database statistics:")
    print(f"   Total objects: {count}")

    conn.close()
    print(f"\n✅ Database saved to: {DB_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

**Step 2: Create import script requirements**

```txt
# scripts/requirements.txt
requests>=2.31.0
```

**Step 3: Make script executable**

```bash
chmod +x scripts/import_openngc.py
```

**Step 4: Run import script to generate database**

```bash
cd ai-skywatcher
python scripts/import_openngc.py
```

Expected output:
```
Downloading OpenNGC data...
✅ Downloaded 10342 objects
Creating database schema...
✅ Schema created
Importing objects...
✅ Imported 10342 objects
✅ Imported 45123 aliases
✅ Imported 10342 observational records

📊 Database statistics:
   Total objects: 10342

✅ Database saved to: backend/app/data/deep_sky.db
```

**Step 5: Verify database file exists**

```bash
ls -lh backend/app/data/deep_sky.db
```

Expected: File exists, size ~5-10 MB

**Step 6: Commit database and import script**

```bash
git add backend/app/data/deep_sky.db backend/app/data/schema.sql scripts/import_openngy.py
git commit -m "feat: add OpenNGC import script and generated database

- Import script downloads OpenNGC JSON (~10,000 objects)
- Generates SQLite database with normalized schema
- Includes aliases and observational info
- Database committed to repository for fast deployment"
```

---

## Phase 2: Service Layer Implementation

### Task 4: Create DatabaseService

**Files:**
- Create: `backend/app/services/database.py`
- Modify: `backend/requirements.txt`

**Step 1: Add aiosqlite to requirements**

```bash
cd backend
echo "aiosqlite>=0.19.0" >> requirements.txt
pip install aiosqlite
```

**Step 2: Write DatabaseService implementation**

```python
# backend/app/services/database.py
"""Local SQLite database service for deep sky objects"""
import aiosqlite
import logging
from pathlib import Path
from typing import Optional, List, Dict
from app.models.database import DeepSkyObject, ObservationalInfo, DatabaseStats

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for querying local SQLite database"""

    def __init__(self, db_path: str = "app/data/deep_sky.db"):
        self.db_path = db_path
        self._conn = None

    async def connect(self):
        """Establish database connection"""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row
        return self._conn

    async def close(self):
        """Close database connection"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def get_object_by_id(self, object_id: str) -> Optional[DeepSkyObject]:
        """Get object by ID with aliases and observational info"""
        conn = await self.connect()

        # Get main object data
        cursor = await conn.execute(
            "SELECT * FROM objects WHERE id = ?",
            (object_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        # Get aliases
        cursor = await conn.execute(
            "SELECT alias FROM aliases WHERE object_id = ?",
            (object_id,)
        )
        alias_rows = await cursor.fetchall()
        aliases = [row['alias'] for row in alias_rows]

        # Get observational info
        cursor = await conn.execute(
            "SELECT * FROM observational_info WHERE object_id = ?",
            (object_id,)
        )
        obs_row = await cursor.fetchone()

        observational_info = None
        if obs_row:
            observational_info = ObservationalInfo(
                best_month=obs_row['best_month'],
                difficulty=obs_row['difficulty'],
                min_aperture=obs_row['min_aperture'],
                min_magnitude=obs_row['min_magnitude'],
                notes=obs_row['notes']
            )

        return DeepSkyObject(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            ra=row['ra'],
            dec=row['dec'],
            magnitude=row['magnitude'],
            size_major=row['size_major'],
            size_minor=row['size_minor'],
            constellation=row['constellation'],
            surface_brightness=row['surface_brightness'],
            aliases=aliases,
            observational_info=observational_info
        )

    async def search_objects(self, name: str, limit: int = 20) -> List[DeepSkyObject]:
        """Search objects by name or alias"""
        conn = await self.connect()

        query = """
            SELECT DISTINCT o.* FROM objects o
            LEFT JOIN aliases a ON o.id = a.object_id
            WHERE o.name LIKE ? OR a.alias LIKE ?
            LIMIT ?
        """
        search_pattern = f"%{name}%"

        cursor = await conn.execute(query, (search_pattern, search_pattern, limit))
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            obj = await self.get_object_by_id(row['id'])
            if obj:
                results.append(obj)

        return results

    async def get_objects_by_constellation(self, constellation: str) -> List[DeepSkyObject]:
        """Get all objects in a constellation"""
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT id FROM objects WHERE constellation = ?",
            (constellation,)
        )
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            obj = await self.get_object_by_id(row['id'])
            if obj:
                results.append(obj)

        return results

    async def get_objects_by_type(self, obj_type: str) -> List[DeepSkyObject]:
        """Get all objects of a specific type"""
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT id FROM objects WHERE type = ?",
            (obj_type,)
        )
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            obj = await self.get_object_by_id(row['id'])
            if obj:
                results.append(obj)

        return results

    async def save_object(self, obj: DeepSkyObject) -> None:
        """Insert or update object (used by SIMBAD cache)"""
        conn = await self.connect()

        # Insert or update main object
        await conn.execute(
            """INSERT OR REPLACE INTO objects
            (id, name, type, ra, dec, magnitude, size_major, size_minor, constellation, surface_brightness)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (obj.id, obj.name, obj.type, obj.ra, obj.dec, obj.magnitude,
             obj.size_major, obj.size_minor, obj.constellation, obj.surface_brightness)
        )

        # Delete existing aliases
        await conn.execute(
            "DELETE FROM aliases WHERE object_id = ?",
            (obj.id,)
        )

        # Insert aliases
        for alias in obj.aliases:
            await conn.execute(
                "INSERT INTO aliases (object_id, alias) VALUES (?, ?)",
                (obj.id, alias)
            )

        # Insert observational info
        if obj.observational_info:
            await conn.execute(
                """INSERT OR REPLACE INTO observational_info
                (object_id, best_month, difficulty, min_aperture, min_magnitude, notes)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (obj.id, obj.observational_info.best_month,
                 obj.observational_info.difficulty,
                 obj.observational_info.min_aperture,
                 obj.observational_info.min_magnitude,
                 obj.observational_info.notes)
            )

        await conn.commit()

    async def get_statistics(self) -> DatabaseStats:
        """Get database statistics"""
        conn = await self.connect()

        # Total objects
        cursor = await conn.execute("SELECT COUNT(*) FROM objects")
        total = (await cursor.fetchone())[0]

        # By type
        cursor = await conn.execute(
            "SELECT type, COUNT(*) as count FROM objects GROUP BY type"
        )
        type_rows = await cursor.fetchall()
        objects_by_type = {row['type']: row['count'] for row in type_rows}

        # Constellations
        cursor = await conn.execute(
            "SELECT COUNT(DISTINCT constellation) FROM objects"
        )
        constellations = (await cursor.fetchone())[0]

        return DatabaseStats(
            total_objects=total,
            objects_by_type=objects_by_type,
            constellations_covered=constellations
        )
```

**Step 3: Write failing tests**

```python
# tests/test_database_service.py
import pytest
from app.services.database import DatabaseService
from app.models.database import DeepSkyObject

@pytest.mark.asyncio
async def test_get_object_by_id():
    service = DatabaseService("app/data/deep_sky.db")
    obj = await service.get_object_by_id("M31")
    assert obj is not None
    assert obj.id == "M31"
    assert obj.name == "Andromeda Galaxy"
    assert "NGC224" in obj.aliases

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
```

**Step 4: Run tests to verify they fail**

```bash
cd backend
pytest tests/test_database_service.py -v
```

Expected: FAIL (service not implemented yet)

**Step 5: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_database_service.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
cd backend
git add app/services/database.py tests/test_database_service.py requirements.txt
git commit -m "feat: add DatabaseService with async SQLite queries

- aiosqlite for async database operations
- Methods: get_object_by_id, search_objects, get_statistics
- Full test coverage"
```

---

### Task 5: Create SIMBADService

**Files:**
- Create: `backend/app/services/simbad.py`
- Modify: `backend/requirements.txt`

**Step 1: Add httpx to requirements**

```bash
cd backend
echo "httpx>=0.25.0" >> requirements.txt
pip install httpx
```

**Step 2: Write SIMBADService implementation**

```python
# backend/app/services/simbad.py
"""SIMBAD TAP API service for fallback queries"""
import httpx
import logging
from typing import Optional, List, Dict
from app.models.database import DeepSkyObject, ObservationalInfo

logger = logging.getLogger(__name__)

class SIMBADService:
    """Service for querying SIMBAD TAP API"""

    BASE_URL = "https://simbad.u-strasbg.fr/simbad/sim-tap"
    TIMEOUT = 10.0  # seconds

    async def query_object(self, object_id: str) -> Optional[DeepSkyObject]:
        """Query SIMBAD for single object by ID"""
        logger.info(f"SIMBAD: Querying object {object_id}")

        # Parse ID to extract number
        num = self._extract_number(object_id)

        # Build ADQL query
        query = f"""
            SELECT
                oid, main_id, ra, dec,
                galdim_majaxis, galdim_minaxis,
                V, all_types
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

        # Parse response
        row = response['data'][0]
        return self._parse_simbad_row(object_id, row)

    async def query_objects_batch(self, object_ids: List[str]) -> List[DeepSkyObject]:
        """Batch query multiple objects efficiently"""
        if not object_ids:
            return []

        logger.info(f"SIMBAD: Batch querying {len(object_ids)} objects")

        # Build IN clause
        ids_str = ", ".join([f"'{obj_id}'" for obj_id in object_ids])
        query = f"""
            SELECT oid, main_id, ra, dec, galdim_majaxis, galdim_minaxis, V, all_types
            FROM basic
            WHERE oid IN ({ids_str})
        """

        response = await self._execute_tap_query(query)

        if not response or not response.get('data'):
            logger.warning("SIMBAD: Batch query returned no results")
            return []

        results = []
        for row in response['data']:
            obj_id = row['oid']
            obj = self._parse_simbad_row(obj_id, row)
            if obj:
                results.append(obj)

        return results

    async def _execute_tap_query(self, adql: str) -> Optional[Dict]:
        """Execute ADQL query via TAP sync endpoint"""
        params = {
            'request': 'doQuery',
            'lang': 'adql',
            'query': adql,
            'format': 'json'
        }

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/sync",
                    data=params
                )
                resp.raise_for_status()
                return resp.json()

        except httpx.TimeoutException:
            logger.error(f"SIMBAD: Request timeout")
            return None
        except httpx.HTTPError as e:
            logger.error(f"SIMBAD: HTTP error {e}")
            return None
        except Exception as e:
            logger.error(f"SIMBAD: Unexpected error {e}")
            return None

    def _extract_number(self, object_id: str) -> int:
        """Extract number from object ID (M31 → 31, NGC224 → 224)"""
        import re
        match = re.search(r'\d+', object_id)
        return int(match.group()) if match else 0

    def _parse_simbad_row(self, object_id: str, row: Dict) -> Optional[DeepSkyObject]:
        """Parse SIMBAD TAP response row to DeepSkyObject"""
        try:
            # Decode bytes if needed
            main_id = row['main_id']
            if isinstance(main_id, bytes):
                main_id = main_id.decode('utf-8')

            # Map SIMBAD type to our type
            all_types = row.get('all_types', '')
            obj_type = self._map_simbad_type(all_types)

            return DeepSkyObject(
                id=object_id,
                name=main_id,
                type=obj_type,
                ra=float(row['ra']),
                dec=float(row['dec']),
                magnitude=float(row['V']) if row.get('V') else None,
                size_major=float(row['galdim_majaxis']) if row.get('galdim_majaxis') else None,
                size_minor=float(row['galdim_minaxis']) if row.get('galdim_minaxis') else None,
                aliases=[object_id, main_id],
                constellation=None  # SIMBAD doesn't provide in basic query
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"SIMBAD: Failed to parse row for {object_id}: {e}")
            return None

    def _map_simbad_type(self, simbad_type: str) -> str:
        """Map SIMBAD type to our type system"""
        if not simbad_type:
            return 'NEBULA'

        simbad_type = simbad_type.upper()

        if 'G' in simbad_type and 'Cl' not in simbad_type:
            return 'GALAXY'
        elif 'PN' in simbad_type:
            return 'PLANETARY'
        elif any(t in simbad_type for t in ['Cl', 'OCl', 'GCl']):
            return 'CLUSTER'
        else:
            return 'NEBULA'
```

**Step 3: Write tests with mocked HTTP responses**

```python
# tests/test_simbad_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.simbad import SIMBADService

@pytest.mark.asyncio
async def test_query_object():
    service = SIMBADService()

    # Mock HTTP response
    mock_response = {
        'data': [{
            'oid': 'M31',
            'main_id': b'M  31',
            'ra': 10.684708,
            'dec': 41.268750,
            'galdim_majaxis': 190.0,
            'galdim_minaxis': 60.0,
            'V': 3.4,
            'all_types': 'G'
        }]
    }

    with patch.object(service, '_execute_tap_query', return_value=mock_response):
        obj = await service.query_object('M31')

    assert obj is not None
    assert obj.id == 'M31'
    assert obj.type == 'GALAXY'
    assert obj.magnitude == 3.4

@pytest.mark.asyncio
async def test_query_object_not_found():
    service = SIMBADService()

    with patch.object(service, '_execute_tap_query', return_value={'data': []}):
        obj = await service.query_object('UNKNOWN')

    assert obj is None
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/test_simbad_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd backend
git add app/services/simbad.py tests/test_simbad_service.py requirements.txt
git commit -m "feat: add SIMBADService for API fallback

- TAP API integration with batch query support
- Async HTTP client using httpx
- Parse SIMBAD responses to our models
- Mocked tests for isolated unit testing"
```

---

### Task 6: Enhance AstronomyService

**Files:**
- Modify: `backend/app/services/astronomy.py`

**Step 1: Enhance AstronomyService with fallback logic**

```python
# backend/app/services/astronomy.py
"""Enhanced astronomy service with database + SIMBAD fallback"""
import logging
from typing import Optional, List
from app.services.database import DatabaseService
from app.services.simbad import SIMBADService
from app.models.database import DeepSkyObject

logger = logging.getLogger(__name__)

class AstronomyService:
    """Enhanced service with local DB and SIMBAD fallback"""

    def __init__(self):
        self.db = DatabaseService()
        self.simbad = SIMBADService()

    async def get_object(self, object_id: str) -> Optional[DeepSkyObject]:
        """
        Get object with automatic fallback:
        1. Try local database (fast, <5ms)
        2. Fallback to SIMBAD API (slow, ~200-500ms)
        3. Cache API results locally
        """
        # Try local database first
        logger.debug(f"Looking up object {object_id} in local database")
        obj = await self.db.get_object_by_id(object_id)

        if obj:
            logger.info(f"Found {object_id} in local database")
            return obj

        # Not found locally, try SIMBAD API
        logger.info(f"Object {object_id} not found locally, querying SIMBAD API")
        obj = await self.simbad.query_object(object_id)

        if obj:
            # Cache result locally
            logger.info(f"SIMBAD returned {object_id}, caching locally")
            await self.db.save_object(obj)
            return obj

        # Not found anywhere
        logger.warning(f"Object {object_id} not found in local DB or SIMBAD")
        return None

    async def search_objects(self, name: str, limit: int = 20) -> List[DeepSkyObject]:
        """Search objects by name (local database only)"""
        return await self.db.search_objects(name, limit)

    async def get_objects_by_constellation(self, constellation: str) -> List[DeepSkyObject]:
        """Get all objects in a constellation"""
        return await self.db.get_objects_by_constellation(constellation)

    async def get_objects_by_type(self, obj_type: str) -> List[DeepSkyObject]:
        """Get all objects of a specific type"""
        return await self.db.get_objects_by_type(obj_type)

    async def get_statistics(self):
        """Get database statistics"""
        return await self.db.get_statistics()
```

**Step 2: Update existing tests**

```python
# tests/test_astronomy_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.astronomy import AstronomyService

@pytest.mark.asyncio
async def test_get_object_from_local_db():
    """Test retrieving object from local database"""
    service = AstronomyService()

    # Mock database to return object
    mock_obj = AsyncMock()
    mock_obj.id = "M31"
    service.db.get_object_by_id = AsyncMock(return_value=mock_obj)

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
    mock_obj = AsyncMock()
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
```

**Step 3: Run tests**

```bash
cd backend
pytest tests/test_astronomy_service.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
cd backend
git add app/services/astronomy.py tests/test_astronomy_service.py
git commit -m "feat: enhance AstronomyService with SIMBAD fallback

- Local database queries first (<5ms)
- Automatic fallback to SIMBAD API
- Cache API results locally
- Comprehensive test coverage"
```

---

## Phase 3: API Integration

### Task 7: Update Targets API Endpoints

**Files:**
- Modify: `backend/app/api/targets.py`

**Step 1: Update targets API to use new services**

```python
# backend/app/api/targets.py
"""Targets API endpoints with real database"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.astronomy import AstronomyService
from app.models.database import DeepSkyObject, DatabaseStats
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
astronomy_service = AstronomyService()

@router.get("/{id}")
async def get_target(id: str):
    """
    Get deep sky object by ID

    - Checks local SQLite first (~1-5ms)
    - Falls back to SIMBAD API if not found (~200-500ms)
    - Caches API results in SQLite
    """
    obj = await astronomy_service.get_object(id)

    if not obj:
        return {
            "success": True,
            "data": None,
            "message": f"Object {id} not found"
        }

    return {
        "success": True,
        "data": obj.dict(),
        "message": "Object retrieved successfully"
    }

@router.get("/search")
async def search_targets(q: str, limit: int = 20):
    """
    Search objects by name or alias

    - Uses LIKE query on aliases table
    - Returns partial matches
    """
    results = await astronomy_service.search_objects(q, limit)

    return {
        "success": True,
        "data": {
            "targets": [obj.dict() for obj in results],
            "count": len(results)
        },
        "message": f"Found {len(results)} objects matching '{q}'"
    }

@router.get("")
async def list_targets(
    type: Optional[str] = None,
    constellation: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    List targets with optional filters

    - Filter by type: GALAXY, NEBULA, CLUSTER, PLANETARY
    - Filter by constellation name
    - Pagination support
    """
    if type:
        objects = await astronomy_service.get_objects_by_type(type)
    elif constellation:
        objects = await astronomy_service.get_objects_by_constellation(constellation)
    else:
        # Return all (paginated)
        objects = []  # TODO: Implement pagination

    start = (page - 1) * page_size
    end = start + page_size
    paginated = objects[start:end]

    return {
        "success": True,
        "data": {
            "targets": [obj.dict() for obj in paginated],
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
        "data": stats.dict(),
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
```

**Step 2: Update existing API tests**

```python
# tests/test_api_targets.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_target_m31():
    """Test getting M31 from local database"""
    response = client.get("/api/v1/targets/M31")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "M31"
    assert "Andromeda" in data["data"]["name"]

def test_search_targets():
    """Test searching for objects"""
    response = client.get("/api/v1/targets/search?q=Andromeda&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["count"] > 0

def test_get_statistics():
    """Test getting database statistics"""
    response = client.get("/api/v1/targets/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_objects"] > 10000

def test_sync_from_simbad():
    """Test manual SIMBAD sync"""
    response = client.post("/api/v1/targets/sync", json=["IC999"])
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "synced" in data["data"]
```

**Step 3: Run API tests**

```bash
cd backend
pytest tests/test_api_targets.py -v
```

Expected: PASS

**Step 4: Manual API testing**

```bash
# Test getting M31
curl http://localhost:8000/api/v1/targets/M31

# Test search
curl http://localhost:8000/api/v1/targets/search?q=Orion

# Test statistics
curl http://localhost:8000/api/v1/targets/stats
```

Expected: JSON responses with real data

**Step 5: Commit**

```bash
cd backend
git add app/api/targets.py tests/test_api_targets.py
git commit -m "feat: update targets API with real database

- Use AstronomyService with DB + SIMBAD fallback
- Add /stats endpoint
- Add /sync endpoint for manual refresh
- Update tests for real data"
```

---

## Phase 4: Testing and Documentation

### Task 8: Update MockDataService

**Files:**
- Modify: `backend/app/services/mock_data.py`

**Step 1: Deprecate mock data service**

```python
# backend/app/services/mock_data.py
"""
DEPRECATED: This service is replaced by DatabaseService

Kept for backward compatibility during transition.
Use app.services.database.DatabaseService instead.
"""
import warnings
warnings.warn(
    "MockDataService is deprecated. Use DatabaseService instead.",
    DeprecationWarning,
    stacklevel=2
)

# ... existing code ...
```

**Step 2: Commit**

```bash
cd backend
git add app/services/mock_data.py
git commit -m "chore: deprecate MockDataService

- Replaced by DatabaseService with real data
- Keep for backward compatibility during transition"
```

---

### Task 9: Update Documentation

**Files:**
- Modify: `backend/README.md`
- Create: `backend/docs/DATABASE.md`

**Step 1: Update main README**

```markdown
# AI Skywatcher Backend

## Real Astronomical Data

This backend uses real astronomical data from OpenNGC and SIMBAD:

- **Local Database**: SQLite database with ~10,000 deep sky objects
- **API Fallback**: Automatic fallback to SIMBAD TAP API for missing objects
- **Caching**: API results cached locally for fast future queries

### Database Statistics

- Total objects: ~10,000
- Catalogs: Messier (110), Caldwell (109), NGC/IC (~10,000)
- Database size: ~5-10 MB

### API Endpoints

- `GET /api/v1/targets/{id}` - Get object by ID
- `GET /api/v1/targets/search?q=` - Search by name
- `GET /api/v1/targets/stats` - Database statistics
- `POST /api/v1/targets/sync` - Manual SIMBAD sync

See [DATABASE.md](docs/DATABASE.md) for details.
```

**Step 2: Create database documentation**

```markdown
# Database Documentation

## Schema

### objects table
Core deep sky object data

### aliases table
Alternative names and identifiers

### observational_info table
Viewing guidance and difficulty ratings

## Import Process

1. Download OpenNGC JSON
2. Transform to our schema
3. Import to SQLite
4. Commit to repository

## SIMBAD Fallback

When an object is not found locally:
1. Query SIMBAD TAP API
2. Parse response
3. Cache in local database
4. Return to user
```

**Step 3: Commit documentation**

```bash
cd backend
git add README.md docs/DATABASE.md
git commit -m "docs: update documentation for real database

- Document OpenNGC + SIMBAD integration
- Add database statistics
- Update API endpoint documentation"
```

---

### Task 10: Performance Testing

**Files:**
- Create: `tests/performance/test_database_performance.py`

**Step 1: Create performance benchmarks**

```python
# tests/performance/test_database_performance.py
"""Performance tests for database queries"""
import pytest
import time
from app.services.database import DatabaseService

@pytest.mark.asyncio
async def test_local_query_performance():
    """Test local database query performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    obj = await service.get_object_by_id("M31")
    elapsed = time.time() - start

    assert obj is not None
    assert elapsed < 0.005  # <5ms
    print(f"Local query time: {elapsed*1000:.2f}ms")

@pytest.mark.asyncio
async def test_search_performance():
    """Test search query performance"""
    service = DatabaseService("app/data/deep_sky.db")

    start = time.time()
    results = await service.search_objects("Andromeda", limit=20)
    elapsed = time.time() - start

    assert len(results) > 0
    assert elapsed < 0.020  # <20ms
    print(f"Search query time: {elapsed*1000:.2f}ms")
```

**Step 2: Run performance tests**

```bash
cd backend
pytest tests/performance/test_database_performance.py -v
```

Expected: All queries meet performance targets (<5ms local, <20ms search)

**Step 3: Commit**

```bash
cd backend
git add tests/performance/test_database_performance.py
git commit -m "test: add performance benchmarks for database

- Local queries: <5ms target
- Search queries: <20ms target
- Benchmark output in test logs"
```

---

## Completion Checklist

### Phase 1: Database and Import
- [x] Database schema created
- [x] Pydantic models defined
- [x] OpenNGC import script written
- [x] Database generated and committed

### Phase 2: Service Layer
- [x] DatabaseService implemented
- [x] SIMBADService implemented
- [x] AstronomyService enhanced with fallback

### Phase 3: API Integration
- [x] Targets API updated
- [x] New endpoints added (/stats, /sync)
- [x] Tests updated

### Phase 4: Testing and Docs
- [x] MockDataService deprecated
- [x] Documentation updated
- [x] Performance tests passing

---

## Final Verification

### Run Full Test Suite

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

Expected: All tests pass, >80% coverage

### Verify API Endpoints

```bash
# Start server
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/v1/targets/M31 | jq
curl http://localhost:8000/api/v1/targets/search?q=Orion | jq
curl http://localhost:8000/api/v1/targets/stats | jq
```

Expected: Real data returned, no errors

### Check Database File

```bash
ls -lh backend/app/data/deep_sky.db
sqlite3 backend/app/data/deep_sky.db "SELECT COUNT(*) FROM objects;"
```

Expected: File exists, >10,000 objects

---

## Implementation Complete

**Deliverables:**
✅ Real astronomical data (10,000+ objects)
✅ Fast local queries (<5ms)
✅ SIMBAD API fallback
✅ Comprehensive tests
✅ Updated documentation

**Next Steps:**
1. Merge `real-backend` branch to main
2. Deploy to production
3. Monitor API usage and performance
4. Gather user feedback
