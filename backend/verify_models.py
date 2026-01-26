#!/usr/bin/env python3
"""Quick verification script for database models"""
import sys
sys.path.insert(0, '/Users/rinzlacus/Downloads/Coding/ai-skywatcher/backend')

from app.models.database import DeepSkyObject, ObservationalInfo

# Test DeepSkyObject
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
print("✓ DeepSkyObject model works correctly")

# Test ObservationalInfo
info = ObservationalInfo(
    best_month=10,
    difficulty="EASY",
    min_aperture=50.0,
    notes="Visible to naked eye under dark skies"
)
assert info.best_month == 10
assert info.difficulty == "EASY"
print("✓ ObservationalInfo model works correctly")

print("\n✓ All models verified successfully!")
