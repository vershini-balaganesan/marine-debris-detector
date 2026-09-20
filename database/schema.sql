-- database/schema.sql
-- Run once to create all tables for the prototype.

CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    image_name VARCHAR(255) NOT NULL,
    image_path TEXT NOT NULL,
    debris_type VARCHAR(100) NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    location_name VARCHAR(255),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    zone_id VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS zones (
    zone_id VARCHAR(255) PRIMARY KEY,
    centroid_latitude DOUBLE PRECISION NOT NULL,
    centroid_longitude DOUBLE PRECISION NOT NULL,
    total_count INTEGER NOT NULL DEFAULT 0,
    dominant_debris VARCHAR(100),
    class_breakdown JSONB,
    risk_level VARCHAR(20),
    trend VARCHAR(20),
    recommendation TEXT,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS zone_history (
    id SERIAL PRIMARY KEY,
    zone_id VARCHAR(255) NOT NULL REFERENCES zones(zone_id),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS uploads (
    id SERIAL PRIMARY KEY,
    image_name VARCHAR(255) NOT NULL,
    image_path TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_detections_zone_id ON detections(zone_id);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS location_name VARCHAR(255);
ALTER TABLE detections ALTER COLUMN zone_id TYPE VARCHAR(255);
UPDATE detections
SET location_name = latitude::TEXT || ',' || longitude::TEXT
WHERE location_name IS NULL;