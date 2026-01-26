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
