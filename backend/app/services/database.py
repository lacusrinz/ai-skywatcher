"""Local SQLite database service for deep sky objects"""
import aiosqlite
import logging
from pathlib import Path
from typing import Optional, List
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
        """Get all objects of a specific type (optimized with JOIN)"""
        conn = await self.connect()

        # Single query with JOIN to get all data at once
        query = """
            SELECT
                o.id, o.name, o.type, o.ra, o.dec, o.magnitude,
                o.size_major, o.size_minor, o.constellation, o.surface_brightness,
                oi.best_month, oi.difficulty, oi.min_aperture, oi.notes as obs_notes,
                GROUP_CONCAT(a.alias, ',') as aliases_str
            FROM objects o
            LEFT JOIN observational_info oi ON o.id = oi.object_id
            LEFT JOIN aliases a ON o.id = a.object_id
            WHERE o.type = ?
            GROUP BY o.id
        """
        cursor = await conn.execute(query, (obj_type,))
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            try:
                # Parse aliases
                aliases_str = row['aliases_str']
                aliases = aliases_str.split(',') if aliases_str else []

                # Create observational info
                obs_info = None
                if row['obs_notes']:
                    obs_info = ObservationalInfo(
                        best_month=row['best_month'],
                        difficulty=row['difficulty'],
                        min_aperture=row['min_aperture'],
                        min_magnitude=None,
                        notes=row['obs_notes']
                    )

                obj = DeepSkyObject(
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
                    observational_info=obs_info
                )
                results.append(obj)
            except Exception as e:
                logger.error(f"Error parsing row {row['id']}: {e}")
                continue

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
