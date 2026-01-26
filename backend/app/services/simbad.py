"""SIMBAD TAP API service for fallback queries"""
import httpx
import logging
import re
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

        simbad_type_upper = simbad_type.upper()

        if 'G' in simbad_type_upper and 'CL' not in simbad_type_upper:
            return 'GALAXY'
        elif 'PN' in simbad_type_upper:
            return 'PLANETARY'
        elif any(t.upper() in simbad_type_upper for t in ['Cl', 'OCl', 'GCl']):
            return 'CLUSTER'
        else:
            return 'NEBULA'
