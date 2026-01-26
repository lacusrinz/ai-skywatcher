#!/usr/bin/env python3
"""
OpenNGC → SQLite Import Script
Downloads OpenNGC CSV data and imports to SQLite database

Usage:
    python scripts/import_openngc.py

Output:
    backend/app/data/deep_sky.db
"""

import csv
import sqlite3
import urllib.request
import math
from pathlib import Path
from typing import Dict, List
from io import StringIO

# Configuration
OPENNGC_NGC_URL = "https://raw.githubusercontent.com/mattiaverga/OpenNGC/refs/heads/master/database_files/NGC.csv"
OPENNGC_ADDENDUM_URL = "https://raw.githubusercontent.com/mattiaverga/OpenNGC/refs/heads/master/database_files/addendum.csv"
DB_PATH = Path(__file__).parent.parent / "backend" / "app" / "data" / "deep_sky.db"
SCHEMA_PATH = Path(__file__).parent.parent / "backend" / "app" / "data" / "schema.sql"

def download_csv(url: str) -> List[Dict]:
    """Download OpenNGC CSV data"""
    print(f"Downloading from {url}...")
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
        # Parse CSV with semicolon delimiter
        reader = csv.DictReader(StringIO(content), delimiter=';')
        data = list(reader)
    print(f"✅ Downloaded {len(data)} objects")
    return data

def parse_ra_dec(ra_str: str, dec_str: str) -> tuple[float, float]:
    """Parse RA and Dec from HH:MM:SS.SS and +/-DD:MM:SS.SS format to degrees"""
    # RA: HH:MM:SS.SS → degrees
    try:
        h, m, s = ra_str.split(':')
        ra_deg = (float(h) + float(m)/60 + float(s)/3600) * 15
    except:
        ra_deg = 0.0

    # Dec: +/-DD:MM:SS.SS → degrees
    try:
        sign = -1 if dec_str.startswith('-') else 1
        d, m, s = dec_str[1:].split(':') if dec_str.startswith('+') or dec_str.startswith('-') else dec_str.split(':')
        dec_deg = sign * (float(d) + float(m)/60 + float(s)/3600)
    except:
        dec_deg = 0.0

    return ra_deg, dec_deg

def map_type(openngc_type: str) -> str:
    """Map OpenNGC type to our type system"""
    type_mapping = {
        'G': 'GALAXY', 'GPair': 'GALAXY', 'GTrpl': 'GALAXY', 'GGroup': 'GALAXY',
        'PN': 'PLANETARY',
        'OCl': 'CLUSTER', 'GCl': 'CLUSTER', '*Ass': 'CLUSTER', 'Cl+N': 'CLUSTER',
        '*': 'STAR',
        'HII': 'NEBULA', 'EmN': 'NEBULA', 'RfN': 'NEBULA', 'Neb': 'NEBULA',
        'DrkN': 'NEBULA', 'SNR': 'NEBULA'
    }
    return type_mapping.get(openngc_type, 'NEBULA')

def calculate_best_month(ra: float) -> int:
    """Calculate best viewing month from Right Ascension"""
    hour = ra / 15.0
    month = int((hour + 2) % 12) + 1
    return month

def calculate_difficulty(mag: float, size: float) -> str:
    """Calculate difficulty rating from magnitude and size"""
    if mag is None or size is None:
        return 'MODERATE'

    surface_brightness = mag + 2.5 * math.log10(size * size) if size > 0 else mag

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
    """Import objects from OpenNGC CSV data"""
    print("Importing objects...")

    objects = []
    aliases = []
    observational = []

    for item in data:
        # Parse name and ID
        name = item.get('Name', '')
        obj_type = item.get('Type', '')

        # Skip non-existent or duplicated objects
        if obj_type in ['NonEx', 'Dup']:
            continue

        # Generate primary ID
        if name.startswith('NGC'):
            obj_id = name
        elif name.startswith('IC'):
            obj_id = name
        elif name.startswith('M'):
            obj_id = name
        else:
            continue

        # Parse coordinates
        ra_str = item.get('RA', '0:0:0')
        dec_str = item.get('Dec', '+0:0:0')
        ra, dec = parse_ra_dec(ra_str, dec_str)

        # Parse magnitude (prefer V-Mag, then B-Mag)
        mag_str = item.get('V-Mag') or item.get('B-Mag') or ''
        magnitude = float(mag_str) if mag_str else None

        # Parse size (major axis in arcmin)
        size_str = item.get('MajAx', '') or item.get('MinAx', '')
        size_major = float(size_str) if size_str else None

        size_str = item.get('MinAx', '')
        size_minor = float(size_str) if size_str else size_major

        # Parse surface brightness (for galaxies)
        surf_br = item.get('SurfBr', '')
        surface_brightness = float(surf_br) if surf_br else None

        # Extract common name
        common_name = item.get('Common names', '')
        display_name = common_name if common_name else name

        # Extract object data
        obj = {
            'id': obj_id,
            'name': display_name,
            'type': map_type(obj_type),
            'ra': ra,
            'dec': dec,
            'magnitude': magnitude,
            'size_major': size_major,
            'size_minor': size_minor,
            'constellation': item.get('Const', ''),
            'surface_brightness': surface_brightness
        }
        objects.append(obj)

        # Extract identifiers as aliases
        identifiers = item.get('Identifiers', '')
        if identifiers:
            for alias in identifiers.split(','):
                alias = alias.strip()
                if alias:
                    aliases.append({
                        'object_id': obj_id,
                        'alias': alias
                    })

        # Add cross-references (M, NGC, IC columns)
        for col in ['M', 'NGC', 'IC']:
            cross_ref = item.get(col, '')
            if cross_ref:
                aliases.append({
                    'object_id': obj_id,
                    'alias': f"{col}{cross_ref}"
                })

        # Generate observational info
        obs_info = {
            'object_id': obj_id,
            'best_month': calculate_best_month(ra),
            'difficulty': calculate_difficulty(magnitude, size_major),
            'min_aperture': estimate_aperture(magnitude),
            'notes': f"{map_type(obj_type)}"
        }
        observational.append(obs_info)

    # Batch insert
    conn.executemany(
        "INSERT INTO objects (id, name, type, ra, dec, magnitude, size_major, size_minor, constellation, surface_brightness) "
        "VALUES (:id, :name, :type, :ra, :dec, :magnitude, :size_major, :size_minor, :constellation, :surface_brightness)",
        objects
    )

    conn.executemany(
        "INSERT OR IGNORE INTO aliases (object_id, alias) VALUES (:object_id, :alias)",
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

    # Download data from both files
    print("\nDownloading NGC.csv...")
    ngc_data = download_csv(OPENNGC_NGC_URL)

    print("\nDownloading addendum.csv...")
    addendum_data = download_csv(OPENNGC_ADDENDUM_URL)

    # Combine data
    all_data = ngc_data + addendum_data

    # Create database
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    # Create schema
    create_database(conn)

    # Import data
    import_objects(conn, all_data)

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
